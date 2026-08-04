"""Qt Admin components, one module per component.

Names with a leading underscore are internal to the Qt backend but are
re-exported here (and by ``uniui.qt_components``) because tests and the
examples reach for them.
"""
from .app_shell import QtAppShellAdapter, _ResponsiveShellWidget
from .breadcrumb import QtBreadcrumbAdapter, _breadcrumb_button_style
from .card import QtCardAdapter
from .chart import QtChartAdapter, _ChartWidget
from .drawer import QtDrawerAdapter
from .gauge import QtGaugeAdapter, _GaugeWidget
from .metric_list import QtMetricListAdapter
from .sidebar import QtSidebarAdapter, _sidebar_style
from .stat_card import QtStatCardAdapter
from .table import (
    QtTableAdapter,
    _StatusPillDelegate,
    _status_colors,
    _table_style,
)

__all__ = [
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
    "_ChartWidget",
    "_GaugeWidget",
    "_ResponsiveShellWidget",
    "_StatusPillDelegate",
    "_breadcrumb_button_style",
    "_sidebar_style",
    "_status_colors",
    "_table_style",
]
