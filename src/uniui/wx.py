"""
wxPython backend.

Native widgets, adapters, and factory for the wxPython platform.
Each widget class wraps a wx widget and exposes the IWidget interface.
"""
from __future__ import annotations
from typing import List, Optional, Callable

# Import capability interfaces from core
from .core import *
from .strategies import normalize_text, parse_float
from .theme import THEME

# wxPython imports
import wx

T = THEME

def _hex_to_wx(hex_color):
    """Convert hex color string to wx.Colour"""
    h = hex_color.lstrip('#')
    return wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ============================================================================
# Native Widget Classes (camelCase methods from widgets/wx_widgets.py)
# ============================================================================

class WxLabel(wx.StaticText):
    """wxPython Label Widget - native implementation"""
    def __init__(self, parent=None):
        if parent is None:
            # Get the app's top window, or create a temporary one
            app = wx.App.Get()
            parent = app.GetTopWindow() if app else wx.Frame(None)
        super().__init__(parent)

        # Set modern font
        font = self.GetFont()
        font.SetPointSize(T["font_size"])
        font.SetFaceName(T["font_family"])
        self.SetFont(font)

        # Set text color
        self.SetForegroundColour(_hex_to_wx(T["fg"]))

    def setText(self, text):
        self.SetLabel(text)

    def getText(self):
        return self.GetLabel()

    def hide(self):
        self.Hide()

    def show(self):
        self.Show()

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


class WxVBoxLayout(wx.BoxSizer):
    """wxPython Vertical Box Layout - native implementation"""
    def __init__(self):
        super().__init__(wx.VERTICAL)

    def addItem(self, item):
        if isinstance(item, wx.Sizer):
            # Use 2px gap for tighter button rows
            self.Add(item, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 2)
        elif isinstance(item, wx.TextCtrl) and item.IsMultiLine():
            self.Add(item, 0, wx.EXPAND | wx.ALL, T["padding_inner"])
        else:
            self.Add(item, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, T["padding_inner"])

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


class WxImage(wx.StaticBitmap):
    """wxPython Image Widget - native implementation"""
    def __init__(self, parent=None):
        super().__init__(parent or wx.GetApp().GetTopWindow())

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

    def setImage(self, image_path):
        img = wx.Image(image_path, wx.BITMAP_TYPE_ANY)
        self.SetBitmap(wx.Bitmap(img))

    def setImageFromUrl(self, url):
        raise NotSupportedError(
            "Image URL loading is not supported in the wxPython backend. "
            "Use setImage with a local file path."
        )


class WxGroupBox(wx.StaticBoxSizer):
    """wxPython Group Box - native implementation"""
    def __init__(self, parent=None):
        box = wx.StaticBox(parent or wx.GetApp().GetTopWindow())
        # Apply theme foreground so title is visible in dark mode from the start
        h = T["fg_muted"].lstrip('#')
        box.SetForegroundColour(wx.Colour(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)))
        box.SetBackgroundColour(_hex_to_wx(T["bg"]))
        super().__init__(box, wx.VERTICAL)

    def setTitle(self, title):
        self.GetStaticBox().SetLabel(title)

    def setLayout(self, layout):
        """Add all items from the given layout (sizer) into this group box sizer"""
        if isinstance(layout, wx.Sizer):
            self.Add(layout, 0, wx.EXPAND | wx.ALL, T["padding_inner"])


# ============================================================================
# Adapter Classes (snake_case interface methods)
# ============================================================================

class WxLabelAdapter(ILabel):
    """wxPython Label adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: WxLabel):
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
        return self._native.IsShown()

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)


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


class WxImageAdapter(IImage):
    """wxPython Image adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: WxImage):
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


class WxGroupBoxAdapter(IGroupBox):
    """wxPython GroupBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: WxGroupBox):
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
# wxPython Widget Factory
# ============================================================================

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
