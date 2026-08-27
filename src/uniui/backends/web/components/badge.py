"""Badge: a small status pill, reusing Table's shared status-pill CSS classes."""
from __future__ import annotations

from nicegui import ui

from ....components import IBadge
from ....models.status import classify_status
from ..primitives import _WebAdapter
from ..styles import install_admin_css


class WebBadgeAdapter(_WebAdapter, IBadge):
    def __init__(self):
        install_admin_css()
        native = ui.label("").classes("uniui-status-pill uniui-status-neutral")
        super().__init__(native)
        self._status = "neutral"

    def set_text(self, text: str) -> None:
        self._native.set_text(str(text) if text else "")

    def set_status(self, status: str) -> None:
        classified = classify_status(status)
        if classified == self._status:
            return
        self._native.classes(remove=f"uniui-status-{self._status}", add=f"uniui-status-{classified}")
        self._status = classified
