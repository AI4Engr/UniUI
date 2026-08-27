"""Jupyter Admin components, one module per component."""
from .app_shell import JupyterAppShellAdapter
from .badge import JupyterBadgeAdapter
from .breadcrumb import JupyterBreadcrumbAdapter
from .card import JupyterCardAdapter
from .chart import JupyterChartAdapter
from .drawer import JupyterDrawerAdapter
from .gauge import JupyterGaugeAdapter
from .metric_list import JupyterMetricListAdapter
from .sidebar import JupyterSidebarAdapter
from .stat_card import JupyterStatCardAdapter
from .table import JupyterTableAdapter

__all__ = [
    "JupyterAppShellAdapter",
    "JupyterBadgeAdapter",
    "JupyterBreadcrumbAdapter",
    "JupyterCardAdapter",
    "JupyterChartAdapter",
    "JupyterDrawerAdapter",
    "JupyterGaugeAdapter",
    "JupyterMetricListAdapter",
    "JupyterSidebarAdapter",
    "JupyterStatCardAdapter",
    "JupyterTableAdapter",
]
