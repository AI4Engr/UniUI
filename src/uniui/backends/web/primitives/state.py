"""Process-wide mutable state for the Web primitive backend.

Everything here is shared by modules that would otherwise have no reason to
import each other: ``base`` registers each adapter, ``theming`` walks them, and
the CSS guard has to stay a single flag no matter who triggers installation.

None of these are re-exported by ``uniui.web``. Three of them are rebound
through ``global``, so a re-export would be a stale snapshot rather than a
view - patch them here, in their owning module.
"""
from __future__ import annotations

from typing import Any, List

from nicegui import ui

from ....theme import THEME

#: Alias for the live theme dict, mutated in place on a theme switch.
T = THEME

#: Every adapter ever constructed, so a theme switch can restyle them all.
#: A plain list rather than a WeakSet: NiceGUI elements are owned by their page
#: slot, and dropping one here would silently stop restyling it.
_adapters: List[Any] = []

_css_installed = False
_dark_mode = None
_backend_active = False


def register_adapter(adapter: Any) -> None:
    """Track an adapter so :func:`refresh_theme_web` can restyle it.

    A function rather than a direct ``_adapters`` import: the list is private
    to this module, and callers that bind the object risk holding a stale one
    if it is ever replaced instead of mutated.
    """
    _adapters.append(adapter)


def adapters() -> List[Any]:
    """Return a snapshot of the tracked adapters, safe to iterate."""
    return list(_adapters)


def set_backend_active(active: bool) -> None:
    global _backend_active
    _backend_active = bool(active)


def is_backend_active() -> bool:
    """Read the flag through a function so callers never bind a stale copy."""
    return _backend_active


def _install_css() -> None:
    global _css_installed
    if _css_installed:
        return
    ui.add_css(
        """
        body { margin: 0; }
        .uniui-root { min-height: 100vh; box-sizing: border-box; }
        .uniui-vbox, .uniui-hbox { gap: var(--uniui-spacing, 8px); }
        .uniui-hbox { flex-wrap: wrap; }
        .uniui-label { font-weight: 600; }
        .uniui-button { min-height: 32px; font-weight: 600; }
        .uniui-input .q-field__control,
        .uniui-select .q-field__control { border-radius: var(--uniui-radius, 8px); }
        .uniui-textarea { overflow: auto; white-space: pre-wrap; width: 100%; box-sizing: border-box; }
        .uniui-group { width: 100%; box-sizing: border-box; }
        .uniui-group-title { font-weight: 700; }
        @media (max-width: 640px) {
            .uniui-root { width: 100% !important; padding: 10px !important; }
            .uniui-hbox { flex-direction: column; align-items: stretch; }
            .uniui-hbox > * { width: 100%; }
        }
        """,
        shared=True,
    )
    _css_installed = True
