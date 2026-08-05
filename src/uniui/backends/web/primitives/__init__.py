"""Web (NiceGUI) primitive widgets: the controls every web app gets.

The Admin components live one level up in ``backends.web.components``.
``_BaseNiceGUIWidgetFactory`` marks the split: a plain NiceGUI app never
imports the Admin adapters.

Shared mutable state lives in :mod:`.state` and is deliberately not re-exported
from here or from ``uniui.web`` - see that module for why.
"""
from __future__ import annotations

from .base import _WebAdapter
from .factory import _BaseNiceGUIWidgetFactory
from .helpers import _plain_html, _set_enabled, _style_size
from .inputs import (
    WebButtonAdapter, WebComboBoxAdapter, WebDropdownAdapter,
    WebLineEditAdapter, WebTextAreaAdapter, _WebSelectAdapter,
)
from .layouts import (
    WebGridAdapter, WebHBoxAdapter, WebOverlayAdapter, WebScrollViewAdapter,
    WebSplitPaneAdapter, WebTabWidgetAdapter, WebVBoxAdapter, WebWrapAdapter,
)
from .state import _install_css, set_backend_active
from .text import WebGroupBoxAdapter, WebImageAdapter, WebLabelAdapter
from .theming import refresh_theme_web, schedule_after_web

__all__ = [
    "_BaseNiceGUIWidgetFactory",
    "_WebAdapter",
    "_WebSelectAdapter",
    "_install_css",
    "_plain_html",
    "_set_enabled",
    "_style_size",
    "WebButtonAdapter",
    "WebComboBoxAdapter",
    "WebDropdownAdapter",
    "WebGridAdapter",
    "WebGroupBoxAdapter",
    "WebHBoxAdapter",
    "WebImageAdapter",
    "WebLabelAdapter",
    "WebLineEditAdapter",
    "WebOverlayAdapter",
    "WebScrollViewAdapter",
    "WebSplitPaneAdapter",
    "WebTabWidgetAdapter",
    "WebTextAreaAdapter",
    "WebVBoxAdapter",
    "WebWrapAdapter",
    "refresh_theme_web",
    "schedule_after_web",
    "set_backend_active",
]
