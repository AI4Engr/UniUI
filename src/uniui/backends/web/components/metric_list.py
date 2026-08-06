"""Metric list: a dense two-column key/value list."""
from __future__ import annotations

from typing import Dict, List

from nicegui import ui

from ....components import IMetricList
from ..primitives import _WebAdapter
from ..runtime import clear
from ..styles import install_admin_css

class WebMetricListAdapter(_WebAdapter, IMetricList):
    """Dense two-column key/value list for secondary metrics."""

    def __init__(self):
        install_admin_css()
        root = ui.column().classes("w-full items-stretch gap-0")
        super().__init__(root)

    def set_items(self, items: List[Dict]) -> None:
        clear(self._native)
        with self._native:
            for index, item in enumerate(items):
                classes = "w-full uniui-web-metric-row"
                if index > 0:
                    classes += " uniui-metric-divider"
                with ui.row().classes(classes):
                    ui.label(str(item.get("label", ""))).classes("uniui-web-metric-label")
                    ui.label(str(item.get("value", ""))).classes("uniui-web-metric-value")


def metric_list_css() -> str:
    """The MetricList CSS fragment, composed into the sheet by ``styles.install_admin_css``."""
    return """        .uniui-web-metric-row {padding:8px 0!important;justify-content:space-between!important;align-items:center!important}
        .uniui-web-metric-row.uniui-metric-divider {border-top:1px solid var(--uniui-border)}
        .uniui-web-metric-label {color:var(--uniui-text_muted)!important;font-size:var(--uniui-stat-label-size)}
        .uniui-web-metric-value {color:var(--uniui-text)!important;font-size:13px;font-weight:600}
"""
