from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static


HELP_BODY = """\
[bold]Toolbar buttons[/bold]
  [bold green]Open[/]        Open selected PR in browser
  [bold green]Details[/]     PR details page
  [bold green]Stats[/]       Statistics overview
  [bold green]Repos[/]       Repositories breakdown
  [bold green]Search[/]      Live search bar
  [bold green]Sort[/]        Cycle sort mode
  [bold green]Refresh[/]     Reload PRs from GitHub
  [bold green]User[/]        Change tracked GitHub username
  [bold green]Help[/]        This help screen

[bold]Keyboard[/bold]
  [bold green]↑ / ↓[/]       Move between rows
  [bold green]Enter / d[/]   Open PR details
  [bold green]o[/]           Open in browser
  [bold green]/[/]           Live search (title, repo, #, status)
  [bold green]s[/]           Sort · LOC → Date → Title → Repo → Files → #
  [bold green]t[/]           Statistics
  [bold green]e[/]           Repositories
  [bold green]u[/]           Change user
  [bold green]r[/]           Refresh
  [bold green]?[/]           Help
  [bold green]Esc[/]         Clear search / go back
  [bold green]q[/]           Quit (or go back)

[bold]On detail / stats / repos[/bold]
  [bold green]o[/]           Open current item in browser
  [bold green]Esc / q[/]     Return to dashboard
"""


class HelpScreen(ModalScreen[None]):
    """Centered help overlay for RPlusView."""

    BINDINGS = [
        ("escape", "dismiss_help", "Close"),
        ("q", "dismiss_help", "Close"),
        ("question_mark", "dismiss_help", "Close"),
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
