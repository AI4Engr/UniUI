"""Backend detection and factory selection.

This is the one place that knows which backends exist and how to reach them.
``uniui/__init__.py`` used to carry it, which meant the public package module
imported backend-selection logic just to re-export three functions.

The active factory is *mutable module state*: ``use()`` rebinds it and
``_get_factory()`` reads it back, so both must go through this module's
global. ``uniui.__init__`` re-exports the *functions*, never ``_factory``
itself - a re-exported ``_factory`` would be a stale snapshot taken at import
time, and ``use()`` would appear to do nothing. ``routing.py`` relies on this:
it calls ``_get_factory()`` lazily, per navigation, precisely so it observes
the current backend.
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

    # 3. Detect wxPython
    try:
        import wx
        return 'wx'
    except ImportError:
        pass

    # 4. Detect Tkinter (Python built-in)
    try:
        import tkinter
        return 'tk'
    except ImportError:
        pass

    raise ImportError(
        "No available UI framework found! "
        "Please install PySide2, wxPython, or use Jupyter."
    )


#: Legacy backends warn on construction. Kept as data so the two branches
#: cannot drift apart.
_LEGACY = {
    'wx': "The wxPython backend ('wx') is legacy and no longer supported. "
          "No new features will be developed. Please migrate to 'qt' or 'jupyter'.",
    'tk': "The Tkinter backend ('tk') is legacy and no longer supported. "
          "No new features will be developed. Please migrate to 'qt' or 'jupyter'.",
}


def _create_factory(framework: str = 'auto') -> IWidgetFactory:
    """Create factory for specified framework"""
    if framework == 'auto':
        framework = _detect_framework()

    # Only poke the web backend if it has already been imported: touching
    # uniui.web here would drag NiceGUI into every Qt/Tk process.
    web_module = sys.modules.get("uniui.web")
    if web_module is not None:
        web_module.set_backend_active(framework == "web")

    if framework in _LEGACY:
        import warnings
        warnings.warn(_LEGACY[framework], DeprecationWarning, stacklevel=2)

    if framework == 'qt':
        from ..qt_components import QtWidgetFactory
        return QtWidgetFactory()
    elif framework == 'jupyter':
        from ..jupyter_components import JupyterWidgetFactory
        return JupyterWidgetFactory()
    elif framework == 'web':
        try:
            from ..web_components import NiceGUIWidgetFactory
        except ImportError as exc:
            raise ImportError(
                "The Web backend requires NiceGUI. Install it with "
                "'pip install -e .[web]'."
            ) from exc
        return NiceGUIWidgetFactory()
    elif framework == 'wx':
        from ..wx import WxWidgetFactory
        return WxWidgetFactory()
    elif framework == 'tk':
        from ..tk import TkWidgetFactory
        return TkWidgetFactory()
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
