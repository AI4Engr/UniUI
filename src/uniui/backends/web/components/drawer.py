"""Drawer: a fixed-position slide-in panel toggled by a CSS class."""
from __future__ import annotations


from nicegui import ui

from ....components import IDrawer
from ....web import _WebAdapter
from ..runtime import clear, native
from ..styles import install_admin_css

class WebDrawerAdapter(_WebAdapter, IDrawer):
    def __init__(self):
        install_admin_css(); self._open = False
        root = ui.element("div").classes("uniui-web-drawer-root")
        with root:
            scrim = ui.element("div").classes("uniui-web-drawer-scrim")
            panel = ui.card().classes("uniui-web-drawer-panel")
            with panel:
                with ui.row().classes("uniui-web-drawer-header"):
                    self._title = ui.label("").classes("uniui-web-drawer-title")
                    close = ui.button("", color=None, on_click=lambda _event: self.close()).props("flat round dense")
                    close.add_slot("default", '<span class="uniui-svg-icon uniui-icon-close"></span>')
                self._content = ui.column().classes("w-full items-stretch")
        scrim.on("click", lambda _event: self.close())
        super().__init__(root)
    def set_title(self, title: str) -> None: self._title.set_text(str(title))
    def set_content(self, widget) -> None: clear(self._content); native(widget).move(self._content)
    def open(self) -> None: self._open = True; self._native.classes(add="uniui-open")
    def close(self) -> None: self._open = False; self._native.classes(remove="uniui-open")
    def toggle(self) -> None: self.close() if self._open else self.open()
    def is_open(self) -> bool: return self._open
