"""
Modern Admin components for the Jupyter/ipywidgets backend.

Compatibility layer. The implementations live in
:mod:`uniui.backends.jupyter`; this module re-exports them so existing imports
keep working - ``examples/`` imports this module as its admin backend.

Everything below is a re-export. Nothing is defined here, including
``JupyterWidgetFactory``: that is now
:mod:`uniui.backends.jupyter.factory`, so the canonical path
``registry -> backends.jupyter.factory -> primitives + components`` does not
detour through this module. No production code imports it.
"""
from __future__ import annotations

from uniui.components import (
    IAppShell, IBadge, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, IProgressBar, ISidebar, IStatCard, ITable,
)
from uniui.backends.jupyter.factory import JupyterWidgetFactory
from uniui.backends.jupyter.primitives import _BaseJupyterWidgetFactory
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
    JupyterBadgeAdapter,
    JupyterProgressBarAdapter,
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


__all__ = [
    "JupyterWidgetFactory",
    "JupyterCardAdapter", "JupyterStatCardAdapter", "JupyterMetricListAdapter",
    "JupyterBadgeAdapter",
    "JupyterProgressBarAdapter",
    "JupyterTableAdapter", "JupyterSidebarAdapter", "JupyterAppShellAdapter",
    "JupyterBreadcrumbAdapter", "JupyterGaugeAdapter", "JupyterChartAdapter",
    "JupyterDrawerAdapter",
    "get_palette", "is_dark", "set_theme",
    "get_admin_palette", "is_admin_dark", "set_admin_theme",
]
