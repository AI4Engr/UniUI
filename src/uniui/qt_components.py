"""
Qt/PySide2 implementations of admin components.

Compatibility layer. The implementations live in :mod:`uniui.backends.qt`;
this module re-exports them so existing imports keep working - ``examples/``
imports ``get_admin_palette`` and ``set_admin_theme`` from here.

Everything below is a re-export. Nothing is defined here, including
``QtWidgetFactory``: that is now :mod:`uniui.backends.qt.factory`, so the
canonical path ``registry -> backends.qt.factory -> primitives + components``
does not detour through this module. No production code imports it.

``_C`` is bound to the *same* dict object that ``backends.qt.runtime`` mutates
in place on a theme change - never rebind it, or this module would freeze at
whatever theme was active when it was first imported.
"""
from __future__ import annotations

from uniui.components import (
    IAppShell, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, ISidebar, IStatCard, ITable,
)
from uniui.backends.qt.factory import QtWidgetFactory
from uniui.backends.qt.primitives import _BaseQtWidgetFactory
from uniui.backends.qt.runtime import (
    C as _C,
    M as _M,
    THEMED_ADAPTERS as _THEMED_ADAPTERS,
    _qt_tokens,
    as_widget as _as_widget,
    clear_layout as _clear_layout,
    get_palette,
    is_dark,
    label as _label,
    native as _native,
    nav_icon as _nav_icon,
    set_theme,
    sync_palette as _sync_palette,
    track_themed as _track_themed,
)
from uniui.backends.qt.styles import (
    _SCROLLBAR_TEMPLATE,
    card_style as _card_style,
    scrollbar_rules as _scrollbar_rules,
)
from uniui.backends.qt.components import (
    QtAppShellAdapter,
    QtBreadcrumbAdapter,
    QtCardAdapter,
    QtChartAdapter,
    QtDrawerAdapter,
    QtGaugeAdapter,
    QtMetricListAdapter,
    QtSidebarAdapter,
    QtStatCardAdapter,
    QtTableAdapter,
    _breadcrumb_button_style,
    _ChartWidget,
    _GaugeWidget,
    _ResponsiveShellWidget,
    _sidebar_style,
    _StatusPillDelegate,
    _status_colors,
    _table_style,
)

# Names used before the admin_ prefix was dropped.
get_admin_palette = get_palette
is_admin_dark = is_dark
set_admin_theme = set_theme


__all__ = [
    "QtWidgetFactory",
    "QtAppShellAdapter",
    "QtBreadcrumbAdapter",
    "QtCardAdapter",
    "QtChartAdapter",
    "QtDrawerAdapter",
    "QtGaugeAdapter",
    "QtMetricListAdapter",
    "QtSidebarAdapter",
    "QtStatCardAdapter",
    "QtTableAdapter",
    "get_palette",
    "is_dark",
    "set_theme",
    "get_admin_palette",
    "is_admin_dark",
    "set_admin_theme",
]
