"""Web Admin components, one module per component."""
from .app_shell import WebAppShellAdapter
from .breadcrumb import WebBreadcrumbAdapter
from .card import WebCardAdapter
from .chart import WebChartAdapter
from .drawer import WebDrawerAdapter
from .gauge import WebGaugeAdapter
from .metric_list import WebMetricListAdapter
from .sidebar import WebSidebarAdapter
from .stat_card import WebStatCardAdapter
from .table import WebTableAdapter

__all__ = [
    "WebAppShellAdapter",
    "WebBreadcrumbAdapter",
    "WebCardAdapter",
    "WebChartAdapter",
    "WebDrawerAdapter",
    "WebGaugeAdapter",
    "WebMetricListAdapter",
    "WebSidebarAdapter",
    "WebStatCardAdapter",
    "WebTableAdapter",
]
