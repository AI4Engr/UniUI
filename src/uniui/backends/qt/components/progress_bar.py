"""Qt IProgressBar: a themed QProgressBar."""
from __future__ import annotations

from PySide2 import QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import IProgressBar
from ....models.status import classify_status, status_token_names
from ..runtime import C, track_themed


class QtProgressBarAdapter(VisibilityMixin, EnableMixin, SizeMixin, IProgressBar):
    def __init__(self):
        self._bar = QtWidgets.QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._status = "neutral"
        track_themed(self, self._bar)
        self.apply_theme()

    def get_native(self): return self._bar

    def set_value(self, value: float) -> None:
        self._bar.setValue(max(0, min(100, int(value))))

    def set_status(self, status: str) -> None:
        self._status = classify_status(status)
        self.apply_theme()

    def apply_theme(self) -> None:
        fg_token, _ = status_token_names(self._status)
        chunk_color = C["accent"] if self._status == "neutral" else C[fg_token]
        self._bar.setStyleSheet(
            f"QProgressBar {{ background: {C['border']}; border: none; border-radius: 4px; }}"
            f"QProgressBar::chunk {{ background: {chunk_color}; border-radius: 4px; }}"
        )
