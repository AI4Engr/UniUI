"""
Tkinter backend (LEGACY - UNSUPPORTED).

Native widgets, adapters, and factory for the Tkinter platform.
This backend is deprecated and no longer supported. No new features should be developed.

The implementation now lives in :mod:`uniui.backends.tk.primitives`, split by
category (text, inputs, layouts, factory). This module stays as the public
import surface, including the names it has always re-exported incidentally.
"""

from __future__ import annotations

# Import capability interfaces from core
from .core import *
from .strategies import normalize_text, parse_float
from .theme import THEME

# Tkinter imports
import tkinter as tk
from tkinter import ttk

T = THEME

from .backends.tk.primitives.inputs import _BTNTYPE_KEY
from .backends.tk.primitives import (
    TkButtonAdapter, TkComboBox, TkComboBoxAdapter, TkDropdown,
    TkDropdownAdapter, TkGroupBox, TkGroupBoxAdapter, TkHBoxLayout,
    TkHBoxLayoutAdapter, TkImage, TkImageAdapter, TkLabel, TkLabelAdapter,
    TkLineEdit, TkLineEditAdapter, TkPushButton, TkTabWidget,
    TkTabWidgetAdapter, TkTextAreaAdapter, TkTextarea, TkVBoxLayout,
    TkVBoxLayoutAdapter, TkWidgetFactory,
)
