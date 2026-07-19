"""GitHub Pulls-style inbox with categorized panels."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, LoadingIndicator, Static

from rplusview.github_client import (
    INBOX_SECTIONS,
    check_summary,
    get_inbox,
    inbox_action_label,
    pr_comments,
)
from rplusview.safe import open_github_url, user_facing_error
from rplusview.widget.help_screen import HelpScreen
from rplusview.widget.status_bar import StatusBar
from rplusview.widget.title_bar import TitleBar
from rplusview.widget.vim_nav import VIM_NAV_BINDINGS, VimDataTable, VimNavMixin


class InboxScreen(VimNavMixin, Screen):
    """Inbox panels: drafts, needs action, review requests, etc."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("o", "open_browser", "Browser", show=False),
        Binding("question_mark", "help", "Help", show=False),
        *VIM_NAV_BINDINGS,
    ]

    def __init__(self, username: str) -> None:
        super().__init__()
        self.username = username
        self._inbox: dict[str, list[dict[str, Any]]] = {key: [] for key, _ in INBOX_SECTIONS}
        self._expanded: dict[str, bool] = {
            "needs_review": False,
            "needs_team_review": False,
            "drafts": True,
            "waiting": False,
            "needs_action": True,
            "ready": False,
        }
        self._active_section = "drafts"
        self._pr_by_url: dict[str, dict[str, Any]] = {}

    def compose(self) -> ComposeResult:
        yield TitleBar("RPlusView", "inbox")
        with Vertical(id="inbox-root"):
            with Vertical(id="inbox-loading"):
                yield LoadingIndicator()
                yield Static("Loading inbox…", id="inbox-loading-label")
            with VerticalScroll(id="inbox-scroll"):
                yield Static("", id="inbox-header", markup=True)
                for key, title in INBOX_SECTIONS:
                    with Vertical(classes="inbox-section", id=f"sec-{key}"):
                        yield Button(
                            f"▸ {title}  0",
                            id=f"hdr-{key}",
                            classes="inbox-header-btn",
                            flat=True,
                            compact=True,
                        )
                        yield VimDataTable(
                            id=f"tbl-{key}",
                            classes="inbox-table",
                        )
        yield StatusBar()

    def on_mount(self) -> None:
        self.query_one("#inbox-scroll").display = False
        for key, _ in INBOX_SECTIONS:
            table = self.query_one(f"#tbl-{key}", VimDataTable)
            table.cursor_type = "row"
            table.zebra_stripes = True
            table.add_columns("Title", "Repo", "Status", "Checks", "Comments", "Updated")
            table.display = self._expanded[key]
        self.query_one(StatusBar).set_message(
            " j/k gg G  ctrl+d/u  ctrl+f/b  Enter/o Open   r Refresh   Esc/q Back "
        )
        self.action_refresh()

    def action_refresh(self) -> None:
        self.query_one("#inbox-loading").display = True
        self.query_one("#inbox-scroll").display = False
        self.query_one(StatusBar).set_message(f"Fetching inbox for @{self.username}…")
        self.load_inbox()

    @work(exclusive=True, thread=True)
    def load_inbox(self) -> None:
        try:
            data, warnings = get_inbox(self.username)
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._on_error, user_facing_error(exc))
            return
        self.app.call_from_thread(self._on_loaded, data, warnings)

    def _on_error(self, message: str) -> None:
        self.query_one("#inbox-loading").display = False
        self.query_one("#inbox-scroll").display = True
        self.query_one("#inbox-header", Static).update(
            f"[bold red]Failed to load inbox[/]\n[dim]{message}[/]"
        )
        self.notify(message, severity="error", timeout=6)

    def _on_loaded(
        self,
        data: dict[str, list[dict[str, Any]]],
        warnings: list[str] | None = None,
    ) -> None:
        self._inbox = data
        self._pr_by_url = {}
        total = 0
        for key, _ in INBOX_SECTIONS:
            items = data.get(key) or []
            total += len(items)
            if items and key in {"drafts", "needs_action", "needs_review", "waiting"}:
                self._expanded[key] = True
            self._fill_section(key, items)

        warn_bits = ""
        if warnings:
            warn_bits = " · [bold #d29922]partial[/]"
            for msg in warnings:
                self.notify(msg, severity="warning", timeout=5)

        self.query_one("#inbox-header", Static).update(
            f"[bold]Inbox[/]  [dim]@{self.username} · {total} items · "
            f"Updated: open PRs[/]{warn_bits}"
        )
        self.query_one(TitleBar).set_meta(f"@{self.username} · inbox · {total} items")
        self.query_one("#inbox-loading").display = False
        self.query_one("#inbox-scroll").display = True
        self.query_one(StatusBar).set_message(
            " j/k gg G  ctrl+d/u  click section to expand   r Refresh   Esc/q Back "
        )
        self._focus_first_table()

    def _fill_section(self, key: str, items: list[dict[str, Any]]) -> None:
        title = dict(INBOX_SECTIONS)[key]
        chevron = "▾" if self._expanded[key] else "▸"
        btn = self.query_one(f"#hdr-{key}", Button)
        btn.label = f"{chevron} {title}  {len(items)}"

        table = self.query_one(f"#tbl-{key}", VimDataTable)
        table.clear()
        table.display = self._expanded[key] and bool(items)
        # Keep empty expanded sections hidden to save space
        if self._expanded[key] and not items:
            table.display = False

        for pr in items:
            url = pr.get("url") or ""
            self._pr_by_url[url] = pr
            action = inbox_action_label(pr, section=key)
            checks, check_style = check_summary(pr)
            author = (pr.get("author") or {}).get("login") or ""
            repo = pr.get("repository", {}).get("nameWithOwner") or ""
            meta_title = Text(pr.get("title") or "")
            repo_cell = Text(f"{repo}#{pr.get('number')}  @{author}", style="#8b9bb0")
            table.add_row(
                meta_title,
                repo_cell,
                Text(action, style=_action_style(action)),
                Text(checks, style=check_style),
                str(pr_comments(pr)),
                (f"Updated {pr['updatedAt'][:10]}" if pr.get("updatedAt") else ""),
                key=url,
            )

    def _focus_first_table(self) -> None:
        for key, _ in INBOX_SECTIONS:
            table = self.query_one(f"#tbl-{key}", VimDataTable)
            if table.display and table.row_count:
                self._active_section = key
                table.focus()
                return

    def _toggle_section(self, key: str) -> None:
        self._expanded[key] = not self._expanded[key]
        items = self._inbox.get(key) or []
        self._fill_section(key, items)

    @on(Button.Pressed)
    def on_header_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("hdr-"):
            key = bid[4:]
            if key in self._expanded:
                self._toggle_section(key)

    @on(VimDataTable.RowSelected)
    def on_row_selected(self, event: VimDataTable.RowSelected) -> None:
        url = str(event.row_key.value)
        if not url:
            return
        if not open_github_url(url):
            self.notify("Blocked non-GitHub URL", severity="warning", timeout=3)
            return
        self.notify("Opened in browser", timeout=2)

    def _vim_table(self) -> VimDataTable | None:
        return self._active_table()

    def _active_table(self) -> VimDataTable | None:
        focused = self.focused
        if isinstance(focused, VimDataTable) and (focused.id or "").startswith("tbl-"):
            self._active_section = (focused.id or "")[4:]
            return focused
        table = self.query_one(f"#tbl-{self._active_section}", VimDataTable)
        if table.display and table.row_count:
            return table
        return None

    def action_open_browser(self) -> None:
        table = self._active_table()
        if not table or table.row_count == 0:
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        url = str(row_key.value)
        if not url:
            return
        if not open_github_url(url):
            self.notify("Blocked non-GitHub URL", severity="warning", timeout=3)
            return
        self.notify("Opened in browser", timeout=2)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())


def _action_style(label: str) -> str:
    styles = {
        "Not ready": "#8b9bb0",
        "Changes requested": "#f85149",
        "Merge conflicts": "#d29922",
        "Approved": "#3dd68c",
        "Ready to merge": "#3dd68c",
        "Review requested": "#58a6ff",
        "Review required": "#d29922",
        "Waiting": "#8b9bb0",
    }
    return styles.get(label, "#8b9bb0")
