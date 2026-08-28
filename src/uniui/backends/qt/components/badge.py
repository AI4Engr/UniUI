"""Qt IBadge: a small status pill label."""
from __future__ import annotations

from PySide2 import QtCore, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import IBadge
from ....models.status import classify_status, status_token_names
from ..runtime import C, track_themed


class QtBadgeAdapter(VisibilityMixin, EnableMixin, SizeMixin, IBadge):
    def __init__(self):
        self._label = QtWidgets.QLabel("")
        self._label.setAlignment(QtCore.Qt.AlignCenter)
        # Without a fixed height, a QLabel stretches to fill whatever row
        # it's placed in (e.g. a toolbar's full height) - the "pill" QSS
        # background then paints that whole stretched rect, turning a small
        # badge into a large solid-color block next to taller siblings.
        self._label.setFixedHeight(20)
        self._label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self._status = "neutral"
        track_themed(self, self._label)
        self.apply_theme()

    def get_native(self): return self._label

    def set_text(self, text: str) -> None:
        self._label.setText(str(text) if text else "")

    def set_status(self, status: str) -> None:
        self._status = classify_status(status)
        self.apply_theme()

    def apply_theme(self) -> None:
        fg_token, bg_token = status_token_names(self._status)
        self._label.setStyleSheet(
            f"QLabel {{ background: {C[bg_token]}; color: {C[fg_token]}; "
            f"border-radius: 10px; padding: 0 8px; font-size: 11px; font-weight: 700; }}"
        )
