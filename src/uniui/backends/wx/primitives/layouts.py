"""Layout and container primitives."""
from __future__ import annotations

from typing import Callable, List, Optional

import wx

from ....core import *
from ....strategies import normalize_text, parse_float
from ....theme import THEME

#: Alias for the live theme dict, mutated in place on a theme switch.
T = THEME

from .helpers import _hex_to_wx

class WxVBoxLayout(wx.BoxSizer):
    """wxPython Vertical Box Layout - native implementation"""
    def __init__(self):
        super().__init__(wx.VERTICAL)

    def addItem(self, item):
        if isinstance(item, wx.Sizer):
            self.Add(item, 0, wx.EXPAND | wx.ALL, 2)
        elif isinstance(item, wx.TextCtrl) and item.IsMultiLine():
            self.Add(item, 1, wx.EXPAND | wx.ALL, T["padding_inner"])
        else:
            self.Add(item, 0, wx.EXPAND | wx.ALL, T["padding_inner"])

    def addStretch(self):
        self.AddStretchSpacer()

    def setAlignmentTop(self):
        pass
class WxHBoxLayout(wx.BoxSizer):
    """wxPython Horizontal Box Layout - native implementation"""
    def __init__(self):
        super().__init__(wx.HORIZONTAL)

    def addItem(self, item):
        # 3px gap between buttons gives a tighter, more modern grid
        self.Add(item, 1, wx.EXPAND | wx.ALL, 3)

    def addStretch(self):
        self.AddStretchSpacer()

    def setAlignmentTop(self):
        pass
class WxTabWidget(wx.Notebook):
    """wxPython Tab Widget - native implementation"""
    def __init__(self, parent=None):
        super().__init__(parent or wx.GetApp().GetTopWindow())

    def addTab(self, item, tab_name):
        # For wx.Notebook, item should be a wx.Panel
        if not isinstance(item, wx.Panel):
            panel = wx.Panel(self)
            if isinstance(item, wx.Sizer):
                panel.SetSizer(item)
            item = panel
        self.AddPage(item, tab_name)

    def currentIndex(self):
        return self.GetSelection()

    def hide(self):
        self.Hide()

    def show(self):
        self.Show()

    def removeTabs(self):
        self.DeleteAllPages()
class WxVBoxLayoutAdapter(IVBoxLayout):
    """wxPython VBox adapter - implements snake_case interface convention"""

    def __init__(self, native_layout: WxVBoxLayout):
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
class WxHBoxLayoutAdapter(IHBoxLayout):
    """wxPython HBox adapter - implements snake_case interface convention"""

    def __init__(self, native_layout: WxHBoxLayout):
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
class WxTabWidgetAdapter(ITabWidget):
    """wxPython TabWidget adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: WxTabWidget):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITabCapable
    def add_tab(self, widget: IWidget, name: str):
        # wxPython needs to wrap Sizer in Panel
        native = widget.get_native()
        if isinstance(native, wx.Sizer):
            panel = wx.Panel(self._native)
            panel.SetSizer(native)
            self._native.addTab(panel, name)
        else:
            self._native.addTab(native, name)

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
        return self._native.IsShown()
