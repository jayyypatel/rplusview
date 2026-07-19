from textual.widgets import Static

from rplusview.safe import escape_markup

APP_NAME = "RPlusView"


class TitleBar(Static):
    """Custom top chrome for RPlusView."""

    def __init__(self, title: str = APP_NAME, subtitle: str = "") -> None:
        self._title = title
        label = f"  ◆  {title}  "
        if subtitle:
            label += f"—  {subtitle}  "
        super().__init__(label, id="title-bar")

    def set_meta(self, text: str) -> None:
        # Escape untrusted bits (e.g. live search query) so Rich markup cannot inject.
        safe = escape_markup(text) if text else ""
        base = f"  ◆  {self._title}  "
        self.update(f"{base}—  {safe}  " if safe else base)
