"""Compatibility re-exports for :mod:`uniui.backends.jupyter.primitives.styles`.

The implementation moved into the Jupyter backend's primitives package, next to
the factory that marks widgets for it.  This module stays so that existing
imports keep working; it owns nothing.
"""
from __future__ import annotations

from .backends.jupyter.primitives.styles import (  # noqa: F401
    WIDGET_CLASS,
    _BASE_RULES,
    _STYLE_NODES,
    base_control_rules,
    base_css,
    get_admin_palette,
    mark,
    palette_declarations,
    refresh,
    style_widget_html,
)

__all__ = ["WIDGET_CLASS", "base_css", "mark", "refresh", "style_widget_html"]
