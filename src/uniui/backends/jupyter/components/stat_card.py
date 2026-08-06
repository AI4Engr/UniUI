"""Stat card: a single headline number with a trend line."""
from __future__ import annotations

from html import escape

import ipywidgets as widgets

from ....components import IStatCard
from ....models.stat_card import (
    TREND_DOWN, TREND_UP, normalize_card_status, trend_presentation,
)
from ....models.status import STATUS_ERROR, STATUS_WARN
from ..runtime import M, html

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


def stat_card_css() -> str:
    """The StatCard CSS fragment, composed into the shell sheet by ``styles.css``."""
    return f""".uniui-stat-card {{
  min-width:190px; min-height:136px; padding:15px 18px 14px;
  background:var(--uniui-surface); border:1px solid var(--uniui-border);
  border-radius:14px;
  box-shadow:none; gap:1px; flex:1 1 190px;
}}
.uniui-stat-label, .uniui-stat-label p {{margin:0;color:var(--uniui-text_muted);font-size:{M['stat_label_size']}px;font-weight:600}}
.uniui-stat-value, .uniui-stat-value p {{margin:2px 0 0;color:var(--uniui-text);font-size:{M['stat_value_size']}px;line-height:1.15;font-weight:750}}
.uniui-stat-unit, .uniui-stat-unit p {{margin:0;color:var(--uniui-text_muted);font-size:11px}}
.uniui-stat-trend, .uniui-stat-trend p {{margin:9px 0 0;color:var(--uniui-text_muted);font-size:11px;font-weight:650}}
.uniui-stat-trend.uniui-up, .uniui-stat-trend.uniui-up p {{color:var(--uniui-ok)}}
.uniui-stat-trend.uniui-down, .uniui-stat-trend.uniui-down p {{color:var(--uniui-error)}}
.uniui-stat-trend.uniui-status-warn, .uniui-stat-trend.uniui-status-warn p {{color:var(--uniui-warn)}}
.uniui-stat-trend.uniui-status-error, .uniui-stat-trend.uniui-status-error p {{color:var(--uniui-error)}}"""
