"""Gauge: an SVG dial re-rendered on every value or theme change."""
from __future__ import annotations


from ....components import IGauge
from ....models.gauge import GaugeModel
from ....visuals import render_gauge_svg
from ..runtime import get_palette, html, track_themed

class JupyterGaugeAdapter(IGauge):
    def __init__(self):
        self._model = GaugeModel()
        self._native = html("", "uniui-admin-gauge")
        track_themed(self)
        self._render()
    def get_native(self): return self._native
    def set_label(self, label: str) -> None: self._model.set_label(label); self._render()
    def set_value(self, value: float) -> None: self._model.set_value(value); self._render()
    def set_range(self, minimum: float, maximum: float) -> None:
        self._model.set_range(minimum, maximum); self._render()
    def set_unit(self, unit: str) -> None: self._model.set_unit(unit); self._render()
    def set_status(self, status: str) -> None:
        self._model.set_status(status); self._render()
    def _render(self) -> None:
        self._native.value = render_gauge_svg(*self._model.render_args(), get_palette())
    def apply_theme(self) -> None: self._render()


def gauge_css() -> str:
    """The Gauge CSS fragment, composed into the shell sheet by ``styles.css``.

    Gauge and Chart share one selector list because both render a single
    responsive ``<svg>`` into the same kind of wrapper; keeping one copy avoids
    the two drifting apart. :func:`..chart.chart_css` returns the same block.
    """
    return """.uniui-admin-gauge,.uniui-admin-chart {width:100%;min-width:0}
.uniui-admin-gauge svg,.uniui-admin-chart svg {display:block;width:100%;height:auto;max-height:250px}"""
