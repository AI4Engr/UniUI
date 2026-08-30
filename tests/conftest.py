"""
Pytest configuration and shared fixtures for UniUI tests.
"""
import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from uniui import create_factory, use


def pytest_addoption(parser):
    parser.addoption(
        "--ui",
        default="qt",
        choices=["qt", "jupyter", "web"],
        help="UI framework to use for contract tests (default: qt)",
    )


@pytest.fixture
def factory(request):
    """Widget factory for the chosen UI framework.

    Re-asserts ``use(framework)`` on every test, not just once per session:
    other tests call ``use("web")``/``use("jupyter")`` directly and never
    restore it, so a session-scoped fixture could hand out a factory that
    doesn't match the facade functions' (``Label()``, ``VBox()``, ...)
    active global backend depending on test order.
    """
    framework = request.config.getoption("--ui")
    use(framework)
    return create_factory(framework)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "contract: marks tests as widget contract tests"
    )
