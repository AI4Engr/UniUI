"""Stat card: a single headline number with a trend line."""
from __future__ import annotations

from html import escape

import ipywidgets as widgets

from ....components import IStatCard
from ....models.stat_card import (
    TREND_DOWN, TREND_UP, normalize_card_status, trend_presentation,
)
from ....models.status import STATUS_ERROR, STATUS_WARN
from ..runtime import html

class JupyterStatCardAdapter(IStatCard):
    def __init__(self):
        self._label = html("", "uniui-stat-label")
        self._value = html("<p>—</p>", "uniui-stat-value")
        self._unit = html("", "uniui-stat-unit")
        self._trend_widget = html(
            f"<p>{trend_presentation(0, separator=' &nbsp;').text}</p>",
            "uniui-stat-trend",
        )
        self._native = widgets.VBox([self._label, self._value, self._unit, self._trend_widget])
        self._native.add_class("uniui-stat-card")
        self._status = "ok"
        self._trend = 0.0

    def get_native(self): return self._native

    def set_label(self, label: str) -> None:
        self._label.value = f"<p>{escape(str(label))}</p>"

    def set_value(self, value: str) -> None:
        self._value.value = f"<p>{escape(str(value))}</p>"

    def set_unit(self, unit: str) -> None:
        self._unit.value = f"<p>{escape(str(unit))}</p>" if unit else ""

    def set_trend(self, trend: float) -> None:
        self._trend = float(trend)
        self._apply_trend()

    #: Trend style -> CSS class. ``flat`` needs no class of its own.
    _TREND_CLASSES = {
        TREND_UP: "uniui-up",
        TREND_DOWN: "uniui-down",
        STATUS_WARN: "uniui-status-warn",
        STATUS_ERROR: "uniui-status-error",
    }

    def _apply_trend(self) -> None:
        for name in self._TREND_CLASSES.values():
            self._trend_widget.remove_class(name)
        # ``&nbsp;`` keeps the gap around the arrow from collapsing in HTML.
        text, style = trend_presentation(self._trend, self._status, " &nbsp;")
        class_name = self._TREND_CLASSES.get(style)
        if class_name:
            self._trend_widget.add_class(class_name)
        self._trend_widget.value = f"<p>{text}</p>"

    def set_status(self, status: str) -> None:
        self._status = normalize_card_status(status)
        self._apply_trend()
