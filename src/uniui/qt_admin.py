"""
Qt/PySide2 implementations of admin components.

Registered into QtWidgetFactory when imported (done automatically by uniui
when 'qt' framework is selected).
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional
import weakref

from PySide2 import QtWidgets, QtCore, QtGui

from uniui.admin import ICard, IStatCard, ITable, ISidebar, IAppShell, IBreadcrumb
from uniui.core import IWidget


# ---------------------------------------------------------------------------
# Theme tokens
# ---------------------------------------------------------------------------
_LIGHT = {
    "bg":           "#f5f7fb",   # page background
    "surface":      "#ffffff",   # card / panel background
    "surface_subtle":"#f9fafb",
    "border":       "#e4e7ec",   # subtle border
    "border_strong":"#d0d5dd",
    "sidebar_bg":   "#101828",   # dark sidebar
    "sidebar_fg":   "#d0d5dd",   # sidebar text
    "sidebar_act":  "#344054",   # active item highlight
    "sidebar_hover":"#1d2939",
    "sidebar_edge": "#53b1fd",
    "sidebar_act_fg": "#ffffff",
    "header_bg":    "#ffffff",
    "header_border":"#eaecf0",
    "text":         "#101828",   # primary text
    "text_muted":   "#667085",   # secondary text
    "ok":           "#12b76a",
    "warn":         "#f79009",
    "error":        "#f04438",
    "accent":       "#2563eb",
    "accent_hover": "#1d4ed8",
    "accent_press": "#1e40af",
    "accent_soft":  "#eff6ff",
    "row_alt":      "#f9fafb",   # alternating table row
    "row_sel":      "#eff6ff",   # selected row
    "row_sel_fg":   "#1d4ed8",
    "input_bg":     "#ffffff",
    "disabled":     "#b2ccff",
    "scrollbar":    "#d0d5dd",
    "avatar_bg":    "#e0e7ff",
    "avatar_fg":    "#3730a3",
}

_DARK = {
    "bg":           "#0b1120",
    "surface":      "#111827",
    "surface_subtle":"#0f172a",
    "border":       "#263244",
    "border_strong":"#344054",
    "sidebar_bg":   "#070d19",
    "sidebar_fg":   "#cbd5e1",
    "sidebar_act":  "#172554",
    "sidebar_hover":"#111c30",
    "sidebar_edge": "#60a5fa",
    "sidebar_act_fg": "#ffffff",
    "header_bg":    "#111827",
    "header_border":"#263244",
    "text":         "#f8fafc",
    "text_muted":   "#94a3b8",
    "ok":           "#34d399",
    "warn":         "#fbbf24",
    "error":        "#fb7185",
    "accent":       "#3b82f6",
    "accent_hover": "#60a5fa",
    "accent_press": "#2563eb",
    "accent_soft":  "#172554",
    "row_alt":      "#0f172a",
    "row_sel":      "#172554",
    "row_sel_fg":   "#dbeafe",
    "input_bg":     "#0f172a",
    "disabled":     "#334155",
    "scrollbar":    "#475569",
    "avatar_bg":    "#312e81",
    "avatar_fg":    "#e0e7ff",
}

_C = dict(_LIGHT)
_ADMIN_DARK = False
_THEMED_ADAPTERS = weakref.WeakSet()


def _card_style() -> str:
    return f"""
    QFrame[card="1"] {{
        background: {_C['surface']};
        border: 1px solid {_C['border']};
        border-radius: 12px;
    }}
"""


def _table_style() -> str:
    return f"""
    QTableWidget {{
        background: {_C['surface']};
        border: 1px solid {_C['border']};
        border-radius: 10px;
        gridline-color: {_C['border']};
        font-size: 13px;
        color: {_C['text']};
        outline: none;
    }}
    QTableWidget::item {{
        padding: 0 14px;
        border: none;
    }}
    QTableWidget::item:alternate {{
        background: {_C['row_alt']};
    }}
    QTableWidget::item:selected {{
        background: {_C['row_sel']};
        color: {_C['row_sel_fg']};
    }}
    QHeaderView::section {{
        background: {_C['bg']};
        color: {_C['text_muted']};
        font-weight: 600;
        font-size: 12px;
        padding: 0 14px;
        border: none;
        border-bottom: 1px solid {_C['border']};
    }}
"""


def _sidebar_style() -> str:
    return f"""
    QListWidget {{
        background: {_C['sidebar_bg']};
        border: none;
        outline: none;
        padding: 12px 0;
    }}
    QListWidget::item {{
        color: {_C['sidebar_fg']};
        padding: 11px 14px;
        font-size: 13px;
        font-weight: 500;
        border-radius: 8px;
        margin: 2px 10px;
    }}
    QListWidget::item:hover {{
        background: {_C['sidebar_hover']};
    }}
    QListWidget::item:selected {{
        background: {_C['sidebar_act']};
        color: {_C['sidebar_act_fg']};
        border-left: 3px solid {_C['sidebar_edge']};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255,255,255,0.2);
        border-radius: 2px;
    }}
"""


def _breadcrumb_button_style() -> str:
    return f"""
    QPushButton {{
        color: {_C['accent']};
        background: transparent;
        border: none;
        padding: 0 2px;
        font-size: 13px;
        font-weight: 500;
        min-height: 0;
        min-width: 0;
    }}
    QPushButton:hover {{ color: {_C['accent_hover']}; }}
"""


def get_admin_palette() -> Dict[str, str]:
    """Return a copy of the active Admin design tokens."""
    return dict(_C)


def is_admin_dark() -> bool:
    return _ADMIN_DARK


def set_admin_theme(dark: bool) -> bool:
    """Switch every live Qt Admin adapter without rebuilding its widget tree."""
    global _ADMIN_DARK
    _ADMIN_DARK = bool(dark)
    _C.clear()
    _C.update(_DARK if _ADMIN_DARK else _LIGHT)
    for adapter in list(_THEMED_ADAPTERS):
        adapter.apply_theme()
    return _ADMIN_DARK


def _track_themed(adapter, native_widget) -> None:
    """Keep the adapter alive for as long as its native Qt widget is alive."""
    _THEMED_ADAPTERS.add(adapter)
    native_widget._uniui_theme_adapter = adapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _native(widget) -> QtWidgets.QWidget:
    """Extract Qt native from a UniUI widget."""
    if hasattr(widget, "get_native"):
        return widget.get_native()
    return widget


def _as_widget(widget) -> QtWidgets.QWidget:
    """Like _native but wraps a QLayout in a container QWidget if needed."""
    obj = _native(widget)
    if isinstance(obj, QtWidgets.QLayout):
        container = QtWidgets.QWidget()
        container.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        container.setStyleSheet("background: transparent;")
        container.setLayout(obj)
        return container
    return obj


def _clear_layout(layout: QtWidgets.QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.setParent(None)


def _label(text: str, bold: bool = False, size: int = 13,
           color: str = _C["text"]) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(text)
    lbl.setStyleSheet(
        f"color: {color}; font-size: {size}px;"
        + (" font-weight: 600;" if bold else "")
    )
    return lbl


def _nav_icon(name: str, color: str = "#98a2b3") -> QtGui.QIcon:
    """Draw a small backend-owned line icon; avoids platform-dependent emoji."""
    pixmap = QtGui.QPixmap(20, 20)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    pen = QtGui.QPen(QtGui.QColor(color), 1.7)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    pen.setJoinStyle(QtCore.Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(QtCore.Qt.NoBrush)

    if name == "dashboard":
        for rect in (
            QtCore.QRectF(3, 3, 5, 5), QtCore.QRectF(12, 3, 5, 5),
            QtCore.QRectF(3, 12, 5, 5), QtCore.QRectF(12, 12, 5, 5),
        ):
            painter.drawRoundedRect(rect, 1.2, 1.2)
    elif name == "users":
        painter.drawEllipse(QtCore.QRectF(7, 3, 6, 6))
        painter.drawArc(QtCore.QRectF(4, 9, 12, 8), 10 * 16, 160 * 16)
        painter.drawEllipse(QtCore.QRectF(2.5, 6, 4, 4))
        painter.drawEllipse(QtCore.QRectF(13.5, 6, 4, 4))
    elif name == "settings":
        painter.drawLine(3, 5, 17, 5)
        painter.drawLine(3, 10, 17, 10)
        painter.drawLine(3, 15, 17, 15)
        painter.setBrush(QtGui.QColor(_C["sidebar_bg"]))
        painter.drawEllipse(QtCore.QRectF(6, 3, 4, 4))
        painter.drawEllipse(QtCore.QRectF(11, 8, 4, 4))
        painter.drawEllipse(QtCore.QRectF(5, 13, 4, 4))
    else:
        painter.end()
        return QtGui.QIcon()

    painter.end()
    return QtGui.QIcon(pixmap)


# ---------------------------------------------------------------------------
# ICard
# ---------------------------------------------------------------------------

class QtCardAdapter(ICard):
    def __init__(self):
        self._frame = QtWidgets.QFrame()
        self._frame.setProperty("card", "1")
        self._frame.setMinimumWidth(0)
        self._frame.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding
        )
        self._frame.setStyleSheet(_card_style())

        outer = QtWidgets.QVBoxLayout(self._frame)
        outer.setContentsMargins(20, 18, 20, 20)
        outer.setSpacing(12)

        # Header row: title/subtitle on the left, optional action on the right.
        header = QtWidgets.QWidget()
        header.setStyleSheet("background: transparent;")
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        title_stack = QtWidgets.QWidget()
        title_stack.setStyleSheet("background: transparent;")
        title_layout = QtWidgets.QVBoxLayout(title_stack)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(3)

        self._title_lbl = _label("", bold=True, size=16)
        self._title_lbl.hide()
        self._subtitle_lbl = _label("", size=12, color=_C["text_muted"])
        self._subtitle_lbl.hide()
        title_layout.addWidget(self._title_lbl)
        title_layout.addWidget(self._subtitle_lbl)
        header_layout.addWidget(title_stack, stretch=1)

        self._action_area = QtWidgets.QWidget()
        self._action_area.setStyleSheet("background: transparent;")
        self._action_layout = QtWidgets.QHBoxLayout(self._action_area)
        self._action_layout.setContentsMargins(0, 0, 0, 0)
        self._action_layout.setSpacing(8)
        self._action_area.hide()
        header_layout.addWidget(self._action_area, alignment=QtCore.Qt.AlignTop)

        self._content_area = QtWidgets.QWidget()
        self._content_area.setStyleSheet("background: transparent;")
        self._content_layout = QtWidgets.QVBoxLayout(self._content_area)
        self._content_layout.setContentsMargins(0, 2, 0, 0)
        self._content_layout.setSpacing(0)

        outer.addWidget(header)
        outer.addWidget(self._content_area, stretch=1)
        _track_themed(self, self._frame)
        self.apply_theme()

    def get_native(self): return self._frame

    def set_title(self, title: str) -> None:
        self._title_lbl.setText(title)
        self._title_lbl.setVisible(bool(title))

    def set_subtitle(self, subtitle: str) -> None:
        self._subtitle_lbl.setText(subtitle)
        self._subtitle_lbl.setVisible(bool(subtitle))

    def set_content(self, widget) -> None:
        _clear_layout(self._content_layout)
        self._content_layout.addWidget(_as_widget(widget))

    def set_action(self, widget) -> None:
        _clear_layout(self._action_layout)
        self._action_layout.addWidget(_as_widget(widget))
        self._action_area.show()

    def apply_theme(self) -> None:
        self._frame.setStyleSheet(_card_style())
        self._title_lbl.setStyleSheet(
            f"color: {_C['text']}; font-size: 16px; font-weight: 600; background: transparent;"
        )
        self._subtitle_lbl.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: 12px; background: transparent;"
        )


# ---------------------------------------------------------------------------
# IStatCard
# ---------------------------------------------------------------------------

class QtStatCardAdapter(IStatCard):
    def __init__(self):
        self._frame = QtWidgets.QFrame()
        self._frame.setProperty("card", "1")
        self._status = "ok"
        self._trend = 0.0
        self._frame.setMinimumWidth(150)
        self._frame.setFixedHeight(136)
        self._frame.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed
        )

        layout = QtWidgets.QVBoxLayout(self._frame)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(3)

        self._label_lbl = QtWidgets.QLabel("")
        self._label_lbl.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: 12px; font-weight: 600; "
            "background: transparent;"
        )

        self._value_lbl = QtWidgets.QLabel("—")
        self._value_lbl.setStyleSheet(
            f"color: {_C['text']}; font-size: 29px; font-weight: 700; background: transparent;"
        )

        self._unit_lbl = QtWidgets.QLabel("")
        self._unit_lbl.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: 11px; background: transparent;"
        )
        self._unit_lbl.hide()

        self._trend_lbl = QtWidgets.QLabel("")
        self._trend_lbl.setMinimumWidth(0)
        self._trend_lbl.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred
        )
        self._trend_lbl.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: 12px; font-weight: 600; background: transparent;"
        )

        layout.addWidget(self._label_lbl)
        layout.addSpacing(3)
        layout.addWidget(self._value_lbl)
        layout.addWidget(self._unit_lbl)
        layout.addStretch()
        layout.addWidget(self._trend_lbl)

        _track_themed(self, self._frame)
        self.apply_theme()

    def _set_border_color(self, color: str) -> None:
        self._frame.setStyleSheet(
            _card_style() +
            f"QFrame[card='1'] {{ border-top: 3px solid {color}; }}"
        )

    def get_native(self): return self._frame

    def set_label(self, label: str) -> None:
        self._label_lbl.setText(label)
    def set_value(self, value: str) -> None:
        self._value_lbl.setText(str(value))

    def set_unit(self, unit: str) -> None:
        self._unit_lbl.setText(unit)
        self._unit_lbl.setVisible(bool(unit))

    def set_trend(self, trend: float) -> None:
        self._trend = float(trend)
        self._apply_trend()

    def _apply_trend(self) -> None:
        trend = self._trend
        if trend > 0:
            text, color = f"↗  {trend:.1f}%  vs last period", _C["ok"]
        elif trend < 0:
            text, color = f"↘  {abs(trend):.1f}%  vs last period", _C["error"]
        else:
            text, color = "—  No change", _C["text_muted"]
        self._trend_lbl.setText(text)
        self._trend_lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: 600; background: transparent;"
        )

    def set_status(self, status: str) -> None:
        self._status = status if status in {"ok", "warn", "error"} else "ok"
        self._set_border_color(_C[self._status])

    def apply_theme(self) -> None:
        self._label_lbl.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: 12px; font-weight: 600; background: transparent;"
        )
        self._value_lbl.setStyleSheet(
            f"color: {_C['text']}; font-size: 29px; font-weight: 700; background: transparent;"
        )
        self._unit_lbl.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: 11px; background: transparent;"
        )
        self._set_border_color(_C[self._status])
        self._apply_trend()


# ---------------------------------------------------------------------------
# ITable
# ---------------------------------------------------------------------------

class QtTableAdapter(ITable):
    def __init__(self):
        self._container = QtWidgets.QWidget()
        self._container.setMinimumWidth(0)
        self._container.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding
        )
        self._container.setStyleSheet(f"background: {_C['surface']};")
        vbox = QtWidgets.QVBoxLayout(self._container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        self._table = QtWidgets.QTableWidget()
        self._table.setStyleSheet(_table_style())
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive
        )
        self._table.setShowGrid(False)
        self._table.setFocusPolicy(QtCore.Qt.NoFocus)
        self._table.setWordWrap(False)
        self._table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._table.setMouseTracking(True)
        self._table.verticalHeader().setDefaultSectionSize(44)
        self._table.horizontalHeader().setFixedHeight(40)

        self._overlay = QtWidgets.QLabel("")
        self._overlay.setAlignment(QtCore.Qt.AlignCenter)
        self._overlay.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: 14px; background: transparent;"
        )
        self._overlay.hide()

        vbox.addWidget(self._table)
        vbox.addWidget(self._overlay)

        self._columns: List[Dict] = []
        self._rows: List[Dict] = []
        self._row_click_cb: Optional[Callable] = None
        self._table.cellClicked.connect(self._on_cell_clicked)
        _track_themed(self, self._container)
        self.apply_theme()

    def get_native(self): return self._container

    def set_columns(self, columns: List[Dict]) -> None:
        self._columns = columns
        self._table.setColumnCount(len(columns))
        self._table.setHorizontalHeaderLabels(
            [c.get("label", c.get("key", "")) for c in columns]
        )
        for i, col in enumerate(columns):
            if "width" in col:
                self._table.setColumnWidth(i, col["width"])
                self._table.horizontalHeader().setSectionResizeMode(
                    i, QtWidgets.QHeaderView.Fixed
                )

    def set_rows(self, rows: List[Dict]) -> None:
        self._rows = rows
        self._table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, col in enumerate(self._columns):
                key = col.get("key", "")
                item = QtWidgets.QTableWidgetItem(str(row.get(key, "")))
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self._style_item(item, key, row.get(key, ""))
                self._table.setItem(r_idx, c_idx, item)

    def _style_item(self, item, key: str, raw_value) -> None:
        if key in {"amount", "total", "price"}:
            item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        elif key == "status":
            value = str(raw_value).lower()
            color = {
                "active": _C["ok"], "delivered": _C["ok"],
                "shipped": _C["accent"], "processing": _C["warn"],
                "inactive": _C["text_muted"], "cancelled": _C["error"],
                "failed": _C["error"], "error": _C["error"],
            }.get(value, _C["text"])
            item.setForeground(QtGui.QColor(color))
            font = item.font()
            font.setBold(True)
            item.setFont(font)

    def apply_theme(self) -> None:
        self._container.setStyleSheet(f"background: {_C['surface']};")
        self._table.setStyleSheet(_table_style())
        self._overlay.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: 14px; background: transparent;"
        )
        for r_idx, row in enumerate(self._rows):
            for c_idx, col in enumerate(self._columns):
                item = self._table.item(r_idx, c_idx)
                if item is not None:
                    key = col.get("key", "")
                    self._style_item(item, key, row.get(key, ""))

    def set_loading(self, loading: bool) -> None:
        if loading:
            self._table.hide()
            self._overlay.setText("Loading…")
            self._overlay.show()
        else:
            self._overlay.hide()
            self._table.show()

    def set_error(self, message: str) -> None:
        if message:
            self._table.hide()
            self._overlay.setText(f"⚠  {message}")
            self._overlay.show()
        else:
            self._overlay.hide()
            self._table.show()

    def on_row_click(self, fn: Callable[[Dict], None]) -> None:
        self._row_click_cb = fn

    def _on_cell_clicked(self, row: int, col: int) -> None:
        if self._row_click_cb and 0 <= row < len(self._rows):
            self._row_click_cb(self._rows[row])


# ---------------------------------------------------------------------------
# ISidebar
# ---------------------------------------------------------------------------

_SIDEBAR_EXPANDED = 236
_SIDEBAR_COLLAPSED = 72
_SIDEBAR_MIN = 168
_SIDEBAR_MAX = 360


class QtSidebarAdapter(ISidebar):
    def __init__(self):
        self._list = QtWidgets.QListWidget()
        self._list.setStyleSheet(_sidebar_style())
        self._list.setMinimumWidth(_SIDEBAR_MIN)
        self._list.setMaximumWidth(_SIDEBAR_MAX)
        self._list.setIconSize(QtCore.QSize(18, 18))
        self._list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._keys: List[str] = []
        self._labels: List[str] = []
        self._icons: List[str] = []
        self._select_cb: Optional[Callable] = None
        self._collapsed = False
        self._list.currentRowChanged.connect(self._on_row_changed)
        _track_themed(self, self._list)
        self.apply_theme()

    def get_native(self): return self._list

    def add_item(self, key: str, label: str, icon: str = "") -> None:
        self._keys.append(key)
        self._labels.append(label)
        self._icons.append(icon)
        text = self._item_text(label, icon)
        item = QtWidgets.QListWidgetItem(text)
        named_icon = _nav_icon(icon)
        if not named_icon.isNull():
            item.setIcon(named_icon)
        item.setData(QtCore.Qt.UserRole, key)
        item.setToolTip(label)
        item.setSizeHint(QtCore.QSize(0, 44))
        if self._collapsed:
            item.setTextAlignment(QtCore.Qt.AlignCenter)
        self._list.addItem(item)

    def set_active(self, key: str) -> None:
        if key in self._keys:
            self._list.blockSignals(True)
            self._list.setCurrentRow(self._keys.index(key))
            self._list.blockSignals(False)

    def on_select(self, fn: Callable[[str], None]) -> None:
        self._select_cb = fn

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        if collapsed:
            self._list.setMinimumWidth(_SIDEBAR_COLLAPSED)
            self._list.setMaximumWidth(_SIDEBAR_COLLAPSED)
        else:
            self._list.setMinimumWidth(_SIDEBAR_MIN)
            self._list.setMaximumWidth(_SIDEBAR_MAX)
        for i, (label, icon) in enumerate(zip(self._labels, self._icons)):
            item = self._list.item(i)
            item.setText(self._item_text(label, icon))
            item.setTextAlignment(
                QtCore.Qt.AlignCenter if collapsed else QtCore.Qt.AlignVCenter
            )

    def _item_text(self, label: str, icon: str) -> str:
        if icon in {"dashboard", "users", "settings"}:
            return "" if self._collapsed else label
        if self._collapsed:
            return icon or (label[:1].upper() if label else "?")
        return f"{icon}   {label}" if icon else label

    def apply_theme(self) -> None:
        self._list.setStyleSheet(_sidebar_style())
        for i, icon_name in enumerate(self._icons):
            icon = _nav_icon(icon_name, _C["sidebar_fg"])
            if not icon.isNull():
                self._list.item(i).setIcon(icon)

    def _on_row_changed(self, row: int) -> None:
        if self._select_cb and 0 <= row < len(self._keys):
            self._select_cb(self._keys[row])


# ---------------------------------------------------------------------------
# IAppShell
# ---------------------------------------------------------------------------

class _ResponsiveShellWidget(QtWidgets.QWidget):
    def __init__(self, on_resize):
        super().__init__()
        self._on_resize = on_resize

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._on_resize(event.size().width())


class QtAppShellAdapter(IAppShell):
    def __init__(self):
        self._root = _ResponsiveShellWidget(self._on_resize)
        self._root.setProperty("appShell", "1")
        self._root.setStyleSheet(
            f"QWidget[appShell='1'] {{ background: {_C['bg']}; }}"
        )

        outer = QtWidgets.QVBoxLayout(self._root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header strip
        self._header_area = QtWidgets.QWidget()
        self._header_area.setProperty("shellHeader", "1")
        self._header_area.setStyleSheet(
            f"QWidget[shellHeader='1'] {{ background: {_C['header_bg']}; "
            f"border-bottom: 1px solid {_C['header_border']}; }}"
        )
        self._header_area.setFixedHeight(64)
        self._header_layout = QtWidgets.QHBoxLayout(self._header_area)
        self._header_layout.setContentsMargins(16, 0, 16, 0)
        self._header_layout.setSpacing(8)
        self._header_area.hide()

        # Body: a real splitter so users can resize the navigation rail.
        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setOpaqueResize(True)
        self._splitter.setHandleWidth(5)
        self._splitter.splitterMoved.connect(self._on_splitter_moved)

        # Sidebar slot — starts empty
        self._sidebar_widget: Optional[QtWidgets.QWidget] = None
        self._sidebar_adapter = None
        self._compact_mode: Optional[bool] = None
        self._saved_sidebar_width = _SIDEBAR_EXPANDED

        # Content area
        self._content_wrap = QtWidgets.QWidget()
        self._content_wrap.setProperty("shellContent", "1")
        self._content_wrap.setStyleSheet(
            f"QWidget[shellContent='1'] {{ background: {_C['bg']}; }}"
        )
        self._content_layout = QtWidgets.QVBoxLayout(self._content_wrap)
        self._content_layout.setContentsMargins(28, 24, 28, 28)
        self._content_layout.setSpacing(0)
        self._splitter.addWidget(self._content_wrap)

        # Footer strip
        self._footer_area = QtWidgets.QWidget()
        self._footer_area.setStyleSheet(
            f"background: {_C['surface']}; border-top: 1px solid {_C['border']};"
        )
        self._footer_layout = QtWidgets.QHBoxLayout(self._footer_area)
        self._footer_layout.setContentsMargins(16, 8, 16, 8)
        self._footer_area.hide()

        outer.addWidget(self._header_area)
        outer.addWidget(self._splitter, stretch=1)
        outer.addWidget(self._footer_area)
        _track_themed(self, self._root)
        self.apply_theme()

    def get_native(self): return self._root

    def set_header(self, widget) -> None:
        _clear_layout(self._header_layout)
        self._header_layout.addWidget(_as_widget(widget), stretch=1)
        self._header_area.show()

    def set_sidebar(self, sidebar) -> None:
        self._sidebar_adapter = sidebar if hasattr(sidebar, "set_collapsed") else None
        sidebar_widget = _as_widget(sidebar)
        if self._sidebar_widget is None:
            self._splitter.insertWidget(0, sidebar_widget)
        else:
            old_widget = self._splitter.replaceWidget(0, sidebar_widget)
            if old_widget is not None:
                old_widget.setParent(None)
        self._sidebar_widget = sidebar_widget
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([
            self._saved_sidebar_width,
            max(1, self._root.width() - self._saved_sidebar_width),
        ])
        self._on_resize(self._root.width())

    def set_content(self, widget) -> None:
        _clear_layout(self._content_layout)
        self._content_layout.addWidget(_as_widget(widget))

    def set_footer(self, widget) -> None:
        _clear_layout(self._footer_layout)
        self._footer_layout.addWidget(_as_widget(widget))
        self._footer_area.show()

    def _on_resize(self, width: int) -> None:
        compact = 0 < width < 1020
        if self._sidebar_adapter is not None and compact != self._compact_mode:
            if compact:
                current = self._sidebar_widget.width() if self._sidebar_widget else 0
                if current >= _SIDEBAR_MIN:
                    self._saved_sidebar_width = current
                self._sidebar_adapter.set_collapsed(True)
                self._splitter.setSizes([
                    _SIDEBAR_COLLAPSED,
                    max(1, width - _SIDEBAR_COLLAPSED),
                ])
            else:
                self._sidebar_adapter.set_collapsed(False)
                restored = max(
                    _SIDEBAR_MIN, min(_SIDEBAR_MAX, self._saved_sidebar_width)
                )
                self._splitter.setSizes([restored, max(1, width - restored)])
            self._compact_mode = compact
        margin = 18 if compact else 28
        self._content_layout.setContentsMargins(margin, 22, margin, margin)

    def _on_splitter_moved(self, _pos: int, _index: int) -> None:
        if self._compact_mode is False and self._sidebar_widget is not None:
            width = self._sidebar_widget.width()
            if _SIDEBAR_MIN <= width <= _SIDEBAR_MAX:
                self._saved_sidebar_width = width

    def apply_theme(self) -> None:
        self._root.setStyleSheet(
            f"QWidget[appShell='1'] {{ background: {_C['bg']}; }}"
        )
        self._header_area.setStyleSheet(
            f"QWidget[shellHeader='1'] {{ background: {_C['header_bg']}; "
            f"border-bottom: 1px solid {_C['header_border']}; }}"
        )
        self._content_wrap.setStyleSheet(
            f"QWidget[shellContent='1'] {{ background: {_C['bg']}; }}"
        )
        self._splitter.setStyleSheet(
            f"QSplitter::handle {{ background: {_C['border']}; }}"
            f"QSplitter::handle:hover {{ background: {_C['accent']}; }}"
        )
        self._footer_area.setStyleSheet(
            f"background: {_C['surface']}; border-top: 1px solid {_C['border']};"
        )


# ---------------------------------------------------------------------------
# IBreadcrumb
# ---------------------------------------------------------------------------

class QtBreadcrumbAdapter(IBreadcrumb):
    def __init__(self):
        self._widget = QtWidgets.QWidget()
        self._widget.setStyleSheet("background: transparent;")
        self._layout = QtWidgets.QHBoxLayout(self._widget)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._click_cb = None
        self._items = []
        _track_themed(self, self._widget)

    def get_native(self): return self._widget

    def set_items(self, items) -> None:
        _clear_layout(self._layout)
        items = list(items)
        self._items = items
        for i, crumb in enumerate(items):
            label = crumb.get("label", "")
            path  = crumb.get("path", "")
            is_last = (i == len(items) - 1)

            if i > 0:
                sep = QtWidgets.QLabel("›")
                sep.setStyleSheet(
                    f"color: {_C['text_muted']}; font-size: 13px; background: transparent;"
                )
                self._layout.addWidget(sep)

            if is_last or not path:
                lbl = QtWidgets.QLabel(label)
                lbl.setStyleSheet(
                    f"color: {_C['text']}; font-size: 13px; font-weight: 600;"
                    " background: transparent;"
                )
                self._layout.addWidget(lbl)
            else:
                btn = QtWidgets.QPushButton(label)
                btn.setFlat(True)
                btn.setCursor(QtCore.Qt.PointingHandCursor)
                btn.setStyleSheet(_breadcrumb_button_style())
                btn.setSizePolicy(
                    QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
                )
                captured = path
                btn.clicked.connect(
                    lambda checked=False, p=captured: self._on_click(p)
                )
                self._layout.addWidget(btn)

        self._layout.addStretch()

    def on_click(self, fn) -> None:
        self._click_cb = fn

    def _on_click(self, path: str) -> None:
        if self._click_cb:
            self._click_cb(path)

    def apply_theme(self) -> None:
        self._widget.setStyleSheet("background: transparent;")
        if self._items:
            self.set_items(self._items)


# ---------------------------------------------------------------------------
# Patch QtWidgetFactory
# ---------------------------------------------------------------------------

def _register(factory_class):
    from uniui.admin import ICard, IStatCard, ITable, ISidebar, IAppShell, IBreadcrumb

    def createCard(self)       -> ICard:       return QtCardAdapter()
    def createStatCard(self)   -> IStatCard:   return QtStatCardAdapter()
    def createTable(self)      -> ITable:      return QtTableAdapter()
    def createSidebar(self)    -> ISidebar:    return QtSidebarAdapter()
    def createAppShell(self)   -> IAppShell:   return QtAppShellAdapter()
    def createBreadcrumb(self) -> IBreadcrumb: return QtBreadcrumbAdapter()

    factory_class.createCard       = createCard
    factory_class.createStatCard   = createStatCard
    factory_class.createTable      = createTable
    factory_class.createSidebar    = createSidebar
    factory_class.createAppShell   = createAppShell
    factory_class.createBreadcrumb = createBreadcrumb


try:
    from uniui.qt import QtWidgetFactory
    _register(QtWidgetFactory)
except ImportError:
    pass
