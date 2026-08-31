"""Layout and container primitives."""
from __future__ import annotations

from typing import Callable, List, Optional

import ipywidgets as widgets
from IPython.display import display

from ....core import *
from ...._adapter_mixins import (
    ClearMixin, EnableMixin, JupyterClassMixin, JupyterEnableMixin,
    JupyterSizeMixin, JupyterVisibilityMixin, NativeMixin, SelectionMixin,
    SizeMixin, TextMixin, VisibilityMixin,
)
from ....strategies import normalize_text, parse_float
from ....theme import THEME, is_dark

#: Alias for the live theme dict. ``THEME`` is mutated in place on a theme
#: switch, so this is a view of the current palette, not a snapshot.
T = THEME


class JupyterVBoxLayout(widgets.VBox):
    """Jupyter Vertical Box Layout - native implementation"""
    def __init__(self):
        super().__init__()

    def addItem(self, item):
        old_content = list(self.children)
        old_content.append(item)
        self.children = tuple(old_content)

    def addStretch(self):
        # Jupyter doesn't need stretch
        pass

    def setAlignmentTop(self):
        # Jupyter doesn't have explicit alignment control
        pass

    def setSpec(self, spec):
        self.layout.gap = f"{spec.gap}px" if spec.gap else None
        p = f"{spec.padding}px" if spec.padding else None
        self.layout.padding = p

    def clear(self):
        self.children = ()
class JupyterHBoxLayout(widgets.HBox):
    """Jupyter Horizontal Box Layout - native implementation"""
    def __init__(self):
        super().__init__(
            layout=widgets.Layout(
                display='flex',
                flex_flow='row',
                width='100%'
            )
        )

    def addItem(self, item, grow=0):
        if hasattr(item, 'layout'):
            if grow > 0:
                item.layout.flex = f"{grow} 1 auto"
            else:
                # Don't force flex=1; let items size to content by default
                item.layout.flex = None
                if not item.layout.width:
                    item.layout.width = 'auto'
        old_content = list(self.children)
        old_content.append(item)
        self.children = tuple(old_content)

    def addStretch(self):
        spacer = widgets.Box(layout=widgets.Layout(flex='1'))
        old_content = list(self.children)
        old_content.append(spacer)
        self.children = tuple(old_content)

    def setAlignmentTop(self):
        self.layout.align_items = 'flex-start'

    def setSpec(self, spec):
        self.layout.gap = f"{spec.gap}px" if spec.gap else None
        p = f"{spec.padding}px" if spec.padding else None
        self.layout.padding = p

    def clear(self):
        self.children = ()
class JupyterTabWidget(widgets.Tab):
    """Jupyter Tab Widget - native implementation"""
    def __init__(self):
        super().__init__()
        self.disabled = False

    def addTab(self, item, tab_name):
        old_content = list(self.children)
        old_content.append(item)
        self.children = tuple(old_content)
        self.set_title(len(self.children)-1, tab_name)

    def currentIndex(self):
        return self.selected_index

    def hide(self):
        self.layout.display = 'none'

    def show(self):
        self.layout.display = None

    def isVisible(self):
        return self.layout.display != 'none'

    def removeTabs(self):
        # Clearing children resets selected_index to None on its own; assigning
        # 0 here raises "index out of bounds" because no tab is left to select.
        self.children = []
class JupyterGrid(widgets.GridBox):
    """Jupyter Grid layout using CSS Grid via GridBox."""
    def __init__(self, columns: int = 12):
        super().__init__()
        self._columns = columns
        self.layout.grid_template_columns = f"repeat({columns}, 1fr)"
        self.layout.width = "100%"

    def setColumns(self, count: int):
        self._columns = count
        self.layout.grid_template_columns = f"repeat({count}, 1fr)"

    def addItem(self, item, col_span: int = 1):
        if hasattr(item, 'layout') and col_span > 1:
            item.layout.grid_column = f"span {col_span}"
        old = list(self.children)
        old.append(item)
        self.children = tuple(old)

    def setSpec(self, spec):
        if spec.gap:
            self.layout.gap = f"{spec.gap}px"
        if spec.padding:
            p = f"{spec.padding}px"
            self.layout.padding = p

    def clear(self):
        self.children = ()
class JupyterWrap(widgets.Box):
    """Jupyter Wrap layout — flex-flow: row wrap."""
    def __init__(self):
        super().__init__(layout=widgets.Layout(
            display='flex',
            flex_flow='row wrap',
            width='100%',
        ))

    def addItem(self, item):
        old = list(self.children)
        old.append(item)
        self.children = tuple(old)

    def setSpec(self, spec):
        if spec.gap:
            self.layout.gap = f"{spec.gap}px"
        if spec.padding:
            self.layout.padding = f"{spec.padding}px"

    def clear(self):
        self.children = ()
class JupyterScrollView(widgets.Box):
    """Jupyter ScrollView — overflow-y: auto."""
    def __init__(self):
        super().__init__(layout=widgets.Layout(
            overflow_y='auto',
            width='100%',
        ))

    def setContent(self, item):
        self.children = (item,)

    def setMaxHeight(self, height: int):
        self.layout.max_height = f"{height}px"
        self.layout.overflow_y = 'auto'

    def setMaxWidth(self, width: int):
        self.layout.max_width = f"{width}px"
class JupyterSplitPane(widgets.Box):
    """Jupyter SplitPane with a browser-side draggable divider.

    Pointer movement stays in the browser.  Only the final ratio is synced to
    Python on pointer-up, so dragging does not flood the notebook kernel.
    """
    def __init__(self, orientation: str = "horizontal"):
        self._orientation = orientation
        flex_flow = 'row' if orientation == 'horizontal' else 'column'
        super().__init__(layout=widgets.Layout(
            display='flex',
            flex_flow=flex_flow,
            width='100%',
        ))
        self.add_class('uniui-split-pane')
        self._first: Optional[widgets.Widget] = None
        self._second: Optional[widgets.Widget] = None
        self._ratio = 0.5
        self._syncing_ratio = False
        self._handle = widgets.HTML()
        self._handle.add_class('uniui-split-handle-widget')
        self._ratio_bridge = widgets.FloatText(value=self._ratio)
        self._ratio_bridge.layout.display = 'none'
        self._ratio_bridge.add_class('uniui-split-ratio-bridge')
        self._ratio_bridge.observe(self._on_ratio_bridge, names='value')
        self._configure_handle()

    def setFirst(self, item):
        self._first = item
        if hasattr(item, 'add_class'):
            item.add_class('uniui-split-first')
        if hasattr(item, 'layout'):
            item.layout.min_width = '0'
        self._sync()
        self._apply_ratio()

    def setSecond(self, item):
        self._second = item
        if hasattr(item, 'add_class'):
            item.add_class('uniui-split-second')
        if hasattr(item, 'layout'):
            item.layout.min_width = '0'
        self._sync()
        self._apply_ratio()

    def setOrientation(self, orientation: str):
        self._orientation = orientation
        self.layout.flex_flow = 'row' if orientation == 'horizontal' else 'column'
        self._configure_handle()
        self._apply_ratio()

    def setSizes(self, ratio: float):
        self._ratio = max(0.0, min(1.0, ratio))
        self._apply_ratio()
        if abs(self._ratio_bridge.value - self._ratio) > 1e-9:
            self._syncing_ratio = True
            self._ratio_bridge.value = self._ratio
            self._syncing_ratio = False

    def _apply_ratio(self):
        percent = self._ratio * 100
        if self._first and hasattr(self._first, 'layout'):
            self._first.layout.flex = f"0 0 {percent:.4f}%"
            if self._orientation == 'horizontal':
                self._first.layout.width = f"{percent:.4f}%"
                self._first.layout.height = None
            else:
                self._first.layout.height = f"{percent:.4f}%"
                self._first.layout.width = '100%'
        if self._second and hasattr(self._second, 'layout'):
            self._second.layout.flex = '1 1 0'
            if self._orientation == 'horizontal':
                self._second.layout.width = 'auto'
                self._second.layout.height = None
            else:
                self._second.layout.height = 'auto'
                self._second.layout.width = '100%'

    def _configure_handle(self):
        horizontal = self._orientation == 'horizontal'
        axis = 'clientX' if horizontal else 'clientY'
        origin = 'left' if horizontal else 'top'
        size = 'width' if horizontal else 'height'
        cursor = 'col-resize' if horizontal else 'row-resize'
        self._handle.layout.width = '6px' if horizontal else '100%'
        self._handle.layout.min_width = '6px' if horizontal else None
        self._handle.layout.height = '100%' if horizontal else '6px'
        self._handle.layout.min_height = None if horizontal else '6px'
        self._handle.layout.flex = '0 0 6px'
        self._handle.value = f"""
<div title="Drag to resize" style="width:100%;height:100%;min-height:6px;
 background:#98a2b3;cursor:{cursor};touch-action:none;border-radius:3px"
 onpointerdown="const h=this,root=h.closest('.uniui-split-pane'),first=root.querySelector('.uniui-split-first'),bridge=root.querySelector('.uniui-split-ratio-bridge input'),rect=root.getBoundingClientRect(),start=rect.{origin},total=rect.{size},pid=event.pointerId;h.setPointerCapture(pid);const move=e=>{{const ratio=Math.max(.05,Math.min(.95,(e.{axis}-start)/total));first.style.flex='0 0 '+(ratio*100)+'%';first.style.{size}=(ratio*100)+'%';return ratio;}};const up=e=>{{const ratio=move(e);if(bridge){{bridge.value=String(ratio);bridge.dispatchEvent(new Event('change',{{bubbles:true}}));}}h.removeEventListener('pointermove',move);}};h.addEventListener('pointermove',move);h.addEventListener('pointerup',up,{{once:true}});h.addEventListener('pointercancel',up,{{once:true}});">
</div>"""

    def _on_ratio_bridge(self, change):
        if not self._syncing_ratio:
            self.setSizes(float(change['new']))

    def _sync(self):
        children = []
        if self._first is not None:
            children.append(self._first)
        children.append(self._handle)
        if self._second is not None:
            children.append(self._second)
        children.append(self._ratio_bridge)
        self.children = tuple(children)
class JupyterOverlay(widgets.VBox):
    """Jupyter Overlay: shows one layer at a time.

    Deliberately built on VBox with manual show/hide rather than
    ipywidgets' Stack. Stack needs @jupyter-widgets/controls 2.x on the
    frontend, and renderers that don't implement StackView (notably the
    VS Code notebook renderer) draw nothing at all — the layers are in
    the model but never painted. VBox + layout.display works on every
    frontend.
    """
    def __init__(self):
        super().__init__()
        # Fill whatever container holds us; ipywidgets' DOM wrappers mean a
        # stylesheet rule cannot reliably reach this element.
        self.layout.width = '100%'
        self.layout.flex = '1 1 auto'
        self._layers: List = []
        self._active = 0

    def addLayer(self, item):
        if hasattr(item, 'layout') and item.layout.width is None:
            item.layout.width = '100%'
        self._layers.append(item)
        self._apply_visibility()

    def setActiveIndex(self, index: int):
        self._active = index
        self._apply_visibility()

    def _apply_visibility(self):
        if not self._layers:
            self.children = ()
            return

        # Keep every page object in _layers so RouterView can preserve page
        # state, but only mount the active page in the widget tree.  Updating
        # layout.display on an already-rendered nested widget is not reliably
        # repainted by every notebook frontend (notably VS Code), which can
        # leave the content area blank after navigation.
        self._active = max(0, min(self._active, len(self._layers) - 1))
        active = self._layers[self._active]
        if hasattr(active, 'layout'):
            active.layout.display = None
        self.children = (active,)
class JupyterVBoxAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, JupyterClassMixin, IVBoxLayout):
    """Jupyter VBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: widgets.VBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        self._native.children = self._native.children + (widget.get_native(),)

    def add_stretch(self):
        pass

    def set_alignment_top(self):
        self._native.layout.justify_content = "flex-start"

    def add_item_with_spec(self, widget: IWidget, item):
        native = widget.get_native()
        if item.grow > 0 and hasattr(native, "layout"):
            native.layout.flex = f"{item.grow} 1 auto"
        self._native.children = self._native.children + (native,)

    def set_spec(self, spec):
        self._native.layout.gap = f"{spec.gap}px" if spec.gap else None
        self._native.layout.padding = f"{spec.padding}px" if spec.padding else None

    def clear(self):
        self._native.children = ()
class JupyterHBoxAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, JupyterClassMixin, IHBoxLayout):
    """Jupyter HBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: widgets.HBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        native = widget.get_native()
        if hasattr(native, "layout"):
            native.layout.flex = None
            if not native.layout.width:
                native.layout.width = "auto"
        self._native.children = self._native.children + (native,)

    def add_stretch(self):
        spacer = widgets.Box(layout=widgets.Layout(flex="1 1 auto"))
        self._native.children = self._native.children + (spacer,)

    def set_alignment_top(self):
        self._native.layout.align_items = "flex-start"

    def add_item_with_spec(self, widget: IWidget, item):
        native = widget.get_native()
        if hasattr(native, "layout"):
            if item.grow > 0:
                # basis 0, not auto: with auto the child's content width seeds
                # the distribution, so a row of buttons sizes to its longest
                # label instead of dividing the row evenly.
                basis = item.basis if item.basis is not None else 0
                if isinstance(basis, (int, float)):
                    basis = f"{basis}px" if basis else "0"
                native.layout.flex = f"{item.grow} {item.shrink} {basis}"
                native.layout.min_width = "0"
            else:
                native.layout.flex = None
                if not native.layout.width:
                    native.layout.width = "auto"
        self._native.children = self._native.children + (native,)

    def set_spec(self, spec):
        self._native.layout.gap = f"{spec.gap}px" if spec.gap else None
        self._native.layout.padding = f"{spec.padding}px" if spec.padding else None

    def clear(self):
        self._native.children = ()
class JupyterTabWidgetAdapter(NativeMixin, VisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, ITabWidget):
    """Jupyter TabWidget adapter - implements snake_case interface convention"""

    # ITabCapable
    def add_tab(self, widget: IWidget, name: str):
        self._native.addTab(widget.get_native(), name)

    def remove_tabs(self):
        self._native.removeTabs()

    def get_current_index(self) -> int:
        return self._native.currentIndex()
class JupyterGridAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, JupyterClassMixin, IGrid):
    """Jupyter Grid adapter."""

    def __init__(self, columns: int = 12):
        self._native = JupyterGrid(columns)

    def get_native(self):
        return self._native

    def add_item(self, widget: IWidget, row: int = -1, col: int = -1,
                 row_span: int = 1, col_span: int = 1) -> None:
        self._native.addItem(widget.get_native(), col_span=col_span)

    def set_columns(self, count: int) -> None:
        self._native.setColumns(count)

    def set_spec(self, spec) -> None:
        self._native.setSpec(spec)

    def clear(self) -> None:
        self._native.clear()
class JupyterWrapAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, JupyterClassMixin, IWrap):
    """Jupyter Wrap adapter backed by a stock ipywidgets Box."""

    def __init__(self):
        self._native = widgets.Box(layout=widgets.Layout(
            display="flex", flex_flow="row wrap", width="100%",
        ))

    def get_native(self):
        return self._native

    def add_item(self, widget: IWidget) -> None:
        self._native.children = self._native.children + (widget.get_native(),)

    def set_spec(self, spec) -> None:
        self._native.layout.gap = f"{spec.gap}px" if spec.gap else None
        self._native.layout.padding = f"{spec.padding}px" if spec.padding else None

    def clear(self) -> None:
        self._native.children = ()
class JupyterScrollViewAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, IScrollView):
    """Jupyter ScrollView adapter."""

    def __init__(self):
        self._native = JupyterScrollView()

    def get_native(self):
        return self._native

    def set_content(self, widget: IWidget) -> None:
        self._native.setContent(widget.get_native())

    def set_max_height(self, height: int) -> None:
        self._native.setMaxHeight(height)

    def set_max_width(self, width: int) -> None:
        self._native.setMaxWidth(width)
class JupyterSplitPaneAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, ISplitPane):
    """Jupyter SplitPane adapter."""

    def __init__(self, orientation: str = "horizontal"):
        self._native = JupyterSplitPane(orientation)

    def get_native(self):
        return self._native

    def set_first(self, widget: IWidget) -> None:
        self._native.setFirst(widget.get_native())

    def set_second(self, widget: IWidget) -> None:
        self._native.setSecond(widget.get_native())

    def set_orientation(self, orientation: str) -> None:
        self._native.setOrientation(orientation)

    def set_sizes(self, ratio: float) -> None:
        self._native.setSizes(ratio)
def _close_widget_tree(widget) -> None:
    """Close ``widget`` and every descendant reachable via ``.children``,
    ``.layout``, or ``.style``.

    ipywidgets keeps a permanent strong reference to every un-closed widget
    in its global ``Widget.widgets`` registry (populated when its comm
    opens, popped only by ``close()``) — dropping every Python reference to
    a widget does NOT make it collectible, so this is a real, unbounded
    per-navigation leak, not just untidy state. ``Widget.close()`` itself is
    not recursive (``Box``/``VBox``/``HBox`` don't override it) and doesn't
    touch trait values, so a composite widget — any page with nested
    layouts, or an Admin component like Sidebar or Table — needs every
    descendant closed individually, including the ``Layout``/``Style``
    objects every widget carries (both are ``Widget`` subclasses with their
    own comm, registered in the same registry, and not closed by their
    owner). ``close()`` is idempotent (a no-op once ``self.comm`` is already
    None), so visiting the same widget twice (e.g. once via
    ``JupyterOverlayAdapter``'s original container and once via its
    synthetic render-wrapper, which shares the same child objects) is safe.
    """
    if not isinstance(widget, widgets.Widget):
        return
    for child in getattr(widget, "children", None) or ():
        _close_widget_tree(child)
    _close_widget_tree(getattr(widget, "layout", None))
    _close_widget_tree(getattr(widget, "style", None))
    widget.close()


class JupyterOverlayAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, IOverlay):
    """Jupyter Overlay adapter backed by a stock ipywidgets VBox.

    Keeping the routing state in the adapter avoids asking notebook
    frontends to construct a view for a custom Python widget subclass.  Some
    renderers accept the model but leave that view completely blank.
    """

    def __init__(self):
        self._native = widgets.VBox(
            layout=widgets.Layout(width="100%", flex="1 1 auto")
        )
        self._layers: List = []
        self._render_layers: List = []
        self._active = 0
        # Expose diagnostics on the native object for RouterView tests and
        # notebook troubleshooting without making it a custom widget class.
        self._native._layers = self._layers
        self._native._render_layers = self._render_layers
        self._native._active = self._active

    def get_native(self):
        return self._native

    def add_layer(self, widget: IWidget) -> None:
        native = widget.get_native()
        layout = getattr(native, "layout", None)
        if layout is not None and not layout.width:
            layout.width = "100%"
        self._layers.append(native)
        self._render_layers.append(self._make_render_layer(native))
        self._apply_active()

    def set_active_index(self, index: int) -> None:
        self._active = int(index)
        self._apply_active()

    def remove_layer(self, index: int) -> None:
        native = self._layers[index]
        wrapper = self._render_layers[index]
        del self._layers[index]
        del self._render_layers[index]
        self._native._layers = self._layers
        self._native._render_layers = self._render_layers
        if index <= self._active:
            self._active = max(0, self._active - 1)
        self._apply_active()
        # Close the original container (recursively closes every real
        # descendant widget) and the render wrapper (see _make_render_layer
        # — a distinct object when native.children exists, the same object
        # otherwise; _close_widget_tree/close() are idempotent either way).
        _close_widget_tree(native)
        _close_widget_tree(wrapper)

    def layer_count(self) -> int:
        return len(self._layers)

    def _apply_active(self) -> None:
        if not self._layers:
            self._native.children = ()
            return
        self._active = max(0, min(self._active, len(self._layers) - 1))
        self._native._active = self._active
        self._native.children = (self._render_layers[self._active],)

    @staticmethod
    def _make_render_layer(native):
        """Create a clean frontend container for composite route pages.

        Some notebook renderers can display every child of a route page but
        fail to construct a view for the original parent widget model.  A new
        stock VBox around the exact same child models renders correctly while
        preserving every input, callback, and cached page state.
        """
        children = getattr(native, "children", None)
        if children is None:
            return native

        source_layout = getattr(native, "layout", None)
        wrapper_layout = widgets.Layout(width="100%", min_width="0")
        gap = getattr(source_layout, "gap", None)
        padding = getattr(source_layout, "padding", None)
        if gap:
            wrapper_layout.grid_gap = gap
        if padding:
            wrapper_layout.padding = padding
        wrapper = widgets.VBox(children=tuple(children), layout=wrapper_layout)

        if hasattr(native, "observe"):
            def sync_children(change, target=wrapper):
                target.children = tuple(change["new"])
            native.observe(sync_children, names="children")
            wrapper._uniui_source_children_observer = sync_children
        return wrapper
