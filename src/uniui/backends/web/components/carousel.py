"""Web ICarousel: an image slideshow, backed by NiceGUI's native carousel."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, List

from nicegui import ui

from ....components import ICarousel
from ....state import Handle, safe_call
from ..primitives import _WebAdapter


class WebCarouselAdapter(_WebAdapter, ICarousel):
    def __init__(self):
        self._paths: List[str] = []
        self._slides: List = []
        self._callbacks: List[Callable[[], None]] = []
        #: Bumped on every set_auto_advance(True, ...) call so a stale
        #: rescheduled tick from an earlier interval can tell it's no
        #: longer current and stop rescheduling itself.
        self._generation = 0

        native = ui.carousel(arrows=True, navigation=True).classes("w-full")
        native.style("height: 200px")
        super().__init__(native)
        native.on_value_change(lambda _event: self._emit_change())

    def set_images(self, paths: List[str]) -> None:
        for slide in self._slides:
            slide.delete()
        self._slides = []
        self._paths = list(paths)
        with self._native:
            for i, path in enumerate(self._paths):
                with ui.carousel_slide(name=self._slide_name(i)) as slide:
                    ui.image(Path(path)).classes("w-full h-full")
                self._slides.append(slide)
        if self._paths:
            self._native.set_value(self._slide_name(0))

    def next_slide(self) -> None:
        if not self._paths:
            return
        self.set_current_index((self.get_current_index() + 1) % len(self._paths))

    def previous_slide(self) -> None:
        if not self._paths:
            return
        self.set_current_index((self.get_current_index() - 1) % len(self._paths))

    def get_current_index(self) -> int:
        if not self._paths:
            return 0
        current = self._native.value
        for i in range(len(self._paths)):
            if self._slide_name(i) == current:
                return i
        return 0

    def set_current_index(self, index: int) -> None:
        if not self._paths:
            return
        index = max(0, min(index, len(self._paths) - 1))
        self._native.set_value(self._slide_name(index))

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
            safe_call(callback, backend="web", component="Carousel", method="on_change")

    @staticmethod
    def _slide_name(index: int) -> str:
        return f"slide-{index}"
