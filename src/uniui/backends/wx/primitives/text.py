"""Text and display primitives: labels, images, group boxes."""
from __future__ import annotations

from typing import Callable, List, Optional

import wx

from ....core import *
from ....strategies import normalize_text, parse_float
from ....theme import THEME

#: Alias for the live theme dict, mutated in place on a theme switch.
T = THEME

from .helpers import _hex_to_wx

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
class WxGroupBox(wx.BoxSizer):
    """wxPython Group Box - custom panel-based implementation (no StaticBox white border).

    Uses a wx.Panel with a themed border drawn via wx.BoxSizer nesting,
    avoiding the native wx.StaticBox which renders an unthemeable white border
    on Windows.
    """
    def __init__(self, parent=None):
        super().__init__(wx.VERTICAL)
        self._parent = parent or wx.GetApp().GetTopWindow()
        self._title = ""
        self._panel = None   # created lazily in setLayout / setTitle
        self._inner_sizer = None

    def _ensure_panel(self):
        if self._panel is not None:
            return
        self._panel = _WxGroupPanel(self._parent, self._title)
        # Add panel to self (the outer BoxSizer) so callers can add self to a parent sizer
        self.Add(self._panel, 0, wx.EXPAND | wx.ALL, 2)

    def setTitle(self, title):
        self._title = title
        if self._panel is not None:
            self._panel.set_title(title)

    def setLayout(self, layout):
        """Embed the inner sizer into the group panel."""
        self._ensure_panel()
        if isinstance(layout, wx.Sizer):
            self._panel.set_inner_sizer(layout)
class _WxGroupPanel(wx.Panel):
    """A themed panel that mimics a GroupBox with a colored border and title label."""

    def __init__(self, parent, title=""):
        super().__init__(parent, style=wx.BORDER_NONE)
        self.SetBackgroundColour(_hex_to_wx(T["bg"]))

        self._title_label = wx.StaticText(self, label=title)
        font = self._title_label.GetFont()
        font.SetPointSize(T["font_size"] - 1)
        font.SetFaceName(T["font_family"])
        self._title_label.SetFont(font)
        self._title_label.SetForegroundColour(_hex_to_wx(T["fg_muted"]))
        self._title_label.SetBackgroundColour(_hex_to_wx(T["bg"]))

        self._border_panel = wx.Panel(self, style=wx.BORDER_NONE)
        self._border_panel.SetBackgroundColour(_hex_to_wx(T["bg"]))
        self._border_panel.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self._border_panel.Bind(wx.EVT_PAINT, self._on_border_paint)
        self._border_panel.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)

        self._content_sizer = wx.BoxSizer(wx.VERTICAL)
        self._border_panel.SetSizer(self._content_sizer)

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self._title_label, 0, wx.LEFT | wx.TOP, 4)
        outer.Add(self._border_panel, 0, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(outer)

    def _on_border_paint(self, event):
        dc = wx.BufferedPaintDC(self._border_panel)
        w, h = self._border_panel.GetClientSize()
        bg = _hex_to_wx(T["bg"])
        dc.SetBackground(wx.Brush(bg))
        dc.Clear()
        col = _hex_to_wx(T["border"])
        dc.SetPen(wx.Pen(col, 1))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(0, 0, w, h)

    def set_title(self, title):
        self._title_label.SetLabel(title)
        self.Layout()

    def set_inner_sizer(self, sizer):
        # Reparent all widgets in the sizer to _border_panel before adding,
        # because wx requires sizer-managed windows to be children of the
        # window owning the sizer.
        def _reparent(s, parent):
            for item in s.GetChildren():
                if item.IsWindow():
                    item.GetWindow().Reparent(parent)
                elif item.IsSizer():
                    _reparent(item.GetSizer(), parent)
        _reparent(sizer, self._border_panel)
        self._content_sizer.Add(sizer, 0, wx.EXPAND | wx.ALL, T["padding_inner"])
        self._border_panel.Layout()
        self.Layout()

    def apply_theme(self):
        self.SetBackgroundColour(_hex_to_wx(T["bg"]))
        self._title_label.SetForegroundColour(_hex_to_wx(T["fg_muted"]))
        self._title_label.SetBackgroundColour(_hex_to_wx(T["bg"]))
        self._border_panel.SetBackgroundColour(_hex_to_wx(T["bg"]))
        self._border_panel.Refresh()
        self.Refresh()
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
