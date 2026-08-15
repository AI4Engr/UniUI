"""Input primitives: buttons, text entry, and selection controls."""
from __future__ import annotations

from typing import Callable, List, Optional

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSplitter, QStackedWidget, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget,
)

from ....core import *
from ...._adapter_mixins import (
    ClearMixin, EnableMixin, NativeMixin, SelectionMixin, SizeMixin, TextMixin,
    VisibilityMixin,
)
from ....strategies import normalize_text, parse_float
from .helpers import convert_control_text


class QTComboBox(QtWidgets.QComboBox):
    """Qt ComboBox Widget - native implementation"""
    def __init__(self):
        super().__init__()
        super().setEditable(True)
        # The popup can't reliably inherit the app-wide stylesheet once any
        # ancestor (every Admin component sets one) has a local stylesheet
        # of its own -- see the comment on apply_combo_popup_style.
        from .styles import apply_combo_popup_style
        apply_combo_popup_style(self)

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
        # See the matching comment on QTComboBox.__init__.
        from .styles import apply_combo_popup_style
        apply_combo_popup_style(self)

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
class QtButtonAdapter(NativeMixin, TextMixin, EnableMixin, SizeMixin, IButton):
    """Qt Button adapter - implements snake_case interface convention"""

    # IEventCapable
    def connect(self, callback):
        self._native.connect(callback)
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

    def set_html(self, html: str):
        from ....theme import THEME as T
        full = (
            f'<div style="font-family:Cascadia Code,Consolas,\'Courier New\',monospace;'
            f'font-size:9pt;color:{T["fg"]};background:{T["bg_input"]};white-space:pre">'
            f'{html}</div>'
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
class QtComboBoxAdapter(NativeMixin, SelectionMixin, ClearMixin, EnableMixin,
                        SizeMixin, IComboBox):
    """Qt ComboBox adapter - implements snake_case interface convention"""

    # IChangeEventCapable
    def on_change(self, callback):
        self._native.connect(callback)
class QtDropdownAdapter(NativeMixin, SelectionMixin, ClearMixin, VisibilityMixin,
                       EnableMixin, SizeMixin, IDropdown):
    """Qt Dropdown adapter - implements snake_case interface convention"""

    # IValueCapable
    def set_value(self, value_list: list):
        """Set dropdown items from a list."""
        self._native.setValue(value_list)

    # IChangeEventCapable
    def on_change(self, callback):
        self._native.connect(callback)
