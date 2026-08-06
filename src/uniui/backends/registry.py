"""Backend detection and factory selection.

This is the one place that knows which backends exist and how to reach them.
There are three: ``qt``, ``jupyter`` and ``web``. The legacy ``tk`` and ``wx``
backends were removed; asking for either raises ``ValueError`` like any other
unknown framework name.

``uniui/__init__.py`` used to carry it, which meant the public package module
imported backend-selection logic just to re-export three functions.

The active factory is *mutable module state*: ``use()`` rebinds it and
``_get_factory()`` reads it back, so both must go through this module's
global. ``uniui.__init__`` re-exports the *functions*, never ``_factory``
itself - a re-exported ``_factory`` would be a stale snapshot taken at import
time, and ``use()`` would appear to do nothing. ``routing.py`` relies on this:
it calls ``_get_factory()`` lazily, per navigation, precisely so it observes
the current backend.

Factories are imported from ``backends/<name>/factory.py``, never from the
root ``qt.py`` / ``qt_components.py`` compatibility modules. Those are for
external callers only; routing the canonical path through them would make the
package depend on its own back-compat surface.

Every backend import is deliberately inside the function body. Importing
``uniui`` must not drag in PySide2, ipywidgets or NiceGUI - only asking for a
backend may do that.
"""

from __future__ import annotations

import sys
from typing import Optional

from ..core import IWidgetFactory


def _detect_framework() -> str:
    """Auto-detect available framework (priority order)"""
    # 1. Detect Jupyter notebook/lab (must have an active kernel with a comm_info
    #    method — plain IPython console and IDE kernels lack this).
    try:
        ip = get_ipython()
        kernel = getattr(ip, "kernel", None)
        if ip is not None and callable(getattr(kernel, "comm_info", None)):
            return 'jupyter'
    except NameError:
        pass

    # 2. Detect PySide2/Qt
    try:
        import PySide2
        return 'qt'
    except ImportError:
        pass

    raise ImportError(
        "No available UI framework found! "
        "Please install PySide2, use Jupyter, or install the Web extra."
    )


def _create_factory(framework: str = 'auto') -> IWidgetFactory:
    """Create factory for specified framework"""
    if framework == 'auto':
        framework = _detect_framework()

    # Only poke the web backend if it has already been imported: touching the
    # web backend here would drag NiceGUI into every Qt process.
    #
    # ``state`` is the module that *owns* the flag. It must be addressed
    # directly: ``set_backend_active`` rebinds a module global, so calling it
    # through any module that re-exported it would still work, but reading the
    # flag back through a re-export would see a stale snapshot.
    web_state = sys.modules.get("uniui.backends.web.primitives.state")
    if web_state is not None:
        web_state.set_backend_active(framework == "web")

    if framework == 'qt':
        from .qt.factory import QtWidgetFactory
        return QtWidgetFactory()
    elif framework == 'jupyter':
        from .jupyter.factory import JupyterWidgetFactory
        return JupyterWidgetFactory()
    elif framework == 'web':
        try:
            from .web.factory import NiceGUIWidgetFactory
        except ImportError as exc:
            raise ImportError(
                "The Web backend requires NiceGUI. Install it with "
                "'pip install -e .[web]'."
            ) from exc
        return NiceGUIWidgetFactory()
    else:
        raise ValueError(f"Unsupported framework: {framework}")


# create_factory is the public name; _create_factory is the internal implementation
create_factory = _create_factory

# Global factory instance
_factory: Optional[IWidgetFactory] = None


def _get_factory() -> IWidgetFactory:
    """Get or create the global factory instance"""
    global _factory
    if _factory is None:
        _factory = _create_factory('auto')
    return _factory


def use(framework: str = 'auto'):
    """Set the UI framework to use"""
    global _factory
    _factory = _create_factory(framework)


def parse_args_ui() -> str:
    """Parse --ui argument from command line. Returns framework name."""
    import sys
    if "--ui" in sys.argv:
        idx = sys.argv.index("--ui")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return "auto"
