"""RPlusView — terminal GitHub PR dashboard."""

from __future__ import annotations

import webbrowser
from pathlib import Path
from typing import Any

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Button, DataTable, Input, LoadingIndicator, Static

from rplusview.config import get_saved_username, set_saved_username
from rplusview.github_client import (
    SORT_MODES,
    get_prs,
    get_username,
    pr_loc,
    pr_status,
    search_prs,
    sort_prs,
)
from rplusview.screens import PRDetailScreen, ReposScreen, StatsScreen
from rplusview.widget import ActionBar, HelpScreen, StatusBar, TitleBar
from rplusview.widget.setup_screen import SetupScreen


def _status_cell(status: str) -> Text:
    styles = {"Open": "bold #3fb950", "Merged": "bold #a371f7", "Closed": "bold #f85149"}
    return Text(status, style=styles.get(status, ""))


def _diff_cell(value: int, sign: str) -> Text:
    style = "#3fb950" if sign == "+" else "#f85149"
    return Text(f"{sign}{value}", style=style)


class RPlusView(App):
    CSS_PATH = str(Path(__file__).with_name("rplusview.tcss"))
    TITLE = "RPlusView"
    BINDINGS = [
        Binding("q", "quit", "Quit", show=False),
        Binding("question_mark", "help", "Help", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("slash", "focus_search", "Search", show=False),
        Binding("s", "cycle_sort", "Sort", show=False),
        Binding("o", "open_browser", "Browser", show=False),
        Binding("d", "open_details", "Details", show=False),
        Binding("t", "open_stats", "Stats", show=False),
        Binding("e", "open_repos", "Repos", show=False),
        Binding("u", "change_user", "User", show=False),
        Binding("escape", "clear_search", "Clear", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._prs: list[dict[str, Any]] = []
        self._query = ""
        self._sort = "loc"
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
            yield DataTable(id="pr-table")
        yield StatusBar()

    def on_mount(self) -> None:
        search = self.query_one("#search-input", Input)
        search.display = False

        table = self.query_one("#pr-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.show_header = True
        table.add_columns(
            "#",
            "Repository",
            "Title",
            "+",
            "-",
            "LOC",
            "Files",
            "Status",
            "Created",
        )
        table.display = False

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
        self.query_one(StatusBar).set_message(f"Fetching PRs for @{self._username}…")
        self.load_prs()

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
            self.query_one("#pr-table", DataTable).focus()

    def action_cycle_sort(self) -> None:
        idx = SORT_MODES.index(self._sort) if self._sort in SORT_MODES else 0
        self._sort = SORT_MODES[(idx + 1) % len(SORT_MODES)]
        self._render_table()
        self.notify(f"Sort: {self._sort.upper()}", timeout=1.5)

    def action_open_browser(self) -> None:
        pr = self._selected_pr()
        if not pr:
            return
        webbrowser.open(pr["url"])
        self.notify(f"Opened #{pr['number']} in browser", timeout=2)

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

    # ── events ───────────────────────────────────────────────

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "btn-open": self.action_open_browser,
            "btn-details": self.action_open_details,
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
        self.query_one("#pr-table", DataTable).focus()

    @on(DataTable.RowSelected, "#pr-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        pr = self._pr_by_key(str(event.row_key.value))
        if pr:
            self.push_screen(PRDetailScreen(pr))

    # ── setup ────────────────────────────────────────────────

    def _open_setup(self, *, first_run: bool) -> None:
        self.push_screen(SetupScreen(first_run=first_run), self._on_setup_done)

    def _on_setup_done(self, username: str | None) -> None:
        if not username:
            return
        set_saved_username(username)
        self._username = username
        self.notify(f"Tracking @{username}", timeout=2)
        self.action_refresh()

    # ── data ─────────────────────────────────────────────────

    def _show_loading(self, visible: bool) -> None:
        self.query_one("#loading-pane").display = visible
        self.query_one("#pr-table", DataTable).display = not visible

    @work(exclusive=True, thread=True)
    def load_prs(self) -> None:
        try:
            username = self._username or get_username()
            if not username:
                raise RuntimeError("No username configured")
            prs = get_prs(username)
        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(self._on_load_error, str(exc))
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
        table = self.query_one("#pr-table", DataTable)
        if table.row_count:
            table.focus()

    def _visible_prs(self) -> list[dict[str, Any]]:
        return sort_prs(search_prs(self._prs, self._query), self._sort)

    def _render_table(self) -> None:
        table = self.query_one("#pr-table", DataTable)
        visible = self._visible_prs()
        table.clear()

        open_n = merged_n = closed_n = 0
        for pr in self._prs:
            st = pr_status(pr)
            if st == "Open":
                open_n += 1
            elif st == "Merged":
                merged_n += 1
            else:
                closed_n += 1

        for pr in visible:
            status = pr_status(pr)
            table.add_row(
                Text(f"#{pr['number']}", style="bold"),
                pr["repository"]["nameWithOwner"],
                pr["title"],
                _diff_cell(pr["additions"], "+"),
                _diff_cell(pr["deletions"], "-"),
                str(pr_loc(pr)),
                str(pr["changedFiles"]),
                _status_cell(status),
                pr["createdAt"][:10],
                key=pr["url"],
            )

        user = f"@{self._username}" if self._username else "—"
        bits = [
            user,
            f"{len(visible)}/{len(self._prs)} PRs",
            f"sort:{self._sort}",
        ]
        if self._query:
            bits.append(f"search:“{self._query}”")
        bits.append(f"{open_n} open · {merged_n} merged · {closed_n} closed")
        self.query_one(TitleBar).set_meta(" · ".join(bits))

    def _selected_pr(self) -> dict[str, Any] | None:
        table = self.query_one("#pr-table", DataTable)
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
