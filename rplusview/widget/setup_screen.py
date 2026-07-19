"""First-run / change-user welcome modal."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from rplusview.config import get_saved_username, set_saved_token
from rplusview.github_client import has_token
from rplusview.safe import InvalidUsernameError, validate_github_username


class SetupScreen(ModalScreen[str | None]):
    """Collect GitHub username and optionally update the API token."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, *, first_run: bool = True) -> None:
        super().__init__()
        self.first_run = first_run
        self._has_token = has_token()

    def compose(self) -> ComposeResult:
        title = "Welcome to RPlusView" if self.first_run else "Account settings"
        subtitle = (
            "Enter a GitHub username to load their pull requests."
            if self.first_run
            else "Change the tracked user and/or update your API token."
        )
        saved = get_saved_username() or ""
        token_label = (
            "Personal access token  [dim](required for API access)[/dim]"
            if not self._has_token
            else "Personal access token  [dim](leave blank to keep current)[/dim]"
        )
        token_placeholder = (
            "ghp_… or github_pat_…"
            if not self._has_token
            else "Paste new token to replace the current one"
        )

        with Vertical(id="setup-dialog"):
            yield Static(f"[bold]◆  {title}[/bold]", id="setup-title")
            yield Static(subtitle, id="setup-subtitle")
            yield Static("GitHub username", id="setup-user-label")
            yield Input(
                value=saved,
                placeholder="e.g. octocat",
                id="setup-username",
            )
            yield Static(token_label, id="setup-token-label", markup=True)
            yield Input(
                placeholder=token_placeholder,
                password=True,
                id="setup-token",
            )
            yield Static(
                "[dim]Prefer a fine-grained token with Pull requests: Read. "
                "Classic: public_repo or repo. github.com/settings/tokens[/dim]",
                id="setup-token-hint",
                markup=True,
            )
            yield Static("", id="setup-error")
            with Horizontal(id="setup-actions"):
                if not self.first_run:
                    yield Button("Cancel", id="setup-cancel", flat=True, compact=True)
                yield Button(
                    "Continue →",
                    id="setup-continue",
                    variant="success",
                    flat=True,
                    compact=True,
                )

    def on_mount(self) -> None:
        self.query_one("#setup-username", Input).focus()

    @on(Input.Submitted, "#setup-username")
    def on_username_submitted(self) -> None:
        self.query_one("#setup-token", Input).focus()

    @on(Input.Submitted, "#setup-token")
    def on_token_submitted(self) -> None:
        self._submit()

    @on(Button.Pressed, "#setup-continue")
    def on_continue(self) -> None:
        self._submit()

    @on(Button.Pressed, "#setup-cancel")
    def on_cancel_button(self) -> None:
        self.action_cancel()

    def action_cancel(self) -> None:
        if self.first_run and not get_saved_username():
            self.app.exit()
            return
        self.dismiss(None)

    def _submit(self) -> None:
        raw_username = self.query_one("#setup-username", Input).value.strip()
        token = self.query_one("#setup-token", Input).value.strip()
        error = self.query_one("#setup-error", Static)

        try:
            username = validate_github_username(raw_username)
        except InvalidUsernameError as exc:
            error.update(f"[bold red]{exc}[/]")
            self.query_one("#setup-username", Input).focus()
            return

        if not self._has_token and not token:
            error.update("[bold red]A GitHub token is required to fetch data.[/]")
            self.query_one("#setup-token", Input).focus()
            return

        if token:
            set_saved_token(token)

        error.update("")
        self.dismiss(username)
