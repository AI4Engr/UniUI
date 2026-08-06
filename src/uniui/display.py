"""
Display and theme refresh — the cross-backend dispatcher.

Shows a UniUI layout in a desktop window, browser, or Jupyter output.
Also handles theme refresh: auto-detects framework and reapplies colors.

This module owns *dispatch only*.  Each backend's display, theme-refresh and
scheduling implementation lives in ``backends/<name>/display.py``; the
functions here detect which toolkit a widget belongs to and delegate.  That
keeps the public API stable while letting each backend evolve independently,
and it means importing ``uniui`` never drags in PySide2, ipywidgets or NiceGUI
— every backend import below is inside a function body.

Three backends are supported: Qt, Jupyter and Web.  The legacy Tkinter and
wxPython backends were removed.

Public API:
- show_ui(layout, title, width, height) — display the UI
- refresh_theme(root_widget) — reapply current theme to all widgets
- toggle_theme_and_refresh() — toggle dark/light and refresh the active UI
- schedule_after(ms, callback) — run a callback on the active event loop
- show_qt / show_jupyter — force one backend
"""
import sys
from .theme import THEME, toggle_theme as _toggle_theme

T = THEME

# Module-level root widget, set automatically by show_ui() at display time
_root_widget = None


# ============================================================================
# Qt Stylesheet Generator
# ============================================================================

def _generate_qt_stylesheet():
    """Generate Qt stylesheet from current THEME values.

    Kept as a module-level name because callers outside UniUI have imported it;
    the implementation moved to ``backends/qt/display.py``.
    """
    from .backends.qt.display import generate_stylesheet
    return generate_stylesheet()


# ============================================================================
# Unified Theme Refresh (auto-detect framework)
# ============================================================================

def refresh_theme(root_widget):
    """Refresh UI theme on root_widget, auto-detecting the framework.

    Detection order matters and mirrors :meth:`UniversalDisplay.show`.  Each
    branch delegates to the matching ``backends/<name>/display.py``.

    The per-framework helpers are looked up as module globals rather than
    called directly, so tests (and callers) can monkeypatch e.g.
    ``display.refresh_theme_qt`` and have the dispatcher honour it.

    Args:
        root_widget: The root widget stored by display.py at show-time.
    """
    if root_widget is None:
        return

    # Web / NiceGUI (avoid importing the optional dependency for other backends)
    if root_widget.__class__.__module__.startswith("nicegui."):
        refresh_theme_web(root_widget)
        return

    # Qt
    try:
        from PySide2.QtWidgets import QWidget
        if isinstance(root_widget, QWidget):
            refresh_theme_qt(root_widget)
            return
    except ImportError:
        pass

    # Jupyter
    try:
        import ipywidgets
        if isinstance(root_widget, ipywidgets.Widget):
            refresh_theme_jupyter(root_widget)
            return
    except ImportError:
        pass


def toggle_theme_and_refresh():
    """Toggle dark/light theme and refresh the active UI.

    Returns:
        bool: True if now dark mode.

    Example:
        dark_mode_button = Button("Dark Mode")
        dark_mode_button.connect(toggle_theme_and_refresh)
    """
    is_dark = _toggle_theme()
    refresh_theme(_root_widget)
    return is_dark


# ============================================================================
# Per-Framework Theme Refresh Functions
# ============================================================================
#
# Thin forwarders.  They exist so `refresh_theme` above has a stable, patchable
# module-level name per backend, and so external code that imported
# `refresh_theme_qt` and friends keeps working.  Each import is deferred: by
# the time one of these is called, the dispatcher has already established that
# the relevant toolkit is present.

def refresh_theme_qt(root_widget):
    """Refresh Qt widget tree with current THEME values."""
    from .backends.qt.display import refresh_theme as _impl
    _impl(root_widget)


def refresh_theme_web(root_widget):
    """Refresh the Web/NiceGUI theme by rewriting its CSS custom properties."""
    from .backends.web.display import refresh_theme as _impl
    _impl(root_widget)


def refresh_theme_jupyter(root_widget):
    """Refresh the Jupyter theme by re-emitting its stylesheet."""
    from .backends.jupyter.display import refresh_theme as _impl
    _impl(root_widget)


class UniversalDisplay:
    """
    Universal UI display.

    Responsibility: automatically select the correct display method based on container type.
    Uses the strategy pattern.

    The ``_show_*`` staticmethods are kept as the public-ish entry points they
    have always been (tests and examples call them directly), but each one now
    forwards to ``backends/<name>/display.py``.
    """

    @staticmethod
    def show(container, title="App", width=500, height=400, stylesheet=None):
        """
        Display a UI container (auto-detects framework).

        Args:
            container: UI container (VBox/HBox etc.)
            title: window title
            width: window width
            height: window height
            stylesheet: optional Qt CSS string. None = use default theme stylesheet.
                        Pass "" to apply no stylesheet at all.
        """
        native = container.get_native()

        # Store root widget reference at module level for theme refresh
        def _set_refresh_root(root_widget):
            global _root_widget
            _root_widget = root_widget

        # Try each display method in order (order matters)
        if UniversalDisplay._show_web(native, title, width, height, _set_refresh_root):
            return

        if UniversalDisplay._show_qt(native, title, width, height, _set_refresh_root,
                                     stylesheet=stylesheet):
            return

        if UniversalDisplay._show_jupyter(native, _set_refresh_root):
            return

        raise RuntimeError("Unrecognized UI framework!")

    @staticmethod
    def _show_web(native, title, width, height, _set_refresh_root=None):
        """Run a NiceGUI-backed layout as a standalone Web application."""
        from .backends.web.display import show
        return show(native, title, width, height, _set_refresh_root)

    @staticmethod
    def _show_qt(native, title, width, height, _set_refresh_root=None, stylesheet=None):
        """Qt display method"""
        from .backends.qt.display import show
        return show(native, title, width, height, _set_refresh_root,
                    stylesheet=stylesheet)

    @staticmethod
    def _show_jupyter(native, _set_refresh_root=None):
        """Jupyter display method"""
        from .backends.jupyter.display import show
        return show(native, _set_refresh_root)


# ============================================================================
# Convenience functions
# ============================================================================

def schedule_after(ms: int, callback) -> None:
    """Schedule callback after `ms` milliseconds using the correct mechanism for the active framework.

    Works with Qt, Web/NiceGUI and Jupyter, and falls back to threading.Timer.
    Each backend's ``schedule_after`` returns True when it accepted the work,
    False when its toolkit is not the active one; this function only picks the
    order and owns the fallback.
    """
    # Web / NiceGUI (only when the optional backend has already been selected).
    # Probing sys.modules rather than importing keeps this branch free for the
    # other backends: if nobody has selected Web, NiceGUI stays unimported.
    # The probed module is the one the Web *factory* pulls in, which is what
    # makes it a reliable "Web is in play" signal.
    if sys.modules.get("uniui.backends.web.primitives.theming") is not None:
        from .backends.web.display import schedule_after as _web_schedule
        if _web_schedule(ms, callback):
            return

    # Qt — use a thread-safe relay so this works from background threads too
    try:
        from .backends.qt.display import schedule_after as _qt_schedule
        if _qt_schedule(ms, callback):
            return
    except Exception:
        pass

    # Jupyter / asyncio.  Deliberately inlined rather than delegated to
    # ``backends/jupyter/display.py``: that module imports ipywidgets at import
    # time, so calling into it here would pull the toolkit in on every Qt and
    # fallback schedule.  The check itself is toolkit-free — any running loop
    # will do, which is exactly what a notebook kernel provides.
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.call_later(ms / 1000, callback)
            return
    except Exception:
        pass

    # Fallback
    import threading
    t = threading.Timer(ms / 1000, callback)
    t.daemon = True
    t.start()


def show_ui(container, title="App", width=500, height=400, stylesheet=None):
    """
    Convenience function to display a UI.

    Args:
        container: UI container
        title: window title
        width: window width
        height: window height
        stylesheet: optional Qt CSS override. None = default theme.
                    Pass "" to apply no stylesheet.
    """
    UniversalDisplay.show(container, title, width, height, stylesheet=stylesheet)


# ============================================================================
# Framework-specific convenience functions
# ============================================================================

def show_qt(container, title="Qt App", width=500, height=400):
    """Force display using Qt"""
    from .backends.qt.display import show_forced
    show_forced(container, title, width, height)


def show_jupyter(container):
    """Force display using Jupyter"""
    from .backends.jupyter.display import show_forced
    show_forced(container)


# ============================================================================
# Usage example
# ============================================================================

if __name__ == "__main__":
    """
    Usage example:

    from uniui import create_factory
    from uniui.display import show_ui

    # Create UI
    factory = create_factory()
    vbox = factory.create_vbox()

    label = factory.create_label()
    label.set_text("Hello!")
    vbox.add_item(label)

    # Display (auto-detect framework)
    show_ui(vbox, "My App")

    # Or force a specific framework
    show_qt(vbox, "Qt App")
    show_jupyter(vbox)
    """
    print(__doc__)
