"""Qt IToast: an inline, auto-dismissing status banner."""
from __future__ import annotations

from PySide2 import QtCore, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import IToast
from ....models.status import classify_status, status_token_names
from ..runtime import C, track_themed


class QtToastAdapter(VisibilityMixin, EnableMixin, SizeMixin, IToast):
    def __init__(self):
        self._label = QtWidgets.QLabel("")
        self._label.setWordWrap(True)
        self._label.hide()
        self._status = "neutral"
        self._timer = QtCore.QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)
        track_themed(self, self._label)
        self.apply_theme()

    def get_native(self): return self._label

    def notify(self, message: str, status: str = "neutral", duration: int = 3000) -> None:
        self._status = classify_status(status)
        self._label.setText(str(message))
        self.apply_theme()
        self._label.show()
        self._timer.start(max(1, int(duration)))

    def dismiss(self) -> None:
        self._timer.stop()
        self._label.hide()

    def apply_theme(self) -> None:
        fg_token, bg_token = status_token_names(self._status)
        self._label.setStyleSheet(
            f"QLabel {{ background: {C[bg_token]}; color: {C[fg_token]}; "
            f"border-radius: 8px; padding: 10px 14px; font-size: 12px; font-weight: 600; }}"
        )
