"""
Modern Admin components for the Jupyter/ipywidgets backend.

Compatibility layer. The implementations now live in
:mod:`uniui.backends.jupyter`; this module re-exports them so existing imports
keep working - ``jupyter_style`` imports ``get_admin_palette`` from here, and
``examples/`` imports this module as its admin backend.

Everything below is a re-export, with one exception: ``JupyterWidgetFactory``,
which is still defined here because it is what ``create_factory('jupyter')``
returns.
"""
from __future__ import annotations

from uniui.components import (
    IAppShell, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, ISidebar, IStatCard, ITable,
)
from uniui.backends.jupyter.runtime import (
    M as _M,
    THEME_TARGETS as _theme_targets,
    get_palette,
    html as _html,
    is_dark,
    native as _native,
    set_theme,
    sync_palette as _sync_palette,
    track_themed as _track_themed,
)
from uniui.backends.jupyter.styles import (
    DEBUG_MEASURE_JS as _DEBUG_MEASURE_JS,
    SPLITTER_HTML as _SPLITTER_HTML,
    css as _css,
    debug_html as _debug_html,
    shared_icon_css as _shared_icon_css,
)
from uniui.backends.jupyter.components import (
    JupyterAppShellAdapter,
    JupyterBreadcrumbAdapter,
    JupyterCardAdapter,
    JupyterChartAdapter,
    JupyterDrawerAdapter,
    JupyterGaugeAdapter,
    JupyterMetricListAdapter,
    JupyterSidebarAdapter,
    JupyterStatCardAdapter,
    JupyterTableAdapter,
)

# Names used before the admin_ prefix was dropped.
get_admin_palette = get_palette
is_admin_dark = is_dark
set_admin_theme = set_theme


# ---------------------------------------------------------------------------
# JupyterWidgetFactory: base factory + Card/Table/AppShell/... support
# ---------------------------------------------------------------------------

from uniui.jupyter import _BaseJupyterWidgetFactory


class JupyterWidgetFactory(_BaseJupyterWidgetFactory):
    """The Jupyter factory create_factory('jupyter') actually returns."""

    def createCard(self) -> ICard: return JupyterCardAdapter()
    def createStatCard(self) -> IStatCard: return JupyterStatCardAdapter()
    def createMetricList(self) -> IMetricList: return JupyterMetricListAdapter()
    def createTable(self) -> ITable: return JupyterTableAdapter()
    def createSidebar(self) -> ISidebar: return JupyterSidebarAdapter()
    def createAppShell(self) -> IAppShell: return JupyterAppShellAdapter()
    def createBreadcrumb(self) -> IBreadcrumb: return JupyterBreadcrumbAdapter()
    def createGauge(self) -> IGauge: return JupyterGaugeAdapter()
    def createChart(self) -> IChart: return JupyterChartAdapter()
    def createDrawer(self) -> IDrawer: return JupyterDrawerAdapter()


__all__ = [
    "JupyterWidgetFactory",
    "JupyterCardAdapter", "JupyterStatCardAdapter", "JupyterMetricListAdapter",
    "JupyterTableAdapter", "JupyterSidebarAdapter", "JupyterAppShellAdapter",
    "JupyterBreadcrumbAdapter", "JupyterGaugeAdapter", "JupyterChartAdapter",
    "JupyterDrawerAdapter",
    "get_palette", "is_dark", "set_theme",
    "get_admin_palette", "is_admin_dark", "set_admin_theme",
]
