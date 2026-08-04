"""NiceGUI/Quasar Admin backend.

Importing this package pulls in ``nicegui``; importing :mod:`uniui.backends`
alone does not. Styling is plain CSS scoped under ``.uniui-web-admin``, with the
design tokens emitted as CSS custom properties on the shell element itself -
see ``WebAppShellAdapter.apply_theme``.
"""
from .runtime import get_palette, is_dark, set_theme

__all__ = ["get_palette", "is_dark", "set_theme"]
