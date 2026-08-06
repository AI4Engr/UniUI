"""Web/NiceGUI display, theme refresh and scheduling.

Moved out of the root ``display.py``, which is now a thin dispatcher.

Theme refresh and scheduling live in ``primitives/theming.py`` — the Web theme
spine rewrites CSS custom properties on the client, which plain controls need
whether or not an AppShell exists.  This module re-exports them under the
dispatcher's naming convention so ``display.py`` can treat all three backends
the same way.
"""
from __future__ import annotations

import os
import sys

from ...theme import THEME
from .primitives.theming import (
    refresh_theme_web as refresh_theme,
    schedule_after_web as schedule_after,
)

T = THEME


def show(native, title, width, height, set_refresh_root=None) -> bool:
    """Run a NiceGUI-backed layout as a standalone Web application."""
    if not native.__class__.__module__.startswith("nicegui."):
        return False
    try:
        from nicegui import ui
        from nicegui.element import Element

        if not isinstance(native, Element):
            return False

        def option(name, default=None):
            flag = f"--{name}"
            if flag in sys.argv:
                index = sys.argv.index(flag)
                if index + 1 < len(sys.argv):
                    return sys.argv[index + 1]
            return default

        host = option("host", os.environ.get("UNIUI_WEB_HOST", "127.0.0.1"))
        port_value = option("port", os.environ.get("UNIUI_WEB_PORT", "8080"))
        try:
            port = int(port_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid Web port: {port_value}") from exc

        show_browser = "--no-browser" not in sys.argv
        if os.environ.get("UNIUI_WEB_BROWSER", "").lower() in {"0", "false", "no"}:
            show_browser = False

        native.classes(add="uniui-root")
        native.style(
            f"width: 100%; max-width: 100%; min-height: {height}px; margin: 0 auto"
        )

        refresh_theme(native)

        if set_refresh_root:
            set_refresh_root(native)

        ui.run(
            host=host,
            port=port,
            title=title,
            show=show_browser,
            reload=False,
        )
        return True
    except ImportError:
        return False


__all__ = ["refresh_theme", "schedule_after", "show"]
