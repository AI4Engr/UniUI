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
from ....state import Handle, safe_call
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

    def disconnect(self, function):
        QtCore.QObject.disconnect(
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

    def disconnect(self, function):
        QtCore.QObject.disconnect(
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
class QTCheckbox(QtWidgets.QCheckBox):
    """Qt Checkbox Widget - native implementation.

    A trivial subclass (QCheckBox already has the full isChecked/setChecked/
    toggled/isEnabled/setEnabled/show/hide/isVisible/setFixedWidth camelCase
    protocol the shared mixins expect) kept only so QSS can target
    ``QTCheckbox`` specifically without also matching QTSwitch below.
    """


class QTSwitch(QtWidgets.QCheckBox):
    """Qt Switch Widget - native implementation.

    Qt has no native switch control - reuse QCheckBox's real boolean state
    (isChecked/setChecked/toggled) rather than inventing a parallel one.
    ``QtSwitchAdapter`` is a distinct interface from ``QtCheckboxAdapter``
    (see ISwitch's docstring) even though the native widget is the same
    class today; a track-and-thumb QSS/custom-paint treatment can replace
    this without touching the adapter or interface.
    """


class QTRadioGroup(QtWidgets.QWidget):
    """Qt RadioGroup Widget - native implementation.

    Qt has no single "radio group" control - compose QRadioButtons in a
    QButtonGroup for mutual exclusivity, wrapped in a plain QWidget so the
    shared VisibilityMixin/EnableMixin/SizeMixin camelCase protocol (which
    expects one widget, not a bare QButtonGroup - QButtonGroup is a QObject,
    not a QWidget, and has no show/hide/enabled/size surface at all) works
    the same way it does for every other primitive.
    """
    def __init__(self):
        super().__init__()
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._group = QtWidgets.QButtonGroup(self)
        self._buttons: list = []

    def setOptions(self, options):
        for button in self._buttons:
            self._group.removeButton(button)
            self._layout.removeWidget(button)
            button.deleteLater()
        self._buttons = []
        for option in options:
            button = QtWidgets.QRadioButton(option)
            self._group.addButton(button)
            self._layout.addWidget(button)
            self._buttons.append(button)
        if self._buttons:
            self._buttons[0].setChecked(True)

    def getSelected(self):
        for button in self._buttons:
            if button.isChecked():
                return button.text()
        return ""

    def setSelected(self, option):
        for button in self._buttons:
            if button.text() == option:
                button.setChecked(True)
                return

    def connect(self, function):
        self._group.buttonToggled.connect(function)

    def disconnect(self, function):
        self._group.buttonToggled.disconnect(function)
class QTNumberInput(QtWidgets.QDoubleSpinBox):
    """Qt NumberInput Widget - native implementation.

    QDoubleSpinBox already has the full isEnabled/setEnabled/show/hide/
    isVisible/setFixedWidth camelCase protocol the shared mixins expect,
    plus its own range/step/value surface - a trivial subclass, kept only
    for naming symmetry with the other QTXxx native wrappers.
    """
    def __init__(self):
        super().__init__()
        self.setDecimals(4)
        self.setRange(0.0, 100.0)


class QTPushButton(QtWidgets.QPushButton):
    """Qt Push Button Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def setText(self, text):
        super().setText(text)

    def connect(self, function):
        QtCore.QObject.connect(
            self, QtCore.SIGNAL("pressed()"), function)

    def disconnect(self, function):
        QtCore.QObject.disconnect(
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

    def textChangedDisconnect(self, function):
        super().textChanged.disconnect(function)

    def setFixedWidth(self, width):
        super().setFixedWidth(width)

    def hide(self):
        super().hide()

    def show(self):
        super().show()

    def setEnabled(self, flag):
        super().setEnabled(flag)
class QtButtonAdapter(NativeMixin, TextMixin, VisibilityMixin, EnableMixin, SizeMixin, IButton):
    """Qt Button adapter - implements snake_case interface convention"""

    # IEventCapable
    def connect(self, callback) -> Handle:
        wrapper = lambda: safe_call(callback, backend="qt", component="Button", method="connect")
        self._native.connect(wrapper)
        return Handle(lambda: self._native.disconnect(wrapper))
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
    def on_change(self, callback) -> Handle:
        wrapper = lambda: safe_call(callback, backend="qt", component="LineEdit", method="on_change")
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
class QtTextAreaAdapter(VisibilityMixin, EnableMixin, ITextArea):
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
    def on_change(self, callback) -> Handle:
        wrapper = lambda: safe_call(callback, backend="qt", component="TextArea", method="on_change")
        self._native.textChanged.connect(wrapper)
        return Handle(lambda: self._native.textChanged.disconnect(wrapper))

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)
class QtComboBoxAdapter(NativeMixin, SelectionMixin, ClearMixin, VisibilityMixin,
                        EnableMixin, SizeMixin, IComboBox):
    """Qt ComboBox adapter - implements snake_case interface convention"""

    # IChangeEventCapable
    def on_change(self, callback) -> Handle:
        wrapper = lambda: safe_call(callback, backend="qt", component="ComboBox", method="on_change")
        self._native.connect(wrapper)
        return Handle(lambda: self._native.disconnect(wrapper))
class QtDropdownAdapter(NativeMixin, SelectionMixin, ClearMixin, VisibilityMixin,
                       EnableMixin, SizeMixin, IDropdown):
    """Qt Dropdown adapter - implements snake_case interface convention"""

    # IValueCapable
    def set_value(self, value_list: list):
        """Set dropdown items from a list."""
        self._native.setValue(value_list)

    # IChangeEventCapable
    def on_change(self, callback) -> Handle:
        wrapper = lambda: safe_call(callback, backend="qt", component="Dropdown", method="on_change")
        self._native.connect(wrapper)
        return Handle(lambda: self._native.disconnect(wrapper))
class QtCheckboxAdapter(NativeMixin, VisibilityMixin, EnableMixin, SizeMixin, ICheckbox):
    """Qt Checkbox adapter - implements snake_case interface convention"""

    def is_checked(self) -> bool:
        return self._native.isChecked()

    def set_checked(self, checked: bool) -> None:
        self._native.setChecked(bool(checked))

    def on_change(self, callback) -> Handle:
        wrapper = lambda _checked: safe_call(callback, backend="qt", component="Checkbox", method="on_change")
        self._native.toggled.connect(wrapper)
        return Handle(lambda: self._native.toggled.disconnect(wrapper))
class QtSwitchAdapter(NativeMixin, VisibilityMixin, EnableMixin, SizeMixin, ISwitch):
    """Qt Switch adapter - implements snake_case interface convention"""

    def is_checked(self) -> bool:
        return self._native.isChecked()

    def set_checked(self, checked: bool) -> None:
        self._native.setChecked(bool(checked))

    def on_change(self, callback) -> Handle:
        wrapper = lambda _checked: safe_call(callback, backend="qt", component="Switch", method="on_change")
        self._native.toggled.connect(wrapper)
        return Handle(lambda: self._native.toggled.disconnect(wrapper))
class QtRadioGroupAdapter(NativeMixin, VisibilityMixin, EnableMixin, SizeMixin, IRadioGroup):
    """Qt RadioGroup adapter - implements snake_case interface convention"""

    def set_options(self, options) -> None:
        self._native.setOptions(list(options))

    def get_selected(self) -> str:
        return self._native.getSelected()

    def set_selected(self, option: str) -> None:
        self._native.setSelected(option)

    def on_change(self, callback) -> Handle:
        # QButtonGroup.buttonToggled fires for both the button being
        # unchecked (checked=False) and the one being checked (checked=True)
        # on every selection change - only forward the "checked" half so
        # callers see exactly one call per actual selection change.
        def wrapper(_button, checked):
            if checked:
                safe_call(callback, backend="qt", component="RadioGroup", method="on_change")
        self._native.connect(wrapper)
        return Handle(lambda: self._native.disconnect(wrapper))
class QtNumberInputAdapter(NativeMixin, VisibilityMixin, EnableMixin, SizeMixin, INumberInput):
    """Qt NumberInput adapter - implements snake_case interface convention"""

    def set_range(self, minimum: float, maximum: float) -> None:
        self._native.setRange(minimum, maximum)

    def set_step(self, step: float) -> None:
        self._native.setSingleStep(step)

    def get_value(self) -> float:
        return self._native.value()

    def set_value(self, value: float) -> None:
        self._native.setValue(value)

    def on_change(self, callback) -> Handle:
        wrapper = lambda _value: safe_call(callback, backend="qt", component="NumberInput", method="on_change")
        self._native.valueChanged.connect(wrapper)
        return Handle(lambda: self._native.valueChanged.disconnect(wrapper))
