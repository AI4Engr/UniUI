"""Theme state and widget helpers shared by every Jupyter Admin component.

Unlike the Qt backend there is no live palette dict here: Jupyter restyles by
re-emitting its whole stylesheet, so components call :func:`get_palette` at
render time and get a fresh copy. That means there is nothing to freeze - but
it also means a component that renders colours into HTML *must* register in
``THEME_TARGETS`` and expose ``apply_theme``, or it keeps the old colours after
a switch while everything around it updates.

``M`` (design metrics) is static for the process lifetime and is safe to read
at import time; the palette is not.
"""
from __future__ import annotations

import weakref
from typing import Dict

import ipywidgets as widgets

from ... import theme_runtime
from ...theme import get_admin_metrics, get_admin_tokens


#: Design metrics. Static for the process lifetime.
M = get_admin_metrics()

#: Adapters that render theme colours themselves and must be re-rendered on a
#: theme switch. Weak, so a discarded shell does not keep its widgets alive.
THEME_TARGETS: "weakref.WeakSet[object]" = weakref.WeakSet()

native = theme_runtime.native

#: Alias for components that bind a local variable called ``native`` (the app
#: shell does, for the unwrapped child widget), where the bare name would
#: shadow the helper.
native_of = native


def get_palette() -> Dict[str, str]:
    """Return a copy of the active Jupyter Admin palette."""
    return get_admin_tokens(theme_runtime.is_dark())


def is_dark() -> bool:
    return theme_runtime.is_dark()


@theme_runtime.register_refresh
def sync_palette() -> None:
    """Re-render every live shell after a theme change.

    Registered with theme_runtime, so switching from any backend restyles
    Jupyter too - the per-backend flags used to drift apart.
    """
    for target in list(THEME_TARGETS):
        apply_theme = getattr(target, "apply_theme", None)
        if callable(apply_theme):
            apply_theme()
    # Restyle the plain ipywidgets too. Imported lazily because the primitive
    # stylesheet imports get_palette from this module - a module-level import
    # here would be circular.
    from .primitives.styles import refresh
    refresh()


def set_theme(dark: bool) -> bool:
    """Switch every live shell, on this and every other backend."""
    return theme_runtime.set_theme(dark)


def track_themed(target) -> None:
    """Register an adapter for re-render on a theme switch.

    Forgetting this produces a component that renders correctly on first paint
    and then silently keeps stale colours after a switch.
    """
    THEME_TARGETS.add(target)


def html(text: str, class_name: str = "") -> widgets.HTML:
    """An ``ipywidgets.HTML`` with an optional CSS class already attached."""
    widget = widgets.HTML(value=text)
    if class_name:
        widget.add_class(class_name)
    return widget
