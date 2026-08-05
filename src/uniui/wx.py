"""
wxPython backend (LEGACY - UNSUPPORTED).

Native widgets, adapters, and factory for the wxPython platform.
This backend is deprecated and no longer supported. No new features should be developed.

The implementation now lives in :mod:`uniui.backends.wx.primitives`, split by
category (helpers, text, inputs, layouts, factory). This module stays as the
public import surface, including the names it has always re-exported
incidentally.
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

from .backends.wx.primitives import (
    WxButtonAdapter, WxComboBox, WxComboBoxAdapter, WxDropdown,
    WxDropdownAdapter, WxGroupBox, WxGroupBoxAdapter, WxHBoxLayout,
    WxHBoxLayoutAdapter, WxImage, WxImageAdapter, WxLabel, WxLabelAdapter,
    WxLineEdit, WxLineEditAdapter, WxPushButton, WxTabWidget,
    WxTabWidgetAdapter, WxTextAreaAdapter, WxTextarea, WxVBoxLayout,
    WxVBoxLayoutAdapter, WxWidgetFactory, _hex_to_wx, _WxGroupPanel,
)
