"""
Qt/PySide2 implementations of admin components (Card, StatCard, Table, Sidebar, AppShell).

This module registers itself into QtWidgetFactory when imported.
Import it after qt.py is loaded — done automatically when uniui is initialized with 'qt'.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from PySide2 import QtWidgets, QtCore, QtGui

from uniui.admin import ICard, IStatCard, ITable, ISidebar, IAppShell
from uniui.core import IWidget


def _native(widget) -> QtWidgets.QWidget:
    """Extract the Qt native widget from a UniUI widget or return as-is."""
    if hasattr(widget, "get_native"):
        return widget.get_native()
    return widget


# ---------------------------------------------------------------------------
# ICard — QFrame with title/subtitle/content/action
# ---------------------------------------------------------------------------

class QtCardAdapter(ICard):
    def __init__(self):
        self._frame = QtWidgets.QFrame()
        self._frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        outer = QtWidgets.QVBoxLayout(self._frame)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(4)

        self._title_label = QtWidgets.QLabel("")
        font = self._title_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        self._title_label.setFont(font)
        self._title_label.hide()

        self._subtitle_label = QtWidgets.QLabel("")
        self._subtitle_label.hide()

        self._content_area = QtWidgets.QWidget()
        self._content_layout = QtWidgets.QVBoxLayout(self._content_area)
        self._content_layout.setContentsMargins(0, 0, 0, 0)

        self._action_area = QtWidgets.QWidget()
        self._action_layout = QtWidgets.QVBoxLayout(self._action_area)
        self._action_layout.setContentsMargins(0, 0, 0, 0)
        self._action_area.hide()

        outer.addWidget(self._title_label)
        outer.addWidget(self._subtitle_label)
        outer.addWidget(self._content_area)
        outer.addWidget(self._action_area)

    def get_native(self):
        return self._frame

    def set_title(self, title: str) -> None:
        self._title_label.setText(title)
        self._title_label.setVisible(bool(title))

    def set_subtitle(self, subtitle: str) -> None:
        self._subtitle_label.setText(subtitle)
        self._subtitle_label.setVisible(bool(subtitle))

    def set_content(self, widget) -> None:
        _clear_layout(self._content_layout)
        self._content_layout.addWidget(_native(widget))

    def set_action(self, widget) -> None:
        _clear_layout(self._action_layout)
        self._action_layout.addWidget(_native(widget))
        self._action_area.show()


# ---------------------------------------------------------------------------
# IStatCard — metric display widget
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "ok": "#22c55e",
    "warn": "#f59e0b",
    "error": "#ef4444",
}

class QtStatCardAdapter(IStatCard):
    def __init__(self):
        self._frame = QtWidgets.QFrame()
        self._frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        layout = QtWidgets.QVBoxLayout(self._frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(2)

        self._label_w = QtWidgets.QLabel("")
        self._value_w = QtWidgets.QLabel("—")
        vfont = self._value_w.font()
        vfont.setPointSize(vfont.pointSize() + 8)
        vfont.setBold(True)
        self._value_w.setFont(vfont)

        self._unit_w = QtWidgets.QLabel("")
        self._trend_w = QtWidgets.QLabel("")

        layout.addWidget(self._label_w)
        layout.addWidget(self._value_w)
        layout.addWidget(self._unit_w)
        layout.addWidget(self._trend_w)

        self._status = "ok"

    def get_native(self):
        return self._frame

    def set_label(self, label: str) -> None:
        self._label_w.setText(label)

    def set_value(self, value: str) -> None:
        self._value_w.setText(str(value))

    def set_unit(self, unit: str) -> None:
        self._unit_w.setText(unit)
        self._unit_w.setVisible(bool(unit))

    def set_trend(self, trend: float) -> None:
        if trend > 0:
            text = f"▲ {trend:.1f}%"
            color = "#22c55e"
        elif trend < 0:
            text = f"▼ {abs(trend):.1f}%"
            color = "#ef4444"
        else:
            text = "— 0.0%"
            color = "#6b7280"
        self._trend_w.setText(text)
        self._trend_w.setStyleSheet(f"color: {color};")

    def set_status(self, status: str) -> None:
        self._status = status
        color = _STATUS_COLORS.get(status, "#22c55e")
        self._frame.setStyleSheet(f"QFrame {{ border-left: 4px solid {color}; }}")


# ---------------------------------------------------------------------------
# ITable — QTableWidget
# ---------------------------------------------------------------------------

class QtTableAdapter(ITable):
    def __init__(self):
        self._container = QtWidgets.QWidget()
        self._vbox = QtWidgets.QVBoxLayout(self._container)
        self._vbox.setContentsMargins(0, 0, 0, 0)

        self._table = QtWidgets.QTableWidget()
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)

        self._overlay_label = QtWidgets.QLabel("")
        self._overlay_label.setAlignment(QtCore.Qt.AlignCenter)
        self._overlay_label.hide()

        self._vbox.addWidget(self._table)
        self._vbox.addWidget(self._overlay_label)

        self._columns: List[Dict] = []
        self._rows: List[Dict] = []
        self._row_click_cb: Optional[Callable] = None
        self._table.cellClicked.connect(self._on_cell_clicked)

    def get_native(self):
        return self._container

    def set_columns(self, columns: List[Dict]) -> None:
        self._columns = columns
        self._table.setColumnCount(len(columns))
        labels = [c.get("label", c.get("key", "")) for c in columns]
        self._table.setHorizontalHeaderLabels(labels)
        for i, col in enumerate(columns):
            if "width" in col:
                self._table.setColumnWidth(i, col["width"])

    def set_rows(self, rows: List[Dict]) -> None:
        self._rows = rows
        self._table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, col in enumerate(self._columns):
                key = col.get("key", "")
                value = str(row.get(key, ""))
                item = QtWidgets.QTableWidgetItem(value)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self._table.setItem(r_idx, c_idx, item)

    def set_loading(self, loading: bool) -> None:
        if loading:
            self._table.hide()
            self._overlay_label.setText("Loading…")
            self._overlay_label.show()
        else:
            self._overlay_label.hide()
            self._table.show()

    def set_error(self, message: str) -> None:
        if message:
            self._table.hide()
            self._overlay_label.setText(f"Error: {message}")
            self._overlay_label.show()
        else:
            self._overlay_label.hide()
            self._table.show()

    def on_row_click(self, fn: Callable[[Dict], None]) -> None:
        self._row_click_cb = fn

    def _on_cell_clicked(self, row: int, col: int) -> None:
        if self._row_click_cb and 0 <= row < len(self._rows):
            self._row_click_cb(self._rows[row])


# ---------------------------------------------------------------------------
# ISidebar — QListWidget
# ---------------------------------------------------------------------------

_SIDEBAR_EXPANDED = 240
_SIDEBAR_COLLAPSED = 64


class QtSidebarAdapter(ISidebar):
    def __init__(self):
        self._list = QtWidgets.QListWidget()
        self._list.setFixedWidth(_SIDEBAR_EXPANDED)
        self._keys: List[str] = []
        self._select_cb: Optional[Callable] = None
        self._collapsed = False
        self._list.currentRowChanged.connect(self._on_row_changed)

    def get_native(self):
        return self._list

    def add_item(self, key: str, label: str, icon: str = "") -> None:
        self._keys.append(key)
        display = label if not self._collapsed else (label[:1] if label else "?")
        item = QtWidgets.QListWidgetItem(display)
        item.setData(QtCore.Qt.UserRole, key)
        self._list.addItem(item)

    def set_active(self, key: str) -> None:
        if key in self._keys:
            idx = self._keys.index(key)
            # Block signals to avoid triggering on_select during programmatic selection
            self._list.blockSignals(True)
            self._list.setCurrentRow(idx)
            self._list.blockSignals(False)

    def on_select(self, fn: Callable[[str], None]) -> None:
        self._select_cb = fn

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self._list.setFixedWidth(_SIDEBAR_COLLAPSED if collapsed else _SIDEBAR_EXPANDED)

    def _on_row_changed(self, row: int) -> None:
        if self._select_cb and 0 <= row < len(self._keys):
            self._select_cb(self._keys[row])


# ---------------------------------------------------------------------------
# IAppShell — QWidget with header/sidebar/content/footer
# ---------------------------------------------------------------------------

class QtAppShellAdapter(IAppShell):
    def __init__(self):
        self._root = QtWidgets.QWidget()
        self._outer = QtWidgets.QVBoxLayout(self._root)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        self._header_area = QtWidgets.QWidget()
        self._header_layout = QtWidgets.QVBoxLayout(self._header_area)
        self._header_layout.setContentsMargins(0, 0, 0, 0)
        self._header_area.hide()

        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        self._sidebar_placeholder = QtWidgets.QWidget()  # hidden until sidebar set
        self._content_area = QtWidgets.QWidget()
        self._content_layout = QtWidgets.QVBoxLayout(self._content_area)
        self._content_layout.setContentsMargins(0, 0, 0, 0)

        self._splitter.addWidget(self._sidebar_placeholder)
        self._splitter.addWidget(self._content_area)
        self._splitter.setSizes([240, 800])

        self._footer_area = QtWidgets.QWidget()
        self._footer_layout = QtWidgets.QVBoxLayout(self._footer_area)
        self._footer_layout.setContentsMargins(0, 0, 0, 0)
        self._footer_area.hide()

        self._outer.addWidget(self._header_area)
        self._outer.addWidget(self._splitter, stretch=1)
        self._outer.addWidget(self._footer_area)

    def get_native(self):
        return self._root

    def set_header(self, widget) -> None:
        _clear_layout(self._header_layout)
        self._header_layout.addWidget(_native(widget))
        self._header_area.show()

    def set_sidebar(self, sidebar) -> None:
        # Replace sidebar_placeholder in the splitter
        sidebar_widget = _native(sidebar)
        self._splitter.replaceWidget(0, sidebar_widget)
        self._sidebar_placeholder = sidebar_widget

    def set_content(self, widget) -> None:
        _clear_layout(self._content_layout)
        self._content_layout.addWidget(_native(widget))

    def set_footer(self, widget) -> None:
        _clear_layout(self._footer_layout)
        self._footer_layout.addWidget(_native(widget))
        self._footer_area.show()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _clear_layout(layout: QtWidgets.QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.setParent(None)


# ---------------------------------------------------------------------------
# IBreadcrumb — horizontal row of labels/buttons separated by "›"
# ---------------------------------------------------------------------------

class QtBreadcrumbAdapter:
    """Breadcrumb rendered as a horizontal row of QPushButton / QLabel items."""

    def __init__(self):
        self._widget = QtWidgets.QWidget()
        self._layout = QtWidgets.QHBoxLayout(self._widget)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.addStretch()
        self._click_cb = None
        self._items = []

    def get_native(self):
        return self._widget

    def set_items(self, items):
        self._items = list(items)
        # Remove all existing widgets
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

        for i, crumb in enumerate(items):
            label = crumb.get("label", "")
            path = crumb.get("path", "")
            is_last = (i == len(items) - 1)

            if i > 0:
                sep = QtWidgets.QLabel("›")
                sep.setStyleSheet("color: #9ca3af;")
                self._layout.addWidget(sep)

            if is_last or not path:
                lbl = QtWidgets.QLabel(label)
                lbl.setStyleSheet("color: #111827; font-weight: 500;")
                self._layout.addWidget(lbl)
            else:
                btn = QtWidgets.QPushButton(label)
                btn.setFlat(True)
                btn.setStyleSheet(
                    "QPushButton { color: #3b82f6; text-decoration: underline; "
                    "border: none; padding: 0; } "
                    "QPushButton:hover { color: #2563eb; }"
                )
                captured_path = path
                btn.clicked.connect(lambda checked=False, p=captured_path: self._on_click(p))
                self._layout.addWidget(btn)

        self._layout.addStretch()

    def on_click(self, fn):
        self._click_cb = fn

    def _on_click(self, path: str) -> None:
        if self._click_cb:
            self._click_cb(path)


# ---------------------------------------------------------------------------
# Patch QtWidgetFactory
# ---------------------------------------------------------------------------

def _register(factory_class):
    """Monkey-patch admin factory methods onto QtWidgetFactory."""
    from uniui.admin import ICard, IStatCard, ITable, ISidebar, IAppShell, IBreadcrumb

    def createCard(self) -> ICard:
        return QtCardAdapter()

    def createStatCard(self) -> IStatCard:
        return QtStatCardAdapter()

    def createTable(self) -> ITable:
        return QtTableAdapter()

    def createSidebar(self) -> ISidebar:
        return QtSidebarAdapter()

    def createAppShell(self) -> IAppShell:
        return QtAppShellAdapter()

    def createBreadcrumb(self) -> IBreadcrumb:
        return QtBreadcrumbAdapter()

    factory_class.createCard = createCard
    factory_class.createStatCard = createStatCard
    factory_class.createTable = createTable
    factory_class.createSidebar = createSidebar
    factory_class.createAppShell = createAppShell
    factory_class.createBreadcrumb = createBreadcrumb


# Auto-register when this module is imported
try:
    from uniui.qt import QtWidgetFactory
    _register(QtWidgetFactory)
except ImportError:
    pass
