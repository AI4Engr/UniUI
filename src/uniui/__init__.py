"""
UniUI - Universal UI Framework
Write once, run anywhere (Qt, Web, and Jupyter)

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
from .display import show_ui, refresh_theme, schedule_after

from typing import Optional
import sys


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
        kernel = getattr(ip, "kernel", None)
        if ip is not None and callable(getattr(kernel, "comm_info", None)):
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

    web_module = sys.modules.get("uniui.web")
    if web_module is not None:
        web_module.set_backend_active(framework == "web")

    if framework == 'qt':
        from .qt import QtWidgetFactory
        return QtWidgetFactory()
    elif framework == 'jupyter':
        from .jupyter import JupyterWidgetFactory
        return JupyterWidgetFactory()
    elif framework == 'web':
        try:
            from .web import NiceGUIWidgetFactory
        except ImportError as exc:
            raise ImportError(
                "The Web backend requires NiceGUI. Install it with "
                "'pip install -e .[web]'."
            ) from exc
        return NiceGUIWidgetFactory()
    elif framework == 'wx':
        import warnings
        warnings.warn(
            "The wxPython backend ('wx') is legacy and no longer supported. "
            "No new features will be developed. Please migrate to 'qt' or 'jupyter'.",
            DeprecationWarning,
            stacklevel=2
        )
        from .wx import WxWidgetFactory
        return WxWidgetFactory()
    elif framework == 'tk':
        import warnings
        warnings.warn(
            "The Tkinter backend ('tk') is legacy and no longer supported. "
            "No new features will be developed. Please migrate to 'qt' or 'jupyter'.",
            DeprecationWarning,
            stacklevel=2
        )
        from .tk import TkWidgetFactory
        return TkWidgetFactory()
    else:
        raise ValueError(f"Unsupported framework: {framework}")


# create_factory is the public name; _create_factory is the internal implementation
create_factory = _create_factory

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

    _KIND_MAP = {
        'label':      'create_label',
        'button':     'create_button',
        'line_edit':  'create_line_edit',
        'text_area':  'create_text_area',
        'combo_box':  'create_combo_box',
        'dropdown':   'create_dropdown',
        'vbox':       'create_vbox',
        'hbox':       'create_hbox',
        'tab_widget': 'create_tab_widget',
        'group_box':  'create_group_box',
        'image':      'create_image',
    }

    def __init__(self, framework: str = 'auto'):
        self._framework = framework
        self._factory = _create_factory(framework)

    @property
    def framework(self) -> str:
        return self._framework

    def create(self, kind: str) -> IWidget:
        """Create a widget by kind string"""
        method = self._KIND_MAP.get(kind)
        if method is None:
            raise ValueError(f"Unknown widget kind: {kind}")
        return getattr(self._factory, method)()

    def label(self) -> ILabel:        return self._factory.create_label()
    def button(self) -> IButton:      return self._factory.create_button()
    def line_edit(self) -> ILineEdit: return self._factory.create_line_edit()
    def text_area(self) -> ITextArea: return self._factory.create_text_area()
    def combo_box(self) -> IComboBox: return self._factory.create_combo_box()
    def dropdown(self) -> IDropdown:  return self._factory.create_dropdown()
    def vbox(self) -> IVBoxLayout:    return self._factory.create_vbox()
    def hbox(self) -> IHBoxLayout:    return self._factory.create_hbox()
    def tab_widget(self) -> ITabWidget: return self._factory.create_tab_widget()
    def group_box(self) -> IGroupBox: return self._factory.create_group_box()
    def image(self) -> IImage:        return self._factory.create_image()


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
    'schedule_after',
]

__version__ = '0.6.0'
