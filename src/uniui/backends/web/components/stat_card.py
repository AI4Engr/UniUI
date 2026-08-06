"""Stat card: a single headline number with a trend line."""
from __future__ import annotations


from nicegui import ui

from ....components import IStatCard
from ....models.stat_card import (
    TREND_DOWN, TREND_UP, normalize_card_status, trend_presentation,
)
from ....models.status import STATUS_ERROR, STATUS_WARN
from ..primitives import _WebAdapter
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


def stat_card_css() -> str:
    """The StatCard CSS fragment, composed into the sheet by ``styles.install_admin_css``."""
    return """        .uniui-web-stat {min-width:190px;min-height:136px;flex:1 1 190px;padding:15px 18px!important;gap:1px!important;
          border:1px solid var(--uniui-border)!important;
          border-radius:14px!important;background:var(--uniui-surface)!important;box-shadow:none!important}
        .uniui-web-stat-label {color:var(--uniui-text_muted);font-size:var(--uniui-stat-label-size);font-weight:600}
        .uniui-web-stat-value {color:var(--uniui-text);font-size:var(--uniui-stat-value-size);line-height:1.15;font-weight:750}
        .uniui-web-stat-unit {color:var(--uniui-text_muted);font-size:11px}
        .uniui-web-stat-trend {margin-top:auto;color:var(--uniui-text_muted);font-size:11px;font-weight:650}
        .uniui-web-stat-trend.uniui-up {color:var(--uniui-ok)} .uniui-web-stat-trend.uniui-down {color:var(--uniui-error)}
        .uniui-web-stat-trend.uniui-warn {color:var(--uniui-warn)} .uniui-web-stat-trend.uniui-error {color:var(--uniui-error)}
"""
