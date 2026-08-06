"""Compatibility re-exports for :mod:`uniui.backends.qt.primitives.styles`.

The implementation moved into the Qt backend's primitives package, next to the
factory that applies it.  This module stays so that existing imports (and the
examples) keep working; it owns nothing.
"""
from __future__ import annotations

from .backends.qt.primitives.styles import (  # noqa: F401
    _BASE_QSS,
    _STYLED_APPS,
    _STYLED_ROOTS,
    apply_app_style,
    get_admin_palette,
    apply_base_style,
    base_stylesheet,
    refresh_styled_widgets,
    scrollbar_stylesheet,
)

__all__ = [
    "apply_app_style",
    "apply_base_style",
    "base_stylesheet",
    "refresh_styled_widgets",
    "scrollbar_stylesheet",
]
