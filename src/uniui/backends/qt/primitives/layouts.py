"""Layout and container primitives."""
from __future__ import annotations

from typing import Callable, List, Optional

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSplitter, QStackedWidget, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget,
)

from ....core import *
from ...._adapter_mixins import (
    ClearMixin, EnableMixin, NativeMixin, SelectionMixin, SizeMixin, TextMixin,
    VisibilityMixin,
)
from ....state import Handle, safe_call
from ....strategies import normalize_text, parse_float
from .helpers import ensure_qwidget, is_qlayout


class QTVBoxLayout(QtWidgets.QVBoxLayout):
    """Qt Vertical Box Layout - native implementation"""
    def __init__(self):
        super().__init__()

    def setAlignmentTop(self):
        super().setAlignment(QtCore.Qt.AlignTop)

    def addItem(self, item):
        if is_qlayout(item):
            super().addLayout(item)
        else:
            super().addWidget(item)

    def addStretch(self):
        super().addStretch()
class QTHBoxLayout(QtWidgets.QHBoxLayout):
    """Qt Horizontal Box Layout - native implementation"""
    def __init__(self):
        super().__init__()

    def setAlignmentTop(self):
        super().setAlignment(QtCore.Qt.AlignTop)

    def addItem(self, item):
        if is_qlayout(item):
            super().addLayout(item)
        else:
            super().addWidget(item)

    def addStretch(self):
        super().addStretch()
class QTTabWidget(QtWidgets.QTabWidget):
    """Qt Tab Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def addTab(self, item, tab_name):
        super().addTab(ensure_qwidget(item), tab_name)

    def removeTabs(self):
        while True:
            count = super().count()
            if count > 0:
                super().removeTab(count - 1)
            else:
                break

    def currentIndex(self):
        return super().currentIndex()

    def hide(self):
        super().hide()

    def show(self):
        super().show()
class QtVBoxAdapter(IVBoxLayout):
    """Qt VBox adapter - implements snake_case interface convention"""

    def __init__(self, native_layout: QTVBoxLayout):
        self._native = native_layout

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        self._native.addItem(widget.get_native())

    def add_stretch(self):
        self._native.addStretch()

    def set_alignment_top(self):
        self._native.setAlignmentTop()

    def add_item_with_spec(self, widget: IWidget, item):
        native = widget.get_native()
        stretch = int(item.grow) if item.grow > 0 else 0
        if is_qlayout(native):
            self._native.addLayout(native, stretch)
        else:
            self._native.addWidget(native, stretch)

    def set_spec(self, spec):
        self._native.setSpacing(spec.gap)
        p = spec.padding
        self._native.setContentsMargins(p, p, p, p)

    def clear(self):
        while self._native.count():
            item = self._native.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
class QtHBoxAdapter(IHBoxLayout):
    """Qt HBox adapter - implements snake_case interface convention"""

    def __init__(self, native_layout: QTHBoxLayout):
        self._native = native_layout

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        self._native.addItem(widget.get_native())

    def add_stretch(self):
        self._native.addStretch()

    def set_alignment_top(self):
        self._native.setAlignmentTop()

    def add_item_with_spec(self, widget: IWidget, item):
        native = widget.get_native()
        stretch = int(item.grow) if item.grow > 0 else 0
        if is_qlayout(native):
            self._native.addLayout(native, stretch)
        else:
            self._native.addWidget(native, stretch)

    def set_spec(self, spec):
        self._native.setSpacing(spec.gap)
        p = spec.padding
        self._native.setContentsMargins(p, p, p, p)

    def clear(self):
        while self._native.count():
            item = self._native.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
class QtTabWidgetAdapter(NativeMixin, VisibilityMixin, EnableMixin, SizeMixin, ITabWidget):
    """Qt TabWidget adapter - implements snake_case interface convention"""

    # ITabCapable
    def add_tab(self, widget: IWidget, name: str):
        self._native.addTab(widget.get_native(), name)

    def remove_tabs(self):
        self._native.removeTabs()

    def get_current_index(self) -> int:
        return self._native.currentIndex()
class _QFlowLayout(QtWidgets.QLayout):
    """Flow layout that wraps children to the next row when they overflow.

    Based on the Qt official FlowLayout example.
    """
    def __init__(self, parent=None, h_spacing=-1, v_spacing=-1):
        super().__init__(parent)
        self._h_space = h_spacing
        self._v_space = v_spacing
        self._item_list: List = []

    def addItem(self, item):
        self._item_list.append(item)

    def horizontalSpacing(self):
        if self._h_space >= 0:
            return self._h_space
        return self._smart_spacing(QtWidgets.QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self._v_space >= 0:
            return self._v_space
        return self._smart_spacing(QtWidgets.QStyle.PM_LayoutVerticalSpacing)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QtCore.QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QtCore.QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(left, top, -right, -bottom)
        x, y, line_height = effective.x(), effective.y(), 0

        for item in self._item_list:
            wid = item.widget()
            h_space = self.horizontalSpacing()
            if h_space == -1:
                h_space = wid.style().layoutSpacing(
                    QtWidgets.QSizePolicy.PushButton,
                    QtWidgets.QSizePolicy.PushButton,
                    QtCore.Qt.Horizontal)
            v_space = self.verticalSpacing()
            if v_space == -1:
                v_space = wid.style().layoutSpacing(
                    QtWidgets.QSizePolicy.PushButton,
                    QtWidgets.QSizePolicy.PushButton,
                    QtCore.Qt.Vertical)
            next_x = x + item.sizeHint().width() + h_space
            if next_x - h_space > effective.right() and line_height > 0:
                x = effective.x()
                y = y + line_height + v_space
                next_x = x + item.sizeHint().width() + h_space
                line_height = 0
            if not test_only:
                item.setGeometry(QtCore.QRect(
                    QtCore.QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + bottom

    def _smart_spacing(self, pm):
        parent = self.parent()
        if parent is None:
            return -1
        if parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        return self.spacing()
class _ResizeNotifier(QtWidgets.QWidget):
    """Invisible QWidget that fires a callback on resizeEvent — used by layout adapters."""
    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._callback(event.size().width())
class QtGridAdapter(IGrid):
    """Qt Grid adapter using QGridLayout."""

    def __init__(self, columns: int = 12):
        self._native = QtWidgets.QGridLayout()
        self._columns = columns
        self._auto_row = 0
        self._auto_col = 0
        self._resize_callbacks: List = []
        self._breakpoints = None
        self._last_mode: Optional[str] = None
        self._notifier: Optional[_ResizeNotifier] = None

    def get_native(self):
        return self._native

    def add_item(self, widget: IWidget, row: int = -1, col: int = -1,
                 row_span: int = 1, col_span: int = 1) -> None:
        native = widget.get_native()
        if row < 0 or col < 0:
            # Auto-place: fill columns left to right
            if self._auto_col + col_span > self._columns:
                self._auto_col = 0
                self._auto_row += 1
            r, c = self._auto_row, self._auto_col
            self._auto_col += col_span
        else:
            r, c = row, col
        self._native.addWidget(ensure_qwidget(native), r, c, row_span, col_span)

    def set_columns(self, count: int) -> None:
        self._columns = count
        # Adjust column stretches so all columns are equal
        for i in range(count):
            self._native.setColumnStretch(i, 1)

    def set_spec(self, spec: LayoutSpec) -> None:
        self._native.setSpacing(spec.gap)
        p = spec.padding
        self._native.setContentsMargins(p, p, p, p)

    def clear(self) -> None:
        while self._native.count():
            item = self._native.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._auto_row = 0
        self._auto_col = 0

    def on_resize(self, callback, breakpoints=None) -> Handle:
        from ....core import DEFAULT_BREAKPOINTS
        bp = breakpoints or DEFAULT_BREAKPOINTS
        self._breakpoints = bp
        self._resize_callbacks.append(callback)

        def _on_width(w):
            mode = bp.mode_for(w)
            if mode != self._last_mode:
                self._last_mode = mode
                for cb in self._resize_callbacks:
                    safe_call(cb, mode, backend="qt", component="Grid", method="on_resize")

        if self._notifier is None:
            self._notifier = _ResizeNotifier(_on_width)
            self._native.addWidget(self._notifier, 0, 0, 1, 1)
            self._notifier.hide()

        def cancel():
            if callback in self._resize_callbacks:
                self._resize_callbacks.remove(callback)
        return Handle(cancel)
class QtWrapAdapter(VisibilityMixin, EnableMixin, SizeMixin, IWrap):
    """Qt Wrap adapter using _QFlowLayout."""

    def __init__(self):
        self._flow = _QFlowLayout()
        # Wrap in a QWidget so it can be added to other layouts
        self._container = QtWidgets.QWidget()
        self._container.setLayout(self._flow)

    def get_native(self):
        return self._container

    def add_item(self, widget: IWidget) -> None:
        self._flow.addWidget(ensure_qwidget(widget.get_native()))

    def set_spec(self, spec: LayoutSpec) -> None:
        self._flow._h_space = spec.gap
        self._flow._v_space = spec.gap
        p = spec.padding
        self._flow.setContentsMargins(p, p, p, p)

    def clear(self) -> None:
        while self._flow.count():
            item = self._flow.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
class QtScrollViewAdapter(VisibilityMixin, EnableMixin, SizeMixin, IScrollView):
    """Qt ScrollView adapter using QScrollArea."""

    def __init__(self):
        self._native = QtWidgets.QScrollArea()
        self._native.setWidgetResizable(True)

    def get_native(self):
        return self._native

    def set_content(self, widget: IWidget) -> None:
        self._native.setWidget(ensure_qwidget(widget.get_native()))

    def set_max_height(self, height: int) -> None:
        self._native.setMaximumHeight(height)

    def set_max_width(self, width: int) -> None:
        self._native.setMaximumWidth(width)
class QtSplitPaneAdapter(VisibilityMixin, EnableMixin, SizeMixin, ISplitPane):
    """Qt SplitPane adapter using QSplitter."""

    def __init__(self, orientation: str = "horizontal"):
        from PySide2.QtCore import Qt
        qt_orient = Qt.Horizontal if orientation == "horizontal" else Qt.Vertical
        self._native = QtWidgets.QSplitter(qt_orient)
        self._orientation = orientation

    def get_native(self):
        return self._native

    def set_first(self, widget: IWidget) -> None:
        self._native.insertWidget(0, ensure_qwidget(widget.get_native()))

    def set_second(self, widget: IWidget) -> None:
        self._native.addWidget(ensure_qwidget(widget.get_native()))

    def set_orientation(self, orientation: str) -> None:
        from PySide2.QtCore import Qt
        self._native.setOrientation(
            Qt.Horizontal if orientation == "horizontal" else Qt.Vertical)
        self._orientation = orientation

    def set_sizes(self, ratio: float) -> None:
        total = self._native.width() if self._orientation == "horizontal" else self._native.height()
        if total <= 0:
            total = 1000  # fallback before widget is shown
        first = int(total * max(0.0, min(1.0, ratio)))
        second = total - first
        self._native.setSizes([first, second])
class QtOverlayAdapter(VisibilityMixin, EnableMixin, SizeMixin, IOverlay):
    """Qt Overlay adapter using QStackedWidget."""

    def __init__(self):
        self._native = QtWidgets.QStackedWidget()
        self._native.setMinimumWidth(0)
        self._native.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding
        )

    def get_native(self):
        return self._native

    def add_layer(self, widget: IWidget) -> None:
        self._native.addWidget(ensure_qwidget(widget.get_native()))

    def set_active_index(self, index: int) -> None:
        self._native.setCurrentIndex(index)

    def remove_layer(self, index: int) -> None:
        widget = self._native.widget(index)
        if widget is not None:
            self._native.removeWidget(widget)
            widget.deleteLater()

    def layer_count(self) -> int:
        return self._native.count()
