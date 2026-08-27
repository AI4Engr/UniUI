"""Badge: a small status pill, reusing Table's shared status-pill CSS classes."""
from __future__ import annotations

from html import escape

from ...._adapter_mixins import JupyterEnableMixin, JupyterSizeMixin, JupyterVisibilityMixin
from ....components import IBadge
from ....models.status import classify_status
from ..runtime import html


class JupyterBadgeAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, IBadge):
    def __init__(self):
        self._text = ""
        self._status = "neutral"
        self._native = html("", "uniui-badge")
        self._render()

    def get_native(self): return self._native

    def set_text(self, text: str) -> None:
        self._text = str(text) if text else ""
        self._render()

    def set_status(self, status: str) -> None:
        self._status = classify_status(status)
        self._render()

    def _render(self) -> None:
        self._native.value = (
            f'<span class="uniui-status-pill uniui-status-{self._status}">'
            f'{escape(self._text)}</span>'
        )
