"""
Modern Admin components for the NiceGUI Web backend.

Compatibility layer. The implementations live in :mod:`uniui.backends.web`;
this module re-exports them so existing imports keep working - ``examples/``
imports this module as its admin backend and the tests import the theme
helpers from here.

Everything below is a re-export. Nothing is defined here, including
``NiceGUIWidgetFactory``: that is now :mod:`uniui.backends.web.factory`, so
the canonical path ``registry -> backends.web.factory -> primitives +
components`` does not detour through this module. No production code imports
it.

Note that ``_css_installed`` is deliberately *not* re-exported. It is mutable
state owned by :mod:`uniui.backends.web.styles` (the CSS is emitted once per
process), and a plain import would copy the value rather than alias it - so a
test that reset it here would leave the owning module still believing the CSS
had been installed. Reset it on ``backends.web.styles`` instead.
"""
from __future__ import annotations

from uniui.components import (
    IAppShell, IBadge, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, ISidebar, IStatCard, ITable,
)
from uniui.backends.web.factory import NiceGUIWidgetFactory
from uniui.backends.web.primitives import _BaseNiceGUIWidgetFactory
from uniui.backends.web.runtime import (
    M as _M,
    SHELLS as _shells,
    VISUALS as _visuals,
    clear as _clear,
    get_palette,
    is_dark,
    native as _native,
    set_theme,
    sync_palette as _sync_palette,
)
from uniui.backends.web.styles import (
    install_admin_css as _install_admin_css,
    shared_icon_css as _shared_icon_css,
)
from uniui.backends.web.components import (
    WebAppShellAdapter,
    WebBadgeAdapter,
    WebBreadcrumbAdapter,
    WebCardAdapter,
    WebChartAdapter,
    WebDrawerAdapter,
    WebGaugeAdapter,
    WebMetricListAdapter,
    WebSidebarAdapter,
    WebStatCardAdapter,
    WebTableAdapter,
)

# Names used before the admin_ prefix was dropped.
get_admin_palette = get_palette
is_admin_dark = is_dark
set_admin_theme = set_theme


__all__ = [
    "NiceGUIWidgetFactory",
    "WebCardAdapter", "WebStatCardAdapter", "WebMetricListAdapter",
    "WebBadgeAdapter",
    "WebTableAdapter", "WebSidebarAdapter", "WebAppShellAdapter",
    "WebBreadcrumbAdapter", "WebGaugeAdapter", "WebChartAdapter",
    "WebDrawerAdapter",
    "get_palette", "is_dark", "set_theme",
    "get_admin_palette", "is_admin_dark", "set_admin_theme",
]
