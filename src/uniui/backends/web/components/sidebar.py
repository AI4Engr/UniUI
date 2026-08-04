"""Sidebar: the navigation rail, backed by the shared NavigationModel."""
from __future__ import annotations

from html import escape
from typing import Callable

from nicegui import ui

from ....components import ISidebar
from ....icons import ADMIN_ICON_NAMES
from ....models.navigation import NavigationModel
from ....web import _WebAdapter
from ..styles import install_admin_css

class WebSidebarAdapter(_WebAdapter, ISidebar):
    def __init__(self):
        install_admin_css()
        self._model = NavigationModel(); self._buttons = []; self._select_cb = None
        super().__init__(ui.column().classes("uniui-web-sidebar items-stretch"))
    def add_item(self, key: str, label: str, icon: str = "") -> None:
        item = self._model.add_item(key, label, icon)
        with self._native:
            button = ui.button(
                "",
                color=None,
                on_click=lambda _e, k=item.key: self._emit(k),
            ).props("flat no-caps")
        if item.icon in ADMIN_ICON_NAMES:
            button.add_slot(
                "default",
                f'<span class="uniui-svg-icon uniui-icon-{item.icon}"></span>'
                f'<span class="uniui-nav-label">{escape(item.label)}</span>',
            )
        button.tooltip(item.label)
        self._buttons.append(button)
    def set_active(self, key: str) -> None:
        if not self._model.set_active(key): return
        for item, button in zip(self._model, self._buttons):
            is_active = self._model.is_active(item.key)
            button.classes(add="uniui-active" if is_active else "", remove="" if is_active else "uniui-active")
    def on_select(self, fn: Callable[[str], None]) -> None: self._select_cb = fn
    def set_collapsed(self, collapsed: bool) -> None:
        self._model.set_collapsed(collapsed)
        for button in self._buttons:
            button.classes(
                add="uniui-collapsed" if collapsed else "",
                remove="" if collapsed else "uniui-collapsed",
            )
    def _emit(self, key: str) -> None:
        if self._select_cb: self._select_cb(key)
