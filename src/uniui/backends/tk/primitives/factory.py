"""The Tkinter widget factory.

Unlike Qt/Jupyter/Web there is no ``_Base`` split here: this legacy backend has
no Admin component layer to separate from.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ....core import *
from ....theme import THEME
from .inputs import (
    TkButtonAdapter, TkComboBox, TkComboBoxAdapter, TkDropdown,
    TkDropdownAdapter, TkLineEdit, TkLineEditAdapter, TkPushButton,
    TkTextAreaAdapter, TkTextarea,
)
from .layouts import (
    TkHBoxLayout, TkHBoxLayoutAdapter, TkTabWidget, TkTabWidgetAdapter,
    TkVBoxLayout, TkVBoxLayoutAdapter,
)
from .text import (
    TkGroupBox, TkGroupBoxAdapter, TkImage, TkImageAdapter, TkLabel,
    TkLabelAdapter,
)

T = THEME


class TkWidgetFactory(IWidgetFactory):
    """Tkinter widget factory - creates properly wrapped widgets"""

    def __init__(self):
        # Ensure Tk root is created
        if tk._default_root is None:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide default window
        else:
            self.root = tk._default_root

    # Basic widgets
    def createLabel(self) -> ILabel:
        native = TkLabel(self.root)
        return TkLabelAdapter(native)

    def createButton(self) -> IButton:
        native = TkPushButton(self.root)
        return TkButtonAdapter(native)

    def createLineEdit(self) -> ILineEdit:
        native = TkLineEdit(self.root)
        return TkLineEditAdapter(native)

    def createTextArea(self) -> ITextArea:
        native = TkTextarea(self.root)
        return TkTextAreaAdapter(native)

    def createComboBox(self) -> IComboBox:
        native = TkComboBox(self.root)
        return TkComboBoxAdapter(native)

    def createDropdown(self) -> IDropdown:
        native = TkDropdown(self.root)
        return TkDropdownAdapter(native)

    # Layouts
    def createVBox(self) -> IVBoxLayout:
        native = TkVBoxLayout(self.root)
        return TkVBoxLayoutAdapter(native)

    def createHBox(self) -> IHBoxLayout:
        native = TkHBoxLayout(self.root)
        return TkHBoxLayoutAdapter(native)

    # Advanced widgets
    def createTabWidget(self) -> ITabWidget:
        native = TkTabWidget(self.root)
        return TkTabWidgetAdapter(native)

    def createImage(self) -> IImage:
        native = TkImage(self.root)
        return TkImageAdapter(native)

    def createGroupBox(self) -> IGroupBox:
        native = TkGroupBox(self.root)
        return TkGroupBoxAdapter(native)
