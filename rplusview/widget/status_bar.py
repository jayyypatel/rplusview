from textual.widgets import Static

from rplusview.safe import escape_markup


class StatusBar(Static):
    """Bottom shortcut strip."""

    DEFAULT_TEXT = (
        " j/k gg G  ctrl+d/u  ctrl+f/b  Enter Details   o Open   p Task   i Inbox   "
        "c Closed   / Search   n/N match   u User   r Refresh   ? Help   q Quit "
    )

    def __init__(self) -> None:
        super().__init__(self.DEFAULT_TEXT, id="status-bar")

    def set_message(self, message: str) -> None:
        self.update(f" {escape_markup(message)} ")

    def reset(self) -> None:
        self.update(self.DEFAULT_TEXT)
