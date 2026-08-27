"""The abstract widget and factory contracts every backend implements.

Depends on :mod:`.layout` and :mod:`.exceptions`, never the other way round,
and on no backend. The Admin interfaces (``ICard``, ``ITable``, ...) appear
only as string annotations on ``IWidgetFactory``, so importing
:mod:`uniui.components` here would be an unnecessary cycle.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from .exceptions import NotSupportedError
from .layout import Breakpoints, DEFAULT_BREAKPOINTS, LayoutItem, LayoutSpec
from ..state import Handle


class IWidget(ABC):
    """Base interface for all widgets"""

    @abstractmethod
    def get_native(self):
        """Get the underlying native widget"""
        pass

    # Common capabilities. Non-abstract so a backend that hasn't wired one up
    # yet doesn't fail ABC instantiation; adapters shadow these with a real
    # implementation (typically via a shared mixin operating on get_native()).
    def show(self) -> None:
        pass

    def hide(self) -> None:
        pass

    def is_visible(self) -> bool:
        return True

    def set_enabled(self, enabled: bool) -> None:
        pass

    def is_enabled(self) -> bool:
        return True

    def set_fixed_width(self, width: int) -> None:
        pass

    def set_fixed_height(self, height: int) -> None:
        pass

    def set_minimum_width(self, width: int) -> None:
        pass

    def set_minimum_height(self, height: int) -> None:
        pass


class ILayoutOnly(IWidget):
    """Marker for widgets whose native object is a pure layout manager, not
    a widget — additive documentation, not a behavior change.

    On Qt, `IVBoxLayout`/`IHBoxLayout`/`IGrid`'s native object is a raw
    `QVBoxLayout`/`QHBoxLayout`/`QGridLayout` (a `QLayout`): it has no
    show/hide/enabled/size surface at all, which is why those three
    interfaces override every "common capability" with a `NotSupportedError`
    default instead of inheriting `IWidget`'s real one. Jupyter and Web don't
    have this problem — their VBox/HBox/Grid wrap a real widget — so this
    marker only describes what's true on the *worst-case* backend, not every
    backend; it exists so a reader (or a future static check) can tell "this
    interface's `IWidget` capability methods are not guaranteed to work" at
    a glance, without re-deriving it from the Qt-specific comments on each
    `NotSupportedError` override.
    """
class ILabel(IWidget):
    """Label widget interface"""

    @abstractmethod
    def set_text(self, text: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def hide(self) -> None:
        pass

    @abstractmethod
    def is_visible(self) -> bool:
        pass

    @abstractmethod
    def set_fixed_width(self, width: int) -> None:
        pass
class IButton(IWidget):
    """Button widget interface"""

    @abstractmethod
    def set_text(self, text: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def connect(self, callback: Callable[[], None]) -> Handle:
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        pass
class ILineEdit(IWidget):
    """Line edit widget interface"""

    @abstractmethod
    def set_text(self, text: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def set_value(self, value: Any) -> None:
        pass

    @abstractmethod
    def get_value(self) -> Any:
        pass

    @abstractmethod
    def on_change(self, callback: Callable[[], None]) -> Handle:
        pass

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def hide(self) -> None:
        pass

    @abstractmethod
    def is_visible(self) -> bool:
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        pass

    @abstractmethod
    def set_fixed_width(self, width: int) -> None:
        pass
class ITextArea(IWidget):
    """Text area widget interface"""

    @abstractmethod
    def set_text(self, text: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def append(self, text: str) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def on_change(self, callback: Callable[[], None]) -> Handle:
        pass

    @abstractmethod
    def set_maximum_height(self, height: int) -> None:
        pass

    def set_html(self, html: str) -> None:
        """Render HTML content. Backends that support HTML override this.
        Default: strip tags and fall back to plain text."""
        import re
        plain = re.sub(r'<[^>]+>', '', html)
        plain = (plain.replace('&nbsp;', ' ').replace('&amp;', '&')
                      .replace('&lt;', '<').replace('&gt;', '>'))
        self.set_text(plain)
class IComboBox(IWidget):
    """Combo box widget interface"""

    @abstractmethod
    def add_item(self, item: str) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def set_selection(self, item: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def on_change(self, callback: Callable[[], None]) -> Handle:
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        pass
class IDropdown(IWidget):
    """Dropdown widget interface"""

    @abstractmethod
    def add_item(self, item: str) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def set_selection(self, item: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def set_value(self, value: Any) -> None:
        pass

    @abstractmethod
    def on_change(self, callback: Callable[[], None]) -> Handle:
        pass

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def hide(self) -> None:
        pass

    @abstractmethod
    def is_visible(self) -> bool:
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        pass
class IVBoxLayout(ILayoutOnly):
    """Vertical box layout interface"""

    @abstractmethod
    def add_item(self, widget: IWidget) -> None:
        pass

    @abstractmethod
    def add_stretch(self) -> None:
        pass

    @abstractmethod
    def set_alignment_top(self) -> None:
        pass

    def add_item_with_spec(self, widget: IWidget, item: "LayoutItem") -> None:
        """Add a widget with per-child layout overrides. Default: delegates to add_item."""
        self.add_item(widget)

    def set_spec(self, spec: "LayoutSpec") -> None:
        """Apply container-level layout spec (gap, padding, etc.). Default: no-op."""
        pass

    def clear(self) -> None:
        """Remove all children. Default: not supported."""
        raise NotSupportedError("clear() not supported on this layout")

    # A box layout's native object is a plain layout manager, not a widget
    # (see Qt's QVBoxLayout) — no show/hide/enabled/size surface to forward
    # to. Backends whose native IS a real widget (Jupyter, Web) override
    # these with a real implementation; Qt does not.
    def show(self) -> None:
        raise NotSupportedError("show() not supported on this layout")

    def hide(self) -> None:
        raise NotSupportedError("hide() not supported on this layout")

    def is_visible(self) -> bool:
        raise NotSupportedError("is_visible() not supported on this layout")

    def set_enabled(self, enabled: bool) -> None:
        raise NotSupportedError("set_enabled() not supported on this layout")

    def is_enabled(self) -> bool:
        raise NotSupportedError("is_enabled() not supported on this layout")

    def set_fixed_width(self, width: int) -> None:
        raise NotSupportedError("set_fixed_width() not supported on this layout")

    def set_fixed_height(self, height: int) -> None:
        raise NotSupportedError("set_fixed_height() not supported on this layout")

    def set_minimum_width(self, width: int) -> None:
        raise NotSupportedError("set_minimum_width() not supported on this layout")

    def set_minimum_height(self, height: int) -> None:
        raise NotSupportedError("set_minimum_height() not supported on this layout")
class IHBoxLayout(ILayoutOnly):
    """Horizontal box layout interface"""

    @abstractmethod
    def add_item(self, widget: IWidget) -> None:
        pass

    @abstractmethod
    def add_stretch(self) -> None:
        pass

    @abstractmethod
    def set_alignment_top(self) -> None:
        pass

    def add_item_with_spec(self, widget: IWidget, item: "LayoutItem") -> None:
        """Add a widget with per-child layout overrides. Default: delegates to add_item."""
        self.add_item(widget)

    def set_spec(self, spec: "LayoutSpec") -> None:
        """Apply container-level layout spec (gap, padding, etc.). Default: no-op."""
        pass

    def set_responsive_stack(self, enabled: bool) -> None:
        """Allow/forbid this row collapsing to a stacked column on narrow
        screens. Default True (matches prior behavior). A key row, toolbar or
        button grid that must stay a row at every width should pass False;
        an ordinary form row of label+input is fine collapsing on mobile.

        No-op on backends without a narrow-screen stacking rule (Qt, Jupyter).
        """
        pass

    def clear(self) -> None:
        """Remove all children. Default: not supported."""
        raise NotSupportedError("clear() not supported on this layout")

    # See IVBoxLayout's identical block: a box layout's native object has no
    # show/hide/enabled/size surface (Qt's QHBoxLayout is not a widget).
    def show(self) -> None:
        raise NotSupportedError("show() not supported on this layout")

    def hide(self) -> None:
        raise NotSupportedError("hide() not supported on this layout")

    def is_visible(self) -> bool:
        raise NotSupportedError("is_visible() not supported on this layout")

    def set_enabled(self, enabled: bool) -> None:
        raise NotSupportedError("set_enabled() not supported on this layout")

    def is_enabled(self) -> bool:
        raise NotSupportedError("is_enabled() not supported on this layout")

    def set_fixed_width(self, width: int) -> None:
        raise NotSupportedError("set_fixed_width() not supported on this layout")

    def set_fixed_height(self, height: int) -> None:
        raise NotSupportedError("set_fixed_height() not supported on this layout")

    def set_minimum_width(self, width: int) -> None:
        raise NotSupportedError("set_minimum_width() not supported on this layout")

    def set_minimum_height(self, height: int) -> None:
        raise NotSupportedError("set_minimum_height() not supported on this layout")
class ITabWidget(IWidget):
    """Tab widget interface"""

    @abstractmethod
    def add_tab(self, widget: IWidget, name: str) -> None:
        pass

    @abstractmethod
    def remove_tabs(self) -> None:
        pass

    @abstractmethod
    def get_current_index(self) -> int:
        pass

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def hide(self) -> None:
        pass

    @abstractmethod
    def is_visible(self) -> bool:
        pass
class IGroupBox(IWidget):
    """Group box interface"""

    @abstractmethod
    def set_layout(self, layout: IWidget) -> None:
        pass

    @abstractmethod
    def set_title(self, title: str) -> None:
        pass
class IImage(IWidget):
    """Image widget interface"""

    @abstractmethod
    def set_image(self, path: str) -> None:
        pass

    @abstractmethod
    def set_image_from_url(self, url: str) -> None:
        pass

    @abstractmethod
    def set_fixed_width(self, width: int) -> None:
        pass
class IGrid(ILayoutOnly):
    """Grid layout interface — maps to QGridLayout / CSS Grid / ui.grid."""

    @abstractmethod
    def add_item(self, widget: "IWidget", row: int = -1, col: int = -1,
                 row_span: int = 1, col_span: int = 1) -> None:
        pass

    @abstractmethod
    def set_columns(self, count: int) -> None:
        pass

    def set_spec(self, spec: "LayoutSpec") -> None:
        pass

    def clear(self) -> None:
        raise NotSupportedError("clear() not supported on this Grid")

    def on_resize(self, callback: Callable[[str], None],
                  breakpoints: "Breakpoints" = None) -> Handle:
        """Register a callback fired when the container crosses a breakpoint.
        callback receives "compact" | "medium" | "wide".
        Default: no-op (backends that support it override this).
        """
        return Handle(lambda: None)

    # See IVBoxLayout's identical block: a grid layout's native object has no
    # show/hide/enabled/size surface (Qt's QGridLayout is not a widget).
    def show(self) -> None:
        raise NotSupportedError("show() not supported on this Grid")

    def hide(self) -> None:
        raise NotSupportedError("hide() not supported on this Grid")

    def is_visible(self) -> bool:
        raise NotSupportedError("is_visible() not supported on this Grid")

    def set_enabled(self, enabled: bool) -> None:
        raise NotSupportedError("set_enabled() not supported on this Grid")

    def is_enabled(self) -> bool:
        raise NotSupportedError("is_enabled() not supported on this Grid")

    def set_fixed_width(self, width: int) -> None:
        raise NotSupportedError("set_fixed_width() not supported on this Grid")

    def set_fixed_height(self, height: int) -> None:
        raise NotSupportedError("set_fixed_height() not supported on this Grid")

    def set_minimum_width(self, width: int) -> None:
        raise NotSupportedError("set_minimum_width() not supported on this Grid")

    def set_minimum_height(self, height: int) -> None:
        raise NotSupportedError("set_minimum_height() not supported on this Grid")
class IWrap(IWidget):
    """Wrapping flow layout — children wrap to next row when they overflow."""

    @abstractmethod
    def add_item(self, widget: "IWidget") -> None:
        pass

    def set_spec(self, spec: "LayoutSpec") -> None:
        pass

    def clear(self) -> None:
        raise NotSupportedError("clear() not supported on this Wrap")
class IScrollView(IWidget):
    """Scrollable container — wraps a single child with overflow scrolling."""

    @abstractmethod
    def set_content(self, widget: "IWidget") -> None:
        pass

    def set_max_height(self, height: int) -> None:
        pass

    def set_max_width(self, width: int) -> None:
        pass
class ISplitPane(IWidget):
    """Two-pane resizable container — maps to QSplitter / flexbox ratio."""

    @abstractmethod
    def set_first(self, widget: "IWidget") -> None:
        pass

    @abstractmethod
    def set_second(self, widget: "IWidget") -> None:
        pass

    @abstractmethod
    def set_orientation(self, orientation: str) -> None:
        """orientation: "horizontal" (side by side) | "vertical" (stacked)."""
        pass

    def set_sizes(self, ratio: float) -> None:
        """Set first-pane fraction (0.0–1.0). Default: 0.5."""
        pass
class IOverlay(IWidget):
    """Stacked layer container — only one layer visible at a time."""

    @abstractmethod
    def add_layer(self, widget: "IWidget") -> None:
        pass

    @abstractmethod
    def set_active_index(self, index: int) -> None:
        pass

    @abstractmethod
    def remove_layer(self, index: int) -> None:
        """Remove and dispose the layer at index, shifting later indices down."""
        pass

    @abstractmethod
    def layer_count(self) -> int:
        pass
class IWidgetFactory(ABC):
    """Widget factory interface"""

    @abstractmethod
    def createLabel(self) -> ILabel:
        pass

    @abstractmethod
    def createButton(self) -> IButton:
        pass

    @abstractmethod
    def createLineEdit(self) -> ILineEdit:
        pass

    @abstractmethod
    def createTextArea(self) -> ITextArea:
        pass

    @abstractmethod
    def createComboBox(self) -> IComboBox:
        pass

    @abstractmethod
    def createDropdown(self) -> IDropdown:
        pass

    @abstractmethod
    def createVBox(self) -> IVBoxLayout:
        pass

    @abstractmethod
    def createHBox(self) -> IHBoxLayout:
        pass

    @abstractmethod
    def createTabWidget(self) -> ITabWidget:
        pass

    @abstractmethod
    def createImage(self) -> IImage:
        pass

    def createGroupBox(self) -> IGroupBox:
        """Create group box widget (optional, not all platforms support this)"""
        raise NotSupportedError("GroupBox not supported on this platform")

    def createGrid(self, columns: int = 12) -> "IGrid":
        """Create grid layout (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("Grid not supported on this platform")

    def createWrap(self) -> "IWrap":
        """Create wrap flow layout (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("Wrap not supported on this platform")

    def createScrollView(self) -> "IScrollView":
        """Create scroll view container (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("ScrollView not supported on this platform")

    def createSplitPane(self, orientation: str = "horizontal") -> "ISplitPane":
        """Create split pane container (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("SplitPane not supported on this platform")

    def createOverlay(self) -> "IOverlay":
        """Create overlay/stack container (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("Overlay not supported on this platform")

    def createCard(self) -> "ICard":
        """Create a titled card container (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("Card not supported on this platform")

    def createStatCard(self) -> "IStatCard":
        """Create a metric stat card (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("StatCard not supported on this platform")

    def createMetricList(self) -> "IMetricList":
        """Create a label/value metric list (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("MetricList not supported on this platform")

    def createBadge(self) -> "IBadge":
        """Create a status badge/tag (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("Badge not supported on this platform")

    def createTable(self) -> "ITable":
        """Create a tabular data table (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("Table not supported on this platform")

    def createSidebar(self) -> "ISidebar":
        """Create a navigation sidebar (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("Sidebar not supported on this platform")

    def createAppShell(self) -> "IAppShell":
        """Create an application shell (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("AppShell not supported on this platform")

    def createBreadcrumb(self) -> "IBreadcrumb":
        """Create a breadcrumb navigation widget (optional, raises NotSupportedError by default)"""
        raise NotSupportedError("Breadcrumb not supported on this platform")

    def createGauge(self) -> "IGauge":
        raise NotSupportedError("Gauge not supported on this platform")

    def createChart(self) -> "IChart":
        raise NotSupportedError("Chart not supported on this platform")

    def createDrawer(self) -> "IDrawer":
        raise NotSupportedError("Drawer not supported on this platform")

    # The snake_case aliases (create_label, create_vbox, ...) are not written
    # out here. They are generated from _SNAKE_ALIASES below and attached to
    # this class at import time - see _install_snake_aliases.


#: camelCase name -> snake_case alias. Generated in one place instead of 26
#: hand-written forwarders that could drift from their camelCase originals.
#:
#: The mapping is explicit rather than computed: a naive camel-to-snake rule
#: turns ``createVBox`` into ``create_v_box``, but the published alias has
#: always been ``create_vbox``. Two irregular pairs, so a table is safer than
#: a regex with special cases.
_SNAKE_ALIASES = {
    "createLabel":      "create_label",
    "createButton":     "create_button",
    "createLineEdit":   "create_line_edit",
    "createTextArea":   "create_text_area",
    "createComboBox":   "create_combo_box",
    "createDropdown":   "create_dropdown",
    "createVBox":       "create_vbox",       # irregular: not create_v_box
    "createHBox":       "create_hbox",       # irregular: not create_h_box
    "createTabWidget":  "create_tab_widget",
    "createImage":      "create_image",
    "createGroupBox":   "create_group_box",
    "createGrid":       "create_grid",
    "createWrap":       "create_wrap",
    "createScrollView": "create_scroll_view",
    "createSplitPane":  "create_split_pane",
    "createOverlay":    "create_overlay",
    "createCard":       "create_card",
    "createStatCard":   "create_stat_card",
    "createMetricList": "create_metric_list",
    "createBadge":      "create_badge",
    "createTable":      "create_table",
    "createSidebar":    "create_sidebar",
    "createAppShell":   "create_app_shell",
    "createBreadcrumb": "create_breadcrumb",
    "createGauge":      "create_gauge",
    "createChart":      "create_chart",
    "createDrawer":     "create_drawer",
}


def _install_snake_aliases(cls, mapping):
    """Attach a snake_case forwarder for each camelCase factory method.

    The forwarder resolves its target by name on ``self`` at call time, so a
    backend that overrides only ``createLabel`` is still reached through
    ``create_label``. Binding the function object here instead would freeze
    the base-class implementation and ignore the override.
    """
    for camel, snake in mapping.items():
        def forward(self, *args, _camel=camel, **kwargs):
            return getattr(self, _camel)(*args, **kwargs)

        original = getattr(cls, camel)
        forward.__name__ = snake
        forward.__qualname__ = f"{cls.__qualname__}.{snake}"
        forward.__doc__ = f"snake_case alias for :meth:`{camel}`."
        forward.__annotations__ = dict(getattr(original, "__annotations__", {}))
        setattr(cls, snake, forward)


_install_snake_aliases(IWidgetFactory, _SNAKE_ALIASES)
