"""Qt ICarousel: an image slideshow with prev/next navigation and dots."""
from __future__ import annotations

from typing import Callable, List

from PySide2 import QtCore, QtGui, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import ICarousel
from ....state import Handle, safe_call
from ..runtime import C, track_themed


class QtCarouselAdapter(VisibilityMixin, EnableMixin, SizeMixin, ICarousel):
    def __init__(self):
        self._paths: List[str] = []
        self._index = 0
        self._callbacks: List[Callable[[], None]] = []

        self._root = QtWidgets.QWidget()
        root_layout = QtWidgets.QVBoxLayout(self._root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        self._image_label = QtWidgets.QLabel()
        self._image_label.setAlignment(QtCore.Qt.AlignCenter)
        self._image_label.setMinimumHeight(160)

        self._prev_btn = QtWidgets.QPushButton("‹")
        self._next_btn = QtWidgets.QPushButton("›")
        self._prev_btn.setFixedWidth(32)
        self._next_btn.setFixedWidth(32)
        self._prev_btn.clicked.connect(self.previous_slide)
        self._next_btn.clicked.connect(self.next_slide)

        slide_row = QtWidgets.QHBoxLayout()
        slide_row.setSpacing(8)
        slide_row.addWidget(self._prev_btn)
        slide_row.addWidget(self._image_label, stretch=1)
        slide_row.addWidget(self._next_btn)
        root_layout.addLayout(slide_row)

        self._dots_row = QtWidgets.QHBoxLayout()
        self._dots_row.setSpacing(6)
        self._dots_row.addStretch()
        dots_container = QtWidgets.QWidget()
        dots_container.setLayout(self._dots_row)
        self._dots_row.addStretch()
        root_layout.addWidget(dots_container)
        self._dot_labels: List[QtWidgets.QLabel] = []

        self._timer = QtCore.QTimer()
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self.next_slide)

        track_themed(self, self._root)
        self.apply_theme()
        self._render()

    def get_native(self):
        return self._root

    def set_images(self, paths: List[str]) -> None:
        self._paths = list(paths)
        self._index = 0
        self._rebuild_dots()
        self._render()

    def next_slide(self) -> None:
        if not self._paths:
            return
        self._index = (self._index + 1) % len(self._paths)
        self._render()
        self._emit_change()

    def previous_slide(self) -> None:
        if not self._paths:
            return
        self._index = (self._index - 1) % len(self._paths)
        self._render()
        self._emit_change()

    def get_current_index(self) -> int:
        return self._index

    def set_current_index(self, index: int) -> None:
        if not self._paths:
            return
        self._index = max(0, min(index, len(self._paths) - 1))
        self._render()
        self._emit_change()

    def set_auto_advance(self, enabled: bool, interval_ms: int = 3000) -> None:
        if enabled:
            self._timer.start(max(1, int(interval_ms)))
        else:
            self._timer.stop()

    def on_change(self, callback: Callable[[], None]) -> Handle:
        self._callbacks.append(callback)

        def cancel():
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return Handle(cancel)

    def _emit_change(self) -> None:
        for callback in list(self._callbacks):
            safe_call(callback, backend="qt", component="Carousel", method="on_change")

    def _render(self) -> None:
        if not self._paths:
            self._image_label.setPixmap(QtGui.QPixmap())
            self._image_label.setText("No slides")
        else:
            pixmap = QtGui.QPixmap(self._paths[self._index])
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self._image_label.width() or 320, 160,
                    QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation,
                )
            self._image_label.setPixmap(pixmap)
        self._update_dots()

    def _rebuild_dots(self) -> None:
        for label in self._dot_labels:
            self._dots_row.removeWidget(label)
            label.deleteLater()
        self._dot_labels = []
        for _ in self._paths:
            dot = QtWidgets.QLabel()
            dot.setFixedSize(8, 8)
            self._dots_row.insertWidget(self._dots_row.count() - 1, dot)
            self._dot_labels.append(dot)
        self._update_dots()

    def _update_dots(self) -> None:
        for i, dot in enumerate(self._dot_labels):
            color = C["accent"] if i == self._index else C["border_strong"]
            dot.setStyleSheet(f"background: {color}; border-radius: 4px;")

    def apply_theme(self) -> None:
        self._prev_btn.setStyleSheet(
            f"QPushButton {{ background: {C['surface']}; color: {C['text']}; "
            f"border: 1px solid {C['border_strong']}; border-radius: 6px; }}"
            f"QPushButton:hover {{ background: {C['surface_subtle']}; }}"
        )
        self._next_btn.setStyleSheet(self._prev_btn.styleSheet())
        self._update_dots()
