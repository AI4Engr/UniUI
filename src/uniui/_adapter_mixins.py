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
    """show / hide / is_visible.

    Calls through ``get_native()`` rather than ``self._native`` directly, so
    it works both for adapters that pair it with ``NativeMixin`` and for
    adapters that store their native widget under a different attribute name
    but still implement ``get_native()`` (e.g. every Qt Admin component).
    """

    def show(self) -> None:
        self.get_native().show()

    def hide(self) -> None:
        self.get_native().hide()

    def is_visible(self) -> bool:
        return self.get_native().isVisible()


class SizeMixin:
    """Fixed and minimum sizing. See :class:`VisibilityMixin` on ``get_native()``."""

    def set_fixed_width(self, width: int) -> None:
        self.get_native().setFixedWidth(width)

    def set_fixed_height(self, height: int) -> None:
        self.get_native().setFixedHeight(height)

    def set_minimum_width(self, width: int) -> None:
        self.get_native().setMinimumWidth(width)

    def set_minimum_height(self, height: int) -> None:
        self.get_native().setMinimumHeight(height)


class EnableMixin:
    """set_enabled / is_enabled. See :class:`VisibilityMixin` on ``get_native()``."""

    def set_enabled(self, enabled: bool) -> None:
        self.get_native().setEnabled(enabled)

    def is_enabled(self) -> bool:
        return self.get_native().isEnabled()


class ClassMixin:
    """add_class / remove_class via a Qt dynamic property + QSS attribute
    selector ([name="true"]), repolished so an already-applied stylesheet
    picks up the change immediately. Verified empirically: hyphenated
    property names work fine in PySide2's QSS parser, and multiple
    independent boolean properties on one widget compose without collision
    - no translation table or single combined "classes" property needed.
    """

    def add_class(self, name: str) -> None:
        native = self.get_native()
        native.setProperty(name, True)
        native.style().unpolish(native)
        native.style().polish(native)

    def remove_class(self, name: str) -> None:
        native = self.get_native()
        native.setProperty(name, False)
        native.style().unpolish(native)
        native.style().polish(native)


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


class JupyterVisibilityMixin:
    """show / hide / is_visible via ``ipywidgets.Widget.layout`` directly.

    Unlike Qt's native wrapper classes, raw ``ipywidgets`` widgets (a plain
    ``widgets.VBox``, as every Jupyter Admin component's native widget is)
    have no camelCase show/hide protocol — but every ``ipywidgets.Widget``
    has a ``.layout``, so this works uniformly for custom wrapper classes
    and stock ipywidgets containers alike.
    """

    def show(self) -> None:
        self.get_native().layout.display = None

    def hide(self) -> None:
        self.get_native().layout.display = 'none'

    def is_visible(self) -> bool:
        return self.get_native().layout.display != 'none'


class JupyterSizeMixin:
    """Fixed and minimum sizing via ``ipywidgets.Widget.layout``."""

    def set_fixed_width(self, width: int) -> None:
        self.get_native().layout.width = f'{width}px'

    def set_fixed_height(self, height: int) -> None:
        self.get_native().layout.height = f'{height}px'

    def set_minimum_width(self, width: int) -> None:
        self.get_native().layout.min_width = f'{width}px'

    def set_minimum_height(self, height: int) -> None:
        self.get_native().layout.min_height = f'{height}px'


class JupyterEnableMixin:
    """set_enabled / is_enabled via ``ipywidgets.Widget.disabled``.

    ``disabled`` is a real trait on interactive controls but not on plain
    containers (``VBox``/``HBox``/``Box``) — setting it there still succeeds
    (traitlets allows a plain attribute write) but has no visual effect, and
    reading it before ever being set raises ``AttributeError``, hence the
    ``getattr`` default below.
    """

    def set_enabled(self, enabled: bool) -> None:
        self.get_native().disabled = not bool(enabled)

    def is_enabled(self) -> bool:
        return not getattr(self.get_native(), 'disabled', False)


class JupyterClassMixin:
    """add_class / remove_class via ipywidgets' own DOM class list."""

    def add_class(self, name: str) -> None:
        self.get_native().add_class(name)

    def remove_class(self, name: str) -> None:
        self.get_native().remove_class(name)


__all__ = [
    "ClassMixin",
    "ClearMixin",
    "EnableMixin",
    "JupyterClassMixin",
    "JupyterEnableMixin",
    "JupyterSizeMixin",
    "JupyterVisibilityMixin",
    "NativeMixin",
    "SelectionMixin",
    "SizeMixin",
    "TextMixin",
    "VisibilityMixin",
]
