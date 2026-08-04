"""
Qt/PySide2 implementations of admin components.

Compatibility layer. The implementations now live in :mod:`uniui.backends.qt`;
this module re-exports them so existing imports keep working - ``qt_style``
imports the palette helpers from here, and ``examples/`` imports
``get_admin_palette`` and ``set_admin_theme``.

Everything below is a re-export, with one exception: ``QtWidgetFactory``,
which is still defined here because it is what ``create_factory('qt')``
returns.

``_C`` is bound to the *same* dict object that ``backends.qt.runtime`` mutates
in place on a theme change - never rebind it, or this module would freeze at
whatever theme was active when it was first imported.
"""
from __future__ import annotations

from uniui.components import (
    IAppShell, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, ISidebar, IStatCard, ITable,
)
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


# ---------------------------------------------------------------------------
# QtWidgetFactory: base factory + Card/Table/AppShell/... support
# ---------------------------------------------------------------------------

from uniui.qt import _BaseQtWidgetFactory


class QtWidgetFactory(_BaseQtWidgetFactory):
    """The Qt factory create_factory('qt') actually returns."""

    def createCard(self)       -> ICard:       return QtCardAdapter()
    def createStatCard(self)   -> IStatCard:   return QtStatCardAdapter()
    def createMetricList(self) -> IMetricList: return QtMetricListAdapter()
    def createTable(self)      -> ITable:      return QtTableAdapter()
    def createSidebar(self)    -> ISidebar:    return QtSidebarAdapter()
    def createAppShell(self)   -> IAppShell:   return QtAppShellAdapter()
    def createBreadcrumb(self) -> IBreadcrumb: return QtBreadcrumbAdapter()
    def createGauge(self)      -> IGauge:      return QtGaugeAdapter()
    def createChart(self)      -> IChart:      return QtChartAdapter()
    def createDrawer(self)     -> IDrawer:     return QtDrawerAdapter()


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
