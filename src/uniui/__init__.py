"""
UniUI - Universal UI Framework
Write once, run anywhere (Qt, Web, and Jupyter)

Example:
    >>> from uniui import Label, Button, VBox
    >>> label = Label("Hello World")
    >>> button = Button("Click Me")
    >>> layout = VBox(label, button)
"""

from .core import (
    # Exceptions
    UniUIException,
    NotSupportedError,
    WidgetCreationError,
    InvalidValueError,
    ConfigurationError,

    # Widget interfaces
    IWidget,
    ILabel,
    IButton,
    ILineEdit,
    ITextArea,
    IComboBox,
    IDropdown,
    IVBoxLayout,
    IHBoxLayout,
    ITabWidget,
    IGroupBox,
    IImage,

    # Advanced layout interfaces
    IGrid,
    IWrap,
    IScrollView,
    ISplitPane,
    IOverlay,

    # Layout data models
    SizeSpec,
    LayoutSpec,
    LayoutItem,
    Breakpoints,
    DEFAULT_BREAKPOINTS,

    # Factory interface
    IWidgetFactory,
)

# Reactive state and scheduling
from .state import State, Computed, Handle, TaskRunner
from .state import bind_text, bind_value, bind_items, bind_enabled, bind_visible

# Routing
from .routing import Router, Route, RouteContext, RouterView, RouteNotFoundError, NavMenu, sync_breadcrumb

# Admin component interfaces
from .admin import (
    IAppShell, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, ISidebar, IStatCard, ITable,
)

# Value parsing helpers
from .strategies import parse_float, parse_int, parse_flexible, normalize_text

# Theme configuration
from .theme import THEME, THEME_LIGHT, THEME_DARK, toggle_theme, is_dark

# Display
from .display import show_ui, refresh_theme, schedule_after

from typing import Optional
import sys


# ============================================================================
# Backward Compatibility - Widget Constants
# ============================================================================

LABEL = 'label'
BUTTON = 'button'
LINE_EDIT = 'line_edit'
TEXT_AREA = 'text_area'
COMBO_BOX = 'combo_box'
DROPDOWN = 'dropdown'
VBOX = 'vbox'
HBOX = 'hbox'
TAB_WIDGET = 'tab_widget'
GROUP_BOX = 'group_box'
IMAGE = 'image'
GRID = 'grid'
WRAP = 'wrap'
SCROLL_VIEW = 'scroll_view'
SPLIT_PANE = 'split_pane'
OVERLAY = 'overlay'
CARD = 'card'
STAT_CARD = 'stat_card'
METRIC_LIST = 'metric_list'
TABLE = 'table'
SIDEBAR = 'sidebar'
APP_SHELL = 'app_shell'
BREADCRUMB = 'breadcrumb'
GAUGE = 'gauge'
CHART = 'chart'
DRAWER = 'drawer'


# ============================================================================
# Platform Detection and Factory Selection
# ============================================================================

def _detect_framework() -> str:
    """Auto-detect available framework (priority order)"""
    # 1. Detect Jupyter notebook/lab (must have an active kernel with a comm_info
    #    method — plain IPython console and IDE kernels lack this).
    try:
        ip = get_ipython()
        kernel = getattr(ip, "kernel", None)
        if ip is not None and callable(getattr(kernel, "comm_info", None)):
            return 'jupyter'
    except NameError:
        pass

    # 2. Detect PySide2/Qt
    try:
        import PySide2
        return 'qt'
    except ImportError:
        pass

    # 3. Detect wxPython
    try:
        import wx
        return 'wx'
    except ImportError:
        pass

    # 4. Detect Tkinter (Python built-in)
    try:
        import tkinter
        return 'tk'
    except ImportError:
        pass

    raise ImportError(
        "No available UI framework found! "
        "Please install PySide2, wxPython, or use Jupyter."
    )


def _create_factory(framework: str = 'auto') -> IWidgetFactory:
    """Create factory for specified framework"""
    if framework == 'auto':
        framework = _detect_framework()

    web_module = sys.modules.get("uniui.web")
    if web_module is not None:
        web_module.set_backend_active(framework == "web")

    if framework == 'qt':
        from .qt import QtWidgetFactory
        from . import qt_admin  # noqa: F401 — registers admin methods on QtWidgetFactory
        return QtWidgetFactory()
    elif framework == 'jupyter':
        from .jupyter import JupyterWidgetFactory
        from . import jupyter_admin  # noqa: F401 — registers Admin methods
        return JupyterWidgetFactory()
    elif framework == 'web':
        try:
            from .web import NiceGUIWidgetFactory
            from . import web_admin  # noqa: F401 — registers Admin methods
        except ImportError as exc:
            raise ImportError(
                "The Web backend requires NiceGUI. Install it with "
                "'pip install -e .[web]'."
            ) from exc
        return NiceGUIWidgetFactory()
    elif framework == 'wx':
        import warnings
        warnings.warn(
            "The wxPython backend ('wx') is legacy and no longer supported. "
            "No new features will be developed. Please migrate to 'qt' or 'jupyter'.",
            DeprecationWarning,
            stacklevel=2
        )
        from .wx import WxWidgetFactory
        return WxWidgetFactory()
    elif framework == 'tk':
        import warnings
        warnings.warn(
            "The Tkinter backend ('tk') is legacy and no longer supported. "
            "No new features will be developed. Please migrate to 'qt' or 'jupyter'.",
            DeprecationWarning,
            stacklevel=2
        )
        from .tk import TkWidgetFactory
        return TkWidgetFactory()
    else:
        raise ValueError(f"Unsupported framework: {framework}")


# create_factory is the public name; _create_factory is the internal implementation
create_factory = _create_factory

# Global factory instance
_factory: Optional[IWidgetFactory] = None


def _get_factory() -> IWidgetFactory:
    """Get or create the global factory instance"""
    global _factory
    if _factory is None:
        _factory = _create_factory('auto')
    return _factory


def use(framework: str = 'auto'):
    """Set the UI framework to use"""
    global _factory
    _factory = _create_factory(framework)


def parse_args_ui() -> str:
    """Parse --ui argument from command line. Returns framework name."""
    import sys
    if "--ui" in sys.argv:
        idx = sys.argv.index("--ui")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return "auto"


# ============================================================================
# Direct Widget Creation Functions
# ============================================================================

def Label(text: str = "") -> ILabel:
    """Create a label widget"""
    label = _get_factory().create_label()
    if text:
        label.set_text(text)
    return label


def Button(text: str = "", on_click=None) -> IButton:
    """Create a button widget"""
    button = _get_factory().create_button()
    if text:
        button.set_text(text)
    if on_click:
        button.connect(on_click)
    return button


def LineEdit(text: str = "", on_change=None) -> ILineEdit:
    """Create a line edit widget"""
    line_edit = _get_factory().create_line_edit()
    if text:
        line_edit.set_text(text)
    if on_change:
        line_edit.on_change(on_change)
    return line_edit


def TextArea(text: str = "", on_change=None) -> ITextArea:
    """Create a text area widget"""
    text_area = _get_factory().create_text_area()
    if text:
        text_area.set_text(text)
    if on_change:
        text_area.on_change(on_change)
    return text_area


def ComboBox(items=None, on_change=None) -> IComboBox:
    """Create a combo box widget"""
    combo = _get_factory().create_combo_box()
    if items:
        for item in items:
            combo.add_item(item)
    if on_change:
        combo.on_change(on_change)
    return combo


def Dropdown(items=None, on_change=None) -> IDropdown:
    """Create a dropdown widget"""
    dropdown = _get_factory().create_dropdown()
    if items:
        for item in items:
            dropdown.add_item(item)
    if on_change:
        dropdown.on_change(on_change)
    return dropdown


def VBox(*children) -> IVBoxLayout:
    """Create a vertical box layout"""
    vbox = _get_factory().create_vbox()
    for child in children:
        if child is not None:
            vbox.add_item(child)
    return vbox


def HBox(*children) -> IHBoxLayout:
    """Create a horizontal box layout"""
    hbox = _get_factory().create_hbox()
    for child in children:
        if child is not None:
            hbox.add_item(child)
    return hbox


def Column(*children, spec: LayoutSpec = None) -> IVBoxLayout:
    """Create a vertical column layout (alias for VBox with optional LayoutSpec)"""
    col = _get_factory().create_vbox()
    if spec is not None:
        col.set_spec(spec)
    for child in children:
        if child is not None:
            col.add_item(child)
    return col


def Row(*children, spec: LayoutSpec = None) -> IHBoxLayout:
    """Create a horizontal row layout (alias for HBox with optional LayoutSpec)"""
    row = _get_factory().create_hbox()
    if spec is not None:
        row.set_spec(spec)
    for child in children:
        if child is not None:
            row.add_item(child)
    return row


def Grid(columns: int = 12, spec: LayoutSpec = None) -> IGrid:
    """Create a grid layout with the given number of columns."""
    grid = _get_factory().create_grid(columns)
    if spec is not None:
        grid.set_spec(spec)
    return grid


def Wrap(spec: LayoutSpec = None) -> IWrap:
    """Create a wrapping flow layout."""
    wrap = _get_factory().create_wrap()
    if spec is not None:
        wrap.set_spec(spec)
    return wrap


def ScrollView(content=None, max_height: int = None) -> IScrollView:
    """Create a scrollable container. Optionally set initial content and max height."""
    sv = _get_factory().create_scroll_view()
    if max_height is not None:
        sv.set_max_height(max_height)
    if content is not None:
        sv.set_content(content)
    return sv


def SplitPane(first=None, second=None, orientation: str = "horizontal",
              ratio: float = 0.5) -> ISplitPane:
    """Create a two-pane split container."""
    sp = _get_factory().create_split_pane(orientation)
    if first is not None:
        sp.set_first(first)
    if second is not None:
        sp.set_second(second)
    sp.set_sizes(ratio)
    return sp


def Overlay(*layers) -> IOverlay:
    """Create a stacked overlay container. First layer is active by default."""
    ov = _get_factory().create_overlay()
    for layer in layers:
        if layer is not None:
            ov.add_layer(layer)
    return ov


def Card(title: str = "", subtitle: str = "", content=None) -> ICard:
    """Create a titled card container."""
    card = _get_factory().create_card()
    if title:
        card.set_title(title)
    if subtitle:
        card.set_subtitle(subtitle)
    if content is not None:
        card.set_content(content)
    return card


def StatCard(label: str = "", value: str = "", unit: str = "",
             trend: float = 0.0, status: str = "ok") -> IStatCard:
    """Create a metric stat card."""
    sc = _get_factory().create_stat_card()
    if label:
        sc.set_label(label)
    if value:
        sc.set_value(value)
    if unit:
        sc.set_unit(unit)
    sc.set_trend(trend)
    sc.set_status(status)
    return sc


def MetricList(items=None) -> IMetricList:
    """Create a compact key/value metric list."""
    ml = _get_factory().create_metric_list()
    if items is not None:
        ml.set_items(items)
    return ml


def Table(columns=None, rows=None) -> ITable:
    """Create a data table."""
    tbl = _get_factory().create_table()
    if columns is not None:
        tbl.set_columns(columns)
    if rows is not None:
        tbl.set_rows(rows)
    return tbl


def Sidebar() -> ISidebar:
    """Create a navigation sidebar."""
    return _get_factory().create_sidebar()


def AppShell(header=None, sidebar=None, content=None, footer=None) -> IAppShell:
    """Create an application shell."""
    shell = _get_factory().create_app_shell()
    if header is not None:
        shell.set_header(header)
    if sidebar is not None:
        shell.set_sidebar(sidebar)
    if content is not None:
        shell.set_content(content)
    if footer is not None:
        shell.set_footer(footer)
    return shell


def Breadcrumb(items=None) -> IBreadcrumb:
    """Create a breadcrumb navigation widget."""
    bc = _get_factory().create_breadcrumb()
    if items is not None:
        bc.set_items(items)
    return bc


def Gauge(label: str = "", value: float = 0.0, unit: str = "",
          minimum: float = 0.0, maximum: float = 100.0,
          status: str = "ok") -> IGauge:
    gauge = _get_factory().create_gauge()
    gauge.set_range(minimum, maximum)
    gauge.set_label(label)
    gauge.set_unit(unit)
    gauge.set_status(status)
    gauge.set_value(value)
    return gauge


def Chart(chart_type: str = "line", title: str = "", x=None,
          series=None, max_points: int = 120, **options) -> IChart:
    if "type" in options:
        chart_type = options.pop("type")
    if options:
        unknown = ", ".join(sorted(options))
        raise TypeError(f"Unknown Chart option(s): {unknown}")
    chart = _get_factory().create_chart()
    chart.set_type(chart_type)
    chart.set_title(title)
    chart.set_max_points(max_points)
    chart.set_data(list(x or []), list(series or []))
    return chart


def Drawer(title: str = "", content=None) -> IDrawer:
    drawer = _get_factory().create_drawer()
    drawer.set_title(title)
    if content is not None:
        drawer.set_content(content)
    return drawer


def TabWidget() -> ITabWidget:
    """Create a tab widget"""
    return _get_factory().create_tab_widget()


def GroupBox(title: str = "", layout=None) -> IGroupBox:
    """Create a group box widget"""
    group = _get_factory().create_group_box()
    if title:
        group.set_title(title)
    if layout:
        group.set_layout(layout)
    return group


def Image(path: str = "") -> IImage:
    """Create an image widget"""
    image = _get_factory().create_image()
    if path:
        image.set_image(path)
    return image


# ============================================================================
# Backward Compatibility - UniUI Class
# ============================================================================

class UniUI:
    """Backward compatible UniUI facade class"""

    _KIND_MAP = {
        'label':       'create_label',
        'button':      'create_button',
        'line_edit':   'create_line_edit',
        'text_area':   'create_text_area',
        'combo_box':   'create_combo_box',
        'dropdown':    'create_dropdown',
        'vbox':        'create_vbox',
        'hbox':        'create_hbox',
        'tab_widget':  'create_tab_widget',
        'group_box':   'create_group_box',
        'image':       'create_image',
        'grid':        'create_grid',
        'wrap':        'create_wrap',
        'scroll_view': 'create_scroll_view',
        'split_pane':  'create_split_pane',
        'overlay':     'create_overlay',
    }

    def __init__(self, framework: str = 'auto'):
        self._framework = framework
        self._factory = _create_factory(framework)

    @property
    def framework(self) -> str:
        return self._framework

    def create(self, kind: str) -> IWidget:
        """Create a widget by kind string"""
        method = self._KIND_MAP.get(kind)
        if method is None:
            raise ValueError(f"Unknown widget kind: {kind}")
        return getattr(self._factory, method)()

    def label(self) -> ILabel:        return self._factory.create_label()
    def button(self) -> IButton:      return self._factory.create_button()
    def line_edit(self) -> ILineEdit: return self._factory.create_line_edit()
    def text_area(self) -> ITextArea: return self._factory.create_text_area()
    def combo_box(self) -> IComboBox: return self._factory.create_combo_box()
    def dropdown(self) -> IDropdown:  return self._factory.create_dropdown()
    def vbox(self) -> IVBoxLayout:    return self._factory.create_vbox()
    def hbox(self) -> IHBoxLayout:    return self._factory.create_hbox()
    def tab_widget(self) -> ITabWidget: return self._factory.create_tab_widget()
    def group_box(self) -> IGroupBox: return self._factory.create_group_box()
    def image(self) -> IImage:        return self._factory.create_image()


__all__ = [
    # Reactive state
    'State',
    'Computed',
    'Handle',
    'TaskRunner',
    'bind_text',
    'bind_value',
    'bind_items',
    'bind_enabled',
    'bind_visible',

    # Routing
    'Router',
    'Route',
    'RouteContext',
    'RouterView',
    'RouteNotFoundError',
    'NavMenu',
    'sync_breadcrumb',

    # Admin interfaces
    'ICard',
    'IStatCard',
    'IMetricList',
    'ITable',
    'ISidebar',
    'IAppShell',
    'IBreadcrumb',
    'IGauge',
    'IChart',
    'IDrawer',

    # Widget creation functions
    'Label',
    'Button',
    'LineEdit',
    'TextArea',
    'ComboBox',
    'Dropdown',
    'VBox',
    'HBox',
    'Column',
    'Row',
    'Grid',
    'Wrap',
    'ScrollView',
    'SplitPane',
    'Overlay',
    'Card',
    'StatCard',
    'MetricList',
    'Table',
    'Sidebar',
    'AppShell',
    'Breadcrumb',
    'Gauge',
    'Chart',
    'Drawer',
    'TabWidget',
    'GroupBox',
    'Image',

    # Layout data models
    'SizeSpec',
    'LayoutSpec',
    'LayoutItem',
    'Breakpoints',
    'DEFAULT_BREAKPOINTS',

    # Backward compatibility
    'UniUI',
    'LABEL', 'BUTTON', 'LINE_EDIT', 'TEXT_AREA',
    'COMBO_BOX', 'DROPDOWN', 'VBOX', 'HBOX', 'TAB_WIDGET', 'GROUP_BOX', 'IMAGE',
    'GRID', 'WRAP', 'SCROLL_VIEW', 'SPLIT_PANE', 'OVERLAY',
    'CARD', 'STAT_CARD', 'METRIC_LIST', 'TABLE', 'SIDEBAR', 'APP_SHELL', 'BREADCRUMB',
    'GAUGE', 'CHART', 'DRAWER',

    # Framework selection
    'use',
    'create_factory',
    'parse_args_ui',

    # Exceptions
    'UniUIException',
    'NotSupportedError',
    'WidgetCreationError',
    'InvalidValueError',
    'ConfigurationError',

    # Interfaces
    'IWidget',
    'IWidgetFactory',
    'ILabel',
    'IButton',
    'ILineEdit',
    'ITextArea',
    'IComboBox',
    'IDropdown',
    'IVBoxLayout',
    'IHBoxLayout',
    'IGrid',
    'IWrap',
    'IScrollView',
    'ISplitPane',
    'IOverlay',
    'ITabWidget',
    'IGroupBox',
    'IImage',

    # Parsing helpers
    'parse_float',
    'parse_int',
    'parse_flexible',
    'normalize_text',

    # Theme
    'THEME',
    'THEME_LIGHT',
    'THEME_DARK',
    'toggle_theme',
    'is_dark',

    # Display
    'show_ui',
    'refresh_theme',
    'schedule_after',
]

__version__ = '0.6.0'
