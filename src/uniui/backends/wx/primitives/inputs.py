"""Input primitives: buttons, text entry, and selection controls."""
from __future__ import annotations

from typing import Callable, List, Optional

import wx

from ....core import *
from ....strategies import normalize_text, parse_float
from ....theme import THEME

#: Alias for the live theme dict, mutated in place on a theme switch.
T = THEME

from .helpers import _hex_to_wx

class WxPushButton(wx.Control):
    """wxPython owner-draw button with per-category color support.

    Supports btntype values: num | op | sci | action | neutral
    Each maps to a distinct color from THEME, matching Qt stylesheet behavior.
    """

    # Maps btntype → (normal_key, hover_key, press_key) in THEME
    _TYPE_COLORS = {
        "num":     ("accent",         "accent_hover",         "accent_press"),
        "op":      ("accent_op",      "accent_op_hover",      "accent_op_press"),
        "sci":     ("accent_sci",     "accent_sci_hover",     "accent_sci_press"),
        "action":  ("accent_action",  "accent_action_hover",  "accent_action_press"),
        "neutral": ("accent_neutral", "accent_neutral_hover", "accent_neutral_press"),
    }

    def __init__(self, parent=None):
        super().__init__(
            parent or wx.GetApp().GetTopWindow(),
            style=wx.BORDER_NONE | wx.NO_FULL_REPAINT_ON_RESIZE,
        )
        self._btntype = "num"
        self._label = ""
        self._callback = None
        self._hovered = False
        self._pressed = False

        self.SetMinSize((60, 36))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        font = self.GetFont()
        # Slightly larger than theme base, keep readable in light mode
        font.SetPointSize(T["font_size"])
        font.SetFaceName(T["font_family"])
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.SetFont(font)

        self.Bind(wx.EVT_PAINT,          self._on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)
        self.Bind(wx.EVT_ENTER_WINDOW,   self._on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW,   self._on_leave)
        self.Bind(wx.EVT_LEFT_DOWN,      self._on_press)
        self.Bind(wx.EVT_LEFT_UP,        self._on_release)
        self.Bind(wx.EVT_SIZE,           lambda e: self.Refresh())

    # ------------------------------------------------------------------ paint

    def DoGetBestSize(self):
        """Return a fixed best size so all buttons are equally sized by the sizer."""
        return wx.Size(60, 36)

    @staticmethod
    def _parse(hex_color):
        h = hex_color.lstrip('#')
        return wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def _bg_key(self):
        keys = self._TYPE_COLORS.get(self._btntype, self._TYPE_COLORS["num"])
        if self._pressed:
            return keys[2]
        if self._hovered:
            return keys[1]
        return keys[0]

    def _on_paint(self, event):
        dc = wx.BufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return

        w, h = self.GetClientSize()
        bg  = self._parse(T.get(self._bg_key(), T["accent"]))
        fg  = self._parse(T["fg_button"])
        pbg = self._parse(T["bg"])

        # Flood with panel background first (removes edge artifacts)
        gc.SetBrush(wx.Brush(pbg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)

        # Rounded button fill
        gc.SetBrush(wx.Brush(bg))
        gc.DrawRoundedRectangle(1, 1, w - 2, h - 2, 5.0)

        # Centred label
        gc.SetFont(gc.CreateFont(self.GetFont(), fg))
        tw, th = gc.GetTextExtent(self._label)
        gc.DrawText(self._label, (w - tw) / 2, (h - th) / 2)

    # ----------------------------------------------------------------- events

    def _on_enter(self, event):
        self._hovered = True
        self.Refresh()
        event.Skip()

    def _on_leave(self, event):
        self._hovered = False
        self._pressed = False
        self.Refresh()
        event.Skip()

    def _on_press(self, event):
        self._pressed = True
        self.CaptureMouse()
        self.Refresh()
        event.Skip()

    def _on_release(self, event):
        fired = self._pressed and self._hovered
        self._pressed = False
        if self.HasCapture():
            self.ReleaseMouse()
        self.Refresh()
        if fired and self._callback:
            self._callback()
        event.Skip()

    # ------------------------------------------------------------------ API

    def set_btntype(self, btntype):
        """Set color category: num | op | sci | action | neutral."""
        self._btntype = btntype
        self.Refresh()

    def setText(self, text):
        self._label = text
        self.Refresh()

    def getText(self):
        return self._label

    def connect(self, function):
        self._callback = function

    def setEnabled(self, flag):
        self.Enable(flag)
        self.Refresh()

    def setFixedWidth(self, width):
        self.SetMinSize((width, -1))

    def setFixedHeight(self, height):
        self.SetMinSize((-1, height))

    def setMinimumWidth(self, width):
        current_min = self.GetMinSize()
        self.SetMinSize((width, current_min.height))

    def setMinimumHeight(self, height):
        current_min = self.GetMinSize()
        self.SetMinSize((current_min.width, height))
class WxLineEdit(wx.TextCtrl):
    """wxPython Line Edit Widget - native implementation"""
    def __init__(self, parent=None):
        super().__init__(
            parent or wx.GetApp().GetTopWindow(),
            style=wx.TE_PROCESS_ENTER | wx.BORDER_NONE,
        )
        self.SetMinSize((-1, 30))
        self.SetMargins(4, 4)

        font = self.GetFont()
        font.SetPointSize(T["font_size"])
        font.SetFaceName(T["font_family"])
        font.SetWeight(wx.FONTWEIGHT_NORMAL)
        self.SetFont(font)

        self.SetBackgroundColour(_hex_to_wx(T["bg_input"]))
        self.SetForegroundColour(_hex_to_wx(T["fg"]))

    def getText(self):
        return self.GetValue()

    def setText(self, text):
        self.SetValue(text)

    def getValue(self):
        text = self.GetValue()
        if text == "":
            return 0.0
        else:
            try:
                return float(text)
            except ValueError:
                return text

    def setValue(self, value):
        self.SetValue(str(value))

    def finishEditing(self, function):
        self.Bind(wx.EVT_TEXT_ENTER, lambda evt: function())

    def textChanged(self, function):
        self.Bind(wx.EVT_TEXT, lambda evt: function())

    def setFixedWidth(self, width):
        self.SetMinSize((width, 32))

    def setFixedHeight(self, height):
        current_width = self.GetMinSize()[0]
        self.SetMinSize((current_width, height))

    def setMinimumWidth(self, width):
        current_height = self.GetMinSize()[1]
        self.SetMinSize((width, current_height))

    def setMinimumHeight(self, height):
        current_width = self.GetMinSize()[0]
        self.SetMinSize((current_width, height))

    def hide(self):
        self.Hide()

    def show(self):
        self.Show()

    def setEnabled(self, flag):
        self.Enable(flag)

    def setTextColor(self, color, background):
        # color format: "rgb(r, g, b)"
        self.SetForegroundColour(color)
        self.SetBackgroundColour(background)
class WxTextarea(wx.TextCtrl):
    """wxPython Text Area Widget - native implementation"""
    def __init__(self, parent=None):
        super().__init__(
            parent or wx.GetApp().GetTopWindow(),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
        )

        # Set modern font and colors
        font = self.GetFont()
        font.SetPointSize(T["font_size"])
        font.SetFaceName(T["font_family"])
        self.SetFont(font)

        # Match calculator history height and avoid min/max conflicts
        self.SetMinSize((-1, 68))
        self.SetMargins(6, 6)

        self.SetBackgroundColour(_hex_to_wx(T["bg_input"]))
        self.SetForegroundColour(_hex_to_wx(T["fg"]))

    def setText(self, text):
        self.SetValue(text)

    def getText(self):
        return self.GetValue()

    def append(self, text):
        self.AppendText(text)

    def clear(self):
        self.Clear()

    def setMaximumHeight(self, value):
        # Set max height and clamp min height to avoid zero-size in sizers
        self.SetMaxSize((-1, value))
        min_w, min_h = self.GetMinSize()
        self.SetMinSize((min_w, min(min_h, value)))

    def setFixedWidth(self, width):
        self.SetMinSize((width, -1))

    def setFixedHeight(self, height):
        current_width = self.GetMinSize()[0]
        self.SetMinSize((current_width, height))

    def setMinimumWidth(self, width):
        current_height = self.GetMinSize()[1]
        self.SetMinSize((width, current_height))

    def setMinimumHeight(self, height):
        current_width = self.GetMinSize()[0]
        self.SetMinSize((current_width, height))
class WxComboBox(wx.ComboBox):
    """wxPython ComboBox Widget - native implementation (editable)"""
    def __init__(self, parent=None):
        super().__init__(parent or wx.GetApp().GetTopWindow())

    def addItem(self, item):
        self.Append(item)

    def connect(self, function):
        self.Bind(wx.EVT_COMBOBOX, lambda evt: function())

    def currentText(self):
        return self.GetValue()

    def clear(self):
        self.Clear()

    def deleteItem(self, item):
        idx = self.FindString(item)
        if idx != wx.NOT_FOUND:
            self.Delete(idx)

    def setEditable(self, editable):
        # wxComboBox is editable by default
        pass

    def setEditText(self, text):
        self.SetValue(text)

    def setEnabled(self, flag):
        self.Enable(flag)

    def setFixedWidth(self, width):
        self.SetMinSize((width, -1))

    def setFixedHeight(self, height):
        current_width = self.GetMinSize()[0]
        self.SetMinSize((current_width, height))

    def setMinimumWidth(self, width):
        current_height = self.GetMinSize()[1]
        self.SetMinSize((width, current_height))

    def setMinimumHeight(self, height):
        current_width = self.GetMinSize()[0]
        self.SetMinSize((current_width, height))

    def setSelection(self, item):
        idx = self.FindString(item)
        if idx != wx.NOT_FOUND:
            self.SetSelection(idx)

    def sort(self):
        items = [self.GetString(i) for i in range(self.GetCount())]
        items.sort()
        self.Clear()
        for item in items:
            self.Append(item)
class WxDropdown(wx.Choice):
    """wxPython Dropdown Widget - native implementation (read-only)"""
    def __init__(self, parent=None):
        super().__init__(parent or wx.GetApp().GetTopWindow())
        # Set minimum height for better appearance
        self.SetMinSize((-1, 32))

        # Set modern font and colors
        font = self.GetFont()
        font.SetPointSize(T["font_size"])
        font.SetFaceName(T["font_family"])
        self.SetFont(font)

        self.SetBackgroundColour(_hex_to_wx(T["bg_input"]))
        self.SetForegroundColour(_hex_to_wx(T["fg"]))

    def addItem(self, item):
        self.Append(item)

    def clear(self):
        self.Clear()

    def connect(self, function):
        self.Bind(wx.EVT_CHOICE, lambda evt: function())

    def currentText(self):
        return self.GetStringSelection()

    def deleteItem(self, item):
        idx = self.FindString(item)
        if idx != wx.NOT_FOUND:
            self.Delete(idx)

    def hide(self):
        self.Hide()

    def show(self):
        self.Show()

    def setEnabled(self, flag):
        self.Enable(flag)

    def setFixedWidth(self, width):
        self.SetMinSize((width, -1))

    def setFixedHeight(self, height):
        current_width = self.GetMinSize()[0]
        self.SetMinSize((current_width, height))

    def setMinimumWidth(self, width):
        current_height = self.GetMinSize()[1]
        self.SetMinSize((width, current_height))

    def setMinimumHeight(self, height):
        current_width = self.GetMinSize()[0]
        self.SetMinSize((current_width, height))

    def setSelection(self, item):
        idx = self.FindString(item)
        if idx != wx.NOT_FOUND:
            self.SetSelection(idx)

    def setValue(self, value_list):
        self.Clear()
        for item in value_list:
            self.Append(item)
        if len(value_list) > 0:
            self.SetSelection(0)

    def sort(self):
        items = [self.GetString(i) for i in range(self.GetCount())]
        items.sort()
        self.Clear()
        for item in items:
            self.Append(item)
class WxButtonAdapter(IButton):
    """wxPython Button adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: WxPushButton):
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
        return self._native.IsEnabled()

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)
class WxLineEditAdapter(ILineEdit):
    """wxPython LineEdit adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: WxLineEdit):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.getText())

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
        return self._native.IsShown()

    # IEnableCapable
    def set_enabled(self, enabled: bool):
        self._native.setEnabled(enabled)

    def is_enabled(self) -> bool:
        return self._native.IsEnabled()

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)
class WxTextAreaAdapter(ITextArea):
    """wxPython TextArea adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: WxTextarea):
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
        self._native.Bind(wx.EVT_TEXT, lambda evt: callback())

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)
class WxComboBoxAdapter(IComboBox):
    """wxPython ComboBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: WxComboBox):
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
        return self._native.IsEnabled()

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)
class WxDropdownAdapter(IDropdown):
    """wxPython Dropdown adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: WxDropdown):
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
        return self._native.IsShown()

    # IEnableCapable
    def set_enabled(self, enabled: bool):
        self._native.setEnabled(enabled)

    def is_enabled(self) -> bool:
        return self._native.IsEnabled()

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)
