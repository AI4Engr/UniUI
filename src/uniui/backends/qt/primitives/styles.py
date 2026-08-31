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

from PySide2 import QtWidgets

from ..runtime import get_palette as get_admin_palette
from ..styles import scrollbar_rules as _scrollbar_rules


_STYLED_ROOTS: "weakref.WeakSet[QtWidgets.QWidget]" = weakref.WeakSet()
_STYLED_APPS: "weakref.WeakSet[QtWidgets.QApplication]" = weakref.WeakSet()
_STYLED_COMBOS: "weakref.WeakSet[QtWidgets.QComboBox]" = weakref.WeakSet()


def tag_native(native, class_name: str) -> None:
    """Apply a uniui-* class to a raw native Qt widget with no IWidget
    adapter (e.g. a custom QWidget subclass built outside the factory).

    Same mechanism as ClassMixin.add_class (_adapter_mixins.py) - kept as a
    free function here since a widget with no adapter has no get_native()/
    self to hang the mixin method off of.
    """
    native.setProperty(class_name, True)
    native.style().unpolish(native)
    native.style().polish(native)


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
    palette = get_admin_palette()
    return (
        (_BASE_QSS % palette)
        + (_page_css() % palette)
        + (_shell_css() % palette)
        + scrollbar_stylesheet()
    )


def _page_css() -> str:
    """Generic 'uniui-page-*' typography, set via add_class()/setProperty().

    The same semantic classes (uniui-page-subtitle, uniui-page-hint,
    uniui-page-field-label) are styled in backends/jupyter/page_styles.py and
    backends/web/page_styles.py - any app using add_class() with these names
    gets matching styling for free via base_stylesheet(), not just
    examples/admin_demo.py.
    """
    return """
QLabel[uniui-page-subtitle="true"] {
    color: %(text)s;
    font-size: 18px;
    font-weight: 650;
}
QLabel[uniui-page-hint="true"] {
    color: %(text_muted)s;
    background: %(surface_subtle)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
    padding: 8px 10px;
}
QLabel[uniui-page-field-label="true"] {
    color: %(text_muted)s;
    font-size: 12px;
    font-weight: 650;
}
"""


def _shell_css() -> str:
    """Admin-shell chrome ('uniui-shell-*'), set via add_class()/setProperty().

    The same classes are styled in backends/jupyter/page_styles.py and
    backends/web/page_styles.py for their own app-shell adapters - any Qt app
    tagging its own header/footer widgets with these names gets matching
    styling for free, not just examples/admin_demo.py.
    """
    return """
QWidget[uniui-shell-topbar="true"] { background: %(header_bg)s; }
QFrame[uniui-shell-separator="true"] { color: %(header_border)s; background: transparent; }
QLabel[uniui-shell-logo-mark="true"] {
    background: %(accent)s; color: white; border-radius: 8px;
    font-size: 15px; font-weight: 800;
}
QLabel[uniui-shell-product="true"] { color: %(text)s; font-size: 15px; font-weight: 700; }
QLabel[uniui-shell-avatar="true"] {
    background: %(avatar_bg)s; color: %(avatar_fg)s;
    border-radius: 16px; font-size: 11px; font-weight: 700;
}
QLabel[uniui-shell-status-ok="true"] { color: %(ok)s; font-size: 11px; }
QLabel[uniui-shell-footer-meta="true"] { color: %(text_muted)s; font-size: 11px; }
QLineEdit[uniui-shell-header-search="true"] {
    background: %(surface_subtle)s; border: 1px solid transparent;
    border-radius: 7px; padding: 5px 10px; font-size: 12px;
    color: %(text_muted)s;
}
QLineEdit[uniui-shell-header-search="true"]:focus {
    background: %(bg)s; border: 1px solid %(border)s; color: %(text)s;
}
QPushButton[uniui-shell-icon-button="true"] {
    background: transparent; color: %(text_muted)s; border: none;
    border-radius: 7px; padding: 5px 8px; min-width: 18px; min-height: 18px;
}
QPushButton[uniui-shell-icon-button="true"]:hover {
    background: %(surface_subtle)s; color: %(text)s;
}
"""


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

    Deliberately no ``WA_TranslucentBackground`` here: the popup is a
    ``Qt::Popup``-flagged top-level window, and that combination is a known
    bad interaction on Windows without desktop composition active - instead
    of the square corners showing through as transparent, the *entire*
    popup renders solid black. ``_COMBO_POPUP_QSS`` has no ``border-radius``
    for the same reason: with square corners there's nothing to leak, so no
    transparency trick is needed at all.
    """
    combo.setStyleSheet(_combo_popup_stylesheet())
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
    /* No `padding` here: PySide2's Windows-style tab painting computes the
       text-drawing rect differently from the sizeHint contents rect once a
       QSS `padding` is set, clipping both edges of the label (confirmed by
       hands-on repro - "Activity" lost both its leading "A" and trailing
       "y"). `min-width`/`height` reproduce the same visual spacing without
       touching the padding-based content-rect path. */
    background: transparent;
    color: %(text_muted)s;
    font-size: 13px;
    font-weight: 600;
    min-width: 80px;
    height: 30px;
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
