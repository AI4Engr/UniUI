"""Compatibility re-exports for :mod:`uniui.backends.qt.effects`.

The implementation moved into the Qt backend package.  This module stays so
that existing imports keep working; it owns nothing.

``set_motion_enabled`` rebinds a module-level flag, so callers must reach it
through this module's attribute (the re-export below is the same function
object and mutates the canonical module's global).
"""
from __future__ import annotations

from .backends.qt.effects import (
    animate_value,
    is_motion_enabled,
    motion_duration,
    set_motion_enabled,
)

__all__ = [
    "animate_value", "is_motion_enabled", "motion_duration", "set_motion_enabled",
]
