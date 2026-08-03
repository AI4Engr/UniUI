"""
Qt/PySide2 implementations of admin components.

Registered into QtWidgetFactory when imported (done automatically by uniui
when 'qt' framework is selected).
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple
import weakref

from PySide2 import QtWidgets, QtCore, QtGui

from uniui.admin import (
    IAppShell, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, ISidebar, IStatCard, ITable,
)
from uniui.admin_theme import get_admin_metrics, get_admin_tokens
from uniui.admin_visuals import CHART_TYPES, append_chart_point, normalized_series
from uniui.core import IWidget
from uniui.qt_effects import animate_value, motion_duration
from uniui.qt_icons import admin_icon


# ---------------------------------------------------------------------------
# Theme tokens
# ---------------------------------------------------------------------------
def _qt_tokens(dark: bool) -> Dict[str, str]:
    """Add temporary aliases used by the existing Qt renderer."""
    tokens = get_admin_tokens(dark)
    tokens.update({
        "sidebar_act": tokens["sidebar_active"],
        "sidebar_act_fg": tokens["sidebar_active_fg"],
        "row_sel": tokens["row_selected"],
        "row_sel_fg": tokens["row_selected_fg"],
    })
    return tokens


_LIGHT = _qt_tokens(False)
_DARK = _qt_tokens(True)
_M = get_admin_metrics()

_C = dict(_LIGHT)
_ADMIN_DARK = False
_THEMED_ADAPTERS = weakref.WeakSet()


def _card_style() -> str:
    return f"""
    QFrame[card="1"] {{
        background: {_C['surface']};
        border: 1px solid {_C['border']};
        border-radius: {_M['radius_large']}px;
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
    QTableWidget::item:hover {{
        background: {_C['surface_subtle']};
    }}
    QTableWidget::item:alternate {{
        background: {_C['row_alt']};
    }}
    QTableWidget::item:selected {{
        background: {_C['row_sel']};
        color: {_C['row_sel_fg']};
    }}
    QHeaderView::section {{
        background: {_C['surface']};
        color: {_C['text_muted']};
        font-weight: 600;
        font-size: {_M['stat_label_size']}px;
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
        padding: 14px 0;
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
        border-left: {_M['sidebar_edge_width']}px solid {_C['sidebar_edge']};
    }}
    QListWidget::item:disabled {{
        color: {_C['text_muted']};
        background: transparent;
    }}
    QListWidget::item:selected:active {{
        background: {_C['sidebar_act']};
        color: {_C['sidebar_act_fg']};
        border-left: {_M['sidebar_edge_width']}px solid {_C['sidebar_edge']};
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
        try:
            adapter.apply_theme()
        except RuntimeError as exc:
            if "already deleted" not in str(exc):
                raise
            _THEMED_ADAPTERS.discard(adapter)
    return _ADMIN_DARK


def _track_themed(adapter, native_widget) -> None:
    """Keep the adapter alive for as long as its native Qt widget is alive."""
    _THEMED_ADAPTERS.add(adapter)
    native_widget._uniui_theme_adapter = adapter
    native_widget.destroyed.connect(
        lambda *_args, tracked=adapter: _THEMED_ADAPTERS.discard(tracked)
    )


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


def _nav_icon(name: str, color: Optional[str] = None,
              selected_color: Optional[str] = None) -> QtGui.QIcon:
    try:
        return admin_icon(
            name,
            color or _C["sidebar_fg"],
            size=20,
            selected_color=selected_color or _C["sidebar_edge"],
        )
    except KeyError:
        return QtGui.QIcon()


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
        outer.setContentsMargins(22, 20, 22, 20)
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
            f"color: {_C['text']}; font-size: 16px; font-weight: 700; background: transparent;"
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
        self._frame.setMinimumWidth(0)
        self._frame.setFixedHeight(136)
        self._frame.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed
        )

        layout = QtWidgets.QVBoxLayout(self._frame)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(3)

        self._label_lbl = QtWidgets.QLabel("")
        self._label_lbl.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: {_M['stat_label_size']}px; font-weight: 600; "
            "background: transparent;"
        )

        self._value_lbl = QtWidgets.QLabel("—")
        self._value_lbl.setStyleSheet(
            f"color: {_C['text']}; font-size: {_M['stat_value_size']}px; font-weight: 700; background: transparent;"
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
        layout.addSpacing(1)
        layout.addWidget(self._value_lbl)
        layout.addWidget(self._unit_lbl)
        layout.addStretch()
        layout.addWidget(self._trend_lbl)

        self._frame.setStyleSheet(_card_style())
        _track_themed(self, self._frame)
        self.apply_theme()

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
        if self._status != "ok" and trend == 0:
            text, color = ("Needs attention" if self._status == "warn" else "Error"), _C[self._status]
        elif trend > 0:
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
        self._apply_trend()

    def apply_theme(self) -> None:
        self._label_lbl.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: {_M['stat_label_size']}px; font-weight: 600; background: transparent;"
        )
        self._value_lbl.setStyleSheet(
            f"color: {_C['text']}; font-size: {_M['stat_value_size']}px; font-weight: 700; background: transparent;"
        )
        self._unit_lbl.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: 11px; background: transparent;"
        )
        self._frame.setStyleSheet(_card_style())
        self._apply_trend()


# ---------------------------------------------------------------------------
# IMetricList
# ---------------------------------------------------------------------------

class QtMetricListAdapter(IMetricList):
    """Dense two-column key/value list for secondary metrics."""

    def __init__(self):
        self._frame = QtWidgets.QWidget()
        self._frame.setMinimumWidth(0)
        self._layout = QtWidgets.QVBoxLayout(self._frame)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._rows: List[Tuple[QtWidgets.QWidget, QtWidgets.QLabel, QtWidgets.QLabel]] = []
        _track_themed(self, self._frame)
        self.apply_theme()

    def get_native(self): return self._frame

    def set_items(self, items: List[Dict]) -> None:
        _clear_layout(self._layout)
        self._rows = []
        for index, item in enumerate(items):
            row = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(0, 8, 0, 8)
            label = QtWidgets.QLabel(str(item.get("label", "")))
            value = QtWidgets.QLabel(str(item.get("value", "")))
            value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            row_layout.addWidget(label, stretch=1)
            row_layout.addWidget(value)
            if index > 0:
                row.setProperty("metricDivider", "1")
            self._layout.addWidget(row)
            self._rows.append((row, label, value))
        self.apply_theme()

    def apply_theme(self) -> None:
        for row, label, value in self._rows:
            label.setStyleSheet(
                f"color: {_C['text_muted']}; font-size: {_M['stat_label_size']}px; background: transparent;"
            )
            value.setStyleSheet(
                f"color: {_C['text']}; font-size: 13px; font-weight: 600; background: transparent;"
            )
            if row.property("metricDivider"):
                row.setStyleSheet(f"border-top: 1px solid {_C['border']};")


# ---------------------------------------------------------------------------
# ITable
# ---------------------------------------------------------------------------


def _status_colors(value) -> Tuple[str, str]:
    status = str(value).strip().lower()
    if status in {"active", "delivered", "shipped", "success", "ok"}:
        return _C["status_ok_fg"], _C["status_ok_bg"]
    if status in {"processing", "pending", "warning", "warn"}:
        return _C["status_warn_fg"], _C["status_warn_bg"]
    if status in {"inactive", "cancelled", "failed", "error"}:
        return _C["status_error_fg"], _C["status_error_bg"]
    return _C["status_neutral_fg"], _C["status_neutral_bg"]


class _StatusPillDelegate(QtWidgets.QStyledItemDelegate):
    """Paint status values as compact semantic pills matching the Web table."""

    def paint(self, painter, option, index) -> None:
        base_option = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(base_option, index)
        base_option.text = ""
        super().paint(painter, base_option, index)

        text = str(index.data(QtCore.Qt.DisplayRole) or "")
        foreground, background = _status_colors(text)
        font = QtGui.QFont(option.font)
        font.setPixelSize(11)
        font.setWeight(QtGui.QFont.DemiBold)
        metrics = QtGui.QFontMetrics(font)
        pill_width = min(option.rect.width() - 16, metrics.horizontalAdvance(text) + 20)
        if pill_width <= 8:
            return
        pill = QtCore.QRect(
            option.rect.left() + 8,
            option.rect.center().y() - 12,
            pill_width,
            24,
        )
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(background))
        painter.drawRoundedRect(pill, 12, 12)
        painter.setFont(font)
        painter.setPen(QtGui.QColor(foreground))
        text = metrics.elidedText(
            text, QtCore.Qt.ElideRight, max(1, pill.width() - 12)
        )
        painter.drawText(pill, QtCore.Qt.AlignCenter, text)
        painter.restore()


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
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive
        )
        self._table.setShowGrid(False)
        self._table.setFocusPolicy(QtCore.Qt.StrongFocus)
        self._table.setWordWrap(False)
        self._table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._table.setMouseTracking(True)
        self._table.verticalHeader().setDefaultSectionSize(52)
        self._table.horizontalHeader().setFixedHeight(44)
        self._status_delegate = _StatusPillDelegate(self._table)

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
            [str(c.get("label", c.get("key", ""))).upper() for c in columns]
        )
        for i, col in enumerate(columns):
            if col.get("key") == "status":
                self._table.setItemDelegateForColumn(i, self._status_delegate)
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
            item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

    def apply_theme(self) -> None:
        self._container.setStyleSheet(f"background: {_C['surface']};")
        self._table.setStyleSheet(_table_style())
        self._overlay.setStyleSheet(
            f"color: {_C['text_muted']}; font-size: 14px; background: transparent;"
        )
        self._table.viewport().update()
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
# Gauge / Chart / Drawer
# ---------------------------------------------------------------------------


class _GaugeWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.label = ""
        self.value = 0.0
        self.unit = ""
        self.minimum = 0.0
        self.maximum = 100.0
        self.status = "ok"
        self.setMinimumSize(190, 180)
        self.setAccessibleName("Radial gauge")

    def paintEvent(self, _event) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        side = min(self.width(), self.height() - 28)
        arc_size = max(80.0, min(150.0, side - 28.0))
        rect = QtCore.QRectF(
            (self.width() - arc_size) / 2,
            10,
            arc_size,
            arc_size,
        )
        pen = QtGui.QPen(QtGui.QColor(_C["border"]), 13)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, -225 * 16, -270 * 16)

        span = max(1e-9, self.maximum - self.minimum)
        ratio = max(0.0, min(1.0, (self.value - self.minimum) / span))
        pen.setColor(QtGui.QColor(_C.get(self.status, _C["accent"])))
        painter.setPen(pen)
        painter.drawArc(rect, -225 * 16, int(-270 * 16 * ratio))

        value_font = QtGui.QFont(self.font())
        value_font.setPixelSize(25)
        value_font.setBold(True)
        painter.setFont(value_font)
        painter.setPen(QtGui.QColor(_C["text"]))
        center = rect.adjusted(0, 32, 0, -20)
        painter.drawText(center, QtCore.Qt.AlignCenter, f"{self.value:g}")

        unit_font = QtGui.QFont(self.font())
        unit_font.setPixelSize(11)
        painter.setFont(unit_font)
        painter.setPen(QtGui.QColor(_C["text_muted"]))
        painter.drawText(
            QtCore.QRectF(rect.left(), rect.center().y() + 17, rect.width(), 20),
            QtCore.Qt.AlignCenter,
            self.unit,
        )
        label_font = QtGui.QFont(self.font())
        label_font.setPixelSize(12)
        label_font.setWeight(QtGui.QFont.DemiBold)
        painter.setFont(label_font)
        painter.drawText(
            QtCore.QRectF(8, self.height() - 28, self.width() - 16, 20),
            QtCore.Qt.AlignCenter,
            self.label,
        )


class QtGaugeAdapter(IGauge):
    def __init__(self):
        self._widget = _GaugeWidget()
        self._target_value = 0.0
        _track_themed(self, self._widget)

    def get_native(self): return self._widget
    def set_label(self, label: str) -> None:
        self._widget.label = str(label); self._widget.update()
    def set_unit(self, unit: str) -> None:
        self._widget.unit = str(unit); self._widget.update()
    def set_range(self, minimum: float, maximum: float) -> None:
        minimum, maximum = float(minimum), float(maximum)
        if maximum <= minimum:
            maximum = minimum + 1.0
        self._widget.minimum, self._widget.maximum = minimum, maximum
        self._widget.update()
    def set_status(self, status: str) -> None:
        self._widget.status = status if status in {"ok", "warn", "error"} else "ok"
        self._widget.update()
    def set_value(self, value: float) -> None:
        self._target_value = float(value)
        animate_value(
            self._widget,
            self._widget.value,
            self._target_value,
            self._set_display_value,
        )
    def _set_display_value(self, value: float) -> None:
        self._widget.value = value
        self._widget.setAccessibleDescription(
            f"{self._widget.label}: {value:g} {self._widget.unit}".strip()
        )
        self._widget.update()
    def apply_theme(self) -> None: self._widget.update()


class _ChartWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.chart_type = "line"
        self.title = ""
        self.x_values: List = []
        self.series: List[Dict] = []
        self.setMinimumSize(320, 210)
        self.setAccessibleName("Data chart")

    def paintEvent(self, _event) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        title_height = 28 if self.title else 10
        plot = QtCore.QRectF(48, title_height, max(40, self.width() - 64),
                             max(40, self.height() - title_height - 28))
        if self.title:
            font = QtGui.QFont(self.font()); font.setPixelSize(13); font.setBold(True)
            painter.setFont(font); painter.setPen(QtGui.QColor(_C["text"]))
            painter.drawText(QtCore.QRectF(8, 2, self.width() - 16, 22),
                             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, self.title)
        values = [value for item in self.series for value in item.get("data", [])]
        if not values:
            painter.setPen(QtGui.QColor(_C["text_muted"]))
            painter.drawText(plot, QtCore.Qt.AlignCenter, "No data")
            return
        low, high = min(values), max(values)
        if low == high:
            low -= 1.0; high += 1.0
        padding = (high - low) * 0.08
        low -= padding; high += padding
        grid_pen = QtGui.QPen(QtGui.QColor(_C["border"]), 1)
        painter.setPen(grid_pen)
        for index in range(5):
            y = plot.top() + plot.height() * index / 4
            painter.drawLine(QtCore.QPointF(plot.left(), y), QtCore.QPointF(plot.right(), y))
        colors = [_C["accent"], _C["ok"], _C["warn"], _C["error"]]
        for series_index, item in enumerate(self.series):
            data = item.get("data", [])
            if not data:
                continue
            color = QtGui.QColor(colors[series_index % len(colors)])
            points = []
            for index, value in enumerate(data):
                x = plot.left() + plot.width() * index / max(1, len(data) - 1)
                y = plot.bottom() - ((value - low) / (high - low)) * plot.height()
                points.append(QtCore.QPointF(x, y))
            if self.chart_type == "bar":
                slot = plot.width() / max(1, len(data))
                bar_width = max(3.0, slot * 0.62 / max(1, len(self.series)))
                painter.setPen(QtCore.Qt.NoPen); painter.setBrush(color)
                for index, point in enumerate(points):
                    x = plot.left() + index * slot + slot * 0.19 + series_index * bar_width
                    painter.drawRoundedRect(
                        QtCore.QRectF(x, point.y(), bar_width, plot.bottom() - point.y()), 3, 3
                    )
                continue
            path = QtGui.QPainterPath(points[0])
            for point in points[1:]:
                path.lineTo(point)
            if self.chart_type == "area":
                area = QtGui.QPainterPath(path)
                area.lineTo(points[-1].x(), plot.bottom())
                area.lineTo(points[0].x(), plot.bottom())
                area.closeSubpath()
                fill = QtGui.QColor(color); fill.setAlpha(38)
                painter.fillPath(area, fill)
            pen = QtGui.QPen(color, 2.4)
            pen.setCapStyle(QtCore.Qt.RoundCap); pen.setJoinStyle(QtCore.Qt.RoundJoin)
            painter.setPen(pen); painter.setBrush(QtCore.Qt.NoBrush); painter.drawPath(path)


class QtChartAdapter(IChart):
    def __init__(self):
        self._widget = _ChartWidget()
        self._max_points = 120
        _track_themed(self, self._widget)

    def get_native(self): return self._widget
    def set_type(self, chart_type: str) -> None:
        self._widget.chart_type = chart_type if chart_type in CHART_TYPES else "line"
        self._widget.update()
    def set_title(self, title: str) -> None:
        self._widget.title = str(title); self._widget.update()
    def set_data(self, x: List, series: List[Dict]) -> None:
        self._widget.x_values = list(x)[-self._max_points:]
        self._widget.series = normalized_series(series)
        for item in self._widget.series:
            item["data"] = item["data"][-self._max_points:]
        self._widget.update()
    def append_data(self, x, values) -> None:
        append_chart_point(
            self._widget.x_values, self._widget.series, x, values, self._max_points
        )
        self._widget.update()
    def set_max_points(self, max_points: int) -> None:
        self._max_points = max(2, int(max_points))
        self._widget.x_values = self._widget.x_values[-self._max_points:]
        for item in self._widget.series:
            item["data"] = item["data"][-self._max_points:]
    def apply_theme(self) -> None: self._widget.update()


class QtDrawerAdapter(IDrawer):
    def __init__(self):
        self._dialog = QtWidgets.QDialog()
        self._dialog.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint)
        self._dialog.setModal(False)
        self._dialog.setFixedWidth(360)
        self._dialog.setProperty("adminDrawer", "1")
        layout = QtWidgets.QVBoxLayout(self._dialog)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(16)
        header = QtWidgets.QHBoxLayout()
        self._title = QtWidgets.QLabel("")
        self._title.setProperty("drawerTitle", "1")
        self._close_button = QtWidgets.QToolButton()
        self._close_button.setIcon(admin_icon("close", _C["text_muted"], 20))
        self._close_button.setAccessibleName("Close drawer")
        self._close_button.clicked.connect(self.close)
        header.addWidget(self._title, stretch=1)
        header.addWidget(self._close_button)
        self._content = QtWidgets.QWidget()
        self._content_layout = QtWidgets.QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(header)
        layout.addWidget(self._content, stretch=1)
        self._open = False
        self._animation = None
        _track_themed(self, self._dialog)
        self.apply_theme()

    def get_native(self): return self._dialog
    def set_title(self, title: str) -> None: self._title.setText(str(title))
    def set_content(self, widget) -> None:
        _clear_layout(self._content_layout)
        self._content_layout.addWidget(_as_widget(widget))
    def open(self) -> None:
        parent = QtWidgets.QApplication.activeWindow()
        if parent is not None and parent is not self._dialog:
            self._dialog.setParent(
                parent, QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint
            )
            height = parent.height()
            target = QtCore.QRect(parent.width() - 360, 0, 360, height)
            start = QtCore.QRect(parent.width(), 0, 360, height)
        else:
            screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
            target = QtCore.QRect(screen.right() - 359, screen.top(), 360, screen.height())
            start = QtCore.QRect(screen.right() + 1, screen.top(), 360, screen.height())
        self._dialog.setGeometry(start)
        self._dialog.show(); self._dialog.raise_()
        self._animate_geometry(start, target)
        self._open = True
    def close(self) -> None:
        if not self._dialog.isVisible():
            self._open = False; return
        start = self._dialog.geometry()
        target = QtCore.QRect(start.right() + 1, start.top(), start.width(), start.height())
        animation = self._animate_geometry(start, target)
        animation.finished.connect(self._dialog.hide)
        self._open = False
    def toggle(self) -> None: self.close() if self._open else self.open()
    def is_open(self) -> bool: return self._open
    def _animate_geometry(self, start, end):
        animation = QtCore.QPropertyAnimation(self._dialog, b"geometry", self._dialog)
        animation.setStartValue(start); animation.setEndValue(end)
        animation.setDuration(motion_duration(190))
        animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        animation.start(); self._animation = animation
        return animation
    def apply_theme(self) -> None:
        self._dialog.setStyleSheet(
            f"QDialog[adminDrawer='1'] {{background:{_C['surface']};"
            f"border-left:1px solid {_C['border']};}}"
            f"QLabel[drawerTitle='1'] {{color:{_C['text']};font-size:18px;"
            "font-weight:700;background:transparent;}"
            "QToolButton {background:transparent;border:none;padding:5px;}"
            f"QToolButton:hover {{background:{_C['surface_subtle']};border-radius:8px;}}"
        )
        self._close_button.setIcon(admin_icon("close", _C["text_muted"], 20))


# ---------------------------------------------------------------------------
# ISidebar
# ---------------------------------------------------------------------------

_SIDEBAR_EXPANDED = _M["sidebar_expanded"]
_SIDEBAR_COLLAPSED = _M["sidebar_collapsed"]
_SIDEBAR_MIN = _M["sidebar_min"]
_SIDEBAR_MAX = _M["sidebar_max"]


class QtSidebarAdapter(ISidebar):
    def __init__(self):
        self._list = QtWidgets.QListWidget()
        self._list.setAccessibleName("Primary navigation")
        self._list.setFocusPolicy(QtCore.Qt.StrongFocus)
        self._list.setUniformItemSizes(True)
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
            icon = _nav_icon(
                icon_name, _C["sidebar_fg"], _C["sidebar_edge"]
            )
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
        self._header_area.setAccessibleName("Application header")
        self._header_area.setStyleSheet(
            f"QWidget[shellHeader='1'] {{ background: {_C['header_bg']}; "
            f"border-bottom: 1px solid {_C['header_border']}; }}"
        )
        self._header_area.setFixedHeight(_M["header_height"])
        self._header_layout = QtWidgets.QHBoxLayout(self._header_area)
        self._header_layout.setContentsMargins(16, 0, 16, 0)
        self._header_layout.setSpacing(8)
        self._header_area.hide()

        # Body: a real splitter so users can resize the navigation rail.
        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self._splitter.setAccessibleName("Navigation and content splitter")
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
        self._content_wrap.setAccessibleName("Application content")
        self._content_wrap.setStyleSheet(
            f"QWidget[shellContent='1'] {{ background: {_C['bg']}; }}"
        )
        self._content_layout = QtWidgets.QVBoxLayout(self._content_wrap)
        padding = _M["content_padding"]
        self._content_layout.setContentsMargins(padding, 24, padding, padding)
        self._content_layout.setSpacing(0)
        self._content_scroll = QtWidgets.QScrollArea()
        self._content_scroll.setProperty("shellScroll", "1")
        self._content_scroll.setWidgetResizable(True)
        self._content_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._content_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._content_layout.addWidget(self._content_scroll)
        self._splitter.addWidget(self._content_wrap)

        # Footer strip
        self._footer_area = QtWidgets.QWidget()
        self._footer_area.setProperty("shellFooter", "1")
        self._footer_area.setAccessibleName("Application status bar")
        self._footer_area.setStyleSheet(
            f"QWidget[shellFooter='1'] {{ background: {_C['surface']}; "
            f"border-top: 1px solid {_C['border']}; }}"
        )
        self._footer_area.setFixedHeight(_M["footer_height"])
        self._footer_layout = QtWidgets.QHBoxLayout(self._footer_area)
        self._footer_layout.setContentsMargins(20, 0, 20, 0)
        self._footer_layout.setAlignment(QtCore.Qt.AlignVCenter)
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
        old_widget = self._content_scroll.takeWidget()
        if old_widget is not None:
            old_widget.setParent(None)
        content_widget = _as_widget(widget)
        content_widget.setMinimumWidth(0)
        self._content_scroll.setWidget(content_widget)

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
                self._splitter.setHandleWidth(0)
                self._splitter.setSizes([
                    _SIDEBAR_COLLAPSED,
                    max(1, width - _SIDEBAR_COLLAPSED),
                ])
            else:
                self._sidebar_adapter.set_collapsed(False)
                self._splitter.setHandleWidth(5)
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
        self._content_scroll.setStyleSheet(
            f"QScrollArea[shellScroll='1'] {{background:{_C['bg']};border:none;}}"
            f"QScrollArea[shellScroll='1'] > QWidget > QWidget {{background:{_C['bg']};}}"
        )
        self._splitter.setStyleSheet(
            f"QSplitter::handle {{ background: {_C['border']}; }}"
            f"QSplitter::handle:hover {{ background: {_C['accent']}; }}"
        )
        self._footer_area.setStyleSheet(
            f"QWidget[shellFooter='1'] {{ background: {_C['surface']}; "
            f"border-top: 1px solid {_C['border']}; }}"
        )
        footer_palette = self._footer_area.palette()
        footer_palette.setColor(
            QtGui.QPalette.WindowText, QtGui.QColor(_C["text_muted"])
        )
        self._footer_area.setPalette(footer_palette)


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
    def createCard(self)       -> ICard:       return QtCardAdapter()
    def createStatCard(self)   -> IStatCard:   return QtStatCardAdapter()
    def createMetricList(self) -> IMetricList: return QtMetricListAdapter()
    def createTable(self)      -> ITable:      return QtTableAdapter()
    def createSidebar(self)    -> ISidebar:    return QtSidebarAdapter()
    def createAppShell(self)   -> IAppShell:   return QtAppShellAdapter()
    def createBreadcrumb(self) -> IBreadcrumb: return QtBreadcrumbAdapter()
    def createGauge(self)      -> IGauge:      return QtGaugeAdapter()
    def createChart(self)      -> IChart:      return QtChartAdapter()
    def createDrawer(self)     -> IDrawer:     return QtDrawerAdapter()

    factory_class.createCard       = createCard
    factory_class.createStatCard   = createStatCard
    factory_class.createMetricList = createMetricList
    factory_class.createTable      = createTable
    factory_class.createSidebar    = createSidebar
    factory_class.createAppShell   = createAppShell
    factory_class.createBreadcrumb = createBreadcrumb
    factory_class.createGauge      = createGauge
    factory_class.createChart      = createChart
    factory_class.createDrawer     = createDrawer


try:
    from uniui.qt import QtWidgetFactory
    _register(QtWidgetFactory)
except ImportError:
    pass
