"""Jupyter primitive widgets: the controls every notebook app gets.

The Admin components live one level up in ``backends.jupyter.components``.
``_BaseJupyterWidgetFactory`` marks the split: a plain notebook never imports
the Admin adapters.

``uniui.jupyter`` re-exports everything here, so existing imports keep working.
"""
from __future__ import annotations

from .factory import _BaseJupyterWidgetFactory, _mark_created_widgets
from .helpers import convert_control_text
from .inputs import (
    JupyterButtonAdapter, JupyterCheckboxAdapter, JupyterComboBox,
    JupyterComboBoxAdapter, JupyterDropdown, JupyterDropdownAdapter,
    JupyterLineEdit, JupyterLineEditAdapter, JupyterNumberInputAdapter,
    JupyterPushButton, JupyterRadioGroupAdapter, JupyterSliderAdapter,
    JupyterSwitchAdapter, JupyterTextAreaAdapter, JupyterTextarea,
)
from .layouts import (
    JupyterGrid, JupyterGridAdapter, JupyterHBoxAdapter, JupyterHBoxLayout,
    JupyterOverlay, JupyterOverlayAdapter, JupyterScrollView,
    JupyterScrollViewAdapter, JupyterSplitPane, JupyterSplitPaneAdapter,
    JupyterTabWidget, JupyterTabWidgetAdapter, JupyterVBoxAdapter,
    JupyterVBoxLayout, JupyterWrap, JupyterWrapAdapter,
)
from .text import (
    JupyterGroupBox, JupyterGroupBoxAdapter, JupyterImage,
    JupyterImageAdapter, JupyterLabel, JupyterLabelAdapter,
)
from .theming import (
    _generate_jupyter_css, _refresh_widget_tree, refresh_theme_jupyter,
)

__all__ = [
    "_BaseJupyterWidgetFactory",
    "_generate_jupyter_css",
    "_mark_created_widgets",
    "_refresh_widget_tree",
    "JupyterButtonAdapter",
    "JupyterCheckboxAdapter",
    "JupyterComboBox",
    "JupyterComboBoxAdapter",
    "JupyterDropdown",
    "JupyterDropdownAdapter",
    "JupyterGrid",
    "JupyterGridAdapter",
    "JupyterGroupBox",
    "JupyterGroupBoxAdapter",
    "JupyterHBoxAdapter",
    "JupyterHBoxLayout",
    "JupyterImage",
    "JupyterImageAdapter",
    "JupyterLabel",
    "JupyterLabelAdapter",
    "JupyterLineEdit",
    "JupyterLineEditAdapter",
    "JupyterNumberInputAdapter",
    "JupyterOverlay",
    "JupyterOverlayAdapter",
    "JupyterPushButton",
    "JupyterRadioGroupAdapter",
    "JupyterScrollView",
    "JupyterScrollViewAdapter",
    "JupyterSliderAdapter",
    "JupyterSplitPane",
    "JupyterSplitPaneAdapter",
    "JupyterSwitchAdapter",
    "JupyterTabWidget",
    "JupyterTabWidgetAdapter",
    "JupyterTextAreaAdapter",
    "JupyterTextarea",
    "JupyterVBoxAdapter",
    "JupyterVBoxLayout",
    "JupyterWrap",
    "JupyterWrapAdapter",
    "convert_control_text",
    "refresh_theme_jupyter",
]
