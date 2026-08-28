"""The canonical Web (NiceGUI) widget factory.

This is what ``create_factory('web')`` returns. See
:mod:`uniui.backends.qt.factory` for why the class lives beside its backend
rather than in the root ``web_components`` compatibility module.

The class keeps its historical name ``NiceGUIWidgetFactory``; the public
selector is ``web``, so NiceGUI stays replaceable.
"""
from __future__ import annotations

from ...components import (
    IAppShell, IBadge, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, IProgressBar, ISidebar, IStatCard, ITable,
)
from .components import (
    WebAppShellAdapter, WebBadgeAdapter, WebBreadcrumbAdapter, WebCardAdapter,
    WebChartAdapter, WebDrawerAdapter, WebGaugeAdapter, WebMetricListAdapter,
    WebProgressBarAdapter, WebSidebarAdapter, WebStatCardAdapter, WebTableAdapter,
)
from .primitives import _BaseNiceGUIWidgetFactory


class NiceGUIWidgetFactory(_BaseNiceGUIWidgetFactory):
    """The Web factory ``create_factory('web')`` actually returns."""

    def createCard(self)       -> ICard:       return WebCardAdapter()
    def createStatCard(self)   -> IStatCard:   return WebStatCardAdapter()
    def createMetricList(self) -> IMetricList: return WebMetricListAdapter()
    def createBadge(self)      -> IBadge:      return WebBadgeAdapter()
    def createProgressBar(self) -> IProgressBar: return WebProgressBarAdapter()
    def createTable(self)      -> ITable:      return WebTableAdapter()
    def createSidebar(self)    -> ISidebar:    return WebSidebarAdapter()
    def createAppShell(self)   -> IAppShell:   return WebAppShellAdapter()
    def createBreadcrumb(self) -> IBreadcrumb: return WebBreadcrumbAdapter()
    def createGauge(self)      -> IGauge:      return WebGaugeAdapter()
    def createChart(self)      -> IChart:      return WebChartAdapter()
    def createDrawer(self)     -> IDrawer:     return WebDrawerAdapter()


__all__ = ["NiceGUIWidgetFactory"]
