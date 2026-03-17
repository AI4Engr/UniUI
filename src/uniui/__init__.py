"""
UniUI - Universal UI Framework
Write once, run anywhere (Qt, Jupyter, wxPython, Tkinter)

Example:
    >>> from uniui import Label, Button, VBox
    >>> label = Label("Hello World")
    >>> button = Button("Click Me")
    >>> layout = VBox(label, button)
"""

from .core import (
    # Exceptions
    UniUIException,
    NotSupportedError,
    WidgetCreationError,
    InvalidValueError,
    ConfigurationError,

    # Widget interfaces
    IWidget,
    ILabel,
    IButton,
    ILineEdit,
    ITextArea,
    IComboBox,
    IDropdown,
    IVBoxLayout,
    IHBoxLayout,
    ITabWidget,
    IGroupBox,
    IImage,

    # Factory interface
    IWidgetFactory,
)

# Value parsing helpers
from .strategies import parse_float, parse_int, parse_flexible, normalize_text

# Theme configuration
from .theme import THEME, THEME_LIGHT, THEME_DARK, toggle_theme, is_dark

# Display
from .display import show_ui, refresh_theme

from typing import Optional


# ============================================================================
# Backward Compatibility - Widget Constants
# ============================================================================

LABEL = 'label'
BUTTON = 'button'
LINE_EDIT = 'line_edit'
TEXT_AREA = 'text_area'
COMBO_BOX = 'combo_box'
DROPDOWN = 'dropdown'
VBOX = 'vbox'
HBOX = 'hbox'
TAB_WIDGET = 'tab_widget'
GROUP_BOX = 'group_box'
IMAGE = 'image'


# ============================================================================
# Platform Detection and Factory Selection
# ============================================================================

def _detect_framework() -> str:
    """Auto-detect available framework (priority order)"""
    # 1. Detect Jupyter notebook/lab (must have an active kernel with a comm_info
    #    method — plain IPython console and IDE kernels lack this).
    try:
        ip = get_ipython()
        if ip is not None and hasattr(ip, 'kernel'):
            return 'jupyter'
    except NameError:
        pass

    # 2. Detect PySide2/Qt
    try:
        import PySide2
        return 'qt'
    except ImportError:
        pass

    # 3. Detect wxPython
    try:
        import wx
        return 'wx'
    except ImportError:
        pass

    # 4. Detect Tkinter (Python built-in)
    try:
        import tkinter
        return 'tk'
    except ImportError:
        pass

    raise ImportError(
        "No available UI framework found! "
        "Please install PySide2, wxPython, or use Jupyter."
    )


def _create_factory(framework: str = 'auto') -> IWidgetFactory:
    """Create factory for specified framework"""
    if framework == 'auto':
        framework = _detect_framework()

    if framework == 'qt':
        from .qt import QtWidgetFactory
        return QtWidgetFactory()
    elif framework == 'jupyter':
        from .jupyter import JupyterWidgetFactory
        return JupyterWidgetFactory()
    elif framework == 'wx':
        from .wx import WxWidgetFactory
        return WxWidgetFactory()
    elif framework == 'tk':
        from .tk import TkWidgetFactory
        return TkWidgetFactory()
    else:
        raise ValueError(f"Unsupported framework: {framework}")


# Public alias for create_factory
def create_factory(framework: str = 'auto') -> IWidgetFactory:
    """Create factory for specified framework (public API)"""
    return _create_factory(framework)


# Global factory instance
_factory: Optional[IWidgetFactory] = None


def _get_factory() -> IWidgetFactory:
    """Get or create the global factory instance"""
    global _factory
    if _factory is None:
        _factory = _create_factory('auto')
    return _factory


def use(framework: str = 'auto'):
    """Set the UI framework to use"""
    global _factory
    _factory = _create_factory(framework)


def parse_args_ui() -> str:
    """Parse --ui argument from command line. Returns framework name."""
    import sys
    if "--ui" in sys.argv:
        idx = sys.argv.index("--ui")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return "auto"


# ============================================================================
# Direct Widget Creation Functions
# ============================================================================

def Label(text: str = "") -> ILabel:
    """Create a label widget"""
    label = _get_factory().create_label()
    if text:
        label.set_text(text)
    return label


def Button(text: str = "", on_click=None) -> IButton:
    """Create a button widget"""
    button = _get_factory().create_button()
    if text:
        button.set_text(text)
    if on_click:
        button.connect(on_click)
    return button


def LineEdit(text: str = "", on_change=None) -> ILineEdit:
    """Create a line edit widget"""
    line_edit = _get_factory().create_line_edit()
    if text:
        line_edit.set_text(text)
    if on_change:
        line_edit.on_change(on_change)
    return line_edit


def TextArea(text: str = "", on_change=None) -> ITextArea:
    """Create a text area widget"""
    text_area = _get_factory().create_text_area()
    if text:
        text_area.set_text(text)
    if on_change:
        text_area.on_change(on_change)
    return text_area


def ComboBox(items=None, on_change=None) -> IComboBox:
    """Create a combo box widget"""
    combo = _get_factory().create_combo_box()
    if items:
        for item in items:
            combo.add_item(item)
    if on_change:
        combo.on_change(on_change)
    return combo


def Dropdown(items=None, on_change=None) -> IDropdown:
    """Create a dropdown widget"""
    dropdown = _get_factory().create_dropdown()
    if items:
        for item in items:
            dropdown.add_item(item)
    if on_change:
        dropdown.on_change(on_change)
    return dropdown


def VBox(*children) -> IVBoxLayout:
    """Create a vertical box layout"""
    vbox = _get_factory().create_vbox()
    for child in children:
        if child is not None:
            vbox.add_item(child)
    return vbox


def HBox(*children) -> IHBoxLayout:
    """Create a horizontal box layout"""
    hbox = _get_factory().create_hbox()
    for child in children:
        if child is not None:
            hbox.add_item(child)
    return hbox


def TabWidget() -> ITabWidget:
    """Create a tab widget"""
    return _get_factory().create_tab_widget()


def GroupBox(title: str = "", layout=None) -> IGroupBox:
    """Create a group box widget"""
    group = _get_factory().create_group_box()
    if title:
        group.set_title(title)
    if layout:
        group.set_layout(layout)
    return group


def Image(path: str = "") -> IImage:
    """Create an image widget"""
    image = _get_factory().create_image()
    if path:
        image.set_image(path)
    return image


# ============================================================================
# Backward Compatibility - UniUI Class
# ============================================================================

class UniUI:
    """Backward compatible UniUI facade class"""

    def __init__(self, framework: str = 'auto'):
        self._framework = framework
        self._factory = _create_factory(framework)

    @property
    def framework(self) -> str:
        return self._framework

    def create(self, kind: str) -> IWidget:
        """Create a widget by kind string"""
        factory = self._factory
        if kind == LABEL:
            return factory.create_label()
        elif kind == BUTTON:
            return factory.create_button()
        elif kind == LINE_EDIT:
            return factory.create_line_edit()
        elif kind == TEXT_AREA:
            return factory.create_text_area()
        elif kind == COMBO_BOX:
            return factory.create_combo_box()
        elif kind == DROPDOWN:
            return factory.create_dropdown()
        elif kind == VBOX:
            return factory.create_vbox()
        elif kind == HBOX:
            return factory.create_hbox()
        elif kind == TAB_WIDGET:
            return factory.create_tab_widget()
        elif kind == GROUP_BOX:
            return factory.create_group_box()
        elif kind == IMAGE:
            return factory.create_image()
        else:
            raise ValueError(f"Unknown widget kind: {kind}")

    def label(self) -> ILabel:
        return self.create(LABEL)

    def button(self) -> IButton:
        return self.create(BUTTON)

    def line_edit(self) -> ILineEdit:
        return self.create(LINE_EDIT)

    def text_area(self) -> ITextArea:
        return self.create(TEXT_AREA)

    def combo_box(self) -> IComboBox:
        return self.create(COMBO_BOX)

    def dropdown(self) -> IDropdown:
        return self.create(DROPDOWN)

    def vbox(self) -> IVBoxLayout:
        return self.create(VBOX)

    def hbox(self) -> IHBoxLayout:
        return self.create(HBOX)

    def tab_widget(self) -> ITabWidget:
        return self.create(TAB_WIDGET)

    def group_box(self) -> IGroupBox:
        return self.create(GROUP_BOX)

    def image(self) -> IImage:
        return self.create(IMAGE)


__all__ = [
    # Widget creation functions
    'Label',
    'Button',
    'LineEdit',
    'TextArea',
    'ComboBox',
    'Dropdown',
    'VBox',
    'HBox',
    'TabWidget',
    'GroupBox',
    'Image',

    # Backward compatibility
    'UniUI',
    'LABEL', 'BUTTON', 'LINE_EDIT', 'TEXT_AREA',
    'COMBO_BOX', 'DROPDOWN', 'VBOX', 'HBOX', 'TAB_WIDGET', 'GROUP_BOX', 'IMAGE',

    # Framework selection
    'use',
    'create_factory',
    'parse_args_ui',

    # Exceptions
    'UniUIException',
    'NotSupportedError',
    'WidgetCreationError',
    'InvalidValueError',
    'ConfigurationError',

    # Interfaces
    'IWidget',
    'IWidgetFactory',
    'ILabel',
    'IButton',
    'ILineEdit',
    'ITextArea',
    'IComboBox',
    'IDropdown',
    'IVBoxLayout',
    'IHBoxLayout',
    'ITabWidget',
    'IGroupBox',
    'IImage',

    # Parsing helpers
    'parse_float',
    'parse_int',
    'parse_flexible',
    'normalize_text',

    # Theme
    'THEME',
    'THEME_LIGHT',
    'THEME_DARK',
    'toggle_theme',
    'is_dark',

    # Display
    'show_ui',
    'refresh_theme',
]

__version__ = '0.6.0'
