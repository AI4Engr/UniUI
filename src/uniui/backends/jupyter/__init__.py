"""Jupyter/ipywidgets Admin backend.

Importing this package pulls in ``ipywidgets``; importing :mod:`uniui.backends`
alone does not. Layout is kept in CSS where possible, but note that ipywidgets
wraps every child in its own DOM node, so anything that has to size a *flex
item* must be set inline via ``widget.layout`` - a CSS class never reaches the
element that is actually the flex item.
"""
from .runtime import (
    get_palette,
    is_dark,
    set_theme,
)

__all__ = ["get_palette", "is_dark", "set_theme"]
