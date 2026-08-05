"""Text and display primitives: labels, images, group boxes."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, List, Optional

from nicegui import ui

from ....core import *
from ....strategies import normalize_text, parse_float
from ....theme import THEME, is_dark
from .state import T, register_adapter

from .base import _WebAdapter
from .helpers import _plain_html, _style_size

class WebLabelAdapter(_WebAdapter, ILabel):
    def __init__(self):
        super().__init__(ui.label("").classes("uniui-label"))
        self._apply_theme()

    def set_text(self, text: str) -> None:
        self._native.set_text(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.text)

    def _apply_theme(self) -> None:
        self._native.style(f"color: {T.get('fg_muted', T['fg'])}")
class WebGroupBoxAdapter(_WebAdapter, IGroupBox):
    def __init__(self):
        card = ui.card().classes("uniui-group")
        with card:
            self._title = ui.label("").classes("uniui-group-title")
            self._content = ui.column().classes("w-full items-stretch")
        super().__init__(card)
        self._apply_theme()

    def set_title(self, title: str) -> None:
        self._title.set_text(normalize_text(title))

    def set_layout(self, layout) -> None:
        native = layout.get_native() if hasattr(layout, "get_native") else layout
        for child in list(self._content.default_slot.children):
            child.delete()
        native.move(self._content)

    def _apply_theme(self) -> None:
        self._native.style(
            f"color: {T['fg']}; background: {T['bg_input']}; "
            f"border: 1px solid {T['border']}; border-radius: {T['border_radius']}px"
        )
        self._title.style(f"color: {T.get('fg_muted', T['fg'])}")
class WebImageAdapter(_WebAdapter, IImage):
    def __init__(self):
        super().__init__(ui.image(""))

    def set_image(self, path: str) -> None:
        self._native.set_source(Path(path))

    def set_image_from_url(self, url: str) -> None:
        self._native.set_source(url)
