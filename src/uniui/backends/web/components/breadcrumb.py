"""Breadcrumb: the shared BreadcrumbModel rendered as buttons plus separators."""
from __future__ import annotations

from typing import Callable, Dict, List

from nicegui import ui

from ....components import IBreadcrumb
from ....models.navigation import BreadcrumbModel
from ..primitives import _WebAdapter
from ..runtime import clear
from ..styles import install_admin_css

class WebBreadcrumbAdapter(_WebAdapter, IBreadcrumb):
    def __init__(self):
        install_admin_css(); self._click_cb = None; self._model = BreadcrumbModel()
        super().__init__(ui.row().classes("uniui-web-breadcrumb"))
    def set_items(self, items: List[Dict]) -> None:
        self._model.set_items(items); clear(self._native)
        with self._native:
            for index, crumb in enumerate(self._model):
                if index: ui.label(BreadcrumbModel.SEPARATOR).style("color:var(--uniui-text_muted)")
                if crumb.is_link:
                    ui.button(crumb.label, color=None, on_click=lambda _e, p=crumb.path: self._emit(p)).props("flat dense no-caps")
                else: ui.label(crumb.label).style("color:var(--uniui-text);font-weight:650")
    def on_click(self, fn: Callable[[str], None]) -> None: self._click_cb = fn
    def _emit(self, path: str) -> None:
        if self._click_cb: self._click_cb(path)


def breadcrumb_css() -> str:
    """The Breadcrumb CSS fragment, composed into the sheet by ``styles.install_admin_css``."""
    return """        .uniui-web-breadcrumb {gap:4px!important;flex:1 1 auto;flex-wrap:nowrap!important;align-items:center!important;min-width:0}
        .uniui-web-breadcrumb .q-btn {min-height:28px;padding:2px 4px;color:var(--uniui-text_muted)!important;background:transparent!important;font-weight:500}
"""
