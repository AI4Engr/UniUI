"""NiceGUI-powered Web backend for UniUI.

The public backend name is ``web``. NiceGUI remains an implementation detail.
Widgets are created eagerly and moved into containers when UniUI layouts are
assembled, which preserves the existing declarative API.

The implementation now lives in :mod:`uniui.backends.web.primitives`, split by
category (state, base, text, inputs, layouts, theming, factory). This module
stays as the public import surface, including the names it has always
re-exported incidentally.

``_adapters``, ``_css_installed``, ``_dark_mode`` and ``_backend_active`` are
deliberately *not* re-exported. Three of them are rebound through ``global``,
so a re-export would be a stale snapshot rather than a live view. They live in
``backends.web.primitives.state``; read and patch them there.
"""

from __future__ import annotations

import html as html_lib
import re
from pathlib import Path
from typing import Any, Callable, List

from nicegui import ui

from .core import (
    IButton,
    ICheckbox,
    IComboBox,
    IDropdown,
    IGrid,
    IGroupBox,
    IHBoxLayout,
    IImage,
    ILabel,
    ILineEdit,
    IOverlay,
    IRadioGroup,
    IScrollView,
    ISplitPane,
    ISwitch,
    ITabWidget,
    ITextArea,
    IVBoxLayout,
    IWidget,
    IWidgetFactory,
    IWrap,
    InvalidValueError,
    LayoutSpec,
    NotSupportedError,
)
from .strategies import normalize_text, parse_float
from .theme import THEME, is_dark

T = THEME

from .backends.web.primitives import (
    WebButtonAdapter, WebCheckboxAdapter, WebComboBoxAdapter,
    WebDropdownAdapter, WebGridAdapter, WebGroupBoxAdapter, WebHBoxAdapter,
    WebImageAdapter, WebLabelAdapter, WebLineEditAdapter, WebOverlayAdapter,
    WebRadioGroupAdapter, WebScrollViewAdapter, WebSplitPaneAdapter,
    WebSwitchAdapter, WebTabWidgetAdapter, WebTextAreaAdapter, WebVBoxAdapter,
    WebWrapAdapter, _BaseNiceGUIWidgetFactory, _WebAdapter,
    _WebSelectAdapter, _install_css, _plain_html, _set_enabled, _style_size,
    refresh_theme_web, schedule_after_web, set_backend_active,
)
