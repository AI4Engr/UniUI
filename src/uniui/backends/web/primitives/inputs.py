"""Input primitives: buttons, text entry, and selection controls."""
from __future__ import annotations

import html as html_lib

from typing import Any, Callable, List, Optional

from nicegui import ui

from ....core import *
from ....state import Handle, safe_call
from ....strategies import normalize_text, parse_float
from ....theme import THEME, is_dark
from .state import T, register_adapter

from .base import _WebAdapter
from .helpers import _plain_html, _set_enabled, _style_size


def _list_handle(callbacks: List[Callable], callback: Callable) -> Handle:
    def cancel():
        if callback in callbacks:
            callbacks.remove(callback)
    return Handle(cancel)

class WebButtonAdapter(_WebAdapter, IButton):
    _BUTTON_KEYS = {
        "action": "accent_action",
        "op": "accent_op",
        "sci": "accent_sci",
        "neutral": "accent_neutral",
    }

    def __init__(self):
        self._callbacks: List[Callable[[], None]] = []
        self._enabled = True
        self._button_type = None
        native = ui.button("", color=None).classes("uniui-button").props("no-caps unelevated")
        super().__init__(native)
        native._callback = self._emit_click
        native.set_btntype = self.set_btntype
        native.on("click", lambda _event: self._emit_click())
        self._apply_theme()

    def _emit_click(self) -> None:
        if self._enabled:
            for callback in list(self._callbacks):
                safe_call(callback, backend="web", component="Button", method="connect")

    def set_btntype(self, button_type) -> None:
        self._button_type = button_type
        self._apply_theme()

    def set_text(self, text: str) -> None:
        self._native.set_text(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.text)

    def connect(self, callback: Callable[[], None]) -> Handle:
        self._callbacks.append(callback)
        return _list_handle(self._callbacks, callback)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        _set_enabled(self._native, self._enabled)

    def is_enabled(self) -> bool:
        return self._enabled

    def _apply_theme(self) -> None:
        key = self._BUTTON_KEYS.get(self._button_type, "accent")
        self._native.style(
            f"background-color: {T.get(key, T['accent'])}; "
            f"color: {T['fg_button']}; border-radius: {T['border_radius']}px"
        )
class WebLineEditAdapter(_WebAdapter, ILineEdit):
    def __init__(self):
        self._callbacks: List[Callable[[], None]] = []
        self._enabled = True
        self._suppress_change = False
        native = ui.input(value="").classes("uniui-input w-full")
        super().__init__(native)
        native.on_value_change(lambda _event: self._emit_change())
        native.event_generate = lambda _name: self._emit_change()
        self._apply_theme()

    def _emit_change(self) -> None:
        if self._suppress_change:
            return
        for callback in list(self._callbacks):
            safe_call(callback, backend="web", component="LineEdit", method="on_change")

    def set_text(self, text: str) -> None:
        self._suppress_change = True
        try:
            self._native.set_value(normalize_text(text))
        finally:
            self._suppress_change = False
        self._emit_change()

    def get_text(self) -> str:
        return normalize_text(self._native.value)

    def set_value(self, value: Any) -> None:
        self.set_text(value)

    def get_value(self):
        text = self.get_text()
        try:
            return parse_float(text)
        except ValueError as exc:
            raise InvalidValueError(f"Invalid numeric value: {text}") from exc

    def on_change(self, callback: Callable[[], None]) -> Handle:
        self._callbacks.append(callback)
        return _list_handle(self._callbacks, callback)

    def on_finish_edit(self, callback: Callable[[], None]) -> None:
        self._native.on("blur", lambda _event: callback())
        self._native.on("keydown.enter", lambda _event: callback())

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        _set_enabled(self._native, self._enabled)

    def is_enabled(self) -> bool:
        return self._enabled

    def set_leading_icon(self, icon_name: str) -> None:
        self._native.add_slot(
            "prepend", f'<span class="uniui-svg-icon uniui-icon-{icon_name}"></span>'
        )

    def _apply_theme(self) -> None:
        self._native.style(
            f"color: {T['fg']}; background: {T['bg_input']}; "
            f"border-radius: {T['border_radius']}px"
        )
class WebTextAreaAdapter(_WebAdapter, ITextArea):
    def __init__(self):
        self._text = ""
        self._callbacks: List[Callable[[], None]] = []
        native = ui.html("", sanitize=False).classes("uniui-textarea")
        super().__init__(native)
        native.edit_modified = lambda _value=None: None
        native.event_generate = lambda _name: self._emit_change()
        self._apply_theme()

    def _emit_change(self) -> None:
        for callback in list(self._callbacks):
            safe_call(callback, backend="web", component="TextArea", method="on_change")

    def _plain_content(self) -> str:
        escaped = html_lib.escape(self._text)
        return f'<pre style="margin:0;white-space:pre-wrap">{escaped}</pre>'

    def set_text(self, text: str) -> None:
        self._text = "" if text is None else str(text)
        self._native.set_content(self._plain_content())

    def set_html(self, html: str) -> None:
        self._text = _plain_html(html)
        self._native.set_content(html or "")

    def get_text(self) -> str:
        return self._text

    def append(self, text: str) -> None:
        self.set_text(f"{self._text}{'' if text is None else str(text)}")

    def clear(self) -> None:
        self.set_text("")

    def on_change(self, callback: Callable[[], None]) -> Handle:
        self._callbacks.append(callback)
        return _list_handle(self._callbacks, callback)

    def set_maximum_height(self, height: int) -> None:
        _style_size(self._native, "max-height", height)

    def _apply_theme(self) -> None:
        self._native.style(
            f"color: {T['fg']}; background: {T['bg_input']}; "
            f"border: 1px solid {T['border']}; border-radius: {T['border_radius']}px; "
            f"padding: {T['padding_inner']}px"
        )
class _WebSelectAdapter(_WebAdapter):
    def __init__(self, *, editable: bool):
        self._callbacks: List[Callable[[], None]] = []
        self._enabled = True
        self._suppress_change = False
        native = ui.select([], with_input=editable).classes("uniui-select w-full")
        super().__init__(native)
        native.on_value_change(lambda _event: self._emit_change())
        native.event_generate = lambda _name: self._emit_change()
        self._apply_theme()

    def _emit_change(self) -> None:
        if self._suppress_change:
            return
        for callback in list(self._callbacks):
            safe_call(callback, backend="web", component=type(self).__name__, method="on_change")

    def add_item(self, item: str) -> None:
        item = normalize_text(item)
        options = list(self._native.options)
        options.append(item)
        self._native.options = options
        if self._native.value is None:
            self._native.value = item
        self._native.update()

    def clear(self) -> None:
        self._native.options = []
        self._native.value = None
        self._native.update()

    def set_selection(self, item: str) -> None:
        item = normalize_text(item)
        if item in self._native.options:
            self._suppress_change = True
            try:
                self._native.set_value(item)
            finally:
                self._suppress_change = False

    def get_text(self) -> str:
        return normalize_text(self._native.value)

    def on_change(self, callback: Callable[[], None]) -> Handle:
        self._callbacks.append(callback)
        return _list_handle(self._callbacks, callback)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        _set_enabled(self._native, self._enabled)

    def is_enabled(self) -> bool:
        return self._enabled

    def _apply_theme(self) -> None:
        self._native.style(
            f"color: {T['fg']}; background: {T['bg_input']}; "
            f"border-radius: {T['border_radius']}px"
        )
class WebComboBoxAdapter(_WebSelectAdapter, IComboBox):
    def __init__(self):
        super().__init__(editable=True)
class WebDropdownAdapter(_WebSelectAdapter, IDropdown):
    def __init__(self):
        super().__init__(editable=False)

    def set_value(self, values: list) -> None:
        self.clear()
        for value in values:
            self.add_item(value)
class _WebToggleAdapter(_WebAdapter):
    """Shared body for WebCheckboxAdapter/WebSwitchAdapter - both are a
    boolean ``.value`` NiceGUI element (``ui.checkbox``/``ui.switch``) with
    an identical on_change contract, differing only in which element they
    wrap."""

    def __init__(self, native):
        self._callbacks: List[Callable[[], None]] = []
        super().__init__(native)
        native.on_value_change(lambda _event: self._emit_change())

    def _emit_change(self) -> None:
        for callback in list(self._callbacks):
            safe_call(callback, backend="web", component=type(self).__name__, method="on_change")

    def is_checked(self) -> bool:
        return bool(self._native.value)

    def set_checked(self, checked: bool) -> None:
        self._native.value = bool(checked)

    def on_change(self, callback: Callable[[], None]) -> Handle:
        self._callbacks.append(callback)
        return _list_handle(self._callbacks, callback)
class WebCheckboxAdapter(_WebToggleAdapter, ICheckbox):
    def __init__(self):
        super().__init__(ui.checkbox())
class WebSwitchAdapter(_WebToggleAdapter, ISwitch):
    def __init__(self):
        super().__init__(ui.switch())
class WebRadioGroupAdapter(_WebAdapter, IRadioGroup):
    def __init__(self):
        self._callbacks: List[Callable[[], None]] = []
        native = ui.radio([])
        super().__init__(native)
        native.on_value_change(lambda _event: self._emit_change())

    def _emit_change(self) -> None:
        for callback in list(self._callbacks):
            safe_call(callback, backend="web", component="RadioGroup", method="on_change")

    def set_options(self, options: list) -> None:
        options = list(options)
        self._native.options = options
        # Assigning .options after construction does not auto-select the
        # first entry (confirmed empirically: .value stays None) - select
        # it explicitly to match IRadioGroup.set_options's documented
        # "selects the first one", same gap as the Jupyter backend.
        self._native.set_value(options[0] if options else None)
        self._native.update()

    def get_selected(self) -> str:
        return self._native.value or ""

    def set_selected(self, option: str) -> None:
        self._native.set_value(option)

    def on_change(self, callback: Callable[[], None]) -> Handle:
        self._callbacks.append(callback)
        return _list_handle(self._callbacks, callback)
class WebNumberInputAdapter(_WebAdapter, INumberInput):
    def __init__(self):
        self._callbacks: List[Callable[[], None]] = []
        native = ui.number(value=0, min=0, max=100, step=1)
        super().__init__(native)
        native.on_value_change(lambda _event: self._emit_change())

    def _emit_change(self) -> None:
        for callback in list(self._callbacks):
            safe_call(callback, backend="web", component="NumberInput", method="on_change")

    def set_range(self, minimum: float, maximum: float) -> None:
        self._native.props(f"min={minimum} max={maximum}")
        # Unlike Qt's QDoubleSpinBox.setRange()/ipywidgets.BoundedFloatText,
        # NiceGUI's props() only sets the client-side display bound - it
        # does not clamp the current server-side .value (confirmed
        # empirically). Clamp explicitly so the contract - the value is
        # always within the current range - holds on every backend.
        current = self.get_value()
        clamped = max(minimum, min(current, maximum))
        if clamped != current:
            self.set_value(clamped)

    def set_step(self, step: float) -> None:
        self._native.props(f"step={step}")

    def get_value(self) -> float:
        return float(self._native.value or 0)

    def set_value(self, value: float) -> None:
        self._native.set_value(value)

    def on_change(self, callback: Callable[[], None]) -> Handle:
        self._callbacks.append(callback)
        return _list_handle(self._callbacks, callback)
class WebSliderAdapter(_WebAdapter, ISlider):
    def __init__(self):
        self._callbacks: List[Callable[[], None]] = []
        native = ui.slider(min=0, max=100, step=1, value=0)
        super().__init__(native)
        native.on_value_change(lambda _event: self._emit_change())

    def _emit_change(self) -> None:
        for callback in list(self._callbacks):
            safe_call(callback, backend="web", component="Slider", method="on_change")

    def set_range(self, minimum: float, maximum: float) -> None:
        self._native.props(f"min={minimum} max={maximum}")
        # Same gap as WebNumberInputAdapter.set_range - props() only sets
        # the client-side display bound, not the server-side .value.
        current = self.get_value()
        clamped = max(minimum, min(current, maximum))
        if clamped != current:
            self.set_value(clamped)

    def set_step(self, step: float) -> None:
        self._native.props(f"step={step}")

    def get_value(self) -> float:
        return float(self._native.value or 0)

    def set_value(self, value: float) -> None:
        self._native.set_value(value)

    def on_change(self, callback: Callable[[], None]) -> Handle:
        self._callbacks.append(callback)
        return _list_handle(self._callbacks, callback)
