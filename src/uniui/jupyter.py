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

    def setSpec(self, spec):
        self.layout.gap = f"{spec.gap}px" if spec.gap else None
        p = f"{spec.padding}px" if spec.padding else None
        self.layout.padding = p

    def clear(self):
        self.children = ()


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

    def addItem(self, item, grow=0):
        if hasattr(item, 'layout'):
            if grow > 0:
                item.layout.flex = f"{grow} 1 auto"
            else:
                # Don't force flex=1; let items size to content by default
                item.layout.flex = None
                if not item.layout.width:
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
        self.layout.align_items = 'flex-start'

    def setSpec(self, spec):
        self.layout.gap = f"{spec.gap}px" if spec.gap else None
        p = f"{spec.padding}px" if spec.padding else None
        self.layout.padding = p

    def clear(self):
        self.children = ()


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
# Jupyter Advanced Layout Native Classes
# ============================================================================

class JupyterGrid(widgets.GridBox):
    """Jupyter Grid layout using CSS Grid via GridBox."""
    def __init__(self, columns: int = 12):
        super().__init__()
        self._columns = columns
        self.layout.grid_template_columns = f"repeat({columns}, 1fr)"
        self.layout.width = "100%"

    def setColumns(self, count: int):
        self._columns = count
        self.layout.grid_template_columns = f"repeat({count}, 1fr)"

    def addItem(self, item, col_span: int = 1):
        if hasattr(item, 'layout') and col_span > 1:
            item.layout.grid_column = f"span {col_span}"
        old = list(self.children)
        old.append(item)
        self.children = tuple(old)

    def setSpec(self, spec):
        if spec.gap:
            self.layout.gap = f"{spec.gap}px"
        if spec.padding:
            p = f"{spec.padding}px"
            self.layout.padding = p

    def clear(self):
        self.children = ()


class JupyterWrap(widgets.Box):
    """Jupyter Wrap layout — flex-flow: row wrap."""
    def __init__(self):
        super().__init__(layout=widgets.Layout(
            display='flex',
            flex_flow='row wrap',
            width='100%',
        ))

    def addItem(self, item):
        old = list(self.children)
        old.append(item)
        self.children = tuple(old)

    def setSpec(self, spec):
        if spec.gap:
            self.layout.gap = f"{spec.gap}px"
        if spec.padding:
            self.layout.padding = f"{spec.padding}px"

    def clear(self):
        self.children = ()


class JupyterScrollView(widgets.Box):
    """Jupyter ScrollView — overflow-y: auto."""
    def __init__(self):
        super().__init__(layout=widgets.Layout(
            overflow_y='auto',
            width='100%',
        ))

    def setContent(self, item):
        self.children = (item,)

    def setMaxHeight(self, height: int):
        self.layout.max_height = f"{height}px"
        self.layout.overflow_y = 'auto'

    def setMaxWidth(self, width: int):
        self.layout.max_width = f"{width}px"


class JupyterSplitPane(widgets.Box):
    """Jupyter SplitPane — two panels side by side (no drag handle).

    Uses flexbox with fixed percentage widths to simulate a split pane.
    True drag-to-resize is not supported in Jupyter.
    """
    def __init__(self, orientation: str = "horizontal"):
        self._orientation = orientation
        flex_flow = 'row' if orientation == 'horizontal' else 'column'
        super().__init__(layout=widgets.Layout(
            display='flex',
            flex_flow=flex_flow,
            width='100%',
        ))
        self._first: Optional[widgets.Widget] = None
        self._second: Optional[widgets.Widget] = None
        self._ratio = 0.5

    def setFirst(self, item):
        self._first = item
        if hasattr(item, 'layout'):
            item.layout.flex = f"{self._ratio} 0 auto"
        self._sync()

    def setSecond(self, item):
        self._second = item
        if hasattr(item, 'layout'):
            item.layout.flex = f"{1 - self._ratio} 0 auto"
        self._sync()

    def setOrientation(self, orientation: str):
        self._orientation = orientation
        self.layout.flex_flow = 'row' if orientation == 'horizontal' else 'column'

    def setSizes(self, ratio: float):
        self._ratio = max(0.0, min(1.0, ratio))
        if self._first and hasattr(self._first, 'layout'):
            self._first.layout.flex = f"{self._ratio} 0 auto"
        if self._second and hasattr(self._second, 'layout'):
            self._second.layout.flex = f"{1 - self._ratio} 0 auto"

    def _sync(self):
        children = []
        if self._first is not None:
            children.append(self._first)
        if self._second is not None:
            children.append(self._second)
        self.children = tuple(children)


class JupyterOverlay(widgets.Stack):
    """Jupyter Overlay using ipywidgets Stack (ipywidgets >= 8.0).

    Falls back to VBox with manual show/hide for older versions.
    """
    def __init__(self):
        try:
            super().__init__()
            self._use_stack = True
        except Exception:
            # ipywidgets < 8 has no Stack
            widgets.VBox.__init__(self)
            self._use_stack = False
            self._layers: List = []
            self._active = 0

    def addLayer(self, item):
        if self._use_stack:
            old = list(self.children)
            old.append(item)
            self.children = tuple(old)
        else:
            self._layers.append(item)
            self._apply_visibility()

    def setActiveIndex(self, index: int):
        if self._use_stack:
            self.selected_index = index
        else:
            self._active = index
            self._apply_visibility()

    def _apply_visibility(self):
        for i, layer in enumerate(self._layers):
            if hasattr(layer, 'layout'):
                layer.layout.display = None if i == self._active else 'none'
        self.children = tuple(self._layers)


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

    def set_html(self, html: str):
        from .theme import THEME as T
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

    def add_item_with_spec(self, widget: IWidget, item):
        self._native.addItem(widget.get_native())

    def set_spec(self, spec):
        self._native.setSpec(spec)

    def clear(self):
        self._native.clear()


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

    def add_item_with_spec(self, widget: IWidget, item):
        self._native.addItem(widget.get_native(), grow=item.grow)

    def set_spec(self, spec):
        self._native.setSpec(spec)

    def clear(self):
        self._native.clear()


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
# Jupyter Advanced Layout Adapter Classes
# ============================================================================

class JupyterGridAdapter(IGrid):
    """Jupyter Grid adapter."""

    def __init__(self, columns: int = 12):
        self._native = JupyterGrid(columns)

    def get_native(self):
        return self._native

    def add_item(self, widget: IWidget, row: int = -1, col: int = -1,
                 row_span: int = 1, col_span: int = 1) -> None:
        self._native.addItem(widget.get_native(), col_span=col_span)

    def set_columns(self, count: int) -> None:
        self._native.setColumns(count)

    def set_spec(self, spec) -> None:
        self._native.setSpec(spec)

    def clear(self) -> None:
        self._native.clear()


class JupyterWrapAdapter(IWrap):
    """Jupyter Wrap adapter."""

    def __init__(self):
        self._native = JupyterWrap()

    def get_native(self):
        return self._native

    def add_item(self, widget: IWidget) -> None:
        self._native.addItem(widget.get_native())

    def set_spec(self, spec) -> None:
        self._native.setSpec(spec)

    def clear(self) -> None:
        self._native.clear()


class JupyterScrollViewAdapter(IScrollView):
    """Jupyter ScrollView adapter."""

    def __init__(self):
        self._native = JupyterScrollView()

    def get_native(self):
        return self._native

    def set_content(self, widget: IWidget) -> None:
        self._native.setContent(widget.get_native())

    def set_max_height(self, height: int) -> None:
        self._native.setMaxHeight(height)

    def set_max_width(self, width: int) -> None:
        self._native.setMaxWidth(width)


class JupyterSplitPaneAdapter(ISplitPane):
    """Jupyter SplitPane adapter."""

    def __init__(self, orientation: str = "horizontal"):
        self._native = JupyterSplitPane(orientation)

    def get_native(self):
        return self._native

    def set_first(self, widget: IWidget) -> None:
        self._native.setFirst(widget.get_native())

    def set_second(self, widget: IWidget) -> None:
        self._native.setSecond(widget.get_native())

    def set_orientation(self, orientation: str) -> None:
        self._native.setOrientation(orientation)

    def set_sizes(self, ratio: float) -> None:
        self._native.setSizes(ratio)


class JupyterOverlayAdapter(IOverlay):
    """Jupyter Overlay adapter."""

    def __init__(self):
        self._native = JupyterOverlay()

    def get_native(self):
        return self._native

    def add_layer(self, widget: IWidget) -> None:
        self._native.addLayer(widget.get_native())

    def set_active_index(self, index: int) -> None:
        self._native.setActiveIndex(index)



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

    def createGrid(self, columns: int = 12) -> IGrid:
        return JupyterGridAdapter(columns)

    def createWrap(self) -> IWrap:
        return JupyterWrapAdapter()

    def createScrollView(self) -> IScrollView:
        return JupyterScrollViewAdapter()

    def createSplitPane(self, orientation: str = "horizontal") -> ISplitPane:
        return JupyterSplitPaneAdapter(orientation)

    def createOverlay(self) -> IOverlay:
        return JupyterOverlayAdapter()
