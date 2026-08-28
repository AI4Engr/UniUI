"""
UniUI - Universal UI Framework
Write once, run anywhere (Qt, Web, and Jupyter)

Example:
    >>> from uniui import Label, Button, VBox
    >>> label = Label("Hello World")
    >>> button = Button("Click Me")
    >>> layout = VBox(label, button)

This module is the stable public surface. It defines almost nothing itself:
backend detection and factory selection live in
:mod:`uniui.backends.registry`, the convenience constructors and the legacy
``UniUI`` class live in :mod:`uniui.facade`, and the interfaces live in
:mod:`uniui.contracts`. Import paths here are unchanged.

``_factory`` is deliberately *not* re-exported. ``use()`` rebinds it inside the
registry module, so a re-export here would be a stale snapshot and ``use()``
would appear to have no effect. Read it via ``registry._get_factory()``.
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
    ILayoutOnly,
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
from .state import State, Computed, Handle, TaskRunner, batch
from .state import bind_text, bind_value, bind_items, bind_enabled, bind_visible

# Routing
from .routing import (
    Router, Route, RouteContext, RouterView, RouteNotFoundError, NavMenu, Link,
    sync_breadcrumb, sync_page_title,
)

# Admin component interfaces
from .components import (
    IAppShell, IBadge, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, IProgressBar, ISidebar, IStatCard, ITable,
)

# Value parsing helpers
from .strategies import parse_float, parse_int, parse_flexible, normalize_text

# Theme configuration
from .theme import (
    THEME, THEME_LIGHT, THEME_DARK, toggle_theme, set_theme, is_dark,
    set_active_theme, get_active_theme_name, register_theme, list_themes,
)

# Display
from .display import show_ui, refresh_theme, schedule_after

from typing import Optional
import sys

# Backend detection and factory selection
from .backends.registry import (
    _create_factory, _detect_framework, _get_factory, create_factory,
    parse_args_ui, use,
)

# Convenience constructors and the legacy facade class
from .facade import (
    AppShell, Badge, Breadcrumb, Button, Card, Chart, Column, ComboBox, Drawer,
    Dropdown, Gauge, GroupBox, HBox, Image, Label, LineEdit, MetricList,
    Overlay, ProgressBar, Row, ScrollView, Sidebar, SplitPane, StatCard, Table, TabWidget,
    TextArea, UniUI, VBox, Wrap, Grid,
)


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
BADGE = 'badge'
PROGRESS_BAR = 'progress_bar'
TABLE = 'table'
SIDEBAR = 'sidebar'
APP_SHELL = 'app_shell'
BREADCRUMB = 'breadcrumb'
GAUGE = 'gauge'
CHART = 'chart'
DRAWER = 'drawer'


__all__ = [
    # Reactive state
    'State',
    'Computed',
    'Handle',
    'TaskRunner',
    'batch',
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
    'Link',
    'sync_breadcrumb',
    'sync_page_title',

    # Admin interfaces
    'ICard',
    'IStatCard',
    'IMetricList',
    'IBadge',
    'IProgressBar',
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
    'Badge',
    'ProgressBar',
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
    'CARD', 'STAT_CARD', 'METRIC_LIST', 'BADGE', 'PROGRESS_BAR', 'TABLE', 'SIDEBAR', 'APP_SHELL', 'BREADCRUMB',
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
    'ILayoutOnly',
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
    'set_active_theme',
    'get_active_theme_name',
    'register_theme',
    'list_themes',

    # Display
    'show_ui',
    'refresh_theme',
    'schedule_after',
]

__version__ = '0.6.0'
