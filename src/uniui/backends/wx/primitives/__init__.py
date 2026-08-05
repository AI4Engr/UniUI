"""wxPython primitive widgets (legacy backend), split by category.

There is no Admin component layer for wx, so ``WxWidgetFactory`` is the only
factory - unlike Qt/Jupyter/Web, which split a ``_Base`` factory out.

``uniui.wx`` re-exports everything here, so existing imports keep working.
``_hex_to_wx`` and ``_WxGroupPanel`` are private but were reachable as
attributes of the old flat ``uniui.wx`` module, so they are re-exported too.
"""
from __future__ import annotations

from .factory import WxWidgetFactory
from .helpers import _hex_to_wx
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

__all__ = [
    "WxButtonAdapter", "WxComboBox", "WxComboBoxAdapter", "WxDropdown",
    "WxDropdownAdapter", "WxGroupBox", "WxGroupBoxAdapter", "WxHBoxLayout",
    "WxHBoxLayoutAdapter", "WxImage", "WxImageAdapter", "WxLabel",
    "WxLabelAdapter", "WxLineEdit", "WxLineEditAdapter", "WxPushButton",
    "WxTabWidget", "WxTabWidgetAdapter", "WxTextAreaAdapter", "WxTextarea",
    "WxVBoxLayout", "WxVBoxLayoutAdapter", "WxWidgetFactory",
]
