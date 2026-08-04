"""Qt IMetricList: a dense two-column key/value list."""
from __future__ import annotations

from typing import Dict, List, Tuple

from PySide2 import QtCore, QtWidgets

from ....components import IMetricList
from ..runtime import C, M, clear_layout, track_themed

class QtMetricListAdapter(IMetricList):
    """Dense two-column key/value list for secondary metrics."""

    def __init__(self):
        self._frame = QtWidgets.QWidget()
        self._frame.setMinimumWidth(0)
        self._layout = QtWidgets.QVBoxLayout(self._frame)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._rows: List[Tuple[QtWidgets.QWidget, QtWidgets.QLabel, QtWidgets.QLabel]] = []
        track_themed(self, self._frame)
        self.apply_theme()

    def get_native(self): return self._frame

    def set_items(self, items: List[Dict]) -> None:
        clear_layout(self._layout)
        self._rows = []
        for index, item in enumerate(items):
            row = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(0, 8, 0, 8)
            label = QtWidgets.QLabel(str(item.get("label", "")))
            value = QtWidgets.QLabel(str(item.get("value", "")))
            value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            row_layout.addWidget(label, stretch=1)
            row_layout.addWidget(value)
            if index > 0:
                row.setProperty("metricDivider", "1")
            self._layout.addWidget(row)
            self._rows.append((row, label, value))
        self.apply_theme()

    def apply_theme(self) -> None:
        for row, label, value in self._rows:
            label.setStyleSheet(
                f"color: {C['text_muted']}; font-size: {M['stat_label_size']}px; background: transparent;"
            )
            value.setStyleSheet(
                f"color: {C['text']}; font-size: 13px; font-weight: 600; background: transparent;"
            )
            if row.property("metricDivider"):
                row.setStyleSheet(f"border-top: 1px solid {C['border']};")
