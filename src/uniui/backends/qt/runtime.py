"""Theme state and widget helpers shared by every Qt Admin component.

This module owns the live palette. ``_C`` is mutated **in place** by
``_sync_palette`` rather than rebound, and the style helpers read it at call
time, so a theme switch reaches every component without anything having to
re-import. Components must therefore use ``C`` (or ``from .runtime import C``)
and never copy it into a local dict - a copy would freeze at whatever theme was
active when the module was first imported.
"""
from __future__ import annotations

import weakref
from typing import Dict, Optional

from PySide2 import QtCore, QtGui, QtWidgets

from ... import theme_runtime
from .icons import admin_icon
from ...theme import get_admin_metrics


def _qt_tokens() -> Dict[str, str]:
    """Snapshot the active theme, plus temporary aliases the Qt renderer uses.

    Reads ``theme_runtime.get_palette()`` -- the actual active palette --
    rather than re-deriving one from a light/dark bool. A bool-keyed lookup
    only ever knows about the two built-in themes; any theme registered by
    name (``uniui.register_theme``) would silently fall back to plain
    light/dark here even though ``THEME`` itself held the right values.
    """
    tokens = theme_runtime.get_palette()
    tokens.update({
        "sidebar_act": tokens["sidebar_active"],
        "sidebar_act_fg": tokens["sidebar_active_fg"],
        "row_sel": tokens["row_selected"],
        "row_sel_fg": tokens["row_selected_fg"],
    })
    return tokens


#: Design metrics. Static for the process lifetime.
M = get_admin_metrics()

#: The live palette. Mutated in place - never rebind this name.
C = dict(_qt_tokens())

THEMED_ADAPTERS = weakref.WeakSet()

native = theme_runtime.native


def get_palette() -> Dict[str, str]:
    """Return a copy of the active Admin design tokens."""
    return dict(C)


def is_dark() -> bool:
    return theme_runtime.is_dark()


@theme_runtime.register_refresh
def sync_palette() -> None:
    """Re-render every live Qt adapter after a theme change.

    Registered with theme_runtime, so switching from any backend restyles Qt
    too - the per-backend flags used to drift apart.
    """
    C.clear()
    C.update(_qt_tokens())
    for adapter in list(THEMED_ADAPTERS):
        try:
            adapter.apply_theme()
        except RuntimeError as exc:
            if "already deleted" not in str(exc):
                raise
            THEMED_ADAPTERS.discard(adapter)
    # Restyle the plain Qt controls too. Imported lazily because the primitive
    # stylesheet imports the Qt palette from this module for its own rules.
    from .primitives.styles import refresh_styled_widgets
    refresh_styled_widgets()


def set_theme(dark: bool) -> bool:
    """Switch every live adapter, on this and every other backend."""
    return theme_runtime.set_theme(dark)


def track_themed(adapter, native_widget) -> None:
    """Keep the adapter alive for as long as its native Qt widget is alive."""
    THEMED_ADAPTERS.add(adapter)
    native_widget._uniui_theme_adapter = adapter
    native_widget.destroyed.connect(
        lambda *_args, tracked=adapter: THEMED_ADAPTERS.discard(tracked)
    )


def as_widget(widget) -> QtWidgets.QWidget:
    """Like ``native`` but wraps a QLayout in a container QWidget if needed.

    Uses the shared ``ensure_qwidget`` (also used by every primitive
    composition point) for the wrap-if-needed logic itself, then layers on
    the transparent styling every Admin container needs — without it, the
    wrapper's opaque default background would paint over the Card/AppShell/
    Drawer theming it sits inside.
    """
    from .primitives.helpers import ensure_qwidget, is_qlayout

    obj = native(widget)
    was_layout = is_qlayout(obj)
    result = ensure_qwidget(obj)
    if was_layout:
        result.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        result.setStyleSheet("background: transparent;")
    return result


def clear_layout(layout: QtWidgets.QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.setParent(None)


def label(text: str, bold: bool = False, size: int = 13,
          color: Optional[str] = None) -> QtWidgets.QLabel:
    """A themed QLabel.

    ``color`` defaults to the *current* text colour rather than being baked
    into the signature, which would capture the theme active at import time.
    """
    lbl = QtWidgets.QLabel(text)
    lbl.setStyleSheet(
        f"color: {color or C['text']}; font-size: {size}px;"
        + (" font-weight: 600;" if bold else "")
    )
    return lbl


#: Alias used by components that also have a local ``label`` variable or a
#: ``set_label`` parameter, where the bare name would shadow this helper.
label_widget = label


def nav_icon(name: str, color: Optional[str] = None,
             selected_color: Optional[str] = None) -> QtGui.QIcon:
    try:
        return admin_icon(
            name,
            color or C["sidebar_fg"],
            size=20,
            selected_color=selected_color or C["sidebar_edge"],
        )
    except KeyError:
        return QtGui.QIcon()
