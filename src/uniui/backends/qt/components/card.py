"""Qt ICard: a titled surface with an optional action and content slot."""
from __future__ import annotations

from PySide2 import QtCore, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import ICard
from ..runtime import C, as_widget, clear_layout, label_widget, track_themed
from ..styles import card_style

class QtCardAdapter(VisibilityMixin, EnableMixin, SizeMixin, ICard):
    def __init__(self):
        self._frame = QtWidgets.QFrame()
        self._frame.setProperty("card", "1")
        self._frame.setMinimumWidth(0)
        self._frame.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding
        )
        self._frame.setStyleSheet(card_style())

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

        self._title_lbl = label_widget("", bold=True, size=16)
        self._title_lbl.hide()
        self._subtitle_lbl = label_widget("", size=12, color=C["text_muted"])
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
        track_themed(self, self._frame)
        self.apply_theme()

    def get_native(self): return self._frame

    def set_title(self, title: str) -> None:
        self._title_lbl.setText(title)
        self._title_lbl.setVisible(bool(title))

    def set_subtitle(self, subtitle: str) -> None:
        self._subtitle_lbl.setText(subtitle)
        self._subtitle_lbl.setVisible(bool(subtitle))

    def set_content(self, widget) -> None:
        clear_layout(self._content_layout)
        self._content_layout.addWidget(as_widget(widget))

    def set_action(self, widget) -> None:
        clear_layout(self._action_layout)
        self._action_layout.addWidget(as_widget(widget))
        self._action_area.show()

    def apply_theme(self) -> None:
        self._frame.setStyleSheet(card_style())
        self._title_lbl.setStyleSheet(
            f"color: {C['text']}; font-size: 16px; font-weight: 700; background: transparent;"
        )
        self._subtitle_lbl.setStyleSheet(
            f"color: {C['text_muted']}; font-size: 12px; background: transparent;"
        )
