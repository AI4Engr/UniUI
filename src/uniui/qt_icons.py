"""Compatibility re-exports for :mod:`uniui.backends.qt.icons`.

The implementation moved into the Qt backend package.  This module stays so
that existing imports (and the examples) keep working; it owns nothing.
"""
from __future__ import annotations

from .backends.qt.icons import admin_icon, admin_pixmap

__all__ = ["admin_icon", "admin_pixmap"]
