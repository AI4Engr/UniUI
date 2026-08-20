"""Drawer: a slide-in panel driven entirely by a CSS class toggle."""
from __future__ import annotations

from html import escape

import ipywidgets as widgets

from ...._adapter_mixins import JupyterEnableMixin, JupyterSizeMixin, JupyterVisibilityMixin
from ....components import IDrawer
from ..runtime import html, native

class JupyterDrawerAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, IDrawer):
    def __init__(self):
        self._title = html("", "uniui-drawer-title")
        close = widgets.Button(description="", tooltip="Close drawer", layout=widgets.Layout(width="36px"))
        close.add_class("uniui-icon-close"); close.on_click(lambda _button: self.close())
        header = widgets.HBox([self._title, close]); header.add_class("uniui-drawer-header")
        self._content = widgets.Box()
        self._native = widgets.VBox([header, self._content]); self._native.add_class("uniui-admin-drawer")
        self._open = False
    def get_native(self): return self._native
    def set_title(self, title: str) -> None: self._title.value = f"<p>{escape(str(title))}</p>"
    def set_content(self, widget) -> None: self._content.children = (native(widget),)
    def open(self) -> None: self._open = True; self._native.add_class("uniui-open")
    def close(self) -> None: self._open = False; self._native.remove_class("uniui-open")
    def toggle(self) -> None: self.close() if self._open else self.open()
    def is_open(self) -> bool: return self._open


def drawer_css() -> str:
    """The Drawer CSS fragment, composed into the shell sheet by ``styles.css``."""
    return """.uniui-admin-drawer {max-height:0;opacity:0;overflow:hidden;transform:translateX(24px);
  pointer-events:none;padding:0 20px;background:var(--uniui-surface);border:1px solid transparent;
  border-radius:14px;transition:max-height .2s ease,opacity .18s ease,transform .2s ease,padding .2s ease}
.uniui-admin-drawer.uniui-open {max-height:520px;opacity:1;transform:none;pointer-events:auto;
  padding:18px 20px;border-color:var(--uniui-border);box-shadow:var(--uniui-shadow)}
.uniui-drawer-header {align-items:center}
.uniui-drawer-title,.uniui-drawer-title p {margin:0;color:var(--uniui-text);font-size:18px;font-weight:700}"""
