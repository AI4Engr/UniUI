"""The canonical Qt widget factory.

This is what ``create_factory('qt')`` returns. It is the one place that joins
the two halves of the backend:

    primitives/  the controls every app gets (label, button, layouts, ...)
    components/  the Admin layer (Card, Table, AppShell, ...)

``uniui.qt_components`` used to own this class, which made the canonical
dependency chain detour through a root-level compatibility module:

    registry -> uniui.qt_components -> uniui.qt -> backends.qt.primitives

It now runs straight down:

    registry -> backends.qt.factory -> backends.qt.{primitives,components}

``qt_components`` re-exports this class so old imports keep working, but it no
longer defines it.
"""
from __future__ import annotations

from ...components import (
    IAppShell, IBadge, IBreadcrumb, ICard, ICarousel, IChart, IDrawer, IGauge,
    IMetricList, IProgressBar, ISidebar, IStatCard, ITable, IToast,
)
from .components import (
    QtAppShellAdapter, QtBadgeAdapter, QtBreadcrumbAdapter, QtCardAdapter,
    QtCarouselAdapter, QtChartAdapter, QtDrawerAdapter, QtGaugeAdapter,
    QtMetricListAdapter, QtProgressBarAdapter, QtSidebarAdapter,
    QtStatCardAdapter, QtTableAdapter, QtToastAdapter,
)
from .primitives import _BaseQtWidgetFactory


class QtWidgetFactory(_BaseQtWidgetFactory):
    """The Qt factory ``create_factory('qt')`` actually returns."""

    def createCard(self)       -> ICard:       return QtCardAdapter()
    def createStatCard(self)   -> IStatCard:   return QtStatCardAdapter()
    def createMetricList(self) -> IMetricList: return QtMetricListAdapter()
    def createBadge(self)      -> IBadge:      return QtBadgeAdapter()
    def createProgressBar(self) -> IProgressBar: return QtProgressBarAdapter()
    def createToast(self)      -> IToast:      return QtToastAdapter()
    def createCarousel(self)   -> ICarousel:   return QtCarouselAdapter()
    def createTable(self)      -> ITable:      return QtTableAdapter()
    def createSidebar(self)    -> ISidebar:    return QtSidebarAdapter()
    def createAppShell(self)   -> IAppShell:   return QtAppShellAdapter()
    def createBreadcrumb(self) -> IBreadcrumb: return QtBreadcrumbAdapter()
    def createGauge(self)      -> IGauge:      return QtGaugeAdapter()
    def createChart(self)      -> IChart:      return QtChartAdapter()
    def createDrawer(self)     -> IDrawer:     return QtDrawerAdapter()


__all__ = ["QtWidgetFactory"]
