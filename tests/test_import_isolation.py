"""Import-isolation guarantees for the ``src`` refactor.

``docs/src-refactor-plan.md`` states two dependency rules that no behavioural
test would otherwise catch:

  1. ``contracts``, ``models``, and ``shared`` must not import a backend
     toolkit.
  2. Importing ``uniui`` must not import PySide2, NiceGUI, or ipywidgets
     eagerly.

Both are easy to violate by accident - a single convenience import at the top
of a shared module is enough, and everything keeps working locally because the
toolkits happen to be installed. The failure only shows up for a user who
installed ``uniui`` without Qt.

Each check runs in a subprocess so it observes a clean interpreter rather than
modules another test already imported.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"

# Toolkits that must stay lazy. Tk is excluded: it ships with CPython and the
# stdlib may legitimately pull it in.
LAZY_TOOLKITS = ["PySide2", "PySide6", "nicegui", "ipywidgets", "wx"]


def _run(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def test_importing_uniui_does_not_load_toolkits():
    """``import uniui`` must not drag in any optional GUI toolkit."""
    script = f"""
import sys
sys.path.insert(0, {str(SRC)!r})
import uniui
leaked = [m for m in {LAZY_TOOLKITS!r} if m in sys.modules]
assert not leaked, "eagerly imported: " + ", ".join(leaked)
"""
    result = _run(script)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("toolkit", LAZY_TOOLKITS)
def test_uniui_imports_without_toolkit_installed(toolkit):
    """``import uniui`` must succeed when a toolkit is missing entirely.

    Simulated with a meta-path hook that raises ``ImportError`` for the
    toolkit, which is what a user without it installed would see.
    """
    script = f"""
import sys
sys.path.insert(0, {str(SRC)!r})

BLOCKED = {toolkit!r}

class Blocker:
    def find_module(self, name, path=None):
        return self if name == BLOCKED or name.startswith(BLOCKED + ".") else None
    def find_spec(self, name, path=None, target=None):
        if name == BLOCKED or name.startswith(BLOCKED + "."):
            raise ImportError("blocked for test: " + name)
        return None

sys.meta_path.insert(0, Blocker())
for mod in list(sys.modules):
    if mod == BLOCKED or mod.startswith(BLOCKED + "."):
        del sys.modules[mod]

import uniui
from uniui import Label, Button, VBox, Card, Table, AppShell, create_factory
"""
    result = _run(script)
    assert result.returncode == 0, (
        f"importing uniui fails when {toolkit} is unavailable:\n{result.stderr}"
    )


def test_importing_the_backends_package_does_not_load_toolkits():
    """``uniui.backends`` is a namespace, not a backend.

    Only reaching into ``uniui.backends.qt`` (or another concrete backend) may
    pull in a toolkit. If the package ``__init__`` ever imports its
    subpackages for convenience, rule 2 breaks for everyone.
    """
    script = f"""
import sys
sys.path.insert(0, {str(SRC)!r})
import uniui.backends
import uniui.models
leaked = [m for m in {LAZY_TOOLKITS!r} if m in sys.modules]
assert not leaked, "eagerly imported: " + ", ".join(leaked)
"""
    result = _run(script)
    assert result.returncode == 0, result.stderr


def test_models_do_not_import_a_toolkit():
    """Rule 1, checked directly rather than via ``uniui``."""
    script = f"""
import sys
sys.path.insert(0, {str(SRC)!r})
from uniui.models import navigation, table, status, stat_card, gauge, chart
leaked = [m for m in {LAZY_TOOLKITS!r} if m in sys.modules]
assert not leaked, "eagerly imported: " + ", ".join(leaked)
"""
    result = _run(script)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "backend, toolkit, others",
    [
        ("qt", "PySide2", ["nicegui", "ipywidgets"]),
        ("jupyter", "ipywidgets", ["PySide2", "nicegui"]),
        ("web", "nicegui", ["PySide2", "ipywidgets"]),
    ],
)
def test_a_backend_does_not_drag_in_the_other_backends(backend, toolkit, others):
    """Each ``backends/<name>`` package owns exactly one toolkit.

    Now that the three backends share ``models`` and sit under a common
    package, a stray cross-import (or a convenience re-export in
    ``backends/__init__``) would make ``import uniui.backends.qt`` require
    NiceGUI. That breaks Qt-only installs, and nothing else would catch it.
    """
    script = f"""
import sys
sys.path.insert(0, {str(SRC)!r})
pytest_toolkit = {toolkit!r}
try:
    import uniui.backends.{backend}
except ImportError as exc:
    # The backend's own toolkit is not installed here; nothing to check.
    if pytest_toolkit.lower() in str(exc).lower():
        sys.exit(0)
    raise
leaked = [m for m in {others!r} if m in sys.modules]
assert not leaked, "backend {backend} eagerly imported: " + ", ".join(leaked)
"""
    result = _run(script)
    assert result.returncode == 0, result.stderr


def test_public_api_surface_is_importable():
    """The compatibility list from the refactor plan must keep working."""
    script = f"""
import sys
sys.path.insert(0, {str(SRC)!r})
from uniui import Label, Button, VBox, Card, Table, AppShell
from uniui import create_factory, use
"""
    result = _run(script)
    assert result.returncode == 0, result.stderr
