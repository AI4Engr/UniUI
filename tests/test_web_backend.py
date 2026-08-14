"""NiceGUI Web backend integration tests."""

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("nicegui")

from uniui import Button, Label, VBox, create_factory, toggle_theme, use
from uniui.display import UniversalDisplay, refresh_theme
from uniui.web_components import is_admin_dark as is_web_admin_dark
from uniui.web_components import set_admin_theme as set_web_admin_theme


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.mark.web
def test_web_factory_core_surface():
    factory = create_factory("web")
    label = factory.create_label()
    label.set_text("Web")
    assert label.get_text() == "Web"

    called = []
    button = factory.create_button()
    button.connect(lambda: called.append(True))
    button.get_native()._callback()
    assert called == [True]

    changes = []
    line_edit = factory.create_line_edit()
    line_edit.on_change(lambda: changes.append(True))
    line_edit.set_text("updated")
    assert changes == [True]


@pytest.mark.web
def test_web_display_options(monkeypatch):
    use("web")
    layout = VBox(Label("Hello"), Button("OK"))
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("nicegui.ui.run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["app.py", "--ui", "web", "--host", "0.0.0.0", "--port", "9123", "--no-browser"],
    )

    assert UniversalDisplay._show_web(layout.get_native(), "Test", 640, 480)
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 9123
    assert captured["show"] is False
    assert captured["reload"] is False
    assert layout.get_native()._style["width"] == "100%"


@pytest.mark.web
def test_web_theme_refresh_updates_root():
    use("web")
    layout = VBox(Label("Theme"), Button("Toggle"))
    native = layout.get_native()
    before = dict(native._style)
    toggle_theme()
    try:
        refresh_theme(native)
        assert native._style != before
    finally:
        toggle_theme()
        refresh_theme(native)


def test_web_dark_mode_flag_follows_a_custom_registered_theme():
    """ui.dark_mode() is inherently boolean, but is_dark() must stay correct
    for any registered theme, not just the built-in light/dark pair -- this
    is what lets refresh_theme_web need zero Web-specific code to support
    named themes."""
    from uniui import is_dark, list_themes, register_theme, set_active_theme
    from uniui.backends.web.primitives import state as web_state
    from uniui.theme import LIGHT

    use("web")
    register_theme("dusk-web-test", dict(LIGHT, accent="#222222"), dark=True)
    try:
        assert "dusk-web-test" in list_themes()
        set_active_theme("dusk-web-test")
        assert is_dark() is True

        layout = VBox(Label("Theme"))
        refresh_theme(layout.get_native())
        assert web_state._dark_mode.value is True
    finally:
        set_active_theme("dark")
        refresh_theme(layout.get_native())
        from uniui import theme_registry
        theme_registry._REGISTRY.pop("dusk-web-test", None)
        theme_registry._DARK_FLAGS.pop("dusk-web-test", None)


@pytest.mark.web
def test_web_factory_admin_surface_and_theme():
    factory = create_factory("web")
    shell = factory.create_app_shell()
    assert type(factory.create_card()).__name__ == "WebCardAdapter"
    assert type(factory.create_stat_card()).__name__ == "WebStatCardAdapter"
    assert type(factory.create_table()).__name__ == "WebTableAdapter"
    assert type(factory.create_sidebar()).__name__ == "WebSidebarAdapter"
    assert type(factory.create_breadcrumb()).__name__ == "WebBreadcrumbAdapter"

    set_web_admin_theme(True)
    try:
        assert is_web_admin_dark()
        assert shell.get_native()._style["--uniui-bg"] == "#0b0f19"
        assert "uniui-web-body" in shell._splitter._classes
    finally:
        set_web_admin_theme(False)


@pytest.mark.web
def test_web_admin_sidebar_and_table_events():
    factory = create_factory("web")
    sidebar = factory.create_sidebar()
    sidebar.add_item("users", "Users", "users")
    assert "uniui-svg-icon uniui-icon-users" in (
        sidebar._buttons[0].slots["default"].template
    )
    selected = []
    sidebar.on_select(selected.append)
    sidebar._emit("users")
    assert selected == ["users"]

    table = factory.create_table()
    table.set_columns([{"key": "id", "label": "ID"}])
    table.set_rows([{"id": 3}])
    rows = []
    table.on_row_click(rows.append)

    class Event:
        args = {"row": {"id": 3}}

    table._on_row_event(Event())
    assert rows == [{"id": 3}]


@pytest.mark.web
def test_web_gauge_chart_and_drawer_update_in_place():
    factory = create_factory("web")
    gauge = factory.create_gauge(); native_gauge = gauge.get_native()
    gauge.set_label("Load"); gauge.set_unit("%"); gauge.set_value(72)
    chart = factory.create_chart(); native_chart = chart.get_native()
    chart.set_max_points(3)
    chart.set_data([1, 2], [{"name": "Load", "data": [20, 30]}])
    chart.append_data(3, [40]); chart.append_data(4, [50])
    drawer = factory.create_drawer(); drawer.set_title("Details")
    drawer.set_content(factory.create_label()); drawer.open()

    assert gauge.get_native() is native_gauge
    assert chart.get_native() is native_chart
    assert "uniui-gauge-svg" in native_gauge.content
    assert len(chart._model.x_values) == 3
    assert drawer.is_open()
    drawer.close(); assert not drawer.is_open()


@pytest.mark.web
def test_nicegui_is_lazy_imported():
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, uniui; uniui.create_factory('qt'); "
            "assert 'nicegui' not in sys.modules",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.web
@pytest.mark.parametrize(
    ("script", "expected_title"),
    [
        ("hello.py", b"Hello UniUI"),
        ("quick_start.py", b"BMI Calculator"),
        ("examples/sysmon.py", b"System Monitor"),
    ],
)
def test_web_server_smoke(script, expected_title):
    repo_root = Path(__file__).resolve().parents[1]
    port = _free_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    env.pop("PYTEST_CURRENT_TEST", None)
    process = subprocess.Popen(
        [
            sys.executable,
            script,
            "--ui",
            "web",
            "--no-browser",
            "--port",
            str(port),
        ],
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                pytest.fail(
                    f"{script} exited before serving HTTP\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                )
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=1) as response:
                    assert response.status == 200
                    assert expected_title in response.read()
                    break
            except OSError:
                time.sleep(0.25)
        else:
            pytest.fail(f"{script} did not start a Web server within 15 seconds")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
