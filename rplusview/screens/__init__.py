"""Secondary screens for RPlusView."""

from __future__ import annotations

import re
import webbrowser
from typing import Any

from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import LoadingIndicator, Static

from rplusview.github_client import (
    compute_stats,
    get_pr_detail,
    group_by_repo,
    iter_review_comments,
    pr_comments,
    pr_issue_comments,
    pr_loc,
    pr_review_comments,
    pr_status,
)
from rplusview.screens.inbox import InboxScreen
from rplusview.widget.help_screen import HelpScreen
from rplusview.widget.status_bar import StatusBar
from rplusview.widget.title_bar import TitleBar
from rplusview.widget.vim_nav import (
    VIM_NAV_BINDINGS,
    VimDataTable,
    VimNavMixin,
    vim_scroll_bottom,
    vim_scroll_half_down,
    vim_scroll_half_up,
    vim_scroll_top,
)

__all__ = ["InboxScreen", "PRDetailScreen", "ReposScreen", "StatsScreen"]

def _open_url(url: str) -> None:
    if url:
        webbrowser.open(url)


def _escape_markup(text: str) -> str:
    """Escape Rich markup brackets in user content."""
    return text.replace("[", "\\[")


def _trim_body(text: str, limit: int = 600) -> str:
    text = (text or "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) > limit:
        return text[:limit].rstrip() + "…"
    return text


def _format_comments(pr: dict[str, Any]) -> str:
    comments = (pr.get("comments") or {}).get("nodes") or []
    issue_n = pr_issue_comments(pr)
    if not comments:
        if issue_n:
            return (
                f"[bold #58a6ff]{issue_n}[/] conversation comments on GitHub "
                f"[dim](open in browser to read all)[/]"
            )
        return "[dim]No conversation comments yet.[/]"

    blocks: list[str] = []
    for i, node in enumerate(comments, start=1):
        author = (node.get("author") or {}).get("login") or "unknown"
        created = str(node.get("createdAt") or "")[:10]
        body = _escape_markup(_trim_body(node.get("body") or ""))
        if not body:
            body = "[dim]_empty comment_[/]"
        blocks.append(
            f"[bold #58a6ff]#{i}[/]  [bold #3dd68c]@{author}[/]  "
            f"[dim]{created}[/]\n"
            f"[#c9d1d9]{body}[/]"
        )
    more = ""
    if issue_n > len(comments):
        more = (
            f"\n\n[dim]Showing {len(comments)} of {issue_n} conversation comments — "
            f"press o to open the rest in browser[/]"
        )
    return "\n\n".join(blocks) + more


def _format_inline_comments(pr: dict[str, Any]) -> str:
    nodes = iter_review_comments(pr)
    review_n = pr_review_comments(pr)
    if not nodes:
        if review_n:
            return (
                f"[bold #d29922]{review_n}[/] inline review comments on GitHub "
                f"[dim](open in browser to read all)[/]"
            )
        return "[dim]No inline review comments yet.[/]"

    blocks: list[str] = []
    for i, node in enumerate(nodes[:40], start=1):
        author = (node.get("author") or {}).get("login") or "unknown"
        created = str(node.get("createdAt") or "")[:10]
        path = node.get("path") or ""
        line = node.get("line")
        loc = f"{path}:{line}" if path and line else path or "diff"
        resolved = " [dim]resolved[/]" if node.get("_resolved") else ""
        body = _escape_markup(_trim_body(node.get("body") or "", 450))
        if not body:
            body = "[dim]_empty comment_[/]"
        blocks.append(
            f"[bold #d29922]#{i}[/]  [bold #3dd68c]@{author}[/]  "
            f"[#79c0ff]{loc}[/]{resolved}  [dim]{created}[/]\n"
            f"[#c9d1d9]{body}[/]"
        )
    more = ""
    if review_n > len(nodes[:40]):
        more = (
            f"\n\n[dim]Showing {min(len(nodes), 40)} of {review_n} inline comments — "
            f"press o for the rest[/]"
        )
    return "\n\n".join(blocks) + more


def _format_reviews(pr: dict[str, Any]) -> str:
    reviews = (pr.get("reviews") or {}).get("nodes") or []
    total = (pr.get("reviews") or {}).get("totalCount", 0)
    useful = [r for r in reviews if (r.get("body") or "").strip()]
    if not useful:
        if total:
            return f"[dim]{total} review(s) — no written review bodies[/]"
        return "[dim]No reviews yet.[/]"

    state_colors = {
        "APPROVED": "#3dd68c",
        "CHANGES_REQUESTED": "#f85149",
        "COMMENTED": "#58a6ff",
        "DISMISSED": "#8b9bb0",
        "PENDING": "#d29922",
    }
    blocks: list[str] = []
    for node in useful[:15]:
        author = (node.get("author") or {}).get("login") or "unknown"
        state = node.get("state") or "COMMENTED"
        color = state_colors.get(state, "#8b9bb0")
        created = str(node.get("createdAt") or "")[:10]
        body = _escape_markup(_trim_body(node.get("body") or "", 400))
        blocks.append(
            f"[bold {color}]● {state}[/]  [bold #a371f7]@{author}[/]  "
            f"[dim]{created}[/]\n"
            f"[#c9d1d9]{body}[/]"
        )
    return "\n\n".join(blocks)


class PRDetailScreen(Screen):
    """Full pull-request detail view."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("o", "open_browser", "Browser", show=False),
        Binding("question_mark", "help", "Help", show=False),
        Binding("g,g", "scroll_top", "Top", show=False, priority=True),
        Binding("G", "scroll_bottom", "Bottom", show=False, priority=True),
        Binding("ctrl+d", "scroll_half_down", "Half↓", show=False, priority=True),
        Binding("ctrl+u", "scroll_half_up", "Half↑", show=False, priority=True),
        Binding("ctrl+f", "scroll_page_down", "Page↓", show=False, priority=True),
        Binding("ctrl+b", "scroll_page_up", "Page↑", show=False, priority=True),
        Binding("j", "scroll_line_down", "Down", show=False, priority=True),
        Binding("k", "scroll_line_up", "Up", show=False, priority=True),
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
                yield Static("", id="detail-comments-label", markup=True)
                yield Static("", id="detail-comments", markup=True)
                yield Static("", id="detail-inline-label", markup=True)
                yield Static("", id="detail-inline", markup=True)
                yield Static("", id="detail-reviews-label", markup=True)
                yield Static("", id="detail-reviews", markup=True)
        yield StatusBar()

    def on_mount(self) -> None:
        self.query_one("#detail-scroll").display = False
        self.query_one(StatusBar).set_message(
            " j/k gg G  ctrl+d/u  ctrl+f/b scroll   o Open   Esc/q Back   ? Help "
        )
        self.fetch_detail()

    def _detail_scroll(self) -> VerticalScroll | None:
        scroll = self.query_one("#detail-scroll", VerticalScroll)
        return scroll if scroll.display else None

    def action_scroll_top(self) -> None:
        scroll = self._detail_scroll()
        if scroll:
            vim_scroll_top(scroll)

    def action_scroll_bottom(self) -> None:
        scroll = self._detail_scroll()
        if scroll:
            vim_scroll_bottom(scroll)

    def action_scroll_half_down(self) -> None:
        scroll = self._detail_scroll()
        if scroll:
            vim_scroll_half_down(scroll)

    def action_scroll_half_up(self) -> None:
        scroll = self._detail_scroll()
        if scroll:
            vim_scroll_half_up(scroll)

    def action_scroll_page_down(self) -> None:
        scroll = self._detail_scroll()
        if scroll:
            scroll.scroll_page_down()

    def action_scroll_page_up(self) -> None:
        scroll = self._detail_scroll()
        if scroll:
            scroll.scroll_page_up()

    def action_scroll_line_down(self) -> None:
        scroll = self._detail_scroll()
        if scroll:
            scroll.scroll_relative(y=1, animate=False)

    def action_scroll_line_up(self) -> None:
        scroll = self._detail_scroll()
        if scroll:
            scroll.scroll_relative(y=-1, animate=False)

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
        body = _escape_markup(body)

        repo = pr.get("repository", {}).get("nameWithOwner") or "—"
        commits = (pr.get("commits") or {}).get("totalCount", "—")
        issue_n = pr_issue_comments(pr)
        review_n = pr_review_comments(pr)
        comments_n = issue_n + review_n
        reviews_n = (pr.get("reviews") or {}).get("totalCount", 0)

        status_color = {
            "Open": "#3dd68c",
            "Merged": "#a371f7",
            "Closed": "#f85149",
        }.get(status, "#8b9bb0")

        self.query_one("#detail-header", Static).update(
            f"[bold]{_escape_markup(pr.get('title', ''))}[/bold]\n"
            f"[dim]{repo} · #{pr.get('number')} · [/]"
            f"[bold {status_color}]{status}[/]"
        )
        self.query_one("#detail-meta", Static).update(
            f"[bold #3dd68c]Author[/]    [bold]@{author}[/]\n"
            f"[bold #3dd68c]Branch[/]    {pr.get('headRefName', '—')} → {pr.get('baseRefName', '—')}\n"
            f"[bold #3dd68c]Diff[/]      [green]+{pr.get('additions', 0)}[/]  "
            f"[red]-{pr.get('deletions', 0)}[/]  ·  "
            f"{pr.get('changedFiles', 0)} files  ·  LOC {pr_loc(pr)}\n"
            f"[bold #3dd68c]Activity[/]  [bold #d29922]{commits}[/] commits · "
            f"[bold #a371f7]{reviews_n}[/] reviews · "
            f"[bold #58a6ff]{comments_n}[/] comments "
            f"[dim]({issue_n} conversation + {review_n} inline)[/]\n"
            f"[bold #3dd68c]Labels[/]    {labels}\n"
            f"[bold #3dd68c]Created[/]   {str(pr.get('createdAt') or '')[:10]}   "
            f"[bold #3dd68c]Updated[/] {str(pr.get('updatedAt') or '')[:10]}\n"
            f"[bold #3dd68c]URL[/]       [#58a6ff]{pr.get('url', '')}[/]"
        )
        self.query_one("#detail-body", Static).update(body)

        self.query_one("#detail-comments-label", Static).update(
            f"[bold #58a6ff]Conversation comments[/]  [dim]({issue_n})[/]"
        )
        self.query_one("#detail-comments", Static).update(_format_comments(pr))

        self.query_one("#detail-inline-label", Static).update(
            f"[bold #d29922]Inline review comments[/]  [dim]({review_n})[/]"
        )
        self.query_one("#detail-inline", Static).update(_format_inline_comments(pr))

        self.query_one("#detail-reviews-label", Static).update(
            f"[bold #a371f7]Reviews[/]  [dim]({reviews_n})[/]"
        )
        self.query_one("#detail-reviews", Static).update(_format_reviews(pr))

        self.query_one("#detail-loading").display = False
        self.query_one("#detail-scroll").display = True
        self.query_one(TitleBar).set_meta(
            f"PR #{pr.get('number')} · {status} · {comments_n} comments"
        )

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_open_browser(self) -> None:
        _open_url(self.pr.get("url") or "")
        self.notify("Opened in browser", timeout=2)

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())


class StatsScreen(VimNavMixin, Screen):
    """Aggregate statistics across loaded PRs."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("question_mark", "help", "Help", show=False),
        *VIM_NAV_BINDINGS,
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
            yield VimDataTable(id="stats-top-repos")
            yield Static("[bold]Largest PRs by LOC[/bold]", id="stats-large-label", markup=True)
            yield VimDataTable(id="stats-largest")
        yield StatusBar()

    def on_mount(self) -> None:
        stats = compute_stats(self.prs)
        repos = self.query_one("#stats-top-repos", VimDataTable)
        repos.cursor_type = "row"
        repos.zebra_stripes = True
        repos.add_columns("Repository", "PRs")
        for name, count in stats["top_repos"]:
            repos.add_row(name, str(count))

        largest = self.query_one("#stats-largest", VimDataTable)
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

        self.query_one(StatusBar).set_message(
            " j/k gg G  ctrl+d/u  Esc/q Back   ? Help "
        )
        self.query_one(TitleBar).set_meta(
            f"{stats['total']} PRs · {stats['open']} open · {len(stats['repos'])} repos"
        )

    def _vim_table(self) -> VimDataTable | None:
        focused = self.focused
        if isinstance(focused, VimDataTable) and focused.row_count:
            return focused
        largest = self.query_one("#stats-largest", VimDataTable)
        if largest.row_count:
            return largest
        repos = self.query_one("#stats-top-repos", VimDataTable)
        if repos.row_count:
            return repos
        return None

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())


class ReposScreen(VimNavMixin, Screen):
    """Per-repository breakdown of pull requests."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("o", "open_browser", "Browser", show=False),
        Binding("question_mark", "help", "Help", show=False),
        *VIM_NAV_BINDINGS,
    ]

    def __init__(self, prs: list[dict[str, Any]]) -> None:
        super().__init__()
        self.prs = prs
        self._repos = group_by_repo(prs)

    def compose(self) -> ComposeResult:
        yield TitleBar("RPlusView", "repositories")
        yield VimDataTable(id="repos-table")
        yield StatusBar()

    def on_mount(self) -> None:
        table = self.query_one("#repos-table", VimDataTable)
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
            " j/k gg G  ctrl+d/u  Enter/o Open repo   Esc/q Back   ? Help "
        )
        if self._repos:
            table.focus()

    def _vim_table(self) -> VimDataTable | None:
        table = self.query_one("#repos-table", VimDataTable)
        if table.row_count:
            return table
        return None

    @on(VimDataTable.RowSelected, "#repos-table")
    def on_data_table_row_selected(self, event: VimDataTable.RowSelected) -> None:
        _open_url(str(event.row_key.value))
        self.notify("Opened repository in browser", timeout=2)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_open_browser(self) -> None:
        table = self.query_one("#repos-table", VimDataTable)
        if table.row_count == 0:
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        _open_url(str(row_key.value))
        self.notify("Opened repository in browser", timeout=2)

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())
