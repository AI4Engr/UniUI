"""
Core types and interfaces - Simplified.

Defines:
- Widget interfaces: ILabel, IButton, ILineEdit, etc.
- Layout interfaces: IVBoxLayout, IHBoxLayout with sizing/flex support
- Layout data models: SizeSpec, LayoutSpec, LayoutItem
- IWidgetFactory: abstract factory that each supported platform implements
- Exception classes: NotSupportedError, WidgetCreationError, etc.

This is the only module that platform implementations depend on.

The definitions now live in :mod:`uniui.contracts`, split into ``exceptions``,
``layout`` and ``widgets``. This module stays as the import surface every
backend uses via ``from ...core import *``.

The ``abc``/``typing``/``dataclasses`` imports below are re-exported on
purpose. They were reachable through ``import *`` before the split, and
backend modules do rely on picking up names like ``Optional`` and
``Callable`` that way, so dropping them would break those modules.
"""
from abc import ABC, abstractmethod
from typing import Callable, Any, Optional
from dataclasses import dataclass, field

from .contracts.exceptions import (
    ConfigurationError,
    InvalidValueError,
    NotSupportedError,
    UniUIException,
    WidgetCreationError,
)
from .contracts.layout import (
    DEFAULT_BREAKPOINTS,
    Breakpoints,
    LayoutItem,
    LayoutSpec,
    SizeSpec,
)
from .contracts.widgets import (
    IButton,
    ICheckbox,
    IComboBox,
    IDropdown,
    IGrid,
    IGroupBox,
    IHBoxLayout,
    IImage,
    ILabel,
    ILayoutOnly,
    ILineEdit,
    INumberInput,
    IOverlay,
    IRadioGroup,
    IScrollView,
    ISlider,
    ISplitPane,
    ISwitch,
    ITabWidget,
    ITextArea,
    IVBoxLayout,
    IWidget,
    IWidgetFactory,
    IWrap,
)
