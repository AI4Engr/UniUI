"""Live theme refresh and the scheduling helper."""
from __future__ import annotations

from typing import Any, Callable, List, Optional

from nicegui import ui

from ....core import *
from ....strategies import normalize_text, parse_float
from ....theme import THEME, is_dark
from . import state
from .state import T, adapters


def refresh_theme_web(root_widget=None) -> None:
    """Refresh all live NiceGUI-backed UniUI elements."""
    # ``_dark_mode`` is owned by the state module. Assigning through the module
    # object is deliberate: a bare ``global`` here would create a *second*
    # variable local to this module and the toggle would silently stop working.
    ui.colors(primary=T["accent"])
    if state._dark_mode is None:
        state._dark_mode = ui.dark_mode(is_dark())
    elif is_dark():
        state._dark_mode.enable()
    else:
        state._dark_mode.disable()

    for adapter in adapters():
        try:
            adapter._apply_theme()
        except Exception:
            continue

    if root_widget is not None:
        root_widget.classes(add="uniui-root")
        is_admin = "uniui-web-admin" in getattr(root_widget, "_classes", [])
        if is_admin:
            root_widget.style(
                f"background: {T['bg']}; color: {T['fg']}; padding: 0; gap: 0; "
                "width: 100%; max-width: none; height: 100dvh; min-height: 0; "
                "margin: 0; overflow: hidden; "
                f"--uniui-spacing: {T['spacing']}px; --uniui-radius: {T['border_radius']}px"
            )
        else:
            root_widget.style(
                f"background: {T['bg']}; color: {T['fg']}; "
                f"padding: {T['padding']}px; gap: {T['spacing']}px; "
                f"--uniui-spacing: {T['spacing']}px; --uniui-radius: {T['border_radius']}px"
            )
def schedule_after_web(ms: int, callback: Callable[[], None]) -> bool:
    """Schedule a callback on the NiceGUI event loop when Web is active."""
    # Read through the accessor, not a bound copy: the flag flips when a
    # factory is constructed, which happens after this module is imported.
    if not state.is_backend_active():
        return False

    from nicegui import app, core

    delay = max(0, ms) / 1000

    def schedule() -> None:
        if core.loop is not None:
            core.loop.call_later(delay, callback)

    if app.is_started and core.loop is not None:
        core.loop.call_soon_threadsafe(schedule)
    else:
        app.on_startup(schedule)
    return True
