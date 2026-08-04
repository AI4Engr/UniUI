"""Stat card: a single headline number with a trend line."""
from __future__ import annotations


from nicegui import ui

from ....components import IStatCard
from ....models.stat_card import (
    TREND_DOWN, TREND_UP, normalize_card_status, trend_presentation,
)
from ....models.status import STATUS_ERROR, STATUS_WARN
from ....web import _WebAdapter
from ..styles import install_admin_css

class WebStatCardAdapter(_WebAdapter, IStatCard):
    def __init__(self):
        install_admin_css()
        card = ui.card().classes("uniui-web-stat")
        with card:
            self._label = ui.label("").classes("uniui-web-stat-label")
            self._value = ui.label("—").classes("uniui-web-stat-value")
            self._unit = ui.label("").classes("uniui-web-stat-unit")
            self._trend_label = ui.label(
                trend_presentation(0).text
            ).classes("uniui-web-stat-trend")
        super().__init__(card)
        self._status = "ok"
        self._trend = 0.0

    def set_label(self, label: str) -> None: self._label.set_text(str(label))
    def set_value(self, value: str) -> None: self._value.set_text(str(value))
    def set_unit(self, unit: str) -> None: self._unit.set_text(str(unit))
    def set_trend(self, trend: float) -> None:
        self._trend = float(trend)
        self._apply_trend()
    #: Trend style -> CSS class. ``flat`` needs no class of its own.
    _TREND_CLASSES = {
        TREND_UP: "uniui-up",
        TREND_DOWN: "uniui-down",
        STATUS_WARN: "uniui-warn",
        STATUS_ERROR: "uniui-error",
    }

    def _apply_trend(self) -> None:
        self._trend_label.classes(remove=" ".join(self._TREND_CLASSES.values()))
        text, style = trend_presentation(self._trend, self._status)
        self._trend_label.set_text(text)
        class_name = self._TREND_CLASSES.get(style)
        if class_name:
            self._trend_label.classes(add=class_name)

    def set_status(self, status: str) -> None:
        self._status = normalize_card_status(status)
        self._apply_trend()
