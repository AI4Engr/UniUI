"""Gauge: an SVG dial rendered server-side, so it must re-render on a theme change."""
from __future__ import annotations


from nicegui import ui

from ....components import IGauge
from ....models.gauge import GaugeModel
from ....visuals import render_gauge_svg
from ..primitives import _WebAdapter
from ..runtime import get_palette, track_visual
from ..styles import install_admin_css

class WebGaugeAdapter(_WebAdapter, IGauge):
    def __init__(self):
        install_admin_css()
        self._model = GaugeModel()
        super().__init__(ui.html("", sanitize=False).classes("uniui-web-gauge"))
        track_visual(self)
        self._render()
    def set_label(self, label: str) -> None: self._model.set_label(label); self._render()
    def set_value(self, value: float) -> None: self._model.set_value(value); self._render()
    def set_range(self, minimum: float, maximum: float) -> None:
        self._model.set_range(minimum, maximum); self._render()
    def set_unit(self, unit: str) -> None: self._model.set_unit(unit); self._render()
    def set_status(self, status: str) -> None:
        self._model.set_status(status); self._render()
    def _render(self) -> None:
        self._native.set_content(
            render_gauge_svg(*self._model.render_args(), get_palette())
        )
    def apply_theme(self) -> None: self._render()


def gauge_css() -> str:
    """The Gauge CSS fragment, composed into the sheet by ``styles.install_admin_css``.

    Gauge and Chart share one selector list because both render a single
    responsive ``<svg>``; :func:`..chart.chart_css` returns the same block.
    """
    return """        .uniui-web-gauge,.uniui-web-chart {width:100%;min-width:0}
        .uniui-web-gauge svg,.uniui-web-chart svg {display:block;width:100%;height:auto;max-height:250px}
"""
