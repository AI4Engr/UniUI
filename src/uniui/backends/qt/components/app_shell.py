"""Qt IAppShell: header, sidebar, content, and footer in one frame."""
from __future__ import annotations

from typing import Optional

from PySide2 import QtCore, QtGui, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import IAppShell
from ....models.navigation import (
    SIDEBAR_COLLAPSED, SIDEBAR_EXPANDED, SIDEBAR_MIN, SIDEBAR_MAX, clamp_width,
)
from ..runtime import C, M, as_widget, clear_layout, track_themed

class _ResponsiveShellWidget(QtWidgets.QWidget):
    def __init__(self, on_resize):
        super().__init__()
        self._on_resize = on_resize

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._on_resize(event.size().width())


class QtAppShellAdapter(VisibilityMixin, EnableMixin, SizeMixin, IAppShell):
    def __init__(self):
        self._root = _ResponsiveShellWidget(self._on_resize)
        self._root.setProperty("appShell", "1")
        self._root.setStyleSheet(
            f"QWidget[appShell='1'] {{ background: {C['bg']}; }}"
        )

        outer = QtWidgets.QVBoxLayout(self._root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header strip
        self._header_area = QtWidgets.QWidget()
        self._header_area.setProperty("shellHeader", "1")
        self._header_area.setAccessibleName("Application header")
        self._header_area.setStyleSheet(
            f"QWidget[shellHeader='1'] {{ background: {C['header_bg']}; "
            f"border-bottom: 1px solid {C['header_border']}; }}"
        )
        self._header_area.setFixedHeight(M["header_height"])
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
        self._saved_sidebar_width = SIDEBAR_EXPANDED

        # Content area
        self._content_wrap = QtWidgets.QWidget()
        self._content_wrap.setProperty("shellContent", "1")
        self._content_wrap.setAccessibleName("Application content")
        self._content_wrap.setStyleSheet(
            f"QWidget[shellContent='1'] {{ background: {C['bg']}; }}"
        )
        self._content_layout = QtWidgets.QVBoxLayout(self._content_wrap)
        padding = M["content_padding"]
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_scroll = QtWidgets.QScrollArea()
        self._content_scroll.setProperty("shellScroll", "1")
        self._content_scroll.setWidgetResizable(True)
        self._content_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._content_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # Margins live on the viewport, not the outer layout: the scrollbar is
        # drawn at the QScrollArea's own right edge, so a right margin on
        # content_layout would push the scrollbar itself away from the
        # window edge, not add breathing room between the scrollbar and the
        # cards. setViewportMargins keeps the scrollbar flush with the shell
        # edge while still padding the content around it on every side.
        self._content_scroll.setViewportMargins(padding, 24, padding, padding)
        self._content_layout.addWidget(self._content_scroll)
        self._splitter.addWidget(self._content_wrap)

        # Footer strip
        self._footer_area = QtWidgets.QWidget()
        self._footer_area.setProperty("shellFooter", "1")
        self._footer_area.setAccessibleName("Application status bar")
        self._footer_area.setStyleSheet(
            f"QWidget[shellFooter='1'] {{ background: {C['surface']}; "
            f"border-top: 1px solid {C['border']}; }}"
        )
        self._footer_area.setFixedHeight(M["footer_height"])
        self._footer_layout = QtWidgets.QHBoxLayout(self._footer_area)
        self._footer_layout.setContentsMargins(20, 0, 20, 0)
        self._footer_layout.setAlignment(QtCore.Qt.AlignVCenter)
        self._footer_area.hide()

        outer.addWidget(self._header_area)
        outer.addWidget(self._splitter, stretch=1)
        outer.addWidget(self._footer_area)
        track_themed(self, self._root)
        self.apply_theme()

    def get_native(self): return self._root

    def set_header(self, widget) -> None:
        clear_layout(self._header_layout)
        self._header_layout.addWidget(as_widget(widget), stretch=1)
        self._header_area.show()

    def set_sidebar(self, sidebar) -> None:
        self._sidebar_adapter = sidebar if hasattr(sidebar, "set_collapsed") else None
        sidebar_widget = as_widget(sidebar)
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
        content_widget = as_widget(widget)
        content_widget.setMinimumWidth(0)
        self._content_scroll.setWidget(content_widget)

    def set_footer(self, widget) -> None:
        clear_layout(self._footer_layout)
        self._footer_layout.addWidget(as_widget(widget))
        self._footer_area.show()

    def _on_resize(self, width: int) -> None:
        compact = 0 < width < 1020
        if self._sidebar_adapter is not None and compact != self._compact_mode:
            if compact:
                current = self._sidebar_widget.width() if self._sidebar_widget else 0
                if current >= SIDEBAR_MIN:
                    self._saved_sidebar_width = current
                self._sidebar_adapter.set_collapsed(True)
                self._splitter.setHandleWidth(0)
                self._splitter.setSizes([
                    SIDEBAR_COLLAPSED,
                    max(1, width - SIDEBAR_COLLAPSED),
                ])
            else:
                self._sidebar_adapter.set_collapsed(False)
                self._splitter.setHandleWidth(5)
                restored = clamp_width(self._saved_sidebar_width)
                self._splitter.setSizes([restored, max(1, width - restored)])
            self._compact_mode = compact
        margin = 18 if compact else 28
        # See the comment in __init__: margins belong on the viewport so the
        # scrollbar stays flush with the shell edge instead of being pushed
        # outward by its own right margin.
        self._content_scroll.setViewportMargins(margin, 22, margin, margin)

    def _on_splitter_moved(self, _pos: int, _index: int) -> None:
        if self._compact_mode is False and self._sidebar_widget is not None:
            width = self._sidebar_widget.width()
            if SIDEBAR_MIN <= width <= SIDEBAR_MAX:
                self._saved_sidebar_width = width

    def apply_theme(self) -> None:
        self._root.setStyleSheet(
            f"QWidget[appShell='1'] {{ background: {C['bg']}; }}"
        )
        self._header_area.setStyleSheet(
            f"QWidget[shellHeader='1'] {{ background: {C['header_bg']}; "
            f"border-bottom: 1px solid {C['header_border']}; }}"
        )
        self._content_wrap.setStyleSheet(
            f"QWidget[shellContent='1'] {{ background: {C['bg']}; }}"
        )
        self._content_scroll.setStyleSheet(
            f"QScrollArea[shellScroll='1'] {{background:{C['bg']};border:none;}}"
            f"QScrollArea[shellScroll='1'] > QWidget > QWidget {{background:{C['bg']};}}"
        )
        self._splitter.setStyleSheet(
            f"QSplitter::handle {{ background: {C['border']}; }}"
            f"QSplitter::handle:hover {{ background: {C['accent']}; }}"
        )
        self._footer_area.setStyleSheet(
            f"QWidget[shellFooter='1'] {{ background: {C['surface']}; "
            f"border-top: 1px solid {C['border']}; }}"
        )
        footer_palette = self._footer_area.palette()
        footer_palette.setColor(
            QtGui.QPalette.WindowText, QtGui.QColor(C["text_muted"])
        )
        self._footer_area.setPalette(footer_palette)
