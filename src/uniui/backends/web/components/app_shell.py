"""App shell: header / splitter / content / footer, and the CSS-variable theme spine."""
from __future__ import annotations


from nicegui import ui

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
        p = get_palette()
        variables = {f"--uniui-{key}": value for key, value in p.items()}
        variables.update({
            "--uniui-header-height": f"{M['header_height']}px",
            "--uniui-footer-height": f"{M['footer_height']}px",
            "--uniui-shell-bars": f"{M['header_height'] + M['footer_height']}px",
            "--uniui-sidebar-collapsed": f"{M['sidebar_collapsed']}px",
            "--uniui-control-height": f"{M['control_height']}px",
            "--uniui-stat-value-size": f"{M['stat_value_size']}px",
            "--uniui-stat-label-size": f"{M['stat_label_size']}px",
            "--uniui-sidebar-edge-width": f"{M['sidebar_edge_width']}px",
            "--uniui-content-padding": f"{M['content_padding']}px {M['content_padding'] + 4}px {M['content_padding'] + 4}px",
            "--uniui-card-padding": f"{M['card_padding']}px {M['card_padding'] + 2}px",
            "--uniui-card-gap": f"{M['card_gap']}px",
            "--uniui-section-gap": f"{M['section_gap']}px",
        })
        self._native.style(";".join(f"{key}:{value}" for key, value in variables.items()))
