"""Vim-style navigation for DataTable and scrollable views."""

from __future__ import annotations

from typing import ClassVar

from textual.binding import Binding, BindingType
from textual.widgets import DataTable


# App/screen-level bindings (delegate to the active table when possible).
VIM_NAV_BINDINGS: list[BindingType] = [
    Binding("j", "vim_cursor_down", "Down", show=False, priority=True),
    Binding("k", "vim_cursor_up", "Up", show=False, priority=True),
    Binding("g,g", "vim_scroll_top", "Top", show=False, priority=True),
    Binding("G", "vim_scroll_bottom", "Bottom", show=False, priority=True),
    Binding("ctrl+d", "vim_half_page_down", "Half↓", show=False, priority=True),
    Binding("ctrl+u", "vim_half_page_up", "Half↑", show=False, priority=True),
    Binding("ctrl+f", "vim_page_down", "Page↓", show=False, priority=True),
    Binding("ctrl+b", "vim_page_up", "Page↑", show=False, priority=True),
    Binding("n", "vim_search_next", "Next", show=False, priority=True),
    Binding("N", "vim_search_prev", "Prev", show=False, priority=True),
]


class VimDataTable(DataTable):
    """DataTable with vim motion keys when focused."""

    BINDINGS: ClassVar[list[BindingType]] = [
        *DataTable.BINDINGS,
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g,g", "scroll_top", "Top", show=False),
        Binding("G", "scroll_bottom", "Bottom", show=False),
        Binding("ctrl+d", "half_page_down", "Half↓", show=False),
        Binding("ctrl+u", "half_page_up", "Half↑", show=False),
        Binding("ctrl+f", "page_down", "Page↓", show=False),
        Binding("ctrl+b", "page_up", "Page↑", show=False),
    ]

    def _viewport_height(self) -> int:
        height = self.scrollable_content_region.height
        if self.show_header:
            height -= self.header_height
        return max(1, height)

    def _rows_for_scroll(self, *, from_row: int, downward: bool, max_height: int) -> int:
        rows = 0
        offset = 0
        if downward:
            for ordered_row in self.ordered_rows[from_row:]:
                offset += ordered_row.height
                rows += 1
                if offset > max_height:
                    break
        else:
            for ordered_row in reversed(self.ordered_rows[: from_row + 1]):
                offset += ordered_row.height
                rows += 1
                if offset > max_height:
                    break
        return max(1, rows)

    def action_half_page_down(self) -> None:
        """Vim ctrl+d — move down half a screen."""
        self._set_hover_cursor(False)
        if not (self.show_cursor and self.cursor_type in ("cell", "row")) or self.row_count == 0:
            return
        half = max(1, self._viewport_height() // 2)
        row_index, column_index = self.cursor_coordinate
        rows = self._rows_for_scroll(from_row=row_index, downward=True, max_height=half)
        target_row = min(self.row_count - 1, row_index + rows - 1)
        self.scroll_relative(y=half, animate=False, force=True)
        self.move_cursor(row=target_row, column=column_index, scroll=False)
        self._scroll_cursor_into_view(animate=False)

    def action_half_page_up(self) -> None:
        """Vim ctrl+u — move up half a screen."""
        self._set_hover_cursor(False)
        if not (self.show_cursor and self.cursor_type in ("cell", "row")) or self.row_count == 0:
            return
        half = max(1, self._viewport_height() // 2)
        row_index, column_index = self.cursor_coordinate
        rows = self._rows_for_scroll(from_row=row_index, downward=False, max_height=half)
        target_row = max(0, row_index - rows + 1)
        self.scroll_relative(y=-half, animate=False, force=True)
        self.move_cursor(row=target_row, column=column_index, scroll=False)
        self._scroll_cursor_into_view(animate=False)


class VimNavMixin:
    """Mixin for App/Screen: vim keys work even when the table is not focused."""

    def _vim_nav_blocked(self) -> bool:
        return False

    def _vim_table(self) -> VimDataTable | None:
        return None

    def _vim_with_table(self, action: str) -> None:
        if self._vim_nav_blocked():
            return
        table = self._vim_table()
        if not table or not table.display or table.row_count == 0:
            return
        table.focus()
        getattr(table, action)()

    def action_vim_cursor_down(self) -> None:
        self._vim_with_table("action_cursor_down")

    def action_vim_cursor_up(self) -> None:
        self._vim_with_table("action_cursor_up")

    def action_vim_scroll_top(self) -> None:
        self._vim_with_table("action_scroll_top")

    def action_vim_scroll_bottom(self) -> None:
        self._vim_with_table("action_scroll_bottom")

    def action_vim_half_page_down(self) -> None:
        self._vim_with_table("action_half_page_down")

    def action_vim_half_page_up(self) -> None:
        self._vim_with_table("action_half_page_up")

    def action_vim_page_down(self) -> None:
        self._vim_with_table("action_page_down")

    def action_vim_page_up(self) -> None:
        self._vim_with_table("action_page_up")

    def action_vim_search_next(self) -> None:
        self._vim_search_step(1)

    def action_vim_search_prev(self) -> None:
        self._vim_search_step(-1)

    def _vim_search_step(self, delta: int) -> None:
        if self._vim_nav_blocked():
            return
        table = self._vim_table()
        if not table or not table.display or table.row_count == 0:
            return
        table.focus()
        row, column = table.cursor_coordinate
        target = row + delta
        if target >= table.row_count:
            target = 0
        elif target < 0:
            target = table.row_count - 1
        table.move_cursor(row=target, column=column)


def vim_scroll_half_down(scroll) -> None:
    """Half-page down for a VerticalScroll (detail/help views)."""
    height = max(1, scroll.size.height // 2)
    scroll.scroll_relative(y=height, animate=False)


def vim_scroll_half_up(scroll) -> None:
    """Half-page up for a VerticalScroll."""
    height = max(1, scroll.size.height // 2)
    scroll.scroll_relative(y=-height, animate=False)


def vim_scroll_top(scroll) -> None:
    scroll.scroll_home(animate=False)


def vim_scroll_bottom(scroll) -> None:
    scroll.scroll_end(animate=False)
