"""The common base class every Web adapter derives from."""
from __future__ import annotations

from typing import Any, Callable, List, Optional

from nicegui import ui

from ....core import *
from ....strategies import normalize_text, parse_float
from ....theme import THEME, is_dark
from .helpers import _style_size
from .state import T, _install_css, register_adapter


class _WebAdapter:
    def __init__(self, native):
        _install_css()
        self._native = native
        register_adapter(self)

    def get_native(self):
        return self._native

    def _apply_theme(self) -> None:
        pass

    def set_fixed_width(self, width: int) -> None:
        _style_size(self._native, "width", width)

    def set_fixed_height(self, height: int) -> None:
        _style_size(self._native, "height", height)

    def set_minimum_width(self, width: int) -> None:
        _style_size(self._native, "min-width", width)

    def set_minimum_height(self, height: int) -> None:
        _style_size(self._native, "min-height", height)

    def show(self) -> None:
        self._native.set_visibility(True)

    def hide(self) -> None:
        self._native.set_visibility(False)

    def is_visible(self) -> bool:
        return bool(self._native.visible)
