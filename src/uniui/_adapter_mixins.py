"""Shared adapter forwarding for the Qt, Jupyter and Web backends.

Every backend wraps its toolkit in native classes that already expose the same
camelCase protocol (``setText``/``getText``/``show``/``hide``/``isVisible``/
``setFixedWidth``/...).  The adapters on top of them therefore ended up
byte-identical across backends — ``QtLabelAdapter`` and ``JupyterLabelAdapter``
differed only in class name and type hints.

These mixins hold that shared forwarding once.  They all operate on
``self._native`` and assume the camelCase protocol; an adapter whose backend
deviates simply overrides the method.
"""
from __future__ import annotations

from .strategies import normalize_text


class NativeMixin:
    """Store the native widget and expose it."""

    def __init__(self, native_widget):
        self._native = native_widget

    def get_native(self):
        return self._native


class TextMixin:
    """set_text / get_text, normalising None to an empty string."""

    def set_text(self, text: str) -> None:
        self._native.setText(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.getText())


class VisibilityMixin:
    """show / hide / is_visible."""

    def show(self) -> None:
        self._native.show()

    def hide(self) -> None:
        self._native.hide()

    def is_visible(self) -> bool:
        return self._native.isVisible()


class SizeMixin:
    """Fixed and minimum sizing."""

    def set_fixed_width(self, width: int) -> None:
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int) -> None:
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int) -> None:
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int) -> None:
        self._native.setMinimumHeight(height)


class EnableMixin:
    """set_enabled / is_enabled."""

    def set_enabled(self, enabled: bool) -> None:
        self._native.setEnabled(enabled)

    def is_enabled(self) -> bool:
        return self._native.isEnabled()


class ClearMixin:
    """clear()."""

    def clear(self) -> None:
        self._native.clear()


class SelectionMixin:
    """The item-list protocol shared by combo boxes and dropdowns."""

    def add_item(self, item: str) -> None:
        self._native.addItem(item)

    def set_selection(self, item: str) -> None:
        self._native.setSelection(item)

    def get_text(self) -> str:
        return self._native.currentText()


__all__ = [
    "ClearMixin",
    "EnableMixin",
    "NativeMixin",
    "SelectionMixin",
    "SizeMixin",
    "TextMixin",
    "VisibilityMixin",
]
