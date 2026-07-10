from textual.widgets import Static


class StatusBar(Static):
    """Bottom shortcut strip."""

    DEFAULT_TEXT = (
        " ↑↓ Nav   Enter Details   o Open   / Search   "
        "s Sort   t Stats   e Repos   u User   r Refresh   ? Help   q Quit "
    )

    def __init__(self) -> None:
        super().__init__(self.DEFAULT_TEXT, id="status-bar")

    def set_message(self, message: str) -> None:
        self.update(f" {message} ")

    def reset(self) -> None:
        self.update(self.DEFAULT_TEXT)
