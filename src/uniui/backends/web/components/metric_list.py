"""Metric list: a dense two-column key/value list."""
from __future__ import annotations

from typing import Dict, List

from nicegui import ui

from ....components import IMetricList
from ....web import _WebAdapter
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
