"""
Core types and interfaces - Simplified.

Defines:
- Widget interfaces: ILabel, IButton, ILineEdit, etc.
- Layout interfaces: IVBoxLayout, IHBoxLayout with sizing/flex support
- Layout data models: SizeSpec, LayoutSpec, LayoutItem
- IWidgetFactory: abstract factory that each supported platform implements
- Exception classes: NotSupportedError, WidgetCreationError, etc.

This is the only module that platform implementations depend on.
"""
from abc import ABC, abstractmethod
from typing import Callable, Any, Optional
from dataclasses import dataclass, field


# ============================================================================
# Exception Classes
# ============================================================================

class UniUIException(Exception):
    """Base exception for all UniUI errors"""
    pass


class NotSupportedError(UniUIException):
    """Raised when a widget type is not supported on a specific platform."""
    pass


class WidgetCreationError(UniUIException):
    """Raised when widget creation fails."""
    pass


class InvalidValueError(UniUIException):
    """Raised when a value cannot be parsed or is invalid"""
    pass


class ConfigurationError(UniUIException):
    """Raised when there's a configuration problem"""
    pass




# ============================================================================
# Layout Data Models
# ============================================================================

@dataclass
class SizeSpec:
    """Describes how a widget sizes itself along one axis.

    value meanings:
      - None / "auto"  : size to content
      - "fill"         : expand to fill available space (grow=1, shrink=1)
      - int / float    : fixed pixel size
      - str "50%"      : percentage of parent (renderer may interpret)
    min / max are pixel bounds applied after the main value is resolved.
    """
    value: Any = None          # None = "auto"
    min: Optional[int] = None
    max: Optional[int] = None

    # Flexbox-style coefficients
    grow: float = 0.0
    shrink: float = 1.0
    basis: Any = None          # None = auto

    @classmethod
    def auto(cls) -> "SizeSpec":
        return cls(value=None)

    @classmethod
    def fill(cls) -> "SizeSpec":
        return cls(value="fill", grow=1.0, shrink=1.0)

    @classmethod
    def fixed(cls, px: int) -> "SizeSpec":
        return cls(value=px, grow=0.0, shrink=0.0)

    @classmethod
    def pct(cls, percent: float) -> "SizeSpec":
        return cls(value=f"{percent}%")


@dataclass
class LayoutSpec:
    """Layout parameters for a container (Row, Column, etc.).

    gap     : spacing between children in pixels
    padding : inner padding of the container in pixels
    wrap    : allow children to wrap to next row/column
    align   : main-axis alignment ("start", "center", "end", "space-between", "space-around")
    cross_align : cross-axis alignment ("start", "center", "end", "stretch")
    """
    gap: int = 0
    padding: int = 0
    wrap: bool = False
    align: str = "start"
    cross_align: str = "start"


@dataclass
class LayoutItem:
    """Wraps a widget with per-child layout overrides.

    grow / shrink override the parent SizeSpec for this child only.
    align_self overrides cross-axis alignment for this child.
    span is used by Grid layouts (column span).
    """
    widget: Any                # IWidget — forward reference avoids circular import
    grow: float = 0.0
    shrink: float = 1.0
    basis: Any = None
    align_self: Optional[str] = None
    span: int = 1
    key: Optional[str] = None  # stable identity across reflows


# ============================================================================
# Widget Interfaces
# ============================================================================

class IWidget(ABC):
    """Base interface for all widgets"""

    @abstractmethod
    def get_native(self):
        """Get the underlying native widget"""
        pass


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
    def connect(self, callback: Callable[[], None]) -> None:
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
    def on_change(self, callback: Callable[[], None]) -> None:
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
    def on_change(self, callback: Callable[[], None]) -> None:
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
    def on_change(self, callback: Callable[[], None]) -> None:
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
    def on_change(self, callback: Callable[[], None]) -> None:
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


class IVBoxLayout(IWidget):
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


class IHBoxLayout(IWidget):
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

    def clear(self) -> None:
        """Remove all children. Default: not supported."""
        raise NotSupportedError("clear() not supported on this layout")


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




# ============================================================================
# Responsive Breakpoints
# ============================================================================

@dataclass
class Breakpoints:
    """Container-width breakpoints for responsive layout mode switching.

    mode_for(width) returns "compact", "medium", or "wide".
    Default thresholds match TODO.md: compact < 720, medium < 1200, wide >= 1200.
    """
    compact: int = 720
    medium: int = 1200

    def mode_for(self, width: int) -> str:
        if width < self.compact:
            return "compact"
        if width < self.medium:
            return "medium"
        return "wide"


DEFAULT_BREAKPOINTS = Breakpoints()


# ============================================================================
# Advanced Layout Interfaces
# ============================================================================

class IGrid(IWidget):
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
                  breakpoints: "Breakpoints" = None) -> None:
        """Register a callback fired when the container crosses a breakpoint.
        callback receives "compact" | "medium" | "wide".
        Default: no-op (backends that support it override this).
        """
        pass


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


# ============================================================================
# Factory Interface
# ============================================================================

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

    # snake_case aliases
    def create_label(self) -> ILabel:
        return self.createLabel()

    def create_button(self) -> IButton:
        return self.createButton()

    def create_line_edit(self) -> ILineEdit:
        return self.createLineEdit()

    def create_text_area(self) -> ITextArea:
        return self.createTextArea()

    def create_combo_box(self) -> IComboBox:
        return self.createComboBox()

    def create_dropdown(self) -> IDropdown:
        return self.createDropdown()

    def create_vbox(self) -> IVBoxLayout:
        return self.createVBox()

    def create_hbox(self) -> IHBoxLayout:
        return self.createHBox()

    def create_tab_widget(self) -> ITabWidget:
        return self.createTabWidget()

    def create_image(self) -> IImage:
        return self.createImage()

    def create_group_box(self) -> IGroupBox:
        return self.createGroupBox()

    def create_grid(self, columns: int = 12) -> "IGrid":
        return self.createGrid(columns)

    def create_wrap(self) -> "IWrap":
        return self.createWrap()

    def create_scroll_view(self) -> "IScrollView":
        return self.createScrollView()

    def create_split_pane(self, orientation: str = "horizontal") -> "ISplitPane":
        return self.createSplitPane(orientation)

    def create_overlay(self) -> "IOverlay":
        return self.createOverlay()

    def create_card(self) -> "ICard":
        return self.createCard()

    def create_stat_card(self) -> "IStatCard":
        return self.createStatCard()

    def create_table(self) -> "ITable":
        return self.createTable()

    def create_metric_list(self) -> "IMetricList":
        return self.createMetricList()

    def create_sidebar(self) -> "ISidebar":
        return self.createSidebar()

    def create_app_shell(self) -> "IAppShell":
        return self.createAppShell()

    def create_breadcrumb(self) -> "IBreadcrumb":
        return self.createBreadcrumb()

    def create_gauge(self) -> "IGauge":
        return self.createGauge()

    def create_chart(self) -> "IChart":
        return self.createChart()

    def create_drawer(self) -> "IDrawer":
        return self.createDrawer()
