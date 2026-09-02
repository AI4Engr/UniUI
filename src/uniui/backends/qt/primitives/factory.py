"""The base Qt widget factory for primitive controls.

``backends.qt.factory.QtWidgetFactory`` subclasses this to add the Admin
components; keeping the split here is what lets a plain Qt app avoid importing
them.
"""
from __future__ import annotations

from PySide2 import QtCore

from ....core import *
from .inputs import (
    QTCheckbox, QTComboBox, QTDropdown, QTLineEdit, QTNumberInput,
    QTPushButton, QTRadioGroup, QTSlider, QTSwitch, QTTextarea,
    QtButtonAdapter, QtCheckboxAdapter, QtComboBoxAdapter, QtDropdownAdapter,
    QtLineEditAdapter, QtNumberInputAdapter, QtRadioGroupAdapter,
    QtSliderAdapter, QtSwitchAdapter, QtTextAreaAdapter,
)
from .layouts import (
    QTHBoxLayout, QTTabWidget, QTVBoxLayout, QtCenterAdapter, QtGridAdapter, QtHBoxAdapter,
    QtOverlayAdapter, QtScrollViewAdapter, QtSeparatorAdapter,
    QtSplitPaneAdapter, QtTabWidgetAdapter, QtVBoxAdapter, QtWrapAdapter,
)
from .text import (
    QTGroupBox, QTImage, QTLabel, QtGroupBoxAdapter, QtImageAdapter,
    QtLabelAdapter,
)


class _BaseQtWidgetFactory(IWidgetFactory):
    """
    Base Qt Widget Factory — the core widgets every Qt app gets.

    backends.qt.factory.QtWidgetFactory subclasses this to add Card/Table/
    AppShell/etc.  create_factory() always returns that subclass; this base
    class is an internal split point, not something callers construct directly.
    """

    def __init__(self):
        """Initialize factory, ensuring QApplication exists"""
        from PySide2.QtWidgets import QApplication
        import sys

        # Qt 5 requires these flags before QApplication construction. They are
        # no-ops on platforms where high-DPI scaling is already automatic.
        if QApplication.instance() is None:
            if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
                QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
            if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
                QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

        # Ensure QApplication has been created. Stamped with _uniui_owns_app
        # so display.show() can later tell "UniUI created this app" from "a
        # host app already owned one" even though by the time show() runs,
        # QApplication.instance() is never None either way - the factory
        # always creates it first.
        app = QApplication.instance()
        if app is None:
            self.app = QApplication(sys.argv)
            self.app._uniui_owns_app = True
        else:
            self.app = app

        # Give plain Qt widgets the design-system look without requiring the
        # caller to copy a stylesheet.  Imported here because the stylesheet
        # pulls in the admin palette, which imports this module.
        from .styles import apply_app_style
        apply_app_style(self.app)

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

    def createCheckbox(self) -> ICheckbox:
        native = QTCheckbox()
        return QtCheckboxAdapter(native)

    def createSwitch(self) -> ISwitch:
        native = QTSwitch()
        return QtSwitchAdapter(native)

    def createRadioGroup(self) -> IRadioGroup:
        native = QTRadioGroup()
        return QtRadioGroupAdapter(native)

    def createNumberInput(self) -> INumberInput:
        native = QTNumberInput()
        return QtNumberInputAdapter(native)

    def createSlider(self) -> ISlider:
        native = QTSlider()
        return QtSliderAdapter(native)

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

    def createGrid(self, columns: int = 12) -> IGrid:
        adapter = QtGridAdapter(columns)
        adapter.set_columns(columns)
        return adapter

    def createWrap(self) -> IWrap:
        return QtWrapAdapter()

    def createCenter(self) -> ICenter:
        return QtCenterAdapter()

    def createSeparator(self, orientation: str = "horizontal") -> ISeparator:
        sep = QtSeparatorAdapter()
        sep.set_orientation(orientation)
        return sep

    def createScrollView(self) -> IScrollView:
        return QtScrollViewAdapter()

    def createSplitPane(self, orientation: str = "horizontal") -> ISplitPane:
        return QtSplitPaneAdapter(orientation)

    def createOverlay(self) -> IOverlay:
        return QtOverlayAdapter()
