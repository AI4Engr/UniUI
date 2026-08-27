"""
Admin component interfaces for UniUI.

Pure Python — no backend dependencies.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional

from uniui.core import IWidget
from uniui.state import Handle


class ICard(IWidget):
    """Titled card container with optional subtitle, content area, and action area."""

    @abstractmethod
    def set_title(self, title: str) -> None: ...

    @abstractmethod
    def set_subtitle(self, subtitle: str) -> None: ...

    @abstractmethod
    def set_content(self, widget: IWidget) -> None: ...

    @abstractmethod
    def set_action(self, widget: IWidget) -> None: ...


class IStatCard(IWidget):
    """Metric display card: label, value, unit, trend, and status."""

    @abstractmethod
    def set_label(self, label: str) -> None: ...

    @abstractmethod
    def set_value(self, value: str) -> None: ...

    @abstractmethod
    def set_unit(self, unit: str) -> None: ...

    @abstractmethod
    def set_trend(self, trend: float) -> None:
        """Set trend as a signed percentage (e.g. +5.2 or -3.1)."""
        ...

    @abstractmethod
    def set_status(self, status: str) -> None:
        """Set status: 'ok', 'warn', or 'error'."""
        ...


class IMetricList(IWidget):
    """Compact two-column key/value list for dense secondary metrics."""

    @abstractmethod
    def set_items(self, items: List[Dict]) -> None:
        """Set displayed rows.

        Each dict: {"label": str, "value": str}
        """
        ...


class ITable(IWidget):
    """Tabular data display with columns, rows, loading and error states."""

    @abstractmethod
    def set_columns(self, columns: List[Dict]) -> None:
        """Set column definitions.

        Each dict: {"key": str, "label": str, "width": int (optional)}
        """
        ...

    @abstractmethod
    def set_rows(self, rows: List[Dict]) -> None:
        """Set row data. Each dict maps column keys to cell values."""
        ...

    @abstractmethod
    def set_loading(self, loading: bool) -> None:
        """Show or hide a loading indicator."""
        ...

    @abstractmethod
    def set_error(self, message: str) -> None:
        """Show an error message (empty string clears the error state)."""
        ...

    @abstractmethod
    def on_row_click(self, fn: Callable[[Dict], None]) -> Handle:
        """Register a callback fired when the user clicks a row."""
        ...

    @abstractmethod
    def set_sort(self, key: Optional[str], reverse: bool = False) -> None:
        """Sort displayed rows by column ``key``. ``key=None`` clears sorting.

        Display order only; the row data passed to ``set_rows()`` is
        unchanged, so a later ``set_rows()`` call still diffs correctly.
        """
        ...

    @abstractmethod
    def get_selected_row(self) -> Optional[Dict]:
        """The currently selected row, or ``None`` if nothing is selected.

        A row becomes selected when the user clicks it (same click that
        fires ``on_row_click``) and stays selected until a different row is
        clicked or ``set_rows()`` drops it from the data.
        """
        ...

    @abstractmethod
    def set_page_size(self, size: Optional[int]) -> None:
        """Rows per page. ``None`` (or ``0``) disables pagination — every
        row displays, sorted but not sliced."""
        ...

    @abstractmethod
    def set_page(self, page: int) -> None:
        """Jump to ``page`` (0-indexed), clamped to the valid range."""
        ...


class ISidebar(IWidget):
    """Navigation sidebar with selectable items and collapse support."""

    @abstractmethod
    def add_item(self, key: str, label: str, icon: str = "") -> None:
        """Append a navigation item."""
        ...

    @abstractmethod
    def add_group(self, label: str) -> None:
        """Append a non-clickable section header.

        Not addressable by ``set_active``/``on_select`` — it has no key, so
        it can never become the active item or fire a selection callback.
        """
        ...

    @abstractmethod
    def set_active(self, key: str) -> None:
        """Highlight the item with the given key as selected."""
        ...

    @abstractmethod
    def on_select(self, fn: Callable[[str], None]) -> Handle:
        """Register a callback fired when the user selects an item (passes key)."""
        ...

    @abstractmethod
    def set_collapsed(self, collapsed: bool) -> None:
        """Collapse (icon-only, width 64) or expand (width 240) the sidebar."""
        ...


class IAppShell(IWidget):
    """Top-level application shell: header, sidebar, content, footer."""

    @abstractmethod
    def set_header(self, widget: IWidget) -> None: ...

    @abstractmethod
    def set_sidebar(self, sidebar: ISidebar) -> None: ...

    @abstractmethod
    def set_content(self, widget: IWidget) -> None: ...

    @abstractmethod
    def set_footer(self, widget: IWidget) -> None: ...


class IBreadcrumb(IWidget):
    """Breadcrumb navigation trail."""

    @abstractmethod
    def set_items(self, items: List[Dict]) -> None:
        """Set breadcrumb items.

        Each dict: {"label": str, "path": str (optional)}
        The last item is the current page (no link).
        """
        ...

    @abstractmethod
    def on_click(self, fn: Callable[[str], None]) -> Handle:
        """Register callback fired when the user clicks a crumb (passes path)."""
        ...


class IGauge(IWidget):
    """Radial metric display with a numeric range and semantic status."""

    @abstractmethod
    def set_label(self, label: str) -> None: ...

    @abstractmethod
    def set_value(self, value: float) -> None: ...

    @abstractmethod
    def set_range(self, minimum: float, maximum: float) -> None: ...

    @abstractmethod
    def set_unit(self, unit: str) -> None: ...

    @abstractmethod
    def set_status(self, status: str) -> None: ...


class IChart(IWidget):
    """Backend-neutral line, area, or bar chart with streaming updates."""

    @abstractmethod
    def set_type(self, chart_type: str) -> None: ...

    @abstractmethod
    def set_title(self, title: str) -> None: ...

    @abstractmethod
    def set_data(self, x: List[Any], series: List[Dict]) -> None: ...

    @abstractmethod
    def append_data(self, x: Any, values: Any) -> None: ...

    @abstractmethod
    def set_max_points(self, max_points: int) -> None: ...

    @abstractmethod
    def set_loading(self, loading: bool) -> None:
        """Show or hide a loading indicator in place of the chart."""
        ...

    @abstractmethod
    def set_error(self, message: str) -> None:
        """Show an error message in place of the chart (empty string clears it)."""
        ...


class IDrawer(IWidget):
    """Animated secondary panel which can be opened without replacing a page."""

    @abstractmethod
    def set_title(self, title: str) -> None: ...

    @abstractmethod
    def set_content(self, widget: IWidget) -> None: ...

    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def toggle(self) -> None: ...

    @abstractmethod
    def is_open(self) -> bool: ...
