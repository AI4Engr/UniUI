"""One theme state machine, shared by every backend.

Each backend used to keep its own ``_admin_dark`` flag plus its own copy of
``get_admin_palette`` / ``set_admin_theme``.  The flags never talked to each
other, so ``qt_components.set_admin_theme(True)`` left
``jupyter_components.is_admin_dark()`` reporting ``False``.

Backends register a refresh callback here via :func:`register_refresh`.
The actual flip-tokens-and-notify-everyone logic lives in
:mod:`uniui.theme`'s own ``set_theme``/``set_active_theme`` (they call back
into :func:`_run_refreshers` here) — this module's own ``set_theme``/
``set_active_theme`` are thin pass-throughs kept for backend code that
already imports them from here.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List

from . import theme as _theme


_refreshers: List[Callable[[], None]] = []


def register_refresh(callback: Callable[[], None]) -> Callable[[], None]:
    """Register a callback invoked after every theme change.

    Returns the callback so it can be used as a decorator.
    """
    if callback not in _refreshers:
        _refreshers.append(callback)
    return callback


def get_palette() -> Dict[str, Any]:
    """Return a copy of the active palette (colours + metrics + aliases)."""
    return dict(_theme.THEME)


def is_dark() -> bool:
    return _theme.is_dark()


def _run_refreshers() -> None:
    """Fire every registered refresh callback once.

    Shared by theme.py's set_theme/set_active_theme (the real mutation +
    notification now happens there) and this module's own pass-throughs
    below, so there is exactly one refresh-firing implementation regardless
    of which module a caller imports from.
    """
    for refresh in list(_refreshers):
        try:
            refresh()
        except RuntimeError as exc:
            # Qt objects can be deleted underneath us; anything else is a bug.
            if "already deleted" not in str(exc):
                raise


def set_theme(dark: bool) -> bool:
    """Switch the palette and refresh every registered backend."""
    return _theme.set_theme(dark)


def toggle_theme() -> bool:
    """Flip between light and dark, refreshing every backend."""
    return set_theme(not _theme.is_dark())


def set_active_theme(name: str) -> str:
    """Switch to a named theme and refresh every registered backend.

    The named-theme counterpart of :func:`set_theme` — same refresh-firing
    behavior, so a theme picker calling this has every backend follow along
    exactly the way flipping dark/light already does.
    """
    return _theme.set_active_theme(name)


def get_active_theme_name() -> str:
    return _theme.get_active_theme_name()


def list_themes() -> List[str]:
    return _theme.list_themes()


def native(widget):
    """Unwrap a UniUI widget to its toolkit object."""
    return widget.get_native() if hasattr(widget, "get_native") else widget


__all__ = [
    "get_active_theme_name",
    "get_palette",
    "is_dark",
    "list_themes",
    "native",
    "register_refresh",
    "set_active_theme",
    "set_theme",
    "toggle_theme",
]
