"""Sidebar: the navigation rail, backed by the shared NavigationModel."""
from __future__ import annotations

from typing import Callable, List, Optional

import ipywidgets as widgets

from ....components import ISidebar
from ....icons import ADMIN_ICON_NAMES
from ....models.navigation import (
    SIDEBAR_MAX, SIDEBAR_MIN, NavigationModel, clamp_width,
)

class JupyterSidebarAdapter(ISidebar):
    def __init__(self):
        self._native = widgets.VBox()
        self._native.add_class("uniui-admin-sidebar")
        self._model = NavigationModel()
        self._buttons: List[widgets.Button] = []
        self._select_cb: Optional[Callable[[str], None]] = None

    def get_native(self): return self._native

    def add_item(self, key: str, label: str, icon: str = "") -> None:
        nav_item = self._model.add_item(key, label, icon)
        button = widgets.Button(layout=widgets.Layout(width="100%"))
        if nav_item.icon in ADMIN_ICON_NAMES:
            button.add_class(f"uniui-icon-{nav_item.icon}")
        button.tooltip = nav_item.label
        button.on_click(lambda _button, k=nav_item.key: self._on_select(k))
        self._buttons.append(button)
        self._native.children = tuple(self._buttons)
        self._refresh_button(len(self._buttons) - 1)

    def set_active(self, key: str) -> None:
        if not self._model.set_active(key):
            return
        for index, button in enumerate(self._buttons):
            if self._model.is_active(self._model.items[index].key):
                button.add_class("uniui-active")
            else:
                button.remove_class("uniui-active")

    def on_select(self, fn: Callable[[str], None]) -> None:
        self._select_cb = fn

    def set_collapsed(self, collapsed: bool) -> None:
        self._model.set_collapsed(collapsed)
        for index in range(len(self._buttons)):
            self._refresh_button(index)
        self.set_width(self._model.width, fixed=self._model.collapsed)

    def set_width(self, width: int, fixed: bool = False) -> None:
        px = f"{clamp_width(width, fixed)}px"
        self._native.layout.width = px
        self._native.layout.flex = f"0 0 {px}"
        self._native.layout.min_width = px if fixed else f"{SIDEBAR_MIN}px"
        self._native.layout.max_width = px if fixed else f"{SIDEBAR_MAX}px"

    def _refresh_button(self, index: int) -> None:
        item = self._model.items[index]
        self._buttons[index].description = self._model.label_for(item)

    def _on_select(self, key: str) -> None:
        if self._select_cb:
            self._select_cb(key)
