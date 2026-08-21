"""Qt display, theme refresh and scheduling.

Moved out of the root ``display.py``, which is now a thin dispatcher: it
detects the framework and delegates here.  Everything in this module may
import PySide2 freely — nothing imports it until ``display.py`` has already
established that the widget in hand is a Qt widget.

The stylesheet generator reads ``THEME`` through the module-level alias ``T``.
``THEME`` is mutated in place by :func:`uniui.theme.toggle_theme`, so ``T``
always sees the current palette; copying the dict here would freeze this
module on whichever palette was active at import time.
"""
from __future__ import annotations

import sys

from ...theme import THEME

T = THEME


def generate_stylesheet() -> str:
    """Generate the app-wide Qt stylesheet from current THEME values."""
    r = T["border_radius"]
    return f"""
        QWidget {{
            background-color: {T["bg"]};
            font-family: "{T["font_family"]}";
            font-size: {T["font_size"]}pt;
        }}
        QLabel {{
            color: {T.get("fg_muted", T["fg"])};
            font-weight: 600;
            font-size: {T["font_size"]}pt;
            background: transparent;
        }}

        /* ── Display input ── */
        QLineEdit {{
            background-color: {T["bg_input"]};
            color: {T["fg"]};
            border: 2px solid {T["border"]};
            border-radius: {r}px;
            padding: 6px 10px;
            font-size: {T["font_size"]}pt;
            font-weight: 600;
            font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
        }}
        QLineEdit:focus {{
            border: 2px solid {T["accent"]};
        }}

        /* ── History text area ── */
        QTextEdit {{
            background-color: {T["bg_input"]};
            color: {T.get("fg_muted", T["fg"])};
            border: 1px solid {T["border"]};
            border-radius: {r}px;
            padding: {T["padding_inner"]}px;
            font-family: "Cascadia Code", "Consolas", monospace;
            font-size: 9pt;
        }}
        QTextEdit:focus {{
            border: 1px solid {T["accent"]};
        }}

        /* ── Base / numeric buttons ── */
        QPushButton {{
            background-color: {T["accent"]};
            color: {T["fg_button"]};
            border: none;
            border-radius: {r}px;
            padding: 5px 4px;
            font-size: 12pt;
            font-weight: 600;
            min-height: 32px;
        }}
        QPushButton:hover {{
            background-color: {T["accent_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {T["accent_press"]};
        }}

        /* ── Operator buttons (+, −, ×, ÷, (, ), =num) ── */
        QPushButton[btntype="op"] {{
            background-color: {T.get("accent_op", T["accent"])};
        }}
        QPushButton[btntype="op"]:hover {{
            background-color: {T.get("accent_op_hover", T["accent_hover"])};
        }}
        QPushButton[btntype="op"]:pressed {{
            background-color: {T.get("accent_op_press", T["accent_press"])};
        }}

        /* ── Scientific buttons (sin, cos, tan, log, ln, √, xʸ, x², π, e) ── */
        QPushButton[btntype="sci"] {{
            background-color: {T.get("accent_sci", T["accent"])};
            font-size: 11pt;
        }}
        QPushButton[btntype="sci"]:hover {{
            background-color: {T.get("accent_sci_hover", T["accent_hover"])};
        }}
        QPushButton[btntype="sci"]:pressed {{
            background-color: {T.get("accent_sci_press", T["accent_press"])};
        }}

        /* ── Action buttons (=, C) ── */
        QPushButton[btntype="action"] {{
            background-color: {T.get("accent_action", T["accent"])};
            font-size: 14pt;
        }}
        QPushButton[btntype="action"]:hover {{
            background-color: {T.get("accent_action_hover", T["accent_hover"])};
        }}
        QPushButton[btntype="action"]:pressed {{
            background-color: {T.get("accent_action_press", T["accent_press"])};
        }}

        /* ── Neutral buttons (Dark Mode toggle, Clr Hist, ⌫) ── */
        QPushButton[btntype="neutral"] {{
            background-color: {T.get("accent_neutral", "#334155")};
            font-size: 10pt;
        }}
        QPushButton[btntype="neutral"]:hover {{
            background-color: {T.get("accent_neutral_hover", "#475569")};
        }}
        QPushButton[btntype="neutral"]:pressed {{
            background-color: {T.get("accent_neutral_press", "#64748b")};
        }}

        QComboBox {{
            background-color: {T["bg_input"]};
            color: {T["fg"]};
            border: 1px solid {T["border"]};
            border-radius: {r}px;
            padding: 4px {T["padding_inner"]}px;
        }}
        QComboBox:focus {{
            border: 1px solid {T["accent"]};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {T["bg_input"]};
            color: {T["fg"]};
            selection-background-color: {T["accent"]};
            selection-color: {T["fg_button"]};
        }}

        QGroupBox {{
            background-color: {T["bg_input"]};
            border: 1px solid {T["border"]};
            border-radius: {r}px;
            margin-top: 18px;
            padding: 12px {T["padding_inner"]}px {T["padding_inner"]}px {T["padding_inner"]}px;
            font-weight: bold;
            font-size: 9pt;
            color: {T.get("fg_muted", T["fg"])};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: {T.get("fg_muted", T["fg"])};
            font-size: 9pt;
        }}
    """


def refresh_theme(root_widget) -> None:
    """Refresh Qt widget tree with current THEME values."""
    root_widget.setStyleSheet(generate_stylesheet())


def show(native, title, width, height, set_refresh_root=None, stylesheet=None) -> bool:
    """Qt display method.  Returns True when it took ownership of ``native``."""
    try:
        from PySide2.QtWidgets import QWidget, QApplication, QLayout
        from PySide2.QtGui import QFont
        from .primitives.helpers import ensure_qwidget

        # Accept either a QLayout or a QWidget as the root container
        if isinstance(native, (QLayout, QWidget)):
            app = QApplication.instance()
            _app_is_ours = app is None
            if _app_is_ours:
                app = QApplication(sys.argv)

            # Set application-wide font
            font = QFont(T["font_family"], T["font_size"])
            app.setFont(font)

            # Build the top-level window
            widget = ensure_qwidget(native)

            widget.setWindowTitle(title)
            # width/height describe the initial window size, not a hard
            # lower bound.  Layouts and app shells may still define their
            # own sensible minimum size for compact rendering.
            widget.resize(width, height)

            # Apply stylesheet: caller-supplied, default theme, or none ("")
            if stylesheet is None:
                widget.setStyleSheet(generate_stylesheet())
            elif stylesheet != "":
                widget.setStyleSheet(stylesheet)
            # stylesheet == "" → no stylesheet applied

            # Store root widget reference for theme refresh
            if set_refresh_root:
                set_refresh_root(widget)

            widget.show()

            # Only enter the blocking event loop if we created the
            # QApplication ourselves. A host application embedding a
            # UniUI-built widget already owns a running QApplication/event
            # loop; calling exec_() here would start a second, nested loop
            # and block the host until this window closes. Mirrors
            # show_forced()'s ownership check below.
            import sys as _sys
            _in_pytest = "pytest" in _sys.modules or hasattr(_sys, "_called_from_test")
            if _app_is_ours and not _in_pytest:
                app.exec_()
            return True

    except (ImportError, AttributeError):
        pass

    return False


def show_forced(container, title="Qt App", width=500, height=400) -> None:
    """Force display using Qt, bypassing framework detection."""
    from PySide2.QtWidgets import QWidget, QApplication

    app = QApplication.instance()
    _app_is_ours = app is None
    if _app_is_ours:
        app = QApplication(sys.argv)

    widget = QWidget()
    widget.setLayout(container.get_native())
    widget.setWindowTitle(title)
    widget.resize(width, height)
    widget.show()

    if _app_is_ours:
        app.exec_()


def schedule_after(ms: int, callback) -> bool:
    """Schedule ``callback`` on the Qt main thread.  False if Qt isn't running.

    ``QTimer.singleShot`` from a non-Qt thread is silently ignored, so work is
    posted through a QObject that lives on the main thread.  The dispatcher is
    cached on the QApplication so background threads share one relay.
    """
    try:
        from PySide2.QtCore import QTimer, QObject, Signal, Qt
        from PySide2.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            if not hasattr(app, "_uniui_dispatcher"):
                class _Dispatcher(QObject):
                    _invoke = Signal(int, object)
                    def __init__(self):
                        super().__init__()
                        self._invoke.connect(self._run, Qt.QueuedConnection)
                    def _run(self, ms, cb):
                        if ms == 0:
                            cb()
                        else:
                            QTimer.singleShot(ms, cb)
                    def post(self, ms, cb):
                        self._invoke.emit(ms, cb)
                app._uniui_dispatcher = _Dispatcher()
                app._uniui_dispatcher.moveToThread(app.thread())
            app._uniui_dispatcher.post(ms, callback)
            return True
    except Exception:
        pass
    return False


__all__ = [
    "generate_stylesheet", "refresh_theme", "schedule_after",
    "show", "show_forced",
]
