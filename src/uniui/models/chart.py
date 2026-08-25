"""Shared state model for charts.

Type validation, the rolling ``max_points`` window, and series normalisation
were implemented identically in all three backends. This model owns them;
rendering stays with the backend (QPainter for Qt,
:func:`uniui.visuals.render_chart_svg` for the browser backends).
"""
from typing import Any, Dict, List

from ..visuals import CHART_TYPES, append_chart_point, normalized_series

DEFAULT_CHART_TYPE = "line"
DEFAULT_MAX_POINTS = 120

#: Two points are the minimum that can describe a line.
MIN_MAX_POINTS = 2


class ChartModel:
    """Type, title, x values, series, and the loading/error/empty overlay
    decision for a chart."""

    __slots__ = (
        "chart_type", "title", "x_values", "series", "max_points",
        "_loading", "_error",
    )

    def __init__(self, max_points: int = DEFAULT_MAX_POINTS):
        self.chart_type = DEFAULT_CHART_TYPE
        self.title = ""
        self.x_values: List[Any] = []
        self.series: List[Dict] = []
        self.max_points = max(MIN_MAX_POINTS, int(max_points))
        self._loading = False
        self._error = ""

    def set_type(self, chart_type) -> None:
        """Unknown chart types fall back to ``line``."""
        self.chart_type = (
            chart_type if chart_type in CHART_TYPES else DEFAULT_CHART_TYPE
        )

    def set_title(self, title) -> None:
        self.title = str(title)

    def set_data(self, x, series) -> None:
        self.x_values = list(x)
        self.series = normalized_series(series)
        self._trim()

    def append_data(self, x, values) -> None:
        append_chart_point(self.x_values, self.series, x, values, self.max_points)

    def set_max_points(self, max_points) -> None:
        self.max_points = max(MIN_MAX_POINTS, int(max_points))
        self._trim()

    def _trim(self) -> None:
        """Drop everything outside the trailing ``max_points`` window."""
        self.x_values = self.x_values[-self.max_points:]
        for item in self.series:
            item["data"] = item["data"][-self.max_points:]

    def render_args(self):
        """Positional arguments for :func:`uniui.visuals.render_chart_svg`."""
        return (self.chart_type, self.title, self.x_values, self.series)

    # -- overlay state ---------------------------------------------------
    def set_loading(self, loading) -> None:
        self._loading = bool(loading)

    def set_error(self, message) -> None:
        self._error = str(message) if message else ""

    @property
    def loading(self) -> bool:
        return self._loading

    @property
    def error(self) -> str:
        return self._error

    @property
    def has_data(self) -> bool:
        return any(item.get("data") for item in self.series)

    @property
    def shows_overlay(self) -> bool:
        """Whether a status message replaces the chart right now."""
        return self._loading or bool(self._error) or not self.has_data

    def overlay_text(self) -> str:
        """Text for the loading/error/empty overlay, or ``""`` when the chart
        draws. Same priority as Table: error beats loading beats empty."""
        if self._error:
            return f"⚠  {self._error}"
        if self._loading:
            return "Loading…"
        if not self.has_data:
            return "No data"
        return ""
