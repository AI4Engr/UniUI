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
def test_qt_show_skips_event_loop_when_app_already_exists(monkeypatch):
    """Embedding into a host app's existing QApplication must not steal its
    event loop. Regression test for the bug where show() decided whether to
    call exec_() based on "am I running under pytest" rather than "did I
    create this QApplication" — the pytest heuristic happens to mask this in
    every other test in this file, so it's hidden here via monkeypatch to
    exercise the real ownership-check path.

    Ownership is now tracked via a `_uniui_owns_app` flag stamped onto the
    QApplication instance wherever UniUI first creates one (the Qt factory
    usually gets there before show() ever runs), not by asking "is
    QApplication.instance() None right now" — that would call every
    standalone script's own app "a host's", since the factory already
    created it. This test forces that flag off to simulate a genuine
    host-created app, since in this shared test process the existing
    QApplication may well already be UniUI's own from an earlier test.
    """
    pytest.importorskip("PySide2")
    import sys as _sys
    from PySide2.QtWidgets import QApplication, QWidget

    app = QApplication.instance() or QApplication([])
    widget = QWidget()
    exec_calls = []
    monkeypatch.setattr(app, "exec_", lambda: exec_calls.append(1))
    monkeypatch.delitem(_sys.modules, "pytest", raising=False)
    # Simulate a genuine host app: this QApplication must not be marked as
    # UniUI's own, even though in this shared test process it may actually
    # have been created (and stamped) by an earlier test's factory setup.
    monkeypatch.setattr(app, "_uniui_owns_app", False, raising=False)

    try:
        assert display.UniversalDisplay._show_qt(
            widget, "Embedded", 400, 300, stylesheet=""
        ) is True
        assert exec_calls == []
    finally:
        widget.close()


def test_qt_show_enters_event_loop_when_the_factory_created_the_app(monkeypatch):
    """Regression test for the real-world case this fix broke: a normal
    standalone script calls use("qt")/create_factory("qt") - which creates
    the QApplication as a side effect, before any window is ever shown -
    then later calls show_ui(). QApplication.instance() is never None by
    that point, but nothing else is going to run the event loop, so exec_()
    must still fire. Without _uniui_owns_app being stamped by the factory
    itself, `python examples/admin_demo.py` built its whole UI, called
    show(), and exited immediately with no error and no visible window.
    """
    pytest.importorskip("PySide2")
    import sys as _sys
    from PySide2.QtWidgets import QWidget

    factory = create_factory("qt")  # creates + stamps the QApplication
    widget = QWidget()
    exec_calls = []
    monkeypatch.setattr(factory.app, "exec_", lambda: exec_calls.append(1))
    monkeypatch.delitem(_sys.modules, "pytest", raising=False)

    try:
        assert display.UniversalDisplay._show_qt(
            widget, "Standalone", 400, 300, stylesheet=""
        ) is True
        assert exec_calls == [1]
    finally:
        widget.close()


@pytest.mark.qt
def test_show_ui_returns_the_built_native_widget():
    """show_ui()/UniversalDisplay.show() must hand back the widget it built,
    so a host app can embed it — not just stash it in the private
    display._root_widget global.
    """
    pytest.importorskip("PySide2")
    from PySide2.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    factory = create_factory("qt")
    vbox = factory.createVBox()
    label = factory.create_label()
    label.set_text("embedded")
    vbox.add_item(label)

    widget = display.show_ui(vbox, title="Embedded")
    try:
        assert widget is not None
        assert widget is display._root_widget
    finally:
        widget.close()


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
