"""The base NiceGUI widget factory for primitive controls.

``backends.web.factory.NiceGUIWidgetFactory`` subclasses this to add the Admin
components, so a plain NiceGUI app never imports them.
"""
from __future__ import annotations

from typing import Callable, Optional

from nicegui import ui

from ....core import *
from .inputs import (
    WebButtonAdapter, WebCheckboxAdapter, WebComboBoxAdapter,
    WebDropdownAdapter, WebLineEditAdapter, WebNumberInputAdapter,
    WebRadioGroupAdapter, WebSliderAdapter, WebSwitchAdapter,
    WebTextAreaAdapter,
)
from .layouts import (
    WebCenterAdapter,
    WebGridAdapter, WebHBoxAdapter, WebOverlayAdapter, WebScrollViewAdapter,
    WebSeparatorAdapter, WebSplitPaneAdapter, WebTabWidgetAdapter,
    WebVBoxAdapter, WebWrapAdapter,
)
from .state import set_backend_active
from .text import WebGroupBoxAdapter, WebImageAdapter, WebLabelAdapter


class _BaseNiceGUIWidgetFactory(IWidgetFactory):
    """
    Base NiceGUI Widget Factory — the core widgets every Web app gets.

    backends.web.factory.NiceGUIWidgetFactory subclasses this to add
    Card/Table/AppShell/etc.  create_factory() always returns that subclass;
    this base class is an internal split point, not something callers
    construct directly.
    """

    def __init__(self):
        set_backend_active(True)

    def createLabel(self) -> ILabel:
        return WebLabelAdapter()

    def createButton(self) -> IButton:
        return WebButtonAdapter()

    def createLineEdit(self) -> ILineEdit:
        return WebLineEditAdapter()

    def createTextArea(self) -> ITextArea:
        return WebTextAreaAdapter()

    def createComboBox(self) -> IComboBox:
        return WebComboBoxAdapter()

    def createDropdown(self) -> IDropdown:
        return WebDropdownAdapter()

    def createCheckbox(self) -> ICheckbox:
        return WebCheckboxAdapter()

    def createSwitch(self) -> ISwitch:
        return WebSwitchAdapter()

    def createRadioGroup(self) -> IRadioGroup:
        return WebRadioGroupAdapter()

    def createNumberInput(self) -> INumberInput:
        return WebNumberInputAdapter()

    def createSlider(self) -> ISlider:
        return WebSliderAdapter()

    def createVBox(self) -> IVBoxLayout:
        return WebVBoxAdapter()

    def createHBox(self) -> IHBoxLayout:
        return WebHBoxAdapter()

    def createTabWidget(self) -> ITabWidget:
        return WebTabWidgetAdapter()

    def createGroupBox(self) -> IGroupBox:
        return WebGroupBoxAdapter()

    def createGrid(self, columns: int = 12) -> IGrid:
        return WebGridAdapter(columns)

    def createWrap(self) -> IWrap:
        return WebWrapAdapter()

    def createCenter(self) -> ICenter:
        return WebCenterAdapter()

    def createSeparator(self, orientation: str = "horizontal") -> ISeparator:
        sep = WebSeparatorAdapter()
        sep.set_orientation(orientation)
        return sep

    def createScrollView(self) -> IScrollView:
        return WebScrollViewAdapter()

    def createSplitPane(self, orientation: str = "horizontal") -> ISplitPane:
        return WebSplitPaneAdapter(orientation)

    def createOverlay(self) -> IOverlay:
        return WebOverlayAdapter()

    def createImage(self) -> IImage:
        return WebImageAdapter()
