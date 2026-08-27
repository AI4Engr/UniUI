"""Sidebar: the navigation rail, backed by the shared NavigationModel."""
from __future__ import annotations

from html import escape
from typing import Callable, List, Optional, Union

import ipywidgets as widgets

from ...._adapter_mixins import JupyterEnableMixin, JupyterSizeMixin, JupyterVisibilityMixin
from ....components import ISidebar
from ....icons import ADMIN_ICON_NAMES
from ....models.navigation import (
    SIDEBAR_MAX, SIDEBAR_MIN, NavigationModel, clamp_width,
)
from ....state import Handle, safe_call
from ..runtime import M

class JupyterSidebarAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, ISidebar):
    def __init__(self):
        self._native = widgets.VBox()
        self._native.add_class("uniui-admin-sidebar")
        self._model = NavigationModel()
        self._buttons: List[Union[widgets.Button, widgets.HTML]] = []
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

    def add_group(self, label: str) -> None:
        self._model.add_group(label)
        header = widgets.HTML()
        header.add_class("uniui-nav-group")
        self._buttons.append(header)
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

    def on_select(self, fn: Callable[[str], None]) -> Handle:
        self._select_cb = fn
        def cancel():
            if self._select_cb is fn:
                self._select_cb = None
        return Handle(cancel)

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
        widget = self._buttons[index]
        if item.is_group:
            text = "" if self._model.collapsed else escape(item.label).upper()
            widget.value = f"<div class='uniui-nav-group-label'>{text}</div>" if text else ""
            return
        widget.description = self._model.label_for(item)

    def _on_select(self, key: str) -> None:
        if self._select_cb:
            safe_call(self._select_cb, key, backend="jupyter", component="Sidebar", method="on_select")


def sidebar_css() -> str:
    """The Sidebar CSS fragment, composed into the shell sheet by ``styles.css``.

    Includes the splitter rules: the drag handle resizes *this* rail and its
    markup lives in ``app_shell_assets.SPLITTER_HTML``, so the two belong to
    the same visual unit. The collapsed-rail rules under ``@container`` live in
    :func:`..app_shell.app_shell_responsive_css`, because that media query also
    reshapes the header, content and footer.
    """
    return f""".uniui-admin-sidebar {{
  width:{M['sidebar_expanded']}px; min-width:{M['sidebar_min']}px;
  max-width:{M['sidebar_max']}px; flex:0 0 {M['sidebar_expanded']}px;
  padding:14px 10px; gap:5px; overflow:auto; background:var(--uniui-sidebar_bg);
}}
.uniui-admin-sidebar .widget-button {{width:100%}}
.uniui-admin-sidebar .widget-button,
.uniui-admin-sidebar .widget-button button {{
  width:100%; min-height:42px; padding:8px 11px; text-align:left;
  background:transparent!important; color:var(--uniui-sidebar_fg)!important;
  border-color:transparent!important; box-shadow:none!important;
}}
.uniui-admin-sidebar .widget-button:hover,
.uniui-admin-sidebar .widget-button button:hover,
.uniui-admin-sidebar .uniui-active,
.uniui-admin-sidebar .uniui-active button {{
  color:white!important; background:var(--uniui-sidebar_active)!important;
}}
.uniui-admin-sidebar .uniui-active {{box-shadow:inset {M['sidebar_edge_width']}px 0 0 var(--uniui-sidebar_edge)}}
.uniui-admin-sidebar .uniui-nav-group {{width:100%; min-height:0}}
.uniui-nav-group-label {{
  padding:8px 11px 4px; font-size:11px; font-weight:700; letter-spacing:.04em;
  color:var(--uniui-text_muted);
}}
.uniui-admin-sidebar .uniui-active button::before {{background:var(--uniui-accent)}}
.uniui-splitter-widget {{
  width:6px; min-width:6px; flex:0 0 6px; align-self:stretch;
  background:var(--uniui-border); cursor:col-resize; touch-action:none;
}}
.uniui-splitter-widget:hover, .uniui-splitter-widget:active {{background:var(--uniui-accent)}}
.uniui-splitter-handle {{width:100%;height:100%;min-height:520px;touch-action:none}}"""
