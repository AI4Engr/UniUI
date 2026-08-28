"""Web IProgressBar: a NiceGUI linear_progress, recolored by status."""
from __future__ import annotations

from nicegui import ui

from ....components import IProgressBar
from ....models.status import classify_status, status_token_names
from ..primitives import _WebAdapter
from ..runtime import get_palette
from ..styles import install_admin_css


class WebProgressBarAdapter(_WebAdapter, IProgressBar):
    def __init__(self):
        install_admin_css()
        native = ui.linear_progress(value=0, show_value=False).classes("uniui-progress-bar")
        super().__init__(native)
        self._status = "neutral"
        self._apply_color()

    def set_value(self, value: float) -> None:
        self._native.set_value(max(0.0, min(100.0, float(value))) / 100.0)

    def set_status(self, status: str) -> None:
        self._status = classify_status(status)
        self._apply_color()

    def _apply_color(self) -> None:
        palette = get_palette()
        fg_token, _ = status_token_names(self._status)
        color = palette["accent"] if self._status == "neutral" else palette[fg_token]
        self._native.props(f'color="{color}"')
