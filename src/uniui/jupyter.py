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
from ._adapter_mixins import (
    ClearMixin, EnableMixin, NativeMixin, SelectionMixin, SizeMixin,
    TextMixin, VisibilityMixin,
)
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

    This used to skip Admin shells, which carried a second, disagreeing
    palette; both now render from uniui.theme, so one pass suits every tree.

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
        # Clearing options resets index to None on its own; assigning 0 here
        # raises "index out of bounds" because there is no option to select.
        self.options = tuple([])

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
        # Clearing children resets selected_index to None on its own; assigning
        # 0 here raises "index out of bounds" because no tab is left to select.
        self.children = []


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
    """Jupyter SplitPane with a browser-side draggable divider.

    Pointer movement stays in the browser.  Only the final ratio is synced to
    Python on pointer-up, so dragging does not flood the notebook kernel.
    """
    def __init__(self, orientation: str = "horizontal"):
        self._orientation = orientation
        flex_flow = 'row' if orientation == 'horizontal' else 'column'
        super().__init__(layout=widgets.Layout(
            display='flex',
            flex_flow=flex_flow,
            width='100%',
        ))
        self.add_class('uniui-split-pane')
        self._first: Optional[widgets.Widget] = None
        self._second: Optional[widgets.Widget] = None
        self._ratio = 0.5
        self._syncing_ratio = False
        self._handle = widgets.HTML()
        self._handle.add_class('uniui-split-handle-widget')
        self._ratio_bridge = widgets.FloatText(value=self._ratio)
        self._ratio_bridge.layout.display = 'none'
        self._ratio_bridge.add_class('uniui-split-ratio-bridge')
        self._ratio_bridge.observe(self._on_ratio_bridge, names='value')
        self._configure_handle()

    def setFirst(self, item):
        self._first = item
        if hasattr(item, 'add_class'):
            item.add_class('uniui-split-first')
        if hasattr(item, 'layout'):
            item.layout.min_width = '0'
        self._sync()
        self._apply_ratio()

    def setSecond(self, item):
        self._second = item
        if hasattr(item, 'add_class'):
            item.add_class('uniui-split-second')
        if hasattr(item, 'layout'):
            item.layout.min_width = '0'
        self._sync()
        self._apply_ratio()

    def setOrientation(self, orientation: str):
        self._orientation = orientation
        self.layout.flex_flow = 'row' if orientation == 'horizontal' else 'column'
        self._configure_handle()
        self._apply_ratio()

    def setSizes(self, ratio: float):
        self._ratio = max(0.0, min(1.0, ratio))
        self._apply_ratio()
        if abs(self._ratio_bridge.value - self._ratio) > 1e-9:
            self._syncing_ratio = True
            self._ratio_bridge.value = self._ratio
            self._syncing_ratio = False

    def _apply_ratio(self):
        percent = self._ratio * 100
        if self._first and hasattr(self._first, 'layout'):
            self._first.layout.flex = f"0 0 {percent:.4f}%"
            if self._orientation == 'horizontal':
                self._first.layout.width = f"{percent:.4f}%"
                self._first.layout.height = None
            else:
                self._first.layout.height = f"{percent:.4f}%"
                self._first.layout.width = '100%'
        if self._second and hasattr(self._second, 'layout'):
            self._second.layout.flex = '1 1 0'
            if self._orientation == 'horizontal':
                self._second.layout.width = 'auto'
                self._second.layout.height = None
            else:
                self._second.layout.height = 'auto'
                self._second.layout.width = '100%'

    def _configure_handle(self):
        horizontal = self._orientation == 'horizontal'
        axis = 'clientX' if horizontal else 'clientY'
        origin = 'left' if horizontal else 'top'
        size = 'width' if horizontal else 'height'
        cursor = 'col-resize' if horizontal else 'row-resize'
        self._handle.layout.width = '6px' if horizontal else '100%'
        self._handle.layout.min_width = '6px' if horizontal else None
        self._handle.layout.height = '100%' if horizontal else '6px'
        self._handle.layout.min_height = None if horizontal else '6px'
        self._handle.layout.flex = '0 0 6px'
        self._handle.value = f"""
<div title="Drag to resize" style="width:100%;height:100%;min-height:6px;
 background:#98a2b3;cursor:{cursor};touch-action:none;border-radius:3px"
 onpointerdown="const h=this,root=h.closest('.uniui-split-pane'),first=root.querySelector('.uniui-split-first'),bridge=root.querySelector('.uniui-split-ratio-bridge input'),rect=root.getBoundingClientRect(),start=rect.{origin},total=rect.{size},pid=event.pointerId;h.setPointerCapture(pid);const move=e=>{{const ratio=Math.max(.05,Math.min(.95,(e.{axis}-start)/total));first.style.flex='0 0 '+(ratio*100)+'%';first.style.{size}=(ratio*100)+'%';return ratio;}};const up=e=>{{const ratio=move(e);if(bridge){{bridge.value=String(ratio);bridge.dispatchEvent(new Event('change',{{bubbles:true}}));}}h.removeEventListener('pointermove',move);}};h.addEventListener('pointermove',move);h.addEventListener('pointerup',up,{{once:true}});h.addEventListener('pointercancel',up,{{once:true}});">
</div>"""

    def _on_ratio_bridge(self, change):
        if not self._syncing_ratio:
            self.setSizes(float(change['new']))

    def _sync(self):
        children = []
        if self._first is not None:
            children.append(self._first)
        children.append(self._handle)
        if self._second is not None:
            children.append(self._second)
        children.append(self._ratio_bridge)
        self.children = tuple(children)


class JupyterOverlay(widgets.VBox):
    """Jupyter Overlay: shows one layer at a time.

    Deliberately built on VBox with manual show/hide rather than
    ipywidgets' Stack. Stack needs @jupyter-widgets/controls 2.x on the
    frontend, and renderers that don't implement StackView (notably the
    VS Code notebook renderer) draw nothing at all — the layers are in
    the model but never painted. VBox + layout.display works on every
    frontend.
    """
    def __init__(self):
        super().__init__()
        # Fill whatever container holds us; ipywidgets' DOM wrappers mean a
        # stylesheet rule cannot reliably reach this element.
        self.layout.width = '100%'
        self.layout.flex = '1 1 auto'
        self._layers: List = []
        self._active = 0

    def addLayer(self, item):
        if hasattr(item, 'layout') and item.layout.width is None:
            item.layout.width = '100%'
        self._layers.append(item)
        self._apply_visibility()

    def setActiveIndex(self, index: int):
        self._active = index
        self._apply_visibility()

    def _apply_visibility(self):
        if not self._layers:
            self.children = ()
            return

        # Keep every page object in _layers so RouterView can preserve page
        # state, but only mount the active page in the widget tree.  Updating
        # layout.display on an already-rendered nested widget is not reliably
        # repainted by every notebook frontend (notably VS Code), which can
        # leave the content area blank after navigation.
        self._active = max(0, min(self._active, len(self._layers) - 1))
        active = self._layers[self._active]
        if hasattr(active, 'layout'):
            active.layout.display = None
        self.children = (active,)


# ============================================================================
# Adapter Classes (snake_case interface methods)
# ============================================================================

class JupyterLabelAdapter(NativeMixin, TextMixin, VisibilityMixin, SizeMixin, ILabel):
    """Jupyter Label adapter - implements snake_case interface convention"""



class JupyterButtonAdapter(NativeMixin, TextMixin, EnableMixin, SizeMixin, IButton):
    """Jupyter Button adapter - implements snake_case interface convention"""

    # IEventCapable
    def connect(self, callback: Callable[[], None]):
        self._native.connect(callback)


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


class JupyterComboBoxAdapter(NativeMixin, SelectionMixin, ClearMixin, EnableMixin,
                             SizeMixin, IComboBox):
    """Jupyter ComboBox adapter - implements snake_case interface convention"""

    # IChangeEventCapable
    def on_change(self, callback: Callable[[], None]):
        self._native.connect(callback)


class JupyterDropdownAdapter(NativeMixin, SelectionMixin, ClearMixin,
                            VisibilityMixin, EnableMixin, SizeMixin, IDropdown):
    """Jupyter Dropdown adapter - implements snake_case interface convention"""

    # IValueCapable
    def set_value(self, value_list: list):
        """Set dropdown items from a list."""
        self._native.setValue(value_list)

    # IChangeEventCapable
    def on_change(self, callback: Callable[[], None]):
        self._native.connect(callback)


class JupyterVBoxAdapter(IVBoxLayout):
    """Jupyter VBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: widgets.VBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        self._native.children = self._native.children + (widget.get_native(),)

    def add_stretch(self):
        pass

    def set_alignment_top(self):
        self._native.layout.justify_content = "flex-start"

    def add_item_with_spec(self, widget: IWidget, item):
        native = widget.get_native()
        if item.grow > 0 and hasattr(native, "layout"):
            native.layout.flex = f"{item.grow} 1 auto"
        self._native.children = self._native.children + (native,)

    def set_spec(self, spec):
        self._native.layout.gap = f"{spec.gap}px" if spec.gap else None
        self._native.layout.padding = f"{spec.padding}px" if spec.padding else None

    def clear(self):
        self._native.children = ()


class JupyterHBoxAdapter(IHBoxLayout):
    """Jupyter HBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: widgets.HBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        native = widget.get_native()
        if hasattr(native, "layout"):
            native.layout.flex = None
            if not native.layout.width:
                native.layout.width = "auto"
        self._native.children = self._native.children + (native,)

    def add_stretch(self):
        spacer = widgets.Box(layout=widgets.Layout(flex="1 1 auto"))
        self._native.children = self._native.children + (spacer,)

    def set_alignment_top(self):
        self._native.layout.align_items = "flex-start"

    def add_item_with_spec(self, widget: IWidget, item):
        native = widget.get_native()
        if hasattr(native, "layout"):
            if item.grow > 0:
                native.layout.flex = f"{item.grow} 1 auto"
            else:
                native.layout.flex = None
                if not native.layout.width:
                    native.layout.width = "auto"
        self._native.children = self._native.children + (native,)

    def set_spec(self, spec):
        self._native.layout.gap = f"{spec.gap}px" if spec.gap else None
        self._native.layout.padding = f"{spec.padding}px" if spec.padding else None

    def clear(self):
        self._native.children = ()


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


class JupyterTabWidgetAdapter(NativeMixin, VisibilityMixin, ITabWidget):
    """Jupyter TabWidget adapter - implements snake_case interface convention"""

    # ITabCapable
    def add_tab(self, widget: IWidget, name: str):
        self._native.addTab(widget.get_native(), name)

    def remove_tabs(self):
        self._native.removeTabs()

    def get_current_index(self) -> int:
        return self._native.currentIndex()


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
    """Jupyter Wrap adapter backed by a stock ipywidgets Box."""

    def __init__(self):
        self._native = widgets.Box(layout=widgets.Layout(
            display="flex", flex_flow="row wrap", width="100%",
        ))

    def get_native(self):
        return self._native

    def add_item(self, widget: IWidget) -> None:
        self._native.children = self._native.children + (widget.get_native(),)

    def set_spec(self, spec) -> None:
        self._native.layout.gap = f"{spec.gap}px" if spec.gap else None
        self._native.layout.padding = f"{spec.padding}px" if spec.padding else None

    def clear(self) -> None:
        self._native.children = ()


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
    """Jupyter Overlay adapter backed by a stock ipywidgets VBox.

    Keeping the routing state in the adapter avoids asking notebook
    frontends to construct a view for a custom Python widget subclass.  Some
    renderers accept the model but leave that view completely blank.
    """

    def __init__(self):
        self._native = widgets.VBox(
            layout=widgets.Layout(width="100%", flex="1 1 auto")
        )
        self._layers: List = []
        self._render_layers: List = []
        self._active = 0
        # Expose diagnostics on the native object for RouterView tests and
        # notebook troubleshooting without making it a custom widget class.
        self._native._layers = self._layers
        self._native._render_layers = self._render_layers
        self._native._active = self._active

    def get_native(self):
        return self._native

    def add_layer(self, widget: IWidget) -> None:
        native = widget.get_native()
        layout = getattr(native, "layout", None)
        if layout is not None and not layout.width:
            layout.width = "100%"
        self._layers.append(native)
        self._render_layers.append(self._make_render_layer(native))
        self._apply_active()

    def set_active_index(self, index: int) -> None:
        self._active = int(index)
        self._apply_active()

    def _apply_active(self) -> None:
        if not self._layers:
            self._native.children = ()
            return
        self._active = max(0, min(self._active, len(self._layers) - 1))
        self._native._active = self._active
        self._native.children = (self._render_layers[self._active],)

    @staticmethod
    def _make_render_layer(native):
        """Create a clean frontend container for composite route pages.

        Some notebook renderers can display every child of a route page but
        fail to construct a view for the original parent widget model.  A new
        stock VBox around the exact same child models renders correctly while
        preserving every input, callback, and cached page state.
        """
        children = getattr(native, "children", None)
        if children is None:
            return native

        source_layout = getattr(native, "layout", None)
        wrapper_layout = widgets.Layout(width="100%", min_width="0")
        gap = getattr(source_layout, "gap", None)
        padding = getattr(source_layout, "padding", None)
        if gap:
            wrapper_layout.grid_gap = gap
        if padding:
            wrapper_layout.padding = padding
        wrapper = widgets.VBox(children=tuple(children), layout=wrapper_layout)

        if hasattr(native, "observe"):
            def sync_children(change, target=wrapper):
                target.children = tuple(change["new"])
            native.observe(sync_children, names="children")
            wrapper._uniui_source_children_observer = sync_children
        return wrapper



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
        native = widgets.VBox()
        return JupyterVBoxAdapter(native)

    def createHBox(self) -> IHBoxLayout:
        native = widgets.HBox(layout=widgets.Layout(
            display="flex", flex_flow="row", width="100%",
        ))
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


def _mark_created_widgets(factory_class) -> None:
    """Tag every widget the factory creates so the base stylesheet reaches it.

    Wrapping the methods in one place keeps new create* methods covered without
    each having to remember the marker class.
    """
    import functools

    for name in [n for n in vars(factory_class) if n.startswith("create")]:
        original = getattr(factory_class, name)

        @functools.wraps(original)
        def marked(self, *args, _original=original, **kwargs):
            widget = _original(self, *args, **kwargs)
            # Imported lazily: jupyter_style -> jupyter_components -> this module.
            from .jupyter_style import mark
            mark(widget)
            return widget

        setattr(factory_class, name, marked)


_mark_created_widgets(JupyterWidgetFactory)
