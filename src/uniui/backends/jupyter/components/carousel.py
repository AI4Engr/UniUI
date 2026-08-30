"""Jupyter ICarousel: an image slideshow with prev/next navigation and dots."""
from __future__ import annotations

from typing import Callable, List

import ipywidgets as widgets

from ...._adapter_mixins import (
    JupyterEnableMixin, JupyterSizeMixin, JupyterVisibilityMixin,
)
from ....components import ICarousel
from ....state import Handle, safe_call
from ..runtime import get_palette, track_themed


class JupyterCarouselAdapter(JupyterVisibilityMixin, JupyterEnableMixin,
                             JupyterSizeMixin, ICarousel):
    def __init__(self):
        self._paths: List[str] = []
        self._index = 0
        self._callbacks: List[Callable[[], None]] = []
        #: Bumped on every set_auto_advance(True, ...) call so a stale
        #: rescheduled tick from an earlier interval can tell it's no
        #: longer current and stop rescheduling itself.
        self._generation = 0

        self._image = widgets.Image(format="png")
        self._image.layout.max_height = "160px"
        self._image.layout.object_fit = "contain"

        self._prev_btn = widgets.Button(description="‹", layout=widgets.Layout(width="32px"))
        self._next_btn = widgets.Button(description="›", layout=widgets.Layout(width="32px"))
        self._prev_btn.on_click(lambda _btn: self.previous_slide())
        self._next_btn.on_click(lambda _btn: self.next_slide())

        self._dots = widgets.HTML()

        slide_row = widgets.HBox([self._prev_btn, self._image, self._next_btn])
        self._native = widgets.VBox([slide_row, self._dots])

        track_themed(self)
        self.apply_theme()
        self._render()

    def get_native(self):
        return self._native

    def set_images(self, paths: List[str]) -> None:
        self._paths = list(paths)
        self._index = 0
        self._render()

    def next_slide(self) -> None:
        if not self._paths:
            return
        self._index = (self._index + 1) % len(self._paths)
        self._render()
        self._emit_change()

    def previous_slide(self) -> None:
        if not self._paths:
            return
        self._index = (self._index - 1) % len(self._paths)
        self._render()
        self._emit_change()

    def get_current_index(self) -> int:
        return self._index

    def set_current_index(self, index: int) -> None:
        if not self._paths:
            return
        self._index = max(0, min(index, len(self._paths) - 1))
        self._render()
        self._emit_change()

    def set_auto_advance(self, enabled: bool, interval_ms: int = 3000) -> None:
        self._generation += 1
        if not enabled:
            return
        my_generation = self._generation
        interval = max(1, int(interval_ms))

        def _tick():
            if self._generation != my_generation:
                return
            self.next_slide()
            from ....display import schedule_after
            schedule_after(interval, _tick)

        from ....display import schedule_after
        schedule_after(interval, _tick)

    def on_change(self, callback: Callable[[], None]) -> Handle:
        self._callbacks.append(callback)

        def cancel():
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return Handle(cancel)

    def _emit_change(self) -> None:
        for callback in list(self._callbacks):
            safe_call(callback, backend="jupyter", component="Carousel", method="on_change")

    def _render(self) -> None:
        if not self._paths:
            self._image.value = b""
        else:
            with open(self._paths[self._index], "rb") as file:
                self._image.value = file.read()
        self._update_dots()

    def _update_dots(self) -> None:
        palette = get_palette()
        dots = []
        for i in range(len(self._paths)):
            color = palette["accent"] if i == self._index else palette["border_strong"]
            dots.append(
                f'<span style="display:inline-block;width:8px;height:8px;'
                f'border-radius:4px;margin:0 3px;background:{color};"></span>'
            )
        self._dots.value = f'<div style="text-align:center;">{"".join(dots)}</div>'

    def apply_theme(self) -> None:
        self._update_dots()
