"""Theme state and helpers shared by every Web Admin component.

There is no live palette dict here: a theme switch re-emits the CSS custom
properties on each live shell, so components call :func:`get_palette` at render
time. Anything that paints colours into its own markup (the gauge and chart
render SVG server-side) must register via :func:`track_visual` or it keeps stale
colours after a switch.

``M`` (design metrics) is static for the process lifetime and is safe to read at
import time; the palette is not.
"""
from __future__ import annotations

from typing import Dict, List

from ... import theme_runtime
from ...theme import get_admin_metrics


#: Design metrics. Static for the process lifetime.
M = get_admin_metrics()

#: Live shells and self-rendering visuals, refreshed on a theme change. These
#: are plain lists rather than a WeakSet because NiceGUI elements are owned by
#: their page slot, not by the adapter.
SHELLS: List[object] = []
VISUALS: List[object] = []

native = theme_runtime.native


def get_palette() -> Dict[str, str]:
    """Return a copy of the active Web Admin palette.

    Reads theme_runtime.get_palette() -- the actual active palette -- rather
    than re-deriving one from a light/dark bool, which only ever knows about
    the two built-in themes and would silently ignore a named theme
    registered via uniui.register_theme.
    """
    return theme_runtime.get_palette()


def is_dark() -> bool:
    return theme_runtime.is_dark()


@theme_runtime.register_refresh
def sync_palette() -> None:
    """Re-render every live shell and visual after a theme change.

    Registered with theme_runtime, so switching from any backend restyles the
    web components too - the per-backend flags used to drift apart.
    """
    for target in (*list(SHELLS), *list(VISUALS)):
        try:
            target.apply_theme()
        except Exception:
            continue


def set_theme(dark: bool) -> bool:
    """Switch every live shell, on this and every other backend."""
    return theme_runtime.set_theme(dark)


def track_shell(shell) -> None:
    """Register an app shell for CSS-variable refresh on a theme change."""
    SHELLS.append(shell)


def track_visual(visual) -> None:
    """Register a server-rendered visual (gauge, chart) for re-render."""
    VISUALS.append(visual)


def clear(element) -> None:
    """Remove every child of a NiceGUI container."""
    element.clear()
