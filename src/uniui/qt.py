"""
Qt/PySide2 backend.

Native widgets, adapters, and factory for the Qt platform.
Each widget class wraps a PySide2 widget and exposes the IWidget interface.
"""
from __future__ import annotations
from typing import List, Optional, Callable
from urllib.request import urlopen
import socket

# Import capability interfaces from core
from .core import *
from .strategies import normalize_text, parse_float

# Qt imports
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import (
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QVBoxLayout, QHBoxLayout, QWidget,
    QTabWidget, QGroupBox
)
from PySide2.QtCore import Qt


# ============================================================================
# Helper Functions
# ============================================================================

def has_method(o, name):
    """Check if object has a callable method"""
    return callable(getattr(o, name, None))


def convert_control_text(text):
    """Convert control text to appropriate type"""
    try:
        return float(text)
    except ValueError:
        return text


def check_connection():
    """Check if internet connection is available"""
    try:
        host = socket.gethostbyname('www.google.com')
        s = socket.create_connection((host, 80), 2)
        return True
    except:
        return False


# ============================================================================
# Native Widget Classes (camelCase methods from widgets/qt_widgets.py)
# ============================================================================

class QTComboBox(QtWidgets.QComboBox):
    """Qt ComboBox Widget - native implementation"""
    def __init__(self):
        super().__init__()
        super().setEditable(True)

    def addItem(self, item):
        super().addItem(item)

    def connect(self, function):
        QtCore.QObject.connect(
            self, QtCore.SIGNAL("currentIndexChanged(QString)"),
            function)

    def deleteItem(self, item):
        index = super().findText(item, QtCore.Qt.MatchFixedString)
        super().removeItem(index)
        if super().count() > 0:
            super().setCurrentIndex(0)

    def setSelection(self, item):
        index = super().findText(item, QtCore.Qt.MatchFixedString)
        if index >= 0:
            super().setCurrentIndex(index)

    def sort(self):
        super().model().sort(0)

    def currentText(self):
        return super().currentText()

    def clear(self):
        super().clear()


class QTDropdown(QtWidgets.QComboBox):
    """Qt Dropdown Widget - native implementation (read-only)"""
    def __init__(self):
        super().__init__()
        super().setEditable(False)

    def addItem(self, item):
        super().addItem(item)

    def connect(self, function):
        QtCore.QObject.connect(
            self, QtCore.SIGNAL("currentIndexChanged(QString)"),
            function)

    def deleteItem(self, item):
        index = super().findText(item, QtCore.Qt.MatchFixedString)
        super().removeItem(index)

    def getItems(self):
        items = []
        for i in range(super().count()):
            items.append(super().itemText(i))
        return items

    def setSelection(self, item):
        index = super().findText(item, QtCore.Qt.MatchFixedString)
        if index >= 0:
            super().setCurrentIndex(index)

    def setValue(self, value_list):
        if len(value_list) > 0:
            self.blockSignals(True)
            self.clear()
            for each in value_list:
                self.addItem(each)
            self.setSelection(value_list[0])
            self.blockSignals(False)

    def sort(self):
        super().model().sort(0)

    def currentText(self):
        return super().currentText()

    def clear(self):
        super().clear()

    def hide(self):
        super().hide()

    def show(self):
        super().show()


class QTVBoxLayout(QtWidgets.QVBoxLayout):
    """Qt Vertical Box Layout - native implementation"""
    def __init__(self):
        super().__init__()

    def setAlignmentTop(self):
        super().setAlignment(QtCore.Qt.AlignTop)

    def addItem(self, item):
        if has_method(item, "addLayout"):
            super().addLayout(item)
        else:
            super().addWidget(item)

    def addStretch(self):
        super().addStretch()


class QTHBoxLayout(QtWidgets.QHBoxLayout):
    """Qt Horizontal Box Layout - native implementation"""
    def __init__(self):
        super().__init__()

    def setAlignmentTop(self):
        super().setAlignment(QtCore.Qt.AlignTop)

    def addItem(self, item):
        if has_method(item, "addLayout"):
            super().addLayout(item)
        else:
            super().addWidget(item)

    def addStretch(self):
        super().addStretch()


class QTPushButton(QtWidgets.QPushButton):
    """Qt Push Button Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def setText(self, text):
        super().setText(text)

    def connect(self, function):
        QtCore.QObject.connect(
            self, QtCore.SIGNAL("pressed()"), function)

    def getText(self):
        return super().text()


class QTTabWidget(QtWidgets.QTabWidget):
    """Qt Tab Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def addTab(self, item, tab_name):
        if has_method(item, "addLayout"):
            w = QtWidgets.QWidget()
            w.setLayout(item)
            super().addTab(w, tab_name)
        else:
            super().addTab(item, tab_name)

    def removeTabs(self):
        while True:
            count = super().count()
            if count > 0:
                super().removeTab(count - 1)
            else:
                break

    def currentIndex(self):
        return super().currentIndex()

    def hide(self):
        super().hide()

    def show(self):
        super().show()


class QTLabel(QtWidgets.QLabel):
    """Qt Label Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def setText(self, text):
        super().setText(text)

    def getText(self):
        return super().text()

    def setTextColor(self, text_color, background):
        color_string = 'color: ' + text_color + ';  background-color: ' + background
        super().setStyleSheet(color_string)

    def setFixedWidth(self, width):
        super().setFixedWidth(width)

    def hide(self):
        super().hide()

    def show(self):
        super().show()


class QTTextarea(QtWidgets.QTextEdit):
    """Qt Text Area Widget - native implementation"""
    def __init__(self):
        super().__init__()
        super().setReadOnly(True)

    def setText(self, text):
        super().setPlainText(text)

    def getText(self):
        return super().toPlainText()

    def append(self, text):
        super().append(text)

    def clear(self):
        super().clear()

    def setMaximumHeight(self, height):
        super().setMaximumHeight(height)


class QTImage(QtWidgets.QLabel):
    """Qt Image Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def setImage(self, source):
        """Set image from binary data or file path"""
        if isinstance(source, bytes):
            image = QtGui.QImage()
            image.loadFromData(source, 'PNG')
            self.setPixmap(QtGui.QPixmap.fromImage(image))
        else:
            # Assume it's a file path
            pixmap = QtGui.QPixmap(source)
            super().setPixmap(pixmap)
        self.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

    def setImageFromUrl(self, url_str):
        has_internet = check_connection()

        if has_internet:
            url = urlopen(url_str)
            data = url.read()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            super().setPixmap(pixmap)

    def setFixedWidth(self, width):
        super().setFixedWidth(width)


class QTLineEdit(QtWidgets.QLineEdit):
    """Qt Line Edit Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def getText(self):
        return super().text()

    def getValue(self):
        if super().text() == "":
            return 0.0
        else:
            return convert_control_text(super().text())

    def finishEditing(self, function):
        super().editingFinished.connect(function)

    def setText(self, text):
        super().setText(text)

    def setValue(self, value):
        super().setText(str(value))

    def setTextColor(self, text_color, background):
        color_string = 'color: ' + text_color + ';  background-color: ' + background
        super().setStyleSheet(color_string)

    def textChanged(self, function):
        super().textChanged.connect(function)

    def setFixedWidth(self, width):
        super().setFixedWidth(width)

    def hide(self):
        super().hide()

    def show(self):
        super().show()

    def setEnabled(self, flag):
        super().setEnabled(flag)


class QTGroupBox(QtWidgets.QGroupBox):
    """Qt Group Box Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def setTitle(self, title):
        super().setTitle(title)

    def setLayout(self, layout):
        super().setLayout(layout)


# ============================================================================
# Adapter Classes (snake_case interface methods)
# ============================================================================

class QtLabelAdapter(ILabel):
    """Qt Label adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTLabel):
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



class QtButtonAdapter(IButton):
    """Qt Button adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTPushButton):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.getText())

    # IEventCapable
    def connect(self, callback):
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



class QtLineEditAdapter(ILineEdit):
    """Qt LineEdit adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTLineEdit):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(text)

    def get_text(self) -> str:
        return self._native.getText()

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
    def on_change(self, callback):
        self._native.textChanged(lambda: callback())

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



class QtTextAreaAdapter(ITextArea):
    """Qt TextArea adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTTextarea):
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
    def on_change(self, callback):
        self._native.textChanged.connect(callback)

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)



class QtComboBoxAdapter(IComboBox):
    """Qt ComboBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTComboBox):
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
    def on_change(self, callback):
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



class QtDropdownAdapter(IDropdown):
    """Qt Dropdown adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTDropdown):
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
    def on_change(self, callback):
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



class QtVBoxAdapter(IVBoxLayout):
    """Qt VBox adapter - implements snake_case interface convention"""

    def __init__(self, native_layout: QTVBoxLayout):
        self._native = native_layout

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        self._native.addItem(widget.get_native())

    def add_stretch(self):
        self._native.addStretch()

    def set_alignment_top(self):
        self._native.setAlignmentTop()



class QtHBoxAdapter(IHBoxLayout):
    """Qt HBox adapter - implements snake_case interface convention"""

    def __init__(self, native_layout: QTHBoxLayout):
        self._native = native_layout

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        self._native.addItem(widget.get_native())

    def add_stretch(self):
        self._native.addStretch()

    def set_alignment_top(self):
        self._native.setAlignmentTop()



class QtTabWidgetAdapter(ITabWidget):
    """Qt TabWidget adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTTabWidget):
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



class QtImageAdapter(IImage):
    """Qt Image adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTImage):
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



class QtGroupBoxAdapter(IGroupBox):
    """Qt GroupBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTGroupBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # IContainerCapable
    def set_layout(self, layout: IWidget):
        self._native.setLayout(layout.get_native())

    # ITitleCapable
    def set_title(self, title: str):
        self._native.setTitle(title)



# ============================================================================
# Qt Widget Factory
# ============================================================================

class QtWidgetFactory(IWidgetFactory):
    """
    Qt Widget 工厂

    职责：创建 Qt 适配器实例
    设计模式：抽象工厂模式
    """

    def __init__(self):
        """初始化工厂，确保 QApplication 存在"""
        from PySide2.QtWidgets import QApplication
        import sys

        # 确保 QApplication 已创建
        app = QApplication.instance()
        if app is None:
            self.app = QApplication(sys.argv)
        else:
            self.app = app

    def createLabel(self) -> ILabel:
        native = QTLabel()
        return QtLabelAdapter(native)

    def createButton(self) -> IButton:
        native = QTPushButton()
        return QtButtonAdapter(native)

    def createLineEdit(self) -> ILineEdit:
        native = QTLineEdit()
        return QtLineEditAdapter(native)

    def createTextArea(self) -> ITextArea:
        native = QTTextarea()
        return QtTextAreaAdapter(native)

    def createComboBox(self) -> IComboBox:
        native = QTComboBox()
        return QtComboBoxAdapter(native)

    def createDropdown(self) -> IDropdown:
        native = QTDropdown()
        return QtDropdownAdapter(native)

    def createVBox(self) -> IVBoxLayout:
        native = QTVBoxLayout()
        return QtVBoxAdapter(native)

    def createHBox(self) -> IHBoxLayout:
        native = QTHBoxLayout()
        return QtHBoxAdapter(native)

    def createTabWidget(self) -> ITabWidget:
        native = QTTabWidget()
        return QtTabWidgetAdapter(native)

    def createImage(self) -> IImage:
        native = QTImage()
        return QtImageAdapter(native)

    def createGroupBox(self) -> IGroupBox:
        native = QTGroupBox()
        return QtGroupBoxAdapter(native)
