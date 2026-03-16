"""
Core types and interfaces - Simplified.

Defines:
- Widget interfaces: ILabel, IButton, ILineEdit, etc.
- IWidgetFactory: abstract factory that each platform (Qt/wx/Tk/Jupyter) implements
- Exception classes: NotSupportedError, WidgetCreationError, etc.

This is the only module that platform implementations depend on.
"""
from abc import ABC, abstractmethod
from typing import Callable, Any, Optional


# ============================================================================
# Exception Classes
# ============================================================================


# ============================================================================
# Exception Classes
# ============================================================================

class UniUIException(Exception):
    """Base exception for all UniUI errors"""
    pass


class NotSupportedError(UniUIException):
    """Raised when a widget type is not supported on a specific platform."""
    pass


class WidgetCreationError(UniUIException):
    """Raised when widget creation fails."""
    pass


class InvalidValueError(UniUIException):
    """Raised when a value cannot be parsed or is invalid"""
    pass


class ConfigurationError(UniUIException):
    """Raised when there's a configuration problem"""
    pass




# ============================================================================
# Widget Interfaces
# ============================================================================

class IWidget(ABC):
    """Base interface for all widgets"""

    @abstractmethod
    def get_native(self):
        """Get the underlying native widget"""
        pass


class ILabel(IWidget):
    """Label widget interface"""

    @abstractmethod
    def set_text(self, text: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def hide(self) -> None:
        pass

    @abstractmethod
    def set_fixed_width(self, width: int) -> None:
        pass


class IButton(IWidget):
    """Button widget interface"""

    @abstractmethod
    def set_text(self, text: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def connect(self, callback: Callable[[], None]) -> None:
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        pass


class ILineEdit(IWidget):
    """Line edit widget interface"""

    @abstractmethod
    def set_text(self, text: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def set_value(self, value: Any) -> None:
        pass

    @abstractmethod
    def get_value(self) -> Any:
        pass

    @abstractmethod
    def on_change(self, callback: Callable[[], None]) -> None:
        pass

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        pass

    @abstractmethod
    def set_fixed_width(self, width: int) -> None:
        pass


class ITextArea(IWidget):
    """Text area widget interface"""

    @abstractmethod
    def set_text(self, text: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def append(self, text: str) -> None:
        pass

    @abstractmethod
    def on_change(self, callback: Callable[[], None]) -> None:
        pass

    @abstractmethod
    def set_maximum_height(self, height: int) -> None:
        pass


class IComboBox(IWidget):
    """Combo box widget interface"""

    @abstractmethod
    def add_item(self, item: str) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def on_change(self, callback: Callable[[], None]) -> None:
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        pass


class IDropdown(IWidget):
    """Dropdown widget interface"""

    @abstractmethod
    def add_item(self, item: str) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def set_selection(self, item: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def on_change(self, callback: Callable[[], None]) -> None:
        pass

    @abstractmethod
    def show(self) -> None:
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        pass


class IVBoxLayout(IWidget):
    """Vertical box layout interface"""

    @abstractmethod
    def add_item(self, widget: IWidget) -> None:
        pass

    @abstractmethod
    def add_stretch(self) -> None:
        pass

    @abstractmethod
    def set_alignment_top(self) -> None:
        pass


class IHBoxLayout(IWidget):
    """Horizontal box layout interface"""

    @abstractmethod
    def add_item(self, widget: IWidget) -> None:
        pass

    @abstractmethod
    def add_stretch(self) -> None:
        pass


class ITabWidget(IWidget):
    """Tab widget interface"""

    @abstractmethod
    def add_tab(self, widget: IWidget, name: str) -> None:
        pass

    @abstractmethod
    def remove_tabs(self) -> None:
        pass

    @abstractmethod
    def get_current_index(self) -> int:
        pass

    @abstractmethod
    def show(self) -> None:
        pass


class IGroupBox(IWidget):
    """Group box interface"""

    @abstractmethod
    def set_layout(self, layout: IWidget) -> None:
        pass

    @abstractmethod
    def set_title(self, title: str) -> None:
        pass


class IImage(IWidget):
    """Image widget interface"""

    @abstractmethod
    def set_image(self, path: str) -> None:
        pass

    @abstractmethod
    def set_image_from_url(self, url: str) -> None:
        pass

    @abstractmethod
    def set_fixed_width(self, width: int) -> None:
        pass




# ============================================================================
# Factory Interface
# ============================================================================

class IWidgetFactory(ABC):
    """Widget factory interface"""

    @abstractmethod
    def createLabel(self) -> ILabel:
        pass

    @abstractmethod
    def createButton(self) -> IButton:
        pass

    @abstractmethod
    def createLineEdit(self) -> ILineEdit:
        pass

    @abstractmethod
    def createTextArea(self) -> ITextArea:
        pass

    @abstractmethod
    def createComboBox(self) -> IComboBox:
        pass

    @abstractmethod
    def createDropdown(self) -> IDropdown:
        pass

    @abstractmethod
    def createVBox(self) -> IVBoxLayout:
        pass

    @abstractmethod
    def createHBox(self) -> IHBoxLayout:
        pass

    @abstractmethod
    def createTabWidget(self) -> ITabWidget:
        pass

    @abstractmethod
    def createImage(self) -> IImage:
        pass

    def createGroupBox(self) -> IGroupBox:
        """Create group box widget (optional, not all platforms support this)"""
        raise NotSupportedError("GroupBox not supported on this platform")

