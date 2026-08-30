"""Themed QSS for the plain Qt widgets created by the Qt factory.

``backends.qt.components`` styles the Admin-specific components (cards,
tables, sidebars).
This module covers the ordinary controls behind ``create_button()``,
``create_dropdown()``, ``create_tab_widget()`` and friends, so applications
built on the Qt backend inherit the design system without copying stylesheets
out of the examples.

Widgets registered here are restyled in place whenever
:func:`uniui.theme_runtime.set_theme` flips between light and dark.
"""
from __future__ import annotations

import weakref
from typing import Set

from PySide2 import QtCore, QtWidgets

from ..runtime import get_palette as get_admin_palette
from ..styles import scrollbar_rules as _scrollbar_rules


_STYLED_ROOTS: "weakref.WeakSet[QtWidgets.QWidget]" = weakref.WeakSet()
_STYLED_APPS: "weakref.WeakSet[QtWidgets.QApplication]" = weakref.WeakSet()
_STYLED_COMBOS: "weakref.WeakSet[QtWidgets.QComboBox]" = weakref.WeakSet()


def apply_app_style(app=None) -> None:
    """Apply the base widget stylesheet application-wide.

    Called by ``QtWidgetFactory`` so that any Qt app built on UniUI inherits the
    themed controls.  Individual widgets can still override with their own
    stylesheet; Qt gives the more specific stylesheet precedence.
    """
    if app is None:
        app = QtWidgets.QApplication.instance()
    if app is None:
        return
    app.setStyleSheet(base_stylesheet())
    _STYLED_APPS.add(app)


def base_stylesheet() -> str:
    """Return the QSS for the standard Qt controls in the active theme."""
    return (_BASE_QSS % get_admin_palette()) + scrollbar_stylesheet()


def apply_base_style(widget) -> None:
    """Style ``widget`` and its children, and keep them following the theme.

    The widget is stored weakly, so tracking it here never keeps a deleted Qt
    object alive.
    """
    native = widget.get_native() if hasattr(widget, "get_native") else widget
    if not isinstance(native, QtWidgets.QWidget):
        return
    native.setStyleSheet(base_stylesheet())
    _STYLED_ROOTS.add(native)


def refresh_styled_widgets() -> None:
    """Re-apply the stylesheet everywhere it was applied, after a theme change."""
    qss = base_stylesheet()
    for target, registry in (
        *((app, _STYLED_APPS) for app in list(_STYLED_APPS)),
        *((widget, _STYLED_ROOTS) for widget in list(_STYLED_ROOTS)),
    ):
        try:
            target.setStyleSheet(qss)
        except RuntimeError as exc:
            # The underlying C++ object can outlive the Python wrapper.
            if "already deleted" not in str(exc):
                raise
            registry.discard(target)
    refresh_combo_popups()


def _combo_popup_stylesheet() -> str:
    """QSS for just the dropdown popup, applied directly to each QComboBox.

    A QComboBox's popup (QComboBox::item view) is a separate top-level
    window. Qt does not reliably cascade an application-wide stylesheet down
    to it once any ancestor between the combo box and the app sets its own
    local stylesheet (Card and every other Admin component do exactly that)
    -- the popup silently falls back to the platform's native palette
    (confirmed empirically: QListView.palette().color(Base) reads pure black
    under a dark Windows theme even though the app stylesheet's `background`
    value is correct). Setting this directly on the QComboBox, as close to
    the popup as possible, sidesteps that cascade instead of relying on it.
    """
    return _COMBO_POPUP_QSS % get_admin_palette()


def apply_combo_popup_style(combo) -> None:
    """Style one QComboBox's dropdown popup and track it for theme refresh.

    The popup is a separate top-level window, so its rounded corners (set in
    ``_COMBO_POPUP_QSS``) only clip the QSS-painted rectangle -- without
    ``WA_TranslucentBackground`` on the popup's own window, Qt still paints
    the native opaque rectangular window surface underneath, which shows
    through as square black slivers behind the rounded corners.
    """
    combo.setStyleSheet(_combo_popup_stylesheet())
    view = combo.view()
    view.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
    view.window().setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
    _STYLED_COMBOS.add(combo)


def refresh_combo_popups() -> None:
    """Re-apply the popup stylesheet to every live QComboBox."""
    qss = _combo_popup_stylesheet()
    for combo in list(_STYLED_COMBOS):
        try:
            combo.setStyleSheet(qss)
        except RuntimeError as exc:
            if "already deleted" not in str(exc):
                raise
            _STYLED_COMBOS.discard(combo)


_COMBO_POPUP_QSS = """
QComboBox QAbstractItemView {
    background: %(surface)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 9px;
    outline: none;
    selection-background-color: %(accent)s;
    selection-color: white;
    padding: 4px;
}
"""


# Kept as a module constant so the palette is substituted per call rather than
# baked in at import time.
_BASE_QSS = """
QWidget {
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
    font-size: 13px;
    color: %(text)s;
}
QLabel { background: transparent; color: %(text)s; }

QLineEdit {
    background: %(input_bg)s;
    border: 1px solid %(border_strong)s;
    border-radius: 9px;
    padding: 8px 11px;
    color: %(text)s;
    font-size: 13px;
    min-height: 20px;
}
QLineEdit:focus { border: 2px solid %(accent)s; padding: 7px 10px; }
QLineEdit:hover { border-color: %(text_muted)s; }
QLineEdit:disabled {
    color: %(text_muted)s;
    background: %(surface_subtle)s;
    border-color: %(border)s;
}

QTextEdit {
    background: %(input_bg)s;
    border: 1px solid %(border_strong)s;
    border-radius: 9px;
    padding: 8px 11px;
    color: %(text)s;
    font-size: 13px;
}
QTextEdit:focus { border: 2px solid %(accent)s; }

QPushButton {
    background: %(accent)s;
    color: #ffffff;
    border: 1px solid %(accent)s;
    border-radius: 9px;
    padding: 7px 14px;
    font-size: 13px;
    font-weight: 600;
    min-height: 20px;
    qproperty-iconSize: 18px 18px;
}
QPushButton:hover { background: %(accent_hover)s; border-color: %(accent_hover)s; }
QPushButton:pressed { background: %(accent_press)s; }
QPushButton:focus { border: 2px solid %(accent_hover)s; padding: 6px 13px; }
QPushButton:disabled {
    color: %(text_muted)s;
    background: %(disabled)s;
    border-color: %(disabled)s;
}
QPushButton[buttonRole="secondary"] {
    background: %(surface)s;
    color: %(text)s;
    border: 1px solid %(border_strong)s;
}
QPushButton[buttonRole="secondary"]:hover { background: %(surface_subtle)s; }
QPushButton:flat {
    background: transparent;
    color: %(text_muted)s;
    border: none;
    min-height: 0;
    padding: 5px 7px;
}
QPushButton:flat:hover { color: %(text)s; background: %(surface_subtle)s; }

QComboBox {
    background: %(input_bg)s;
    border: 1px solid %(border_strong)s;
    border-radius: 9px;
    padding: 7px 11px;
    color: %(text)s;
    font-size: 13px;
    min-height: 20px;
    min-width: 160px;
}
QComboBox:hover { border-color: %(text_muted)s; }
QComboBox:focus { border: 2px solid %(accent)s; padding: 6px 10px; }
/* Deliberately no ::drop-down / ::down-arrow rules: styling ::drop-down at
   all (even just border/width) makes Qt stop drawing its native platform
   arrow there, and Qt's QSS engine does not render the CSS border-triangle
   trick as a triangle (confirmed empirically -- it paints a solid block
   instead) or support data: URIs for ::down-arrow's image property. Leaving
   both sub-controls unstyled keeps Qt's native arrow, which respects the
   platform theme and is always visible. */
QComboBox QAbstractItemView {
    background: %(surface)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 9px;
    outline: none;
    selection-background-color: %(accent)s;
    selection-color: white;
    padding: 4px;
}

QTabWidget::pane {
    border: none;
    border-top: 1px solid %(border)s;
    padding-top: 14px;
}
QTabBar::tab {
    background: transparent;
    color: %(text_muted)s;
    font-size: 13px;
    font-weight: 600;
    padding: 9px 16px;
    border: none;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected { color: %(accent)s; border-bottom-color: %(accent)s; }
QTabBar::tab:hover:!selected { color: %(text)s; }

QGroupBox {
    border: 1px solid %(border)s;
    border-radius: 10px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: %(text_muted)s;
}
"""


def scrollbar_stylesheet() -> str:
    """Return just the scrollbar rules in the active theme.

    Widgets that call ``setStyleSheet()`` on themselves (``QTableWidget``,
    ``QListWidget``, ...) stop inheriting scrollbar rules from an ancestor
    stylesheet, so they have to embed these rules directly.
    """
    return _scrollbar_rules()


__all__ = [
    "apply_app_style",
    "apply_base_style",
    "apply_combo_popup_style",
    "base_stylesheet",
    "refresh_combo_popups",
    "refresh_styled_widgets",
    "scrollbar_stylesheet",
]
