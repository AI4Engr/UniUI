"""Sidebar: the navigation rail, backed by the shared NavigationModel."""
from __future__ import annotations

from html import escape
from typing import Callable

from nicegui import ui

from ....components import ISidebar
from ....icons import ADMIN_ICON_NAMES
from ....models.navigation import NavigationModel
from ..primitives import _WebAdapter
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


def sidebar_css() -> str:
    """The Sidebar CSS fragment, composed into the sheet by ``styles.install_admin_css``.

    The collapsed-rail rules under ``@media`` live in
    :func:`..app_shell.app_shell_responsive_css`, because that breakpoint also
    reshapes the splitter, content and header.
    """
    return """        .uniui-web-sidebar {width:100%;height:100%;padding:18px 12px;gap:6px!important;overflow:auto;background:var(--uniui-sidebar_bg)}
        .uniui-web-sidebar .q-btn {position:relative;width:100%;min-height:42px;justify-content:flex-start;padding:8px 12px;
          color:var(--uniui-sidebar_fg)!important;background:transparent!important;border-radius:8px;font-size:13px;font-weight:500}
        .uniui-web-sidebar .q-btn .q-icon {width:22px;margin-right:10px;color:#94a3b8;font-size:19px}
        .uniui-web-sidebar .q-btn:hover {color:#fff!important;background:rgba(255,255,255,.055)!important}
        .uniui-web-sidebar .uniui-active {color:#fff!important;background:var(--uniui-sidebar_active)!important;box-shadow:inset var(--uniui-sidebar-edge-width) 0 0 var(--uniui-accent)}
        .uniui-web-sidebar .uniui-active .uniui-svg-icon {color:var(--uniui-accent)}
        .uniui-web-sidebar .uniui-collapsed .uniui-nav-label {display:none}
        .uniui-web-sidebar .uniui-collapsed .uniui-svg-icon {margin-right:0}
"""
