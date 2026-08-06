"""Reusable, optional motion helpers for the Qt Admin backend."""
from __future__ import annotations

from PySide2 import QtCore


_MOTION_ENABLED = True


def set_motion_enabled(enabled: bool) -> bool:
    global _MOTION_ENABLED
    _MOTION_ENABLED = bool(enabled)
    return _MOTION_ENABLED


def is_motion_enabled() -> bool:
    return _MOTION_ENABLED


def motion_duration(milliseconds: int) -> int:
    return max(0, int(milliseconds)) if _MOTION_ENABLED else 0


def animate_value(owner, start: float, end: float, update,
                  milliseconds: int = 220) -> QtCore.QVariantAnimation:
    animation = QtCore.QVariantAnimation(owner)
    animation.setStartValue(float(start))
    animation.setEndValue(float(end))
    duration = motion_duration(milliseconds)
    animation.setDuration(duration)
    animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
    animation.valueChanged.connect(lambda value: update(float(value)))
    owner._uniui_value_animation = animation
    if duration == 0:
        update(float(end))
        return animation
    animation.start()
    return animation


__all__ = [
    "animate_value", "is_motion_enabled", "motion_duration", "set_motion_enabled",
]
