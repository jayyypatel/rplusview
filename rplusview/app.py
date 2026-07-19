"""RPlusView — terminal GitHub PR dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Button, Input, LoadingIndicator, Static

from rplusview.config import get_saved_username, set_saved_username
from rplusview.github_client import (
    SORT_MODES,
    get_pr_detail,
    get_prs,
    get_username,
    pr_comments,
    pr_loc,
    pr_status,
    search_prs,
    sort_prs,
)
from rplusview.odoo_task import open_odoo_task, pr_task_id, pr_task_label, title_without_task
from rplusview.safe import open_github_url, user_facing_error, validate_github_username
from rplusview.screens import InboxScreen, PRDetailScreen, ReposScreen, StatsScreen
from rplusview.widget import ActionBar, HelpScreen, SetupScreen, StatusBar, TitleBar, VimDataTable
from rplusview.widget.vim_nav import VIM_NAV_BINDINGS, VimNavMixin

PRFilter = Literal["open", "closed"]


def _task_cell(pr: dict[str, Any]) -> Text:
    label = pr_task_label(pr)
    if not label:
        return Text("—", style="#8b9bb0")
    return Text(label, style="bold #d29922")


def _status_cell(status: str) -> Text:
    styles = {
        "Open": "bold #3fb950",
        "Draft": "bold #8b9bb0",
        "Merged": "bold #a371f7",
        "Closed": "bold #f85149",
    }
    return Text(status, style=styles.get(status, ""))


def _diff_cell(value: int, sign: str) -> Text:
    style = "#3fb950" if sign == "+" else "#f85149"
    return Text(f"{sign}{value}", style=style)


def _comments_cell(count: int) -> Text:
    if count <= 0:
        return Text("0", style="#8b9bb0")
    if count < 5:
        return Text(str(count), style="bold #58a6ff")
    if count < 15:
        return Text(str(count), style="bold #d29922")
    return Text(str(count), style="bold #f778ba")


class RPlusView(VimNavMixin, App):
    CSS_PATH = str(Path(__file__).with_name("rplusview.tcss"))
    TITLE = "RPlusView"
    BINDINGS = [
        Binding("q", "quit", "Quit", show=False),
        Binding("question_mark", "help", "Help", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("slash", "focus_search", "Search", show=False),
        Binding("s", "cycle_sort", "Sort", show=False),
        Binding("o", "open_browser", "Browser", show=False),
        Binding("p", "open_odoo_task", "Task", show=False),
        Binding("d", "open_details", "Details", show=False),
        Binding("t", "open_stats", "Stats", show=False),
        Binding("e", "open_repos", "Repos", show=False),
        Binding("i", "open_inbox", "Inbox", show=False),
        Binding("c", "toggle_closed", "Closed", show=False),
        Binding("u", "change_user", "User", show=False),
        Binding("escape", "clear_search", "Clear", show=False),
        *VIM_NAV_BINDINGS,
    ]

    def __init__(self) -> None:
        super().__init__()
        self._prs: list[dict[str, Any]] = []
        self._query = ""
        self._sort = "loc"
        self._pr_filter: PRFilter = "open"
        self._username: str | None = get_saved_username()

    def compose(self) -> ComposeResult:
        yield TitleBar("RPlusView", "pull requests")
        yield ActionBar()
        yield Input(
            placeholder="Search title, repo, #number, status…  (Esc to clear)",
            id="search-input",
        )
        with Container(id="body"):
            with Vertical(id="loading-pane"):
                yield LoadingIndicator()
                yield Static("Fetching pull requests…", id="loading-label")
            yield VimDataTable(id="pr-table")
        yield StatusBar()

    def on_mount(self) -> None:
        search = self.query_one("#search-input", Input)
        search.display = False

        table = self.query_one("#pr-table", VimDataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.show_header = True
        table.add_columns(
            "#",
            "Repository",
            "Title",
            "Task",
            "+",
            "-",
            "LOC",
            "Files",
            "Comments",
            "Status",
            "Created",
        )
        table.display = False
        self._sync_closed_button()

        if self._username:
            self.action_refresh()
        else:
            self._show_loading(False)
            self.query_one(TitleBar).set_meta("setup required")
            self.query_one(StatusBar).set_message(" Enter your GitHub username to begin ")
            self._open_setup(first_run=True)

    # ── actions ──────────────────────────────────────────────

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_quit(self) -> None:
        if len(self.screen_stack) > 1:
            self.pop_screen()
            return
        self.exit()

    def action_change_user(self) -> None:
        self._open_setup(first_run=False)

    def action_refresh(self) -> None:
        if not self._username:
            self._open_setup(first_run=True)
            return
        self._show_loading(True)
        label = "open" if self._pr_filter == "open" else "closed"
        self.query_one("#loading-label", Static).update(f"Fetching {label} pull requests…")
        self.query_one(StatusBar).set_message(f"Fetching {label} PRs for @{self._username}…")
        self.load_prs()

    def action_toggle_closed(self) -> None:
        self._pr_filter = "closed" if self._pr_filter == "open" else "open"
        self._sync_closed_button()
        mode = "closed / merged" if self._pr_filter == "closed" else "open"
        self.notify(f"Showing {mode} PRs", timeout=1.5)
        self.action_refresh()

    def action_focus_search(self) -> None:
        search = self.query_one("#search-input", Input)
        search.display = True
        search.focus()

    def action_clear_search(self) -> None:
        search = self.query_one("#search-input", Input)
        if search.has_focus or self._query or search.display:
            search.value = ""
            self._query = ""
            search.display = False
            self._render_table()
            self.query_one("#pr-table", VimDataTable).focus()

    def action_cycle_sort(self) -> None:
        idx = SORT_MODES.index(self._sort) if self._sort in SORT_MODES else 0
        self._sort = SORT_MODES[(idx + 1) % len(SORT_MODES)]
        self._render_table()
        self.notify(f"Sort: {self._sort.upper()}", timeout=1.5)

    def action_open_browser(self) -> None:
        pr = self._selected_pr()
        if not pr:
            return
        if not open_github_url(pr.get("url") or ""):
            self.notify("Blocked non-GitHub URL", severity="warning", timeout=3)
            return
        self.notify(f"Opened #{pr.get('number')} in browser", timeout=2)

    def action_open_odoo_task(self) -> None:
        pr = self._selected_pr()
        if not pr:
            return
        task_id = pr_task_id(pr)
        if task_id:
            self._open_task_id(task_id)
            return
        # List payload may omit body; fetch details then open.
        self.notify("Looking up task in PR description…", timeout=1.5)
        self.resolve_odoo_task(pr)

    def _open_task_id(self, task_id: str) -> None:
        if not open_odoo_task(task_id):
            self.notify("Could not open Odoo task URL", severity="error", timeout=3)
            return
        self.notify(f"Opened task-{task_id} on Odoo", timeout=2)

    def _merge_pr_cache(self, pr: dict[str, Any], detail: dict[str, Any]) -> None:
        """Update the in-memory PR so Task column / later opens see the body."""
        patch = {
            key: detail[key]
            for key in ("body", "title", "headRefName")
            if detail.get(key) is not None
        }
        if not patch:
            return
        pr.update(patch)
        url = pr.get("url")
        if not url:
            return
        for i, cached in enumerate(self._prs):
            if cached.get("url") == url:
                self._prs[i] = {**cached, **patch}
                break

    @work(exclusive=True, thread=True)
    def resolve_odoo_task(self, pr: dict[str, Any]) -> None:
        detail = get_pr_detail(pr)
        task_id = pr_task_id(detail)
        self.call_from_thread(self._on_odoo_task_resolved, pr, detail, task_id)

    def _on_odoo_task_resolved(
        self,
        pr: dict[str, Any],
        detail: dict[str, Any],
        task_id: str | None,
    ) -> None:
        self._merge_pr_cache(pr, detail)
        self._render_table()
        if not task_id:
            self.notify("No task-XXXX found in this PR", severity="warning", timeout=2)
            return
        self._open_task_id(task_id)

    def action_open_details(self) -> None:
        pr = self._selected_pr()
        if pr:
            self.push_screen(PRDetailScreen(pr))

    def action_open_stats(self) -> None:
        if not self._prs:
            self.notify("No PRs loaded yet", severity="warning")
            return
        self.push_screen(StatsScreen(self._prs))

    def action_open_repos(self) -> None:
        if not self._prs:
            self.notify("No PRs loaded yet", severity="warning")
            return
        self.push_screen(ReposScreen(self._prs))

    def action_open_inbox(self) -> None:
        if not self._username:
            self.notify("Set a username first", severity="warning")
            return
        self.push_screen(InboxScreen(self._username))

    def _vim_nav_blocked(self) -> bool:
        search = self.query_one("#search-input", Input)
        return bool(search.display and search.has_focus)

    def _vim_table(self) -> VimDataTable | None:
        table = self.query_one("#pr-table", VimDataTable)
        if table.display and table.row_count:
            return table
        return None

    def action_vim_search_next(self) -> None:
        if not self._query:
            self.notify("Use / to search first", timeout=1.5)
            return
        super().action_vim_search_next()

    def action_vim_search_prev(self) -> None:
        if not self._query:
            self.notify("Use / to search first", timeout=1.5)
            return
        super().action_vim_search_prev()

    # ── events ───────────────────────────────────────────────

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "btn-open": self.action_open_browser,
            "btn-task": self.action_open_odoo_task,
            "btn-details": self.action_open_details,
            "btn-inbox": self.action_open_inbox,
            "btn-closed": self.action_toggle_closed,
            "btn-stats": self.action_open_stats,
            "btn-repos": self.action_open_repos,
            "btn-search": self.action_focus_search,
            "btn-sort": self.action_cycle_sort,
            "btn-refresh": self.action_refresh,
            "btn-user": self.action_change_user,
            "btn-help": self.action_help,
        }
        handler = actions.get(event.button.id or "")
        if handler:
            handler()

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        self._query = event.value
        self._render_table()

    @on(Input.Submitted, "#search-input")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        self.query_one("#pr-table", VimDataTable).focus()

    @on(VimDataTable.RowSelected, "#pr-table")
    def on_row_selected(self, event: VimDataTable.RowSelected) -> None:
        pr = self._pr_by_key(str(event.row_key.value))
        if pr:
            self.push_screen(PRDetailScreen(pr))

    # ── setup ────────────────────────────────────────────────

    def _open_setup(self, *, first_run: bool) -> None:
        self.push_screen(SetupScreen(first_run=first_run), self._on_setup_done)

    def _on_setup_done(self, username: str | None) -> None:
        if not username:
            return
        try:
            username = validate_github_username(username)
            set_saved_username(username)
        except ValueError as exc:
            self.notify(user_facing_error(exc), severity="error", timeout=5)
            return
        self._username = username
        self.notify(f"Tracking @{username}", timeout=2)
        self.action_refresh()

    def _sync_closed_button(self) -> None:
        try:
            btn = self.query_one("#btn-closed", Button)
        except Exception:  # noqa: BLE001
            return
        if self._pr_filter == "closed":
            btn.label = "Open PRs"
        else:
            btn.label = "Closed"

    # ── data ─────────────────────────────────────────────────

    def _show_loading(self, visible: bool) -> None:
        self.query_one("#loading-pane").display = visible
        self.query_one("#pr-table", VimDataTable).display = not visible

    @work(exclusive=True, thread=True)
    def load_prs(self) -> None:
        try:
            username = self._username or get_username()
            if not username:
                raise RuntimeError("No GitHub username configured.")
            username = validate_github_username(username)
            prs = get_prs(username, state=self._pr_filter)
        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._on_load_error, user_facing_error(exc))
            return
        self.call_from_thread(self._on_load_success, prs, username)

    def _on_load_error(self, message: str) -> None:
        self._show_loading(False)
        self.query_one(TitleBar).set_meta("error")
        self.query_one(StatusBar).set_message(f"Error: {message}")
        self.notify(message, severity="error", timeout=8)

    def _on_load_success(self, prs: list[dict[str, Any]], username: str) -> None:
        self._prs = prs
        self._username = username
        self._show_loading(False)
        self._render_table()
        self.query_one(StatusBar).reset()
        table = self.query_one("#pr-table", VimDataTable)
        if table.row_count:
            table.focus()

    def _visible_prs(self) -> list[dict[str, Any]]:
        return sort_prs(search_prs(self._prs, self._query), self._sort)

    def _render_table(self) -> None:
        table = self.query_one("#pr-table", VimDataTable)
        visible = self._visible_prs()
        table.clear()

        open_n = merged_n = closed_n = draft_n = 0
        for pr in self._prs:
            st = pr_status(pr)
            if st == "Open":
                open_n += 1
            elif st == "Draft":
                draft_n += 1
            elif st == "Merged":
                merged_n += 1
            else:
                closed_n += 1

        for pr in visible:
            status = pr_status(pr)
            repo = (pr.get("repository") or {}).get("nameWithOwner") or "?"
            title = title_without_task(pr.get("title"))
            number = pr.get("number") or 0
            created = str(pr.get("createdAt") or "")[:10]
            url = pr.get("url") or f"{repo}#{number}"
            table.add_row(
                Text(f"#{number}", style="bold"),
                repo,
                title,
                _task_cell(pr),
                _diff_cell(int(pr.get("additions") or 0), "+"),
                _diff_cell(int(pr.get("deletions") or 0), "-"),
                str(pr_loc(pr)),
                str(pr.get("changedFiles") or 0),
                _comments_cell(pr_comments(pr)),
                _status_cell(status),
                created,
                key=url,
            )

        user = f"@{self._username}" if self._username else "—"
        bits = [
            user,
            f"{len(visible)}/{len(self._prs)} PRs",
            f"view:{self._pr_filter}",
            f"sort:{self._sort}",
        ]
        if self._query:
            bits.append(f"search:“{self._query}”")
        if self._pr_filter == "open":
            bits.append(f"{open_n} open · {draft_n} draft")
        else:
            bits.append(f"{merged_n} merged · {closed_n} closed")
        self.query_one(TitleBar).set_meta(" · ".join(bits))

    def _selected_pr(self) -> dict[str, Any] | None:
        table = self.query_one("#pr-table", VimDataTable)
        if table.row_count == 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        return self._pr_by_key(str(row_key.value))

    def _pr_by_key(self, url: str) -> dict[str, Any] | None:
        for pr in self._prs:
            if pr.get("url") == url:
                return pr
        return None


def main() -> None:
    RPlusView().run()


if __name__ == "__main__":
    main()
