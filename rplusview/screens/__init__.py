"""Secondary screens for RPlusView."""

from __future__ import annotations

import webbrowser
from typing import Any

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, LoadingIndicator, Static

from rplusview.github_client import (
    compute_stats,
    get_pr_detail,
    group_by_repo,
    pr_loc,
    pr_status,
)
from rplusview.widget.help_screen import HelpScreen
from rplusview.widget.status_bar import StatusBar
from rplusview.widget.title_bar import TitleBar


def _open_url(url: str) -> None:
    if url:
        webbrowser.open(url)


class PRDetailScreen(Screen):
    """Full pull-request detail view."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("o", "open_browser", "Browser", show=False),
        Binding("question_mark", "help", "Help", show=False),
    ]

    def __init__(self, pr: dict[str, Any]) -> None:
        super().__init__()
        self.pr = pr

    def compose(self) -> ComposeResult:
        yield TitleBar("RPlusView", f"PR #{self.pr.get('number')}")
        with Vertical(id="detail-root"):
            with Vertical(id="detail-loading"):
                yield LoadingIndicator()
                yield Static("Loading PR details…", id="detail-loading-label")
            with VerticalScroll(id="detail-scroll"):
                yield Static("", id="detail-header", markup=True)
                yield Static("", id="detail-meta", markup=True)
                yield Static("[bold]Description[/bold]", id="detail-body-label", markup=True)
                yield Static("", id="detail-body", markup=True)
        yield StatusBar()

    def on_mount(self) -> None:
        self.query_one("#detail-scroll").display = False
        self.query_one(StatusBar).set_message(
            " Esc/q Back   o Open in browser   ? Help "
        )
        self.fetch_detail()

    @work(exclusive=True, thread=True)
    def fetch_detail(self) -> None:
        detail = get_pr_detail(self.pr)
        self.app.call_from_thread(self._show_detail, detail)

    def _show_detail(self, pr: dict[str, Any]) -> None:
        self.pr = pr
        status = pr_status(pr)
        labels = ", ".join(
            n["name"] for n in (pr.get("labels") or {}).get("nodes") or []
        ) or "—"
        author = (pr.get("author") or {}).get("login") or "—"
        body = (pr.get("body") or "").strip() or "_No description provided._"
        if len(body) > 4000:
            body = body[:4000] + "\n\n…"

        repo = pr.get("repository", {}).get("nameWithOwner") or "—"
        commits = (pr.get("commits") or {}).get("totalCount", "—")
        comments = (pr.get("comments") or {}).get("totalCount", "—")
        reviews = (pr.get("reviews") or {}).get("totalCount", "—")

        self.query_one("#detail-header", Static).update(
            f"[bold]{pr.get('title', '')}[/bold]\n"
            f"[dim]{repo} · #{pr.get('number')} · {status}[/dim]"
        )
        self.query_one("#detail-meta", Static).update(
            f"[bold green]Author[/]  {author}\n"
            f"[bold green]Branch[/]  {pr.get('headRefName', '—')} → {pr.get('baseRefName', '—')}\n"
            f"[bold green]Diff[/]    [green]+{pr.get('additions', 0)}[/]  "
            f"[red]-{pr.get('deletions', 0)}[/]  ·  "
            f"{pr.get('changedFiles', 0)} files  ·  LOC {pr_loc(pr)}\n"
            f"[bold green]Activity[/] {commits} commits · {reviews} reviews · {comments} comments\n"
            f"[bold green]Labels[/]  {labels}\n"
            f"[bold green]Created[/] {str(pr.get('createdAt') or '')[:10]}   "
            f"[bold green]Updated[/] {str(pr.get('updatedAt') or '')[:10]}\n"
            f"[bold green]URL[/]     {pr.get('url', '')}"
        )
        self.query_one("#detail-body", Static).update(body)
        self.query_one("#detail-loading").display = False
        self.query_one("#detail-scroll").display = True
        self.query_one(TitleBar).set_meta(f"PR #{pr.get('number')} · {status}")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_open_browser(self) -> None:
        _open_url(self.pr.get("url") or "")
        self.notify("Opened in browser", timeout=2)

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())


class StatsScreen(Screen):
    """Aggregate statistics across loaded PRs."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("question_mark", "help", "Help", show=False),
    ]

    def __init__(self, prs: list[dict[str, Any]]) -> None:
        super().__init__()
        self.prs = prs

    def compose(self) -> ComposeResult:
        stats = compute_stats(self.prs)
        yield TitleBar("RPlusView", "statistics")
        with Vertical(id="stats-body"):
            yield Static(
                f"[bold]Overview[/bold]\n\n"
                f"  Total PRs     [bold]{stats['total']}[/bold]\n"
                f"  Open          [bold green]{stats['open']}[/bold green]\n"
                f"  Merged        [bold #a371f7]{stats['merged']}[/bold #a371f7]\n"
                f"  Closed        [bold red]{stats['closed']}[/bold red]\n\n"
                f"  Additions     [green]+{stats['additions']}[/green]\n"
                f"  Deletions     [red]-{stats['deletions']}[/red]\n"
                f"  Net LOC       [bold]{stats['loc']}[/bold]\n"
                f"  Files touched [bold]{stats['files']}[/bold]\n"
                f"  Repositories  [bold]{len(stats['repos'])}[/bold]",
                id="stats-overview",
                markup=True,
            )
            yield Static("[bold]Top repositories[/bold]", id="stats-repos-label", markup=True)
            yield DataTable(id="stats-top-repos")
            yield Static("[bold]Largest PRs by LOC[/bold]", id="stats-large-label", markup=True)
            yield DataTable(id="stats-largest")
        yield StatusBar()

    def on_mount(self) -> None:
        stats = compute_stats(self.prs)
        repos = self.query_one("#stats-top-repos", DataTable)
        repos.cursor_type = "row"
        repos.zebra_stripes = True
        repos.add_columns("Repository", "PRs")
        for name, count in stats["top_repos"]:
            repos.add_row(name, str(count))

        largest = self.query_one("#stats-largest", DataTable)
        largest.cursor_type = "row"
        largest.zebra_stripes = True
        largest.add_columns("#", "Repository", "Title", "LOC", "Status")
        for pr in stats["largest"]:
            largest.add_row(
                f"#{pr['number']}",
                pr["repository"]["nameWithOwner"],
                pr["title"][:48],
                str(pr_loc(pr)),
                pr_status(pr),
                key=pr["url"],
            )

        self.query_one(StatusBar).set_message(" Esc/q Back   ? Help ")
        self.query_one(TitleBar).set_meta(
            f"{stats['total']} PRs · {stats['open']} open · {len(stats['repos'])} repos"
        )

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())


class ReposScreen(Screen):
    """Per-repository breakdown of pull requests."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("o", "open_browser", "Browser", show=False),
        Binding("question_mark", "help", "Help", show=False),
    ]

    def __init__(self, prs: list[dict[str, Any]]) -> None:
        super().__init__()
        self.prs = prs
        self._repos = group_by_repo(prs)

    def compose(self) -> ComposeResult:
        yield TitleBar("RPlusView", "repositories")
        yield DataTable(id="repos-table")
        yield StatusBar()

    def on_mount(self) -> None:
        table = self.query_one("#repos-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("Repository", "PRs", "Open", "Merged", "Closed", "LOC")
        for repo in self._repos:
            table.add_row(
                repo["name"],
                str(repo["total"]),
                Text(str(repo["open"]), style="bold #3fb950"),
                Text(str(repo["merged"]), style="bold #a371f7"),
                Text(str(repo["closed"]), style="bold #f85149"),
                str(repo["loc"]),
                key=repo["url"],
            )
        self.query_one(TitleBar).set_meta(f"{len(self._repos)} repositories")
        self.query_one(StatusBar).set_message(
            " ↑↓ Nav   Enter/o Open repo   Esc/q Back   ? Help "
        )
        if self._repos:
            table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        _open_url(str(event.row_key.value))
        self.notify("Opened repository in browser", timeout=2)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_open_browser(self) -> None:
        table = self.query_one("#repos-table", DataTable)
        if table.row_count == 0:
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        _open_url(str(row_key.value))
        self.notify("Opened repository in browser", timeout=2)

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())
