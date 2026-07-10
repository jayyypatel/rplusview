from textual.widgets import Static

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
        base = f"  ◆  {self._title}  "
        self.update(f"{base}—  {text}  " if text else base)
