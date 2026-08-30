"""Input primitives: buttons, text entry, and selection controls."""
from __future__ import annotations

from typing import Callable, List, Optional

import ipywidgets as widgets
from IPython.display import display

from ....core import *
from ...._adapter_mixins import (
    ClearMixin, EnableMixin, JupyterEnableMixin, JupyterSizeMixin,
    JupyterVisibilityMixin, NativeMixin, SelectionMixin, SizeMixin, TextMixin,
    VisibilityMixin,
)
from ....state import Handle, safe_call
from ....strategies import normalize_text, parse_float
from ....theme import THEME, is_dark

#: Alias for the live theme dict. ``THEME`` is mutated in place on a theme
#: switch, so this is a view of the current palette, not a snapshot.
T = THEME
from .helpers import convert_control_text


class JupyterPushButton(widgets.Button):
    """Jupyter Push Button Widget - native implementation"""

    # btntype -> theme key mapping (mirrors Qt)
    _BTNTYPE_KEY = {
        'action':  'accent_action',
        'op':      'accent_op',
        'sci':     'accent_sci',
        'neutral': 'accent_neutral',
    }

    def __init__(self):
        super().__init__()
        self._btntype = None
        # Apply base styling
        self.style.button_color = T['accent']
        self.style.text_color = T['fg_button']
        self.style.font_weight = 'bold'
        self.layout.min_height = '32px'

    def set_btntype(self, btntype):
        """Apply visual category (action/op/sci/neutral or None for numeric)."""
        self._btntype = btntype
        key = self._BTNTYPE_KEY.get(btntype, 'accent')
        self.style.button_color = T[key]
        self.style.text_color = T['fg_button']

    def setText(self, text):
        self.description = text

    def getText(self):
        return self.description

    def connect(self, function):
        def wrapper(btn):
            safe_call(function, backend="jupyter", component="Button", method="connect")
        self.on_click(wrapper)
        return wrapper

    def disconnect(self, wrapper):
        self.on_click(wrapper, remove=True)

    def setEnabled(self, flag):
        self.disabled = not flag

    def isEnabled(self):
        return not self.disabled

    def setFixedWidth(self, width):
        self.layout.width = f'{width}px'

    def setFixedHeight(self, height):
        self.layout.height = f'{height}px'

    def setMinimumWidth(self, width):
        self.layout.min_width = f'{width}px'

    def setMinimumHeight(self, height):
        self.layout.min_height = f'{height}px'
class JupyterLineEdit(widgets.Text):
    """Jupyter Line Edit Widget - native implementation"""
    def __init__(self):
        super().__init__()
        self.disabled = False
        self.continuous_update = False
        self.style.description_width = '0px'
        self.layout.width = 'auto'

    def getText(self):
        return self.value

    def setText(self, text):
        self.value = text

    def getValue(self):
        if self.value == "":
            return 0.0
        else:
            return convert_control_text(self.value)

    def setValue(self, value):
        self.value = str(value)

    def finishEditing(self, function):
        self.observe(function, 'value')

    def textChanged(self, function):
        self.observe(function, 'value')

    def textChangedDisconnect(self, function):
        self.unobserve(function, 'value')

    def setFixedWidth(self, width):
        self.layout.width = str(width) + 'px'

    def setFixedHeight(self, height):
        self.layout.height = str(height) + 'px'

    def setMinimumWidth(self, width):
        self.layout.min_width = str(width) + 'px'

    def setMinimumHeight(self, height):
        self.layout.min_height = str(height) + 'px'

    def hide(self):
        self.layout.display = 'none'

    def show(self):
        self.layout.display = None

    def isVisible(self):
        return self.layout.display != 'none'

    def setEnabled(self, flag):
        self.disabled = not flag

    def isEnabled(self):
        return not self.disabled

    def setTextColor(self, color, background):
        self.style.text_color = color
        self.style.background = background
class JupyterTextarea(widgets.HTML):
    """Jupyter Text Area Widget — uses HTML for rich text support."""
    def __init__(self):
        super().__init__()
        self.layout.width = 'auto'
        self.layout.overflow_y = 'auto'

    def setText(self, text):
        import html as _html
        escaped = _html.escape(text)
        self.value = (
            f'<pre style="margin:0;font-family:Consolas,\'Courier New\',monospace;'
            f'font-size:9pt;white-space:pre-wrap">{escaped}</pre>'
        )

    def setHtml(self, html):
        self.value = html

    def getText(self):
        import re
        return re.sub(r'<[^>]+>', '', self.value)

    def append(self, text):
        import html as _html
        current = self.getText()
        self.setText(f"{current}\n{text}" if current else text)

    def clear(self):
        self.value = ""

    def setMaximumHeight(self, height):
        self.layout.max_height = str(height) + 'px'
        self.layout.overflow_y = 'auto'

    def setFixedWidth(self, width):
        self.layout.width = str(width) + 'px'

    def setFixedHeight(self, height):
        self.layout.height = str(height) + 'px'

    def setMinimumWidth(self, width):
        self.layout.min_width = str(width) + 'px'

    def setMinimumHeight(self, height):
        self.layout.min_height = str(height) + 'px'
class JupyterComboBox(widgets.Combobox):
    """Jupyter ComboBox Widget - native implementation (editable)"""
    def __init__(self):
        super().__init__()
        self.style.description_width = '0px'
        self.layout.width = 'auto'

    def addItem(self, item):
        old_content = list(self.options)
        old_content.append(item)
        self.options = tuple(old_content)

    def clear(self):
        old_content = list(self.options)
        old_content.clear()
        self.options = tuple(old_content)
        if len(self.options) > 0:
            self.value = self.options[0]
        else:
            self.value = "Unnamed"

    def connect(self, function):
        def wrapper(change):
            safe_call(function, backend="jupyter", component="ComboBox", method="on_change")
        self.observe(wrapper, 'value')
        return wrapper

    def disconnect(self, wrapper):
        self.unobserve(wrapper, 'value')

    def currentText(self):
        return self.value

    def deleteItem(self, item):
        old_content = list(self.options)
        old_content.remove(item)
        self.options = tuple(old_content)
        if len(self.options) > 0:
            self.value = self.options[0]
        else:
            self.value = "Unnamed"

    def setEditable(self, editable):
        # Combobox is always editable
        pass

    def setEditText(self, text):
        self.value = text

    def setEnabled(self, flag):
        self.disabled = not flag

    def isEnabled(self):
        return not self.disabled

    def setFixedWidth(self, width):
        self.layout.width = str(width) + 'px'

    def setFixedHeight(self, height):
        self.layout.height = str(height) + 'px'

    def setMinimumWidth(self, width):
        self.layout.min_width = str(width) + 'px'

    def setMinimumHeight(self, height):
        self.layout.min_height = str(height) + 'px'

    def setSelection(self, item):
        if item in self.options:
            self.value = item

    def sort(self):
        old_content = list(self.options)
        old_content.sort()
        self.options = tuple(old_content)
class JupyterDropdown(widgets.Dropdown):
    """Jupyter Dropdown Widget - native implementation (read-only)"""
    def __init__(self):
        super().__init__()
        self.style.description_width = '0px'
        self.layout.width = 'auto'

    def addItem(self, item):
        old_content = list(self.options)
        old_content.append(item)
        self.options = tuple(old_content)

    def clear(self):
        # Clearing options resets index to None on its own; assigning 0 here
        # raises "index out of bounds" because there is no option to select.
        self.options = tuple([])

    def connect(self, function):
        def wrapper(change):
            safe_call(function, backend="jupyter", component="Dropdown", method="on_change")
        self.observe(wrapper, 'value')
        return wrapper

    def disconnect(self, wrapper):
        self.unobserve(wrapper, 'value')

    def currentText(self):
        if len(self.options) > 0 and self.index is not None:
            return self.options[self.index]
        return ""

    def deleteItem(self, item):
        old_content = list(self.options)
        old_content.remove(item)
        self.options = tuple(old_content)

    def hide(self):
        self.layout.display = 'none'

    def show(self):
        self.layout.display = None

    def isVisible(self):
        return self.layout.display != 'none'

    def setEnabled(self, flag):
        self.disabled = not flag

    def isEnabled(self):
        return not self.disabled

    def setFixedWidth(self, width):
        self.layout.width = str(width) + 'px'

    def setFixedHeight(self, height):
        self.layout.height = str(height) + 'px'

    def setMinimumWidth(self, width):
        self.layout.min_width = str(width) + 'px'

    def setMinimumHeight(self, height):
        self.layout.min_height = str(height) + 'px'

    def setSelection(self, item):
        if item in self.options:
            self.index = self.options.index(item)
            self.value = item

    def setValue(self, value_list):
        if len(value_list) > 0:
            self.options = tuple(value_list)
            self.index = 0
            self.value = self.options[self.index]

    def sort(self):
        old_content = list(self.options)
        old_content.sort()
        self.options = tuple(old_content)
class JupyterButtonAdapter(NativeMixin, TextMixin, JupyterVisibilityMixin, EnableMixin, SizeMixin, IButton):
    """Jupyter Button adapter - implements snake_case interface convention"""

    # IEventCapable
    def connect(self, callback: Callable[[], None]) -> Handle:
        wrapper = self._native.connect(callback)
        return Handle(lambda: self._native.disconnect(wrapper))
class JupyterLineEditAdapter(ILineEdit):
    """Jupyter LineEdit adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterLineEdit):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.getText())

    # IValueCapable
    def set_value(self, value):
        self._native.setValue(value)

    def get_value(self):
        text = self.get_text()
        try:
            return parse_float(text)
        except ValueError:
            raise InvalidValueError(f"Invalid numeric value: {text}")

    # IChangeEventCapable
    def on_change(self, callback: Callable[[], None]) -> Handle:
        wrapper = lambda change: safe_call(callback, backend="jupyter", component="LineEdit", method="on_change")
        self._native.textChanged(wrapper)
        return Handle(lambda: self._native.textChangedDisconnect(wrapper))

    # IVisibilityCapable
    def show(self):
        self._native.show()

    def hide(self):
        self._native.hide()

    def is_visible(self) -> bool:
        return self._native.isVisible()

    # IEnableCapable
    def set_enabled(self, enabled: bool):
        self._native.setEnabled(enabled)

    def is_enabled(self) -> bool:
        return self._native.isEnabled()

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)
class JupyterTextAreaAdapter(JupyterVisibilityMixin, JupyterEnableMixin, ITextArea):
    """Jupyter TextArea adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterTextarea):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(text)

    def set_html(self, html: str):
        from ....theme import THEME as T
        full = (
            f'<div style="font-family:Cascadia Code,Consolas,\'Courier New\',monospace;'
            f'font-size:9pt;color:{T["fg"]};background:{T["bg_input"]};'
            f'padding:6px;white-space:pre">{html}</div>'
        )
        self._native.setHtml(full)

    def get_text(self) -> str:
        return self._native.getText()

    # IMultiLineCapable
    def append(self, text: str):
        self._native.append(text)

    def clear(self):
        self._native.clear()

    def set_maximum_height(self, height: int):
        self._native.setMaximumHeight(height)

    # IChangeEventCapable
    def on_change(self, callback: Callable[[], None]) -> Handle:
        wrapper = lambda change: safe_call(callback, backend="jupyter", component="TextArea", method="on_change")
        self._native.observe(wrapper, 'value')
        return Handle(lambda: self._native.unobserve(wrapper, 'value'))

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)
class JupyterComboBoxAdapter(NativeMixin, SelectionMixin, ClearMixin, JupyterVisibilityMixin,
                             EnableMixin, SizeMixin, IComboBox):
    """Jupyter ComboBox adapter - implements snake_case interface convention"""

    # IChangeEventCapable
    def on_change(self, callback: Callable[[], None]) -> Handle:
        wrapper = self._native.connect(callback)
        return Handle(lambda: self._native.disconnect(wrapper))
class JupyterDropdownAdapter(NativeMixin, SelectionMixin, ClearMixin,
                            VisibilityMixin, EnableMixin, SizeMixin, IDropdown):
    """Jupyter Dropdown adapter - implements snake_case interface convention"""

    # IValueCapable
    def set_value(self, value_list: list):
        """Set dropdown items from a list."""
        self._native.setValue(value_list)

    # IChangeEventCapable
    def on_change(self, callback: Callable[[], None]) -> Handle:
        wrapper = self._native.connect(callback)
        return Handle(lambda: self._native.disconnect(wrapper))
class JupyterCheckboxAdapter(NativeMixin, JupyterVisibilityMixin, JupyterEnableMixin,
                             JupyterSizeMixin, ICheckbox):
    """Jupyter Checkbox adapter - implements snake_case interface convention.

    Wraps a stock ``ipywidgets.Checkbox`` directly - no custom native
    wrapper class is needed since the Jupyter-flavored mixins operate on
    ``.layout``/``.disabled``/``.value`` rather than a camelCase protocol.
    """

    def is_checked(self) -> bool:
        return bool(self._native.value)

    def set_checked(self, checked: bool) -> None:
        self._native.value = bool(checked)

    def on_change(self, callback: Callable[[], None]) -> Handle:
        def wrapper(change):
            safe_call(callback, backend="jupyter", component="Checkbox", method="on_change")
        self._native.observe(wrapper, names="value")
        return Handle(lambda: self._native.unobserve(wrapper, names="value"))
class JupyterSwitchAdapter(NativeMixin, JupyterVisibilityMixin, JupyterEnableMixin,
                           JupyterSizeMixin, ISwitch):
    """Jupyter Switch adapter - implements snake_case interface convention.

    Wraps a stock ``ipywidgets.ToggleButton`` - ipywidgets has no dedicated
    "switch" widget; ToggleButton is the closest boolean on/off control.
    """

    def is_checked(self) -> bool:
        return bool(self._native.value)

    def set_checked(self, checked: bool) -> None:
        self._native.value = bool(checked)

    def on_change(self, callback: Callable[[], None]) -> Handle:
        def wrapper(change):
            safe_call(callback, backend="jupyter", component="Switch", method="on_change")
        self._native.observe(wrapper, names="value")
        return Handle(lambda: self._native.unobserve(wrapper, names="value"))
class JupyterRadioGroupAdapter(NativeMixin, JupyterVisibilityMixin, JupyterEnableMixin,
                               JupyterSizeMixin, IRadioGroup):
    """Jupyter RadioGroup adapter - implements snake_case interface convention.

    Wraps a stock ``ipywidgets.RadioButtons`` directly - it already has the
    exact set_options/get_selected/set_selected semantics via ``.options``/
    ``.value``.
    """

    def set_options(self, options: List[str]) -> None:
        options = list(options)
        self._native.options = tuple(options)
        # Unlike passing options= at construction time, assigning .options
        # afterwards does NOT auto-select the first one (confirmed
        # empirically: .value stays None) - select it explicitly to match
        # IRadioGroup.set_options's documented "selects the first one".
        self._native.value = options[0] if options else None

    def get_selected(self) -> str:
        return self._native.value or ""

    def set_selected(self, option: str) -> None:
        self._native.value = option

    def on_change(self, callback: Callable[[], None]) -> Handle:
        def wrapper(change):
            safe_call(callback, backend="jupyter", component="RadioGroup", method="on_change")
        self._native.observe(wrapper, names="value")
        return Handle(lambda: self._native.unobserve(wrapper, names="value"))
