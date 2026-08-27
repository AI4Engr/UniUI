"""The canonical Jupyter widget factory.

This is what ``create_factory('jupyter')`` returns. See
:mod:`uniui.backends.qt.factory` for why the class lives beside its backend
rather than in the root ``jupyter_components`` compatibility module.
"""
from __future__ import annotations

from ...components import (
    IAppShell, IBadge, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, ISidebar, IStatCard, ITable,
)
from .components import (
    JupyterAppShellAdapter, JupyterBadgeAdapter, JupyterBreadcrumbAdapter,
    JupyterCardAdapter, JupyterChartAdapter, JupyterDrawerAdapter,
    JupyterGaugeAdapter, JupyterMetricListAdapter, JupyterSidebarAdapter,
    JupyterStatCardAdapter, JupyterTableAdapter,
)
from .primitives import _BaseJupyterWidgetFactory


class JupyterWidgetFactory(_BaseJupyterWidgetFactory):
    """The Jupyter factory ``create_factory('jupyter')`` actually returns."""

    def createCard(self)       -> ICard:       return JupyterCardAdapter()
    def createStatCard(self)   -> IStatCard:   return JupyterStatCardAdapter()
    def createMetricList(self) -> IMetricList: return JupyterMetricListAdapter()
    def createBadge(self)      -> IBadge:      return JupyterBadgeAdapter()
    def createTable(self)      -> ITable:      return JupyterTableAdapter()
    def createSidebar(self)    -> ISidebar:    return JupyterSidebarAdapter()
    def createAppShell(self)   -> IAppShell:   return JupyterAppShellAdapter()
    def createBreadcrumb(self) -> IBreadcrumb: return JupyterBreadcrumbAdapter()
    def createGauge(self)      -> IGauge:      return JupyterGaugeAdapter()
    def createChart(self)      -> IChart:      return JupyterChartAdapter()
    def createDrawer(self)     -> IDrawer:     return JupyterDrawerAdapter()


__all__ = ["JupyterWidgetFactory"]
