"""Jupyter IProgressBar: an ipywidgets.FloatProgress, recolored by status."""
from __future__ import annotations

import ipywidgets as widgets

from ...._adapter_mixins import JupyterEnableMixin, JupyterSizeMixin, JupyterVisibilityMixin
from ....components import IProgressBar
from ....models.status import classify_status, status_token_names
from ..runtime import get_palette, track_themed


class JupyterProgressBarAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, IProgressBar):
    def __init__(self):
        self._native = widgets.FloatProgress(value=0, min=0, max=100)
        self._native.add_class("uniui-progress-bar")
        self._status = "neutral"
        track_themed(self)
        self.apply_theme()

    def get_native(self): return self._native

    def set_value(self, value: float) -> None:
        self._native.value = max(0.0, min(100.0, float(value)))

    def set_status(self, status: str) -> None:
        self._status = classify_status(status)
        self.apply_theme()

    def apply_theme(self) -> None:
        palette = get_palette()
        fg_token, _ = status_token_names(self._status)
        color = palette["accent"] if self._status == "neutral" else palette[fg_token]
        self._native.style.bar_color = color
