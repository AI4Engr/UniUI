"""Chart: an SVG chart rendered server-side, so it must re-render on a theme change."""
from __future__ import annotations

from typing import Dict, List

from nicegui import ui

from ....components import IChart
from ....models.chart import ChartModel
from ....visuals import render_chart_svg
from ..primitives import _WebAdapter
from ..runtime import get_palette, track_visual
from ..styles import install_admin_css

class WebChartAdapter(_WebAdapter, IChart):
    def __init__(self):
        install_admin_css()
        self._model = ChartModel()
        super().__init__(ui.html("", sanitize=False).classes("uniui-web-chart"))
        track_visual(self); self._render()
    def set_type(self, chart_type: str) -> None:
        self._model.set_type(chart_type); self._render()
    def set_title(self, title: str) -> None: self._model.set_title(title); self._render()
    def set_data(self, x: List, series: List[Dict]) -> None:
        self._model.set_data(x, series); self._render()
    def append_data(self, x, values) -> None:
        self._model.append_data(x, values); self._render()
    def set_max_points(self, max_points: int) -> None:
        self._model.set_max_points(max_points); self._render()
    def _render(self) -> None:
        self._native.set_content(
            render_chart_svg(*self._model.render_args(), get_palette())
        )
    def apply_theme(self) -> None: self._render()


def chart_css() -> str:
    """The Chart CSS fragment; :func:`..gauge.gauge_css` owns the shared text."""
    from .gauge import gauge_css
    return gauge_css()
