"""
Jupyter/ipywidgets backend.

Native widgets, adapters, and factory for Jupyter notebooks.
Dark mode uses CSS injection + inline style for reliable theming.
HBox/VBox use ipywidgets flexbox layout.
"""
from __future__ import annotations
from typing import List, Optional, Callable

# Import capability interfaces from core
from .core import *
from .strategies import normalize_text, parse_float
from .theme import THEME, is_dark

# IPyWidgets imports
import ipywidgets as widgets
from IPython.display import display

T = THEME


# ============================================================================
# Jupyter Dark Mode CSS Support
# ============================================================================

def _generate_jupyter_css():
    """Generate CSS for Jupyter widgets based on current THEME."""
    return f"""
    <style>
    .uniui-themed {{ background-color: {T["bg"]} !important; }}
    .uniui-themed .widget-label {{ color: {T["fg"]} !important; }}
    .uniui-themed .widget-text input {{
        background-color: {T["bg_input"]} !important;
        color: {T["fg"]} !important;
    }}
    .uniui-themed .widget-dropdown select {{
        background-color: {T["bg_input"]} !important;
        color: {T["fg"]} !important;
        appearance: none !important;
        -webkit-appearance: none !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12'%3E%3Cpath d='M2 4 L6 8 L10 4' fill='none' stroke='{T["fg"].replace("#", "%23")}' stroke-width='2'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: right 8px center !important;
        padding-right: 28px !important;
    }}
    .uniui-themed .widget-button button {{
        background-color: {T["accent"]} !important;
        color: {T["fg_button"]} !important;
        border: none !important;
        border-radius: {T.get('border_radius', 8)}px !important;
        min-height: 32px !important;
        font-weight: 600 !important;
    }}
    .uniui-themed .widget-button button:hover {{
        filter: brightness(1.15) !important;
    }}
    .uniui-themed .widget-box {{
        background-color: {T["bg"]} !important;
    }}
    .uniui-themed .widget-html b {{
        color: {T["fg"]} !important;
    }}
    .uniui-themed .widget-box > .widget-box {{
        border-color: {T["border"]} !important;
    }}
    .jp-OutputArea-output:has(.uniui-themed) {{
        background-color: {T["bg"]} !important;
    }}
    </style>
    """


_jupyter_css_widget = None


def refresh_theme_jupyter(root_widget):
    """Refresh Jupyter widget theme.

    Uses CSS injection for background/dropdown + inline style for text colors.

    Args:
        root_widget: The root ipywidgets container (VBox/HBox)
    """
    global _jupyter_css_widget

    # CSS injection for background and elements that don't support inline style
    root_widget.add_class('uniui-themed')
    css_html = _generate_jupyter_css()

    if _jupyter_css_widget is None:
        _jupyter_css_widget = widgets.HTML(value=css_html)
        children = list(root_widget.children)
        root_widget.children = tuple([_jupyter_css_widget] + children)
    else:
        _jupyter_css_widget.value = css_html

    # Inline style for text colors, button colors, etc.
    _refresh_widget_tree(root_widget)


def _refresh_widget_tree(w):
    """Recursively apply THEME colors to all widgets in the tree."""
    if isinstance(w, widgets.Button):
        # Honour btntype if set
        btntype = getattr(w, '_btntype', None)
        _BTNTYPE_KEY = {
            'action':  'accent_action',
            'op':      'accent_op',
            'sci':     'accent_sci',
            'neutral': 'accent_neutral',
        }
        key = _BTNTYPE_KEY.get(btntype, 'accent')
        w.style.button_color = T[key]
        w.style.text_color = T["fg_button"]
    elif isinstance(w, (widgets.Text, widgets.FloatText, widgets.IntText)):
        w.style.text_color = T["fg"]
    elif isinstance(w, widgets.Label):
        w.style.text_color = T["fg"]
    elif isinstance(w, widgets.HTML):
        # Re-render HTML content with new theme colors (for GroupBox titles)
        if '<b' in w.value:
            import re
            w.value = re.sub(
                r'color:[^;"]+',
                f'color:{T["fg"]}',
                w.value
            )

    # Update GroupBox content border
    if isinstance(w, JupyterGroupBox):
        w._content_box.layout.border = f'1px solid {T["border"]}'

    # Recurse into children
    if hasattr(w, 'children'):
        for child in w.children:
            _refresh_widget_tree(child)


# ============================================================================
# Helper Functions
# ============================================================================

def convert_control_text(text):
    """Convert control text to appropriate type"""
    try:
        return float(text)
    except ValueError:
        return text


# ============================================================================
# Native Widget Classes (camelCase methods from widgets/nb_widgets.py)
# ============================================================================

class JupyterLabel(widgets.Label):
    """Jupyter Label Widget - native implementation"""
    def __init__(self):
        super().__init__()
        self.style.description_width = '0px'
        self.layout.width = 'auto'

    def setText(self, text):
        self.value = text
        self.disabled = True

    def getText(self):
        return self.value

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


class JupyterPushButton(widgets.Button):
    """Jupyter Push Button Widget - native implementation"""

    # btntype -> theme key mapping (mirrors Qt/Tk)
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
        self.on_click(lambda btn: function())

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


class JupyterTextarea(widgets.Textarea):
    """Jupyter Text Area Widget - native implementation"""
    def __init__(self):
        super().__init__()
        self.disabled = True
        self.style.description_width = '0px'
        self.layout.width = 'auto'

    def setText(self, text):
        self.value = text

    def getText(self):
        return self.value

    def append(self, text):
        current = self.value
        self.value = f"{current}\n{text}" if current else text

    def clear(self):
        self.value = ""

    def setMaximumHeight(self, height):
        self.layout.max_height = str(height) + 'px'

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
        self.observe(lambda change: function(), 'value')

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
        self.options = tuple([])
        self.index = 0

    def connect(self, function):
        self.observe(lambda change: function(), 'value')

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


class JupyterVBoxLayout(widgets.VBox):
    """Jupyter Vertical Box Layout - native implementation"""
    def __init__(self):
        super().__init__()

    def addItem(self, item):
        old_content = list(self.children)
        old_content.append(item)
        self.children = tuple(old_content)

    def addStretch(self):
        # Jupyter doesn't need stretch
        pass

    def setAlignmentTop(self):
        # Jupyter doesn't have explicit alignment control
        pass


class JupyterHBoxLayout(widgets.HBox):
    """Jupyter Horizontal Box Layout - native implementation"""
    def __init__(self):
        super().__init__(
            layout=widgets.Layout(
                display='flex',
                flex_flow='row',
                width='100%'
            )
        )

    def addItem(self, item):
        # Set flex=1 so children share equal width inside HBox
        if hasattr(item, 'layout'):
            item.layout.flex = '1'
            item.layout.width = 'auto'
        old_content = list(self.children)
        old_content.append(item)
        self.children = tuple(old_content)

    def addStretch(self):
        spacer = widgets.Box(layout=widgets.Layout(flex='1'))
        old_content = list(self.children)
        old_content.append(spacer)
        self.children = tuple(old_content)

    def setAlignmentTop(self):
        # Jupyter doesn't have explicit alignment control
        pass


class JupyterGroupBox(widgets.VBox):
    """Jupyter GroupBox - emulated using VBox with a styled HTML title"""
    def __init__(self):
        self._title_widget = widgets.HTML(value='')
        self._content_box = widgets.VBox()
        self._content_box.layout.border = f'1px solid {T["border"]}'
        self._content_box.layout.padding = f'{T["padding_inner"]}px'
        super().__init__(children=[self._title_widget, self._content_box])
        self.layout.margin = '4px 0'

    def setTitle(self, title):
        self._title_widget.value = (
            f'<b style="color:{T["fg"]};font-size:{T["font_size"]}pt">{title}</b>'
        )

    def setLayout(self, layout):
        """Set the content layout (a VBox/HBox native widget)"""
        if isinstance(layout, (widgets.Box, widgets.VBox, widgets.HBox)):
            self._content_box.children = (layout,)
        elif hasattr(layout, 'children'):
            self._content_box.children = (layout,)


class JupyterTabWidget(widgets.Tab):
    """Jupyter Tab Widget - native implementation"""
    def __init__(self):
        super().__init__()
        self.disabled = False

    def addTab(self, item, tab_name):
        old_content = list(self.children)
        old_content.append(item)
        self.children = tuple(old_content)
        self.set_title(len(self.children)-1, tab_name)

    def currentIndex(self):
        return self.selected_index

    def hide(self):
        self.layout.display = 'none'

    def show(self):
        self.layout.display = None

    def isVisible(self):
        return self.layout.display != 'none'

    def removeTabs(self):
        self.children = []
        self.selected_index = 0


class JupyterImage(widgets.Image):
    """Jupyter Image Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def setFixedWidth(self, width):
        self.layout.width = str(width) + 'px'

    def setFixedHeight(self, height):
        self.layout.height = str(height) + 'px'

    def setMinimumWidth(self, width):
        self.layout.min_width = str(width) + 'px'

    def setMinimumHeight(self, height):
        self.layout.min_height = str(height) + 'px'

    def setImage(self, image):
        with open(image, "rb") as file:
            self.value = file.read()

    def setImageFromUrl(self, url):
        raise NotSupportedError(
            "Image URL loading is not supported in the Jupyter backend. "
            "Use setImage with a local file path."
        )


# ============================================================================
# Adapter Classes (snake_case interface methods)
# ============================================================================

class JupyterLabelAdapter(ILabel):
    """Jupyter Label adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterLabel):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.getText())

    # IVisibilityCapable
    def show(self):
        self._native.show()

    def hide(self):
        self._native.hide()

    def is_visible(self) -> bool:
        return self._native.isVisible()

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)



class JupyterButtonAdapter(IButton):
    """Jupyter Button adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterPushButton):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.getText())

    # IEventCapable
    def connect(self, callback: Callable[[], None]):
        self._native.connect(callback)

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
    def on_change(self, callback: Callable[[], None]):
        self._native.textChanged(lambda change: callback())

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



class JupyterTextAreaAdapter(ITextArea):
    """Jupyter TextArea adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterTextarea):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(text)

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
    def on_change(self, callback: Callable[[], None]):
        self._native.observe(lambda change: callback(), 'value')

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)


class JupyterComboBoxAdapter(IComboBox):
    """Jupyter ComboBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterComboBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ISelectionCapable
    def add_item(self, item: str):
        self._native.addItem(item)

    def clear(self):
        self._native.clear()

    def set_selection(self, item: str):
        self._native.setSelection(item)

    def get_text(self) -> str:
        return self._native.currentText()

    # IChangeEventCapable
    def on_change(self, callback: Callable[[], None]):
        self._native.connect(callback)

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


class JupyterDropdownAdapter(IDropdown):
    """Jupyter Dropdown adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterDropdown):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ISelectionCapable
    def add_item(self, item: str):
        self._native.addItem(item)

    def clear(self):
        self._native.clear()

    def set_selection(self, item: str):
        self._native.setSelection(item)

    def get_text(self) -> str:
        return self._native.currentText()

    # IValueCapable
    def set_value(self, value_list: list):
        """Set dropdown items from a list."""
        self._native.setValue(value_list)

    # IChangeEventCapable
    def on_change(self, callback: Callable[[], None]):
        self._native.connect(callback)

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



class JupyterVBoxAdapter(IVBoxLayout):
    """Jupyter VBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterVBoxLayout):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        self._native.addItem(widget.get_native())

    def add_stretch(self):
        self._native.addStretch()

    def set_alignment_top(self):
        self._native.setAlignmentTop()


class JupyterHBoxAdapter(IHBoxLayout):
    """Jupyter HBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterHBoxLayout):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        self._native.addItem(widget.get_native())

    def add_stretch(self):
        self._native.addStretch()

    def set_alignment_top(self):
        self._native.setAlignmentTop()


class JupyterGroupBoxAdapter(IGroupBox):
    """Jupyter GroupBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterGroupBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITitleCapable
    def set_title(self, title: str):
        self._native.setTitle(title)

    # IContainerCapable
    def set_layout(self, layout):
        if hasattr(layout, 'get_native'):
            self._native.setLayout(layout.get_native())
        else:
            self._native.setLayout(layout)


class JupyterTabWidgetAdapter(ITabWidget):
    """Jupyter TabWidget adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterTabWidget):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITabCapable
    def add_tab(self, widget: IWidget, name: str):
        self._native.addTab(widget.get_native(), name)

    def remove_tabs(self):
        self._native.removeTabs()

    def get_current_index(self) -> int:
        return self._native.currentIndex()

    # IVisibilityCapable
    def show(self):
        self._native.show()

    def hide(self):
        self._native.hide()

    def is_visible(self) -> bool:
        return self._native.isVisible()


class JupyterImageAdapter(IImage):
    """Jupyter Image adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterImage):
        self._native = native_widget

    def get_native(self):
        return self._native

    # IImageCapable
    def set_image(self, path: str):
        self._native.setImage(path)

    def set_image_from_url(self, url: str):
        self._native.setImageFromUrl(url)

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)



# ============================================================================
# Jupyter Widget Factory
# ============================================================================

class JupyterWidgetFactory(IWidgetFactory):
    """
    Jupyter Widget Factory

    Creates native Jupyter widgets and wraps them in adapters
    """

    def createLabel(self) -> ILabel:
        native = JupyterLabel()
        return JupyterLabelAdapter(native)

    def createButton(self) -> IButton:
        native = JupyterPushButton()
        return JupyterButtonAdapter(native)

    def createLineEdit(self) -> ILineEdit:
        native = JupyterLineEdit()
        return JupyterLineEditAdapter(native)

    def createTextArea(self) -> ITextArea:
        native = JupyterTextarea()
        return JupyterTextAreaAdapter(native)

    def createComboBox(self) -> IComboBox:
        native = JupyterComboBox()
        return JupyterComboBoxAdapter(native)

    def createDropdown(self) -> IDropdown:
        native = JupyterDropdown()
        return JupyterDropdownAdapter(native)

    def createVBox(self) -> IVBoxLayout:
        native = JupyterVBoxLayout()
        return JupyterVBoxAdapter(native)

    def createHBox(self) -> IHBoxLayout:
        native = JupyterHBoxLayout()
        return JupyterHBoxAdapter(native)

    def createTabWidget(self) -> ITabWidget:
        native = JupyterTabWidget()
        return JupyterTabWidgetAdapter(native)

    def createImage(self) -> IImage:
        native = JupyterImage()
        return JupyterImageAdapter(native)

    def createGroupBox(self) -> IGroupBox:
        native = JupyterGroupBox()
        return JupyterGroupBoxAdapter(native)
