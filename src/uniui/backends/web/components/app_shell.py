"""App shell: header / splitter / content / footer, and the CSS-variable theme spine."""
from __future__ import annotations


from nicegui import ui

from ....browser_css import declarations, metric_variables, token_variables
from ....components import IAppShell
from ....web import _WebAdapter
from ..runtime import M, clear, get_palette, native, track_shell
from ..styles import install_admin_css

class WebAppShellAdapter(_WebAdapter, IAppShell):
    def __init__(self):
        install_admin_css()
        root = ui.column().classes("uniui-web-admin w-full items-stretch gap-0")
        with root:
            self._header = ui.row().classes("uniui-web-header")
            self._splitter = ui.splitter(value=18, limits=(12, 28)).classes("uniui-web-body")
            with self._splitter.before:
                self._sidebar_slot = ui.column().classes("w-full h-full items-stretch gap-0")
            with self._splitter.after:
                self._content = ui.column().classes("uniui-web-content items-stretch gap-0")
            self._footer = ui.row().classes("uniui-web-footer items-center")
        self._header.set_visibility(False); self._footer.set_visibility(False)
        super().__init__(root)
        track_shell(self)
        self.apply_theme()
    def set_header(self, widget) -> None:
        clear(self._header); native(widget).move(self._header); self._header.set_visibility(True)
    def set_sidebar(self, sidebar) -> None:
        clear(self._sidebar_slot); native(sidebar).move(self._sidebar_slot)
    def set_content(self, widget) -> None:
        clear(self._content); native(widget).move(self._content)
    def set_footer(self, widget) -> None:
        clear(self._footer); native(widget).move(self._footer); self._footer.set_visibility(True)
    def apply_theme(self) -> None:
        """Rewrite the shell's custom properties.

        This is the whole web theme spine: every rule in ``styles.py`` reads
        ``var(--uniui-*)``, so restyling is one inline ``style`` write rather
        than a stylesheet re-emission.
        """
        variables = token_variables(get_palette())
        variables.update(metric_variables(M))
        self._native.style(declarations(variables))
