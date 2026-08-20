"""Text and display primitives: labels, images, group boxes."""
from __future__ import annotations

from typing import Callable, List, Optional

import ipywidgets as widgets
from IPython.display import display

from ....core import *
from ...._adapter_mixins import (
    ClearMixin, EnableMixin, JupyterEnableMixin, JupyterSizeMixin,
    JupyterVisibilityMixin, NativeMixin, SelectionMixin, SizeMixin, TextMixin,
    VisibilityMixin,
)
from ....strategies import normalize_text, parse_float
from ....theme import THEME, is_dark

#: Alias for the live theme dict. ``THEME`` is mutated in place on a theme
#: switch, so this is a view of the current palette, not a snapshot.
T = THEME


class JupyterLabel(widgets.Label):
    """Jupyter Label Widget - native implementation"""
    def __init__(self):
        super().__init__()
        self.style.description_width = '0px'
        self.layout.width = 'auto'

    def setText(self, text):
        self.value = text
        self.disabled = True

    def getText(self):
        return self.value

    def setFixedWidth(self, width):
        self.layout.width = str(width) + 'px'

    def setFixedHeight(self, height):
        self.layout.height = str(height) + 'px'

    def setMinimumWidth(self, width):
        self.layout.min_width = str(width) + 'px'

    def setMinimumHeight(self, height):
        self.layout.min_height = str(height) + 'px'

    def hide(self):
        self.layout.display = 'none'

    def show(self):
        self.layout.display = None

    def isVisible(self):
        return self.layout.display != 'none'
class JupyterGroupBox(widgets.VBox):
    """Jupyter GroupBox - emulated using VBox with a styled HTML title"""
    def __init__(self):
        self._title_widget = widgets.HTML(value='')
        self._content_box = widgets.VBox()
        self._content_box.layout.border = f'1px solid {T["border"]}'
        self._content_box.layout.padding = f'{T["padding_inner"]}px'
        super().__init__(children=[self._title_widget, self._content_box])
        self.layout.margin = '4px 0'

    def setTitle(self, title):
        self._title_widget.value = (
            f'<b style="color:{T["fg"]};font-size:{T["font_size"]}pt">{title}</b>'
        )

    def setLayout(self, layout):
        """Set the content layout (a VBox/HBox native widget)"""
        if isinstance(layout, (widgets.Box, widgets.VBox, widgets.HBox)):
            self._content_box.children = (layout,)
        elif hasattr(layout, 'children'):
            self._content_box.children = (layout,)
class JupyterImage(widgets.Image):
    """Jupyter Image Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def setFixedWidth(self, width):
        self.layout.width = str(width) + 'px'

    def setFixedHeight(self, height):
        self.layout.height = str(height) + 'px'

    def setMinimumWidth(self, width):
        self.layout.min_width = str(width) + 'px'

    def setMinimumHeight(self, height):
        self.layout.min_height = str(height) + 'px'

    def setImage(self, image):
        with open(image, "rb") as file:
            self.value = file.read()

    def setImageFromUrl(self, url):
        raise NotSupportedError(
            "Image URL loading is not supported in the Jupyter backend. "
            "Use setImage with a local file path."
        )
class JupyterLabelAdapter(NativeMixin, TextMixin, VisibilityMixin, JupyterEnableMixin, SizeMixin, ILabel):
    """Jupyter Label adapter - implements snake_case interface convention"""
class JupyterGroupBoxAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, IGroupBox):
    """Jupyter GroupBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterGroupBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITitleCapable
    def set_title(self, title: str):
        self._native.setTitle(title)

    # IContainerCapable
    def set_layout(self, layout):
        if hasattr(layout, 'get_native'):
            self._native.setLayout(layout.get_native())
        else:
            self._native.setLayout(layout)
class JupyterImageAdapter(JupyterVisibilityMixin, JupyterEnableMixin, IImage):
    """Jupyter Image adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: JupyterImage):
        self._native = native_widget

    def get_native(self):
        return self._native

    # IImageCapable
    def set_image(self, path: str):
        self._native.setImage(path)

    def set_image_from_url(self, url: str):
        self._native.setImageFromUrl(url)

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)
