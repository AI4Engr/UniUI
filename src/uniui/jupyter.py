"""
Jupyter/ipywidgets backend.

Native widgets, adapters, and factory for Jupyter notebooks.
Dark mode uses CSS injection + inline style for reliable theming.
HBox/VBox use ipywidgets flexbox layout.

The implementation now lives in :mod:`uniui.backends.jupyter.primitives`, split
by category (theming, text, inputs, layouts, factory). This module stays as the
public import surface, including the names it has always re-exported
incidentally: the ``core`` interfaces, the adapter mixins, ``widgets``, and the
``T`` theme alias.

Note that importing the factory module applies ``_mark_created_widgets`` to
``_BaseJupyterWidgetFactory`` as a one-shot side effect. This module re-exports
the already-wrapped class; it deliberately does not call it again, which would
double-wrap every ``create*`` method.

``_jupyter_css_widget`` is deliberately *not* re-exported. It is rebound by
``refresh_theme_jupyter`` through a ``global`` statement, so a re-export here
would be a stale snapshot that never tracks the live node. It lives in
``backends.jupyter.primitives.theming``; read and patch it there.
"""
from __future__ import annotations
from typing import List, Optional, Callable

# Import capability interfaces from core
from .core import *
from ._adapter_mixins import (
    ClearMixin, EnableMixin, NativeMixin, SelectionMixin, SizeMixin,
    TextMixin, VisibilityMixin,
)
from .strategies import normalize_text, parse_float
from .theme import THEME, is_dark

# IPyWidgets imports
import ipywidgets as widgets
from IPython.display import display

T = THEME

from .backends.jupyter.primitives import (
    JupyterButtonAdapter, JupyterCheckboxAdapter, JupyterComboBox,
    JupyterComboBoxAdapter, JupyterDropdown, JupyterDropdownAdapter,
    JupyterGrid, JupyterGridAdapter, JupyterGroupBox, JupyterGroupBoxAdapter,
    JupyterHBoxAdapter, JupyterHBoxLayout, JupyterImage, JupyterImageAdapter,
    JupyterLabel, JupyterLabelAdapter, JupyterLineEdit, JupyterLineEditAdapter,
    JupyterOverlay, JupyterOverlayAdapter, JupyterPushButton,
    JupyterScrollView, JupyterScrollViewAdapter, JupyterSplitPane,
    JupyterSplitPaneAdapter, JupyterSwitchAdapter, JupyterTabWidget,
    JupyterTabWidgetAdapter, JupyterTextAreaAdapter, JupyterTextarea,
    JupyterVBoxAdapter, JupyterVBoxLayout, JupyterWrap, JupyterWrapAdapter,
    _BaseJupyterWidgetFactory, _generate_jupyter_css, _mark_created_widgets,
    _refresh_widget_tree, convert_control_text, refresh_theme_jupyter,
)
