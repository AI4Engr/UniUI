"""Web Admin components, one module per component."""
from .app_shell import WebAppShellAdapter
from .badge import WebBadgeAdapter
from .breadcrumb import WebBreadcrumbAdapter
from .card import WebCardAdapter
from .chart import WebChartAdapter
from .drawer import WebDrawerAdapter
from .gauge import WebGaugeAdapter
from .metric_list import WebMetricListAdapter
from .progress_bar import WebProgressBarAdapter
from .sidebar import WebSidebarAdapter
from .stat_card import WebStatCardAdapter
from .toast import WebToastAdapter
from .table import WebTableAdapter

__all__ = [
    "WebAppShellAdapter",
    "WebBadgeAdapter",
    "WebBreadcrumbAdapter",
    "WebCardAdapter",
    "WebChartAdapter",
    "WebDrawerAdapter",
    "WebGaugeAdapter",
    "WebMetricListAdapter",
    "WebProgressBarAdapter",
    "WebSidebarAdapter",
    "WebStatCardAdapter",
    "WebToastAdapter",
    "WebTableAdapter",
]
