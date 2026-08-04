"""App shell: header / sidebar / content / footer, plus the layout debug probes."""
from __future__ import annotations

from typing import Optional

import ipywidgets as widgets

from ....components import IAppShell
from ....models.navigation import clamp_width
from ..styles import DEBUG_MEASURE_JS, SPLITTER_HTML, css, debug_html
from .sidebar import JupyterSidebarAdapter
from ..runtime import M, native_of, track_themed

class JupyterAppShellAdapter(IAppShell):
    def __init__(self):
        self._style = widgets.HTML(value=css())
        self._header = widgets.HBox()
        self._header.add_class("uniui-shell-header")
        self._header.layout.display = "none"
        self._debug = widgets.HTML()
        self._debug.layout.display = "none"
        self._debug.layout.width = "100%"
        self._debug_enabled = False
        self._content = widgets.Box(
            layout=widgets.Layout(
                flex="1 1 0%", min_width="0", min_height="0", width="auto",
                overflow="auto",
            )
        )
        self._content.add_class("uniui-shell-content")
        self._handle = widgets.HTML(value=SPLITTER_HTML)
        self._handle.add_class("uniui-splitter-widget")
        self._width_bridge = widgets.BoundedIntText(
            value=M["sidebar_expanded"],
            min=M["sidebar_min"],
            max=M["sidebar_max"],
        )
        self._width_bridge.layout.display = "none"
        self._width_bridge.add_class("uniui-sidebar-width-bridge")
        self._width_bridge.observe(self._on_width, names="value")
        self._body = widgets.HBox(
            [self._handle, self._content, self._width_bridge],
            layout=widgets.Layout(
                display="flex", flex_flow="row nowrap", flex="1 1 auto",
                width="100%", min_width="0", min_height="0",
                align_items="stretch",
            ),
        )
        self._body.add_class("uniui-shell-body")
        self._footer = widgets.Box()
        self._footer.add_class("uniui-shell-footer")
        self._footer.layout.display = "none"
        self._native = widgets.VBox([
            self._style, self._header, self._debug, self._body, self._footer,
        ])
        self._native.add_class("uniui-admin-shell")
        self._native.layout.width = "100%"
        self._native.layout.min_height = "680px"
        self._native.layout.display = "flex"
        self._native.layout.flex_flow = "column nowrap"
        self._sidebar: Optional[JupyterSidebarAdapter] = None
        self._saved_sidebar_width = M["sidebar_expanded"]
        track_themed(self)

    def get_native(self): return self._native

    def set_header(self, widget) -> None:
        self._header.children = (native_of(widget),)
        self._header.layout.display = "flex"

    def set_sidebar(self, sidebar) -> None:
        native = native_of(sidebar)
        self._sidebar = sidebar if hasattr(sidebar, "set_width") else None
        self._body.children = (native, self._handle, self._content, self._width_bridge)
        if self._sidebar:
            self._sidebar.set_width(self._saved_sidebar_width)

    def set_content(self, widget) -> None:
        # Make the actual content widget the body's flex item.  An additional
        # widgets.Box host can collapse its child to zero size in some
        # notebook renderers even when the Python widget tree is complete.
        old_content = self._content
        native = native_of(widget)
        if hasattr(old_content, "remove_class"):
            old_content.remove_class("uniui-shell-content")
        self._content = native
        if hasattr(native, "add_class"):
            native.add_class("uniui-shell-content")
        layout = getattr(native, "layout", None)
        if layout is not None:
            layout.display = "flex"
            layout.flex_flow = "column nowrap"
            layout.flex = "1 1 0%"
            layout.width = "auto"
            layout.min_width = "0"
            layout.min_height = "0"
            layout.overflow = "auto"

        children = list(self._body.children)
        try:
            index = children.index(old_content)
            children[index] = native
        except ValueError:
            if self._sidebar is not None:
                children = (
                    self._sidebar.get_native(), self._handle, native,
                    self._width_bridge,
                )
            else:
                children = (self._handle, native, self._width_bridge)
        self._body.children = tuple(children)
        if hasattr(native, "observe"):
            native.observe(self._on_content_children, names="children")
        self._refresh_debug()

    def set_debug(self, enabled: bool = True) -> None:
        """Show an in-notebook Python/widget-tree and browser DOM probe."""
        self._debug_enabled = bool(enabled)
        # Some notebook renderers keep the old inline display:none when the
        # Layout trait is reset to None.  Use an explicit display value so the
        # probe is guaranteed to become visible there as well.
        self._debug.layout.display = "block" if self._debug_enabled else "none"
        self._refresh_debug()

    def debug_report(self) -> str:
        """Return the current Python-side widget/layout diagnostics."""
        return self._debug_summary()

    def show_debug(self) -> None:
        """Display the diagnostic probe as a separate notebook output."""
        from IPython.display import HTML, display

        self.set_debug(True)
        print(self.debug_report())
        display(HTML(debug_html(self.debug_report())))

    def measure_debug(self) -> None:
        """Measure the live shell DOM and inject the result above the UI."""
        from IPython.display import Javascript, display

        display(Javascript(DEBUG_MEASURE_JS))

    def debug_script(self) -> str:
        """Return the browser measurement script for diagnostics/tests."""
        return DEBUG_MEASURE_JS

    def _on_content_children(self, _change) -> None:
        self._refresh_debug()

    def _refresh_debug(self) -> None:
        if not self._debug_enabled:
            return
        self._debug.value = debug_html(self._debug_summary())

    def _debug_summary(self) -> str:
        content = self._content
        mounted = tuple(getattr(content, "children", ()))
        layers = list(getattr(content, "_layers", ()))
        active = getattr(content, "_active", "n/a")
        page = mounted[0] if mounted else None
        source_page = (
            layers[active]
            if isinstance(active, int) and 0 <= active < len(layers)
            else None
        )
        wrapped = page is not None and source_page is not None and page is not source_page
        page_children = len(getattr(page, "children", ())) if page is not None else 0
        body_types = ", ".join(type(item).__name__ for item in self._body.children)
        return "\n".join([
            f"content={type(content).__name__}",
            f"active={active} layers={len(layers)} mounted={len(mounted)} page={type(page).__name__ if page is not None else 'None'} wrapped={wrapped} page_children={page_children}",
            f"body_children=[{body_types}]",
            f"root_layout={self._native.layout}",
            f"body_layout={self._body.layout}",
            f"content_layout={getattr(content, 'layout', None)}",
            f"page_layout={getattr(page, 'layout', None)}",
        ])

    def set_footer(self, widget) -> None:
        self._footer.children = (native_of(widget),)
        self._footer.layout.display = None

    def _on_width(self, change) -> None:
        width = clamp_width(change["new"])
        self._saved_sidebar_width = width
        if self._sidebar:
            self._sidebar.set_width(width)

    def apply_theme(self) -> None:
        self._style.value = css()
