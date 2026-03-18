"""
Pytest configuration and shared fixtures for UniUI tests.
"""
import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from uniui import create_factory


def pytest_addoption(parser):
    parser.addoption(
        "--ui",
        default="tk",
        choices=["tk", "qt", "wx", "jupyter"],
        help="UI framework to use for contract tests (default: tk)",
    )


@pytest.fixture(scope="session")
def factory(request):
    """Session-scoped widget factory for the chosen UI framework."""
    framework = request.config.getoption("--ui")
    return create_factory(framework)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "contract: marks tests as widget contract tests"
    )
