"""
Focused tests for display dispatch and theme toggle behavior.
"""
import pytest

from uniui import create_factory
from uniui import display


def test_refresh_theme_with_none_is_noop():
    """Refreshing a missing root widget should be a no-op."""
    display.refresh_theme(None)


def test_toggle_theme_and_refresh_delegates_to_active_root(monkeypatch):
    """Theme toggle should refresh the stored root widget and return the new mode."""
    sentinel = object()
    refreshed = []

    monkeypatch.setattr(display, "_root_widget", sentinel)
    monkeypatch.setattr(display, "_toggle_theme", lambda: True)
    monkeypatch.setattr(display, "refresh_theme", lambda widget: refreshed.append(widget))

    assert display.toggle_theme_and_refresh() is True
    assert refreshed == [sentinel]


def test_refresh_theme_dispatches_qt_widgets(monkeypatch):
    """Qt widgets should route through the Qt theme refresh helper.

    The dispatcher looks its per-backend helpers up as module globals, so
    patching ``display.refresh_theme_qt`` must intercept the call. That
    indirection is the reason ``refresh_theme`` does not import the backend
    helper directly.
    """
    pytest.importorskip("PySide2")
    factory = create_factory("qt")
    label = factory.create_label()
    native = label.get_native()
    refreshed = []

    monkeypatch.setattr(display, "refresh_theme_qt", lambda widget: refreshed.append(widget))

    display.refresh_theme(native)
    assert refreshed == [native]


@pytest.mark.qt
def test_qt_dimensions_are_initial_size_not_minimum_size():
    """A requested launch size must not prevent users from shrinking a window."""
    pytest.importorskip("PySide2")
    from PySide2.QtWidgets import QApplication, QWidget

    app = QApplication.instance() or QApplication([])
    widget = QWidget()
    try:
        assert display.UniversalDisplay._show_qt(
            widget, "Resizable", 900, 640, stylesheet=""
        )
        app.processEvents()
        assert widget.width() == 900
        assert widget.height() == 640
        assert widget.minimumWidth() < 900
        assert widget.minimumHeight() < 640
    finally:
        widget.close()
