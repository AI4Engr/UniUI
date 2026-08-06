"""Metric list: a dense two-column key/value list."""
from __future__ import annotations

from html import escape
from typing import Dict, List

import ipywidgets as widgets

from ....components import IMetricList
from ..runtime import M, html

class JupyterMetricListAdapter(IMetricList):
    """Dense two-column key/value list for secondary metrics."""

    def __init__(self):
        self._html = html("", "uniui-metric-list")
        self._native = widgets.VBox([self._html])
        self._native.add_class("uniui-metric-list-wrap")

    def get_native(self): return self._native

    def set_items(self, items: List[Dict]) -> None:
        rows = []
        for index, item in enumerate(items):
            classes = "uniui-metric-row" + (" uniui-metric-divider" if index > 0 else "")
            label = escape(str(item.get("label", "")))
            value = escape(str(item.get("value", "")))
            rows.append(
                f'<div class="{classes}"><span class="uniui-metric-label">{label}</span>'
                f'<span class="uniui-metric-value">{value}</span></div>'
            )
        self._html.value = "".join(rows)


def metric_list_css() -> str:
    """The MetricList CSS fragment, composed into the shell sheet by ``styles.css``."""
    return f""".uniui-metric-list-wrap {{width:100%; min-width:0}}
.uniui-metric-row {{display:flex; justify-content:space-between; align-items:center; padding:8px 0}}
.uniui-metric-row.uniui-metric-divider {{border-top:1px solid var(--uniui-border)}}
.uniui-metric-label {{color:var(--uniui-text_muted); font-size:{M['stat_label_size']}px}}
.uniui-metric-value {{color:var(--uniui-text); font-size:13px; font-weight:600}}"""
