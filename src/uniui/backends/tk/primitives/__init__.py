"""Tkinter primitive widgets (legacy backend), split by category.

There is no Admin component layer for Tk, so ``TkWidgetFactory`` is the only
factory - unlike Qt/Jupyter/Web, which split a ``_Base`` factory out.

``uniui.tk`` re-exports everything here, so existing imports keep working.
"""
from __future__ import annotations

from .factory import TkWidgetFactory
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

__all__ = [
    "TkButtonAdapter", "TkComboBox", "TkComboBoxAdapter", "TkDropdown",
    "TkDropdownAdapter", "TkGroupBox", "TkGroupBoxAdapter", "TkHBoxLayout",
    "TkHBoxLayoutAdapter", "TkImage", "TkImageAdapter", "TkLabel",
    "TkLabelAdapter", "TkLineEdit", "TkLineEditAdapter", "TkPushButton",
    "TkTabWidget", "TkTabWidgetAdapter", "TkTextAreaAdapter", "TkTextarea",
    "TkVBoxLayout", "TkVBoxLayoutAdapter", "TkWidgetFactory",
]
