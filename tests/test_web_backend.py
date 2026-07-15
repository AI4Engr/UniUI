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
        ("sysmon.py", b"System Monitor"),
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
