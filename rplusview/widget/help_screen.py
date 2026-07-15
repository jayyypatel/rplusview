from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from rplusview.widget.vim_nav import (
    vim_scroll_bottom,
    vim_scroll_half_down,
    vim_scroll_half_up,
    vim_scroll_top,
)


HELP_BODY = """\
[bold]Toolbar buttons[/bold]
  [bold green]Open[/]        Open selected PR in browser
  [bold green]Details[/]     PR details page
  [bold green]Inbox[/]       Pulls inbox (drafts, needs action, …)
  [bold green]Closed[/]      Toggle open ↔ closed/merged PRs
  [bold green]Stats[/]       Statistics overview
  [bold green]Repos[/]       Repositories breakdown
  [bold green]Search[/]      Live search bar
  [bold green]Sort[/]        Cycle sort mode
  [bold green]Refresh[/]     Reload PRs from GitHub
  [bold green]User[/]        Change username and/or API token
  [bold green]Help[/]        This help screen

[bold]Vim navigation (tables)[/bold]
  [bold green]j / k[/]       Line down / up
  [bold green]gg[/]           Jump to first row
  [bold green]G[/]           Jump to last row
  [bold green]ctrl+d[/]      Half page down
  [bold green]ctrl+u[/]      Half page up
  [bold green]ctrl+f[/]      Full page down
  [bold green]ctrl+b[/]      Full page up
  [bold green]↑ / ↓[/]       Also move between rows

[bold]Search & actions[/bold]
  [bold green]/[/]           Live search (title, repo, #, status)
  [bold green]n / N[/]       Next / previous search match
  [bold green]Enter / d[/]   Open PR details
  [bold green]o[/]           Open in browser
  [bold green]s[/]           Sort · LOC → Date → Title → Repo → Files → #
  [bold green]i[/]           Inbox panels
  [bold green]c[/]           Toggle closed PRs
  [bold green]t[/]           Statistics
  [bold green]e[/]           Repositories
  [bold green]u[/]           Change user / token
  [bold green]r[/]           Refresh
  [bold green]?[/]           Help
  [bold green]Esc[/]         Clear search / go back
  [bold green]q[/]           Quit (or go back)

[bold]On detail view[/bold]
  Same scroll keys (j/k, gg, G, ctrl+d/u, ctrl+f/b) scroll the page.

[bold]On stats / repos / inbox[/bold]
  Vim table keys apply to the focused table.
  [bold green]o[/]           Open current item in browser
  [bold green]Esc / q[/]     Return to dashboard
"""


class HelpScreen(ModalScreen[None]):
    """Centered help overlay for RPlusView."""

    BINDINGS = [
        ("escape", "dismiss_help", "Close"),
        ("q", "dismiss_help", "Close"),
        ("question_mark", "dismiss_help", "Close"),
        Binding("g,g", "scroll_top", "Top", show=False, priority=True),
        Binding("G", "scroll_bottom", "Bottom", show=False, priority=True),
        Binding("ctrl+d", "scroll_half_down", "Half↓", show=False, priority=True),
        Binding("ctrl+u", "scroll_half_up", "Half↑", show=False, priority=True),
        Binding("j", "scroll_line_down", "Down", show=False, priority=True),
        Binding("k", "scroll_line_up", "Up", show=False, priority=True),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Static("[bold]RPlusView · Help[/bold]", id="help-title")
            with VerticalScroll(id="help-scroll"):
                yield Static(HELP_BODY, id="help-body", markup=True)
            yield Static(
                "[dim]Press Esc, q, or ? to close[/dim]",
                id="help-footer",
                markup=True,
            )

    def action_dismiss_help(self) -> None:
        self.dismiss()

    def action_scroll_top(self) -> None:
        vim_scroll_top(self.query_one("#help-scroll", VerticalScroll))

    def action_scroll_bottom(self) -> None:
        vim_scroll_bottom(self.query_one("#help-scroll", VerticalScroll))

    def action_scroll_half_down(self) -> None:
        vim_scroll_half_down(self.query_one("#help-scroll", VerticalScroll))

    def action_scroll_half_up(self) -> None:
        vim_scroll_half_up(self.query_one("#help-scroll", VerticalScroll))

    def action_scroll_line_down(self) -> None:
        self.query_one("#help-scroll", VerticalScroll).scroll_relative(y=1, animate=False)

    def action_scroll_line_up(self) -> None:
        self.query_one("#help-scroll", VerticalScroll).scroll_relative(y=-1, animate=False)
