"""The wxPython widget factory.

Like Tk and unlike Qt/Jupyter/Web there is no ``_Base`` split: this legacy
backend has no Admin component layer to separate from.
"""
from __future__ import annotations

from typing import Callable, List, Optional

import wx

from ....core import *
from ....theme import THEME
from .inputs import (
    WxButtonAdapter, WxComboBox, WxComboBoxAdapter, WxDropdown,
    WxDropdownAdapter, WxLineEdit, WxLineEditAdapter, WxPushButton,
    WxTextAreaAdapter, WxTextarea,
)
from .layouts import (
    WxHBoxLayout, WxHBoxLayoutAdapter, WxTabWidget, WxTabWidgetAdapter,
    WxVBoxLayout, WxVBoxLayoutAdapter,
)
from .text import (
    WxGroupBox, WxGroupBoxAdapter, WxImage, WxImageAdapter, WxLabel,
    WxLabelAdapter, _WxGroupPanel,
)

T = THEME


class WxWidgetFactory(IWidgetFactory):
    """
    wxPython Widget Factory

    Creates wxPython widgets wrapped in adapters.
    """

    def __init__(self):
        # Ensure wxApp is created
        app = wx.App.Get()
        if app is None:
            self.app = wx.App()
        else:
            self.app = app

        # Create a temporary parent window (but don't show it)
        self._temp_parent = wx.Frame(None)

    # Basic widgets
    def createLabel(self) -> ILabel:
        native = WxLabel(self._temp_parent)
        return WxLabelAdapter(native)

    def createButton(self) -> IButton:
        native = WxPushButton(self._temp_parent)
        return WxButtonAdapter(native)

    def createLineEdit(self) -> ILineEdit:
        native = WxLineEdit(self._temp_parent)
        return WxLineEditAdapter(native)

    def createTextArea(self) -> ITextArea:
        native = WxTextarea(self._temp_parent)
        return WxTextAreaAdapter(native)

    def createComboBox(self) -> IComboBox:
        native = WxComboBox(self._temp_parent)
        return WxComboBoxAdapter(native)

    def createDropdown(self) -> IDropdown:
        native = WxDropdown(self._temp_parent)
        return WxDropdownAdapter(native)

    # Layout
    def createVBox(self) -> IVBoxLayout:
        native = WxVBoxLayout()
        return WxVBoxLayoutAdapter(native)

    def createHBox(self) -> IHBoxLayout:
        native = WxHBoxLayout()
        return WxHBoxLayoutAdapter(native)

    # Advanced widgets
    def createTabWidget(self) -> ITabWidget:
        native = WxTabWidget(self._temp_parent)
        return WxTabWidgetAdapter(native)

    def createImage(self) -> IImage:
        native = WxImage(self._temp_parent)
        return WxImageAdapter(native)

    def createGroupBox(self) -> IGroupBox:
        native = WxGroupBox(self._temp_parent)
        return WxGroupBoxAdapter(native)
