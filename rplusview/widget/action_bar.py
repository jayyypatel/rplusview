from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static


class ActionBar(Horizontal):
    """Primary action buttons above the PR table."""

    def compose(self) -> ComposeResult:
        yield Static(" Actions ", id="action-label")
        yield Button("Open", id="btn-open", variant="success", flat=True, compact=True)
        yield Button("Task", id="btn-task", variant="warning", flat=True, compact=True)
        yield Button("Details", id="btn-details", variant="primary", flat=True, compact=True)
        yield Button("Inbox", id="btn-inbox", variant="primary", flat=True, compact=True)
        yield Button("Closed", id="btn-closed", variant="default", flat=True, compact=True)
        yield Button("Stats", id="btn-stats", variant="default", flat=True, compact=True)
        yield Button("Repos", id="btn-repos", variant="default", flat=True, compact=True)
        yield Button("Search", id="btn-search", variant="default", flat=True, compact=True)
        yield Button("Sort", id="btn-sort", variant="default", flat=True, compact=True)
        yield Button("Refresh", id="btn-refresh", variant="warning", flat=True, compact=True)
        yield Button("User", id="btn-user", variant="default", flat=True, compact=True)
        yield Button("Help", id="btn-help", variant="default", flat=True, compact=True)
