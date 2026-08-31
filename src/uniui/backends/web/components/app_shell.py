"""App shell: header / splitter / content / footer, and the CSS-variable theme spine."""
from __future__ import annotations


from nicegui import ui

from ....browser_css import declarations, metric_variables, token_variables
from ....components import IAppShell
from ....contracts.layout import DEFAULT_BREAKPOINTS
from ..primitives import _WebAdapter
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


def app_shell_css() -> str:
    """The AppShell chrome: header, body, splitter, content and footer."""
    return """        .uniui-web-header {height:var(--uniui-header-height);min-height:var(--uniui-header-height);width:100%;padding:0 20px!important;gap:10px!important;
          flex-wrap:nowrap!important;align-items:center!important;background:var(--uniui-header_bg);
          border-bottom:1px solid var(--uniui-border);box-shadow:0 1px 2px rgba(16,24,40,.025);z-index:2}
        .uniui-web-body {width:100%;height:calc(100dvh - var(--uniui-shell-bars));min-height:0;background:var(--uniui-bg)}
        .uniui-web-body .q-splitter__separator {width:5px!important;background:var(--uniui-border);transition:.15s}
        .uniui-web-body .q-splitter__separator:hover {background:var(--uniui-accent)}
        .uniui-web-content {width:100%;min-width:0;height:100%;padding:var(--uniui-content-padding);overflow:auto;background:var(--uniui-bg);
          scrollbar-width:thin;scrollbar-color:var(--uniui-border_strong) transparent}
        .uniui-web-footer {height:var(--uniui-footer-height);min-height:var(--uniui-footer-height);width:100%;padding:7px 20px;background:var(--uniui-surface);
          border-top:1px solid var(--uniui-border)}
"""


def app_shell_responsive_css() -> str:
    """The media queries that collapse the shell at narrow widths.

    Kept whole rather than split per component: one breakpoint reshapes the
    sidebar, splitter, content, header and footer as a single layout decision.
    """
    return f"""        @media(max-width:{DEFAULT_BREAKPOINTS.medium - 1}px) {{
          .uniui-web-body .q-splitter__before {{width:var(--uniui-sidebar-collapsed)!important}}
          .uniui-web-body .q-splitter__after {{width:calc(100% - var(--uniui-sidebar-collapsed))!important}}
          .uniui-web-body .q-splitter__separator {{display:none!important}}
          .uniui-web-sidebar {{padding:16px 8px}}.uniui-web-sidebar .q-btn{{font-size:0;justify-content:center;padding:8px 4px}}
          .uniui-web-sidebar .uniui-svg-icon {{margin:0;width:20px;height:20px;flex-basis:20px}}
          .uniui-web-content {{padding:24px 20px}}
          .uniui-shell-product {{display:none}}
        }}
        @media(max-width:{DEFAULT_BREAKPOINTS.compact - 1}px) {{
          .uniui-web-body {{height:calc(100dvh - 60px)}}.uniui-web-content{{padding:20px 14px}}.uniui-web-footer{{display:none}}
          .uniui-web-header{{padding:0 12px!important}}.uniui-shell-theme-button{{font-size:0;min-width:34px!important;padding:0!important}}
          .uniui-page-heading{{align-items:flex-start!important}}.uniui-page-subtitle{{font-size:16px!important}}
        }}
        """
