"""Colour conversion shared by the wx primitive adapters."""
from __future__ import annotations

import wx

def _hex_to_wx(hex_color):
    """Convert hex color string to wx.Colour"""
    h = hex_color.lstrip('#')
    return wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
