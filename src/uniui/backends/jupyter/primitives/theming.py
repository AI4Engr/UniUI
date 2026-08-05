"""Theme CSS generation and live widget-tree restyling."""
from __future__ import annotations

from typing import Callable, List, Optional

import ipywidgets as widgets
from IPython.display import display

from ....core import *
from ...._adapter_mixins import (
    ClearMixin, EnableMixin, NativeMixin, SelectionMixin, SizeMixin, TextMixin,
    VisibilityMixin,
)
from ....strategies import normalize_text, parse_float
from ....theme import THEME, is_dark

#: Alias for the live theme dict. ``THEME`` is mutated in place on a theme
#: switch, so this is a view of the current palette, not a snapshot.
T = THEME


from .text import JupyterGroupBox

#: The single live ``<style>`` node, reused across theme switches so a refresh
#: rewrites the existing widget instead of prepending another one. This is
#: mutable module state, not a re-export: it must be read and written here, so
#: a test that needs to reset it has to patch this module, not ``uniui.jupyter``.
_jupyter_css_widget = None


def _generate_jupyter_css():
    """Generate CSS for Jupyter widgets based on current THEME."""
    return f"""
    <style>
    .uniui-themed {{ background-color: {T["bg"]} !important; }}
    .uniui-themed .widget-label {{ color: {T["fg"]} !important; }}
    .uniui-themed .widget-text input {{
        background-color: {T["bg_input"]} !important;
        color: {T["fg"]} !important;
    }}
    .uniui-themed .widget-dropdown select {{
        background-color: {T["bg_input"]} !important;
        color: {T["fg"]} !important;
        appearance: none !important;
        -webkit-appearance: none !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12'%3E%3Cpath d='M2 4 L6 8 L10 4' fill='none' stroke='{T["fg"].replace("#", "%23")}' stroke-width='2'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: right 8px center !important;
        padding-right: 28px !important;
    }}
    .uniui-themed .widget-button button {{
        background-color: {T["accent"]} !important;
        color: {T["fg_button"]} !important;
        border: none !important;
        border-radius: {T.get('border_radius', 8)}px !important;
        min-height: 32px !important;
        font-weight: 600 !important;
    }}
    .uniui-themed .widget-button button:hover {{
        filter: brightness(1.15) !important;
    }}
    .uniui-themed .widget-box {{
        background-color: {T["bg"]} !important;
    }}
    .uniui-themed .widget-html b {{
        color: {T["fg"]} !important;
    }}
    .uniui-themed .widget-box > .widget-box {{
        border-color: {T["border"]} !important;
    }}
    .jp-OutputArea-output:has(.uniui-themed) {{
        background-color: {T["bg"]} !important;
    }}
    </style>
    """
def refresh_theme_jupyter(root_widget):
    """Refresh Jupyter widget theme.

    Uses CSS injection for background/dropdown + inline style for text colors.

    This used to skip Admin shells, which carried a second, disagreeing
    palette; both now render from uniui.theme, so one pass suits every tree.

    Args:
        root_widget: The root ipywidgets container (VBox/HBox)
    """
    global _jupyter_css_widget

    # CSS injection for background and elements that don't support inline style
    root_widget.add_class('uniui-themed')
    css_html = _generate_jupyter_css()

    if _jupyter_css_widget is None:
        _jupyter_css_widget = widgets.HTML(value=css_html)
        children = list(root_widget.children)
        root_widget.children = tuple([_jupyter_css_widget] + children)
    else:
        _jupyter_css_widget.value = css_html

    # Inline style for text colors, button colors, etc.
    _refresh_widget_tree(root_widget)
def _refresh_widget_tree(w):
    """Recursively apply THEME colors to all widgets in the tree."""
    if isinstance(w, widgets.Button):
        # Honour btntype if set
        btntype = getattr(w, '_btntype', None)
        _BTNTYPE_KEY = {
            'action':  'accent_action',
            'op':      'accent_op',
            'sci':     'accent_sci',
            'neutral': 'accent_neutral',
        }
        key = _BTNTYPE_KEY.get(btntype, 'accent')
        w.style.button_color = T[key]
        w.style.text_color = T["fg_button"]
    elif isinstance(w, (widgets.Text, widgets.FloatText, widgets.IntText)):
        w.style.text_color = T["fg"]
    elif isinstance(w, widgets.Label):
        w.style.text_color = T["fg"]
    elif isinstance(w, widgets.HTML):
        # Re-render HTML content with new theme colors (for GroupBox titles)
        if '<b' in w.value:
            import re
            w.value = re.sub(
                r'color:[^;"]+',
                f'color:{T["fg"]}',
                w.value
            )

    # Update GroupBox content border
    if isinstance(w, JupyterGroupBox):
        w._content_box.layout.border = f'1px solid {T["border"]}'

    # Recurse into children
    if hasattr(w, 'children'):
        for child in w.children:
            _refresh_widget_tree(child)
