"""Toast: an inline, auto-dismissing status banner, reusing Table's status colors."""
from __future__ import annotations

from html import escape

from nicegui import ui

from ....components import IToast
from ....models.status import classify_status
from ..primitives import _WebAdapter
from ..styles import install_admin_css


class WebToastAdapter(_WebAdapter, IToast):
    def __init__(self):
        install_admin_css()
        native = ui.html("", sanitize=False)
        super().__init__(native)
        native.set_visibility(False)
        self._status = "neutral"
        #: Bumped on every notify() so a stale auto-dismiss timer from an
        #: earlier call can tell it's no longer current and skip hiding a
        #: newer message it knows nothing about.
        self._generation = 0

    def notify(self, message: str, status: str = "neutral", duration: int = 3000) -> None:
        from ....display import schedule_after

        self._status = classify_status(status)
        self._generation += 1
        my_generation = self._generation
        self._native.set_content(
            f'<div class="uniui-toast-banner uniui-status-pill uniui-status-{self._status}">'
            f'{escape(str(message))}</div>'
        )
        self._native.set_visibility(True)

        def _maybe_dismiss():
            if self._generation == my_generation:
                self.dismiss()

        schedule_after(max(1, int(duration)), _maybe_dismiss)

    def dismiss(self) -> None:
        self._native.set_visibility(False)


def toast_css() -> str:
    """The Toast CSS fragment - reuses Table's .uniui-status-pill color
    rules, only overriding the shape (block banner, not a small pill)."""
    return """        .uniui-toast-banner {
          display:block; width:100%; box-sizing:border-box;
          padding:10px 14px; border-radius:8px; font-size:12px; font-weight:600;
          min-height:0;
        }
"""
