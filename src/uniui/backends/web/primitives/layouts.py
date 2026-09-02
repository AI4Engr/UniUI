"""Layout and container primitives."""
from __future__ import annotations

from typing import Any, Callable, List, Optional

from nicegui import ui

from ....core import *
from ....state import Handle, safe_call
from ....strategies import normalize_text, parse_float
from ....theme import THEME, is_dark
from .state import T, register_adapter

from .base import _WebAdapter
from .helpers import _plain_html, _style_size


def _wire_resize_observer(container, bridge) -> None:
    """Attach a browser-side ResizeObserver to ``container`` that reports its
    width to Python through ``bridge`` (a hidden ``ui.number`` element).

    Mirrors the hidden-bridge-widget idiom used by the Jupyter backend's
    AppShell splitter (``JupyterAppShellAdapter._width_bridge`` /
    ``SPLITTER_HTML``): raw JS reaches into the DOM, sets a hidden input's
    ``.value``, and dispatches a real ``input`` event so the framework's own
    value-change wiring picks it up - no custom/synthetic NiceGUI event is
    used, since ``ui.grid()``/``ui.row()`` are plain ``<div>`` elements with
    no Vue component behind them to natively emit one (unlike NiceGUI's own
    ``self.on('resize', ...)`` precedents in e.g. ``elements/xterm/xterm.py``,
    which are all backed by a custom Vue component that calls its own
    ``this.$emit(...)`` internally - not available here).

    ``getHtmlElement`` is NiceGUI's own documented helper (see
    ``ui.run_javascript``'s docstring) for resolving an element's real DOM
    node from its ``html_id`` inside injected JavaScript. Throttled client-side
    with a plain timeout, matching the ``throttle=`` behavior NiceGUI's own
    ``.on()`` provides for real socket events (not available here since this
    never goes through ``.on()``'s event-listener path).
    """
    container_id = container.html_id
    bridge_id = bridge.html_id
    script = f"""
    (() => {{
        const container = getHtmlElement({container_id!r});
        const bridgeInput = document.querySelector('#{bridge_id} input');
        if (!container || !bridgeInput) return;
        let timer = null;
        const report = () => {{
            const width = Math.round(container.getBoundingClientRect().width);
            bridgeInput.value = String(width);
            bridgeInput.dispatchEvent(new Event('input', {{bubbles: true}}));
        }};
        const observer = new ResizeObserver(() => {{
            if (timer !== null) clearTimeout(timer);
            timer = setTimeout(report, 100);
        }});
        observer.observe(container);
    }})();
    """
    # ui.run_javascript() asserts a running NiceGUI event loop - true in a
    # real served app, not true when an adapter is built directly in a plain
    # Python/pytest process with no NiceGUI server behind it (the same
    # situation contract tests exercise via create_factory("web")). Same
    # no-op-is-fine posture as the Jupyter backend's JS injection: if there's
    # no live event loop to run the script on, on_resize() simply never
    # fires instead of crashing the caller.
    from nicegui import core
    if not core.is_loop_running():
        return
    try:
        ui.run_javascript(script)
    except Exception:
        pass


def _apply_flex(native, item) -> None:
    """Translate a LayoutItem's flex overrides onto a NiceGUI element.

    ``basis`` defaults to ``0`` rather than CSS's ``auto`` when the caller asks
    to grow: with ``auto`` the item's content width seeds the distribution, so
    a row of buttons ends up as wide as its longest label instead of dividing
    the row evenly.
    """
    if item.grow <= 0 and item.basis is None:
        return
    basis = item.basis if item.basis is not None else (0 if item.grow > 0 else "auto")
    if isinstance(basis, (int, float)):
        basis = f"{basis}px" if basis else "0"
    native.style(f"flex: {item.grow} {item.shrink} {basis}; min-width: 0")


class WebVBoxAdapter(_WebAdapter, IVBoxLayout):
    def __init__(self):
        super().__init__(ui.column().classes("uniui-vbox w-full items-stretch"))
        self._apply_theme()

    def add_item(self, widget: IWidget) -> None:
        widget.get_native().move(self._native)

    def add_item_with_spec(self, widget: IWidget, item) -> None:
        native = widget.get_native()
        native.move(self._native)
        _apply_flex(native, item)

    def add_stretch(self) -> None:
        ui.element("div").classes("grow").move(self._native)

    def set_alignment_top(self) -> None:
        self._native.classes(add="justify-start")

    def _apply_theme(self) -> None:
        self._native.style(f"color: {T['fg']}")
class WebHBoxAdapter(_WebAdapter, IHBoxLayout):
    def __init__(self):
        super().__init__(ui.row().classes("uniui-hbox w-full items-center"))
        self._apply_theme()
        self._resize_callbacks: List = []
        self._breakpoints = None
        self._last_mode: Optional[str] = None
        self._resize_wired = False
        self._resize_bridge = None

    def add_item(self, widget: IWidget) -> None:
        widget.get_native().move(self._native)

    def add_item_with_spec(self, widget: IWidget, item) -> None:
        native = widget.get_native()
        native.move(self._native)
        _apply_flex(native, item)

    def add_stretch(self) -> None:
        ui.element("div").classes("grow").move(self._native)

    def set_alignment_top(self) -> None:
        self._native.classes(add="items-start")

    def set_responsive_stack(self, enabled: bool) -> None:
        self._native.classes(add="" if enabled else "uniui-hbox--no-stack",
                              remove="uniui-hbox--no-stack" if enabled else "")

    def on_resize(self, callback, breakpoints=None) -> Handle:
        from ....core import DEFAULT_BREAKPOINTS
        bp = breakpoints or DEFAULT_BREAKPOINTS
        self._breakpoints = bp
        self._resize_callbacks.append(callback)

        if not self._resize_wired:
            self._resize_wired = True
            self._resize_bridge = ui.number(value=0).classes("hidden")
            self._resize_bridge.move(self._native)
            self._resize_bridge.on_value_change(self._on_width)
            _wire_resize_observer(self._native, self._resize_bridge)

        def cancel():
            if callback in self._resize_callbacks:
                self._resize_callbacks.remove(callback)
        return Handle(cancel)

    def _on_width(self, event) -> None:
        width = event.value
        if width is None:
            return
        mode = self._breakpoints.mode_for(int(width))
        if mode != self._last_mode:
            self._last_mode = mode
            for cb in self._resize_callbacks:
                safe_call(cb, mode, backend="web", component="HBox", method="on_resize")

    def _apply_theme(self) -> None:
        self._native.style(f"color: {T['fg']}")
class WebTabWidgetAdapter(_WebAdapter, ITabWidget):
    def __init__(self):
        root = ui.column().classes("w-full items-stretch")
        with root:
            self._tabs = ui.tabs().classes("w-full")
            self._panels = ui.tab_panels(self._tabs).classes("w-full")
        self._tab_items = []
        self._panel_items = []
        super().__init__(root)
        self._apply_theme()

    def add_tab(self, widget: IWidget, name: str) -> None:
        with self._tabs:
            tab = ui.tab(normalize_text(name))
        with self._panels:
            panel = ui.tab_panel(tab)
        widget.get_native().move(panel)
        self._tab_items.append(tab)
        self._panel_items.append(panel)
        if len(self._tab_items) == 1:
            self._tabs.set_value(tab)
            self._panels.set_value(tab)

    def remove_tabs(self) -> None:
        for panel in self._panel_items:
            panel.delete()
        for tab in self._tab_items:
            tab.delete()
        self._tab_items.clear()
        self._panel_items.clear()

    def get_current_index(self) -> int:
        if not self._tab_items:
            return 0
        current = self._tabs.value
        try:
            return self._tab_items.index(current)
        except ValueError:
            return 0

    def _apply_theme(self) -> None:
        self._native.style(f"color: {T['fg']}; background: {T['bg']}")
class WebGridAdapter(_WebAdapter, IGrid):
    """Web Grid adapter using NiceGUI ui.grid."""

    def __init__(self, columns: int = 12):
        with ui.grid(columns=columns).classes("uniui-grid w-full") as grid:
            pass
        super().__init__(grid)
        self._columns = columns
        self._resize_callbacks: List = []
        self._breakpoints = None
        self._last_mode: Optional[str] = None
        self._resize_wired = False
        self._resize_bridge = None

    def add_item(self, widget: IWidget, row: int = -1, col: int = -1,
                 row_span: int = 1, col_span: int = 1) -> None:
        native = widget.get_native()
        native.move(self._native)
        if col_span > 1:
            native.classes(add=f"col-span-{col_span}")

    def set_columns(self, count: int) -> None:
        self._columns = count
        self._native._props["columns"] = count
        self._native.update()

    def set_spec(self, spec: LayoutSpec) -> None:
        if spec.gap:
            self._native.style(f"gap: {spec.gap}px")
        if spec.padding:
            self._native.style(f"padding: {spec.padding}px")

    def clear(self) -> None:
        self._native.clear()

    def on_resize(self, callback, breakpoints=None) -> Handle:
        from ....core import DEFAULT_BREAKPOINTS
        bp = breakpoints or DEFAULT_BREAKPOINTS
        self._breakpoints = bp
        self._resize_callbacks.append(callback)

        if not self._resize_wired:
            self._resize_wired = True
            self._resize_bridge = ui.number(value=0).classes("hidden")
            self._resize_bridge.move(self._native)
            self._resize_bridge.on_value_change(self._on_width)
            _wire_resize_observer(self._native, self._resize_bridge)

        def cancel():
            if callback in self._resize_callbacks:
                self._resize_callbacks.remove(callback)
        return Handle(cancel)

    def _on_width(self, event) -> None:
        width = event.value
        if width is None:
            return
        mode = self._breakpoints.mode_for(int(width))
        if mode != self._last_mode:
            self._last_mode = mode
            for cb in self._resize_callbacks:
                safe_call(cb, mode, backend="web", component="Grid", method="on_resize")
class WebWrapAdapter(_WebAdapter, IWrap):
    """Web Wrap adapter — flex-wrap row."""

    def __init__(self):
        with ui.row().classes("uniui-wrap w-full flex-wrap") as row:
            pass
        super().__init__(row)

    def add_item(self, widget: IWidget) -> None:
        widget.get_native().move(self._native)

    def set_spec(self, spec: LayoutSpec) -> None:
        if spec.gap:
            self._native.style(f"gap: {spec.gap}px")
        if spec.padding:
            self._native.style(f"padding: {spec.padding}px")

    def clear(self) -> None:
        self._native.clear()
class WebCenterAdapter(_WebAdapter, ICenter):
    """Web Center adapter — flex box centered on both axes."""

    def __init__(self):
        with ui.element("div").classes(
            "uniui-center w-full h-full flex items-center justify-center"
        ) as el:
            pass
        super().__init__(el)

    def set_content(self, widget: IWidget) -> None:
        self._native.clear()
        widget.get_native().move(self._native)
class WebSeparatorAdapter(_WebAdapter, ISeparator):
    """Web Separator adapter using NiceGUI's ui.separator (Quasar q-separator)."""

    def __init__(self):
        sep = ui.separator()
        super().__init__(sep)
        self.set_orientation("horizontal")

    def set_orientation(self, orientation: str) -> None:
        if orientation == "vertical":
            self._native.props("vertical")
        else:
            self._native.props(remove="vertical")
class WebScrollViewAdapter(_WebAdapter, IScrollView):
    """Web ScrollView adapter using NiceGUI ui.scroll_area."""

    def __init__(self):
        with ui.scroll_area().classes("uniui-scroll w-full") as scroll:
            pass
        super().__init__(scroll)

    def set_content(self, widget: IWidget) -> None:
        self._native.clear()
        widget.get_native().move(self._native)

    def set_max_height(self, height: int) -> None:
        self._native.style(f"max-height: {height}px")

    def set_max_width(self, width: int) -> None:
        self._native.style(f"max-width: {width}px")
class WebSplitPaneAdapter(_WebAdapter, ISplitPane):
    """Web SplitPane adapter using NiceGUI ui.splitter."""

    def __init__(self, orientation: str = "horizontal"):
        horizontal = orientation == "horizontal"
        with ui.splitter(horizontal=horizontal).classes("uniui-split w-full") as splitter:
            pass
        super().__init__(splitter)
        self._orientation = orientation

    def set_first(self, widget: IWidget) -> None:
        with self._native.before:
            widget.get_native().move(self._native.before)

    def set_second(self, widget: IWidget) -> None:
        with self._native.after:
            widget.get_native().move(self._native.after)

    def set_orientation(self, orientation: str) -> None:
        self._orientation = orientation
        # NiceGUI splitter orientation is set at creation; updating requires recreation.
        # Log a warning — structural mutation after creation is not supported for Web.
        pass

    def set_sizes(self, ratio: float) -> None:
        pct = int(max(0.0, min(1.0, ratio)) * 100)
        self._native.value = pct
class WebOverlayAdapter(_WebAdapter, IOverlay):
    """Web Overlay adapter — stacked divs, only active one is visible."""

    def __init__(self):
        with ui.element("div").classes("uniui-overlay relative w-full h-full") as container:
            pass
        super().__init__(container)
        self._layers: list = []
        self._active = 0

    def add_layer(self, widget: IWidget) -> None:
        native = widget.get_native()
        native.move(self._native)
        native.classes(add="absolute inset-0")
        self._layers.append(native)
        self._apply_visibility()

    def set_active_index(self, index: int) -> None:
        self._active = index
        self._apply_visibility()

    def remove_layer(self, index: int) -> None:
        layer = self._layers.pop(index)
        layer.delete()
        if index <= self._active:
            self._active = max(0, self._active - 1)
        self._apply_visibility()

    def layer_count(self) -> int:
        return len(self._layers)

    def _apply_visibility(self) -> None:
        for i, layer in enumerate(self._layers):
            if i == self._active:
                layer.classes(remove="hidden")
            else:
                layer.classes(add="hidden")
