"""Chart: an SVG line/bar chart re-rendered on every data or theme change."""
from __future__ import annotations

from typing import Dict, List

from ....components import IChart
from ....models.chart import ChartModel
from ....visuals import render_chart_svg
from ..runtime import get_palette, html, track_themed

class JupyterChartAdapter(IChart):
    def __init__(self):
        self._model = ChartModel()
        self._native = html("", "uniui-admin-chart")
        track_themed(self); self._render()
    def get_native(self): return self._native
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
        self._native.value = render_chart_svg(*self._model.render_args(), get_palette())
    def apply_theme(self) -> None: self._render()


def chart_css() -> str:
    """The Chart CSS fragment.

    Chart and Gauge share one selector list; :func:`..gauge.gauge_css` owns the
    text. ``styles.css`` emits it once, so this is here for symmetry and for
    callers that want the chart rules on their own.
    """
    from .gauge import gauge_css
    return gauge_css()
