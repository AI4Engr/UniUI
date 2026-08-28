"""Qt IStatCard: a headline metric with a unit and a trend line."""
from __future__ import annotations

from PySide2 import QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import IStatCard
from ....models.stat_card import (
    TREND_DOWN, TREND_FLAT, TREND_UP, normalize_card_status, trend_presentation,
)
from ..runtime import C, M, track_themed
from ..styles import card_style


def _label_qss() -> str:
    return (
        f"color: {C['text_muted']}; font-size: {M['stat_label_size']}px; "
        "font-weight: 600; background: transparent;"
    )


def _value_qss() -> str:
    return (
        f"color: {C['text']}; font-size: {M['stat_value_size']}px; "
        "font-weight: 700; background: transparent;"
    )


def _unit_qss() -> str:
    return f"color: {C['text_muted']}; font-size: {M['stat_label_size']}px; background: transparent;"


class QtStatCardAdapter(VisibilityMixin, EnableMixin, SizeMixin, IStatCard):
    def __init__(self):
        self._frame = QtWidgets.QFrame()
        self._frame.setProperty("card", "1")
        self._status = "ok"
        self._trend = 0.0
        self._frame.setMinimumWidth(0)
        self._frame.setFixedHeight(136)
        self._frame.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed
        )

        layout = QtWidgets.QVBoxLayout(self._frame)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(3)

        self._label_lbl = QtWidgets.QLabel("")
        self._label_lbl.setStyleSheet(_label_qss())

        self._value_lbl = QtWidgets.QLabel("—")
        self._value_lbl.setStyleSheet(_value_qss())

        self._unit_lbl = QtWidgets.QLabel("")
        self._unit_lbl.setStyleSheet(_unit_qss())
        self._unit_lbl.hide()

        self._trend_lbl = QtWidgets.QLabel("")
        self._trend_lbl.setMinimumWidth(0)
        self._trend_lbl.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred
        )
        self._trend_lbl.setStyleSheet(
            f"color: {C['text_muted']}; font-size: 12px; font-weight: 600; "
            "background: transparent;"
        )

        layout.addWidget(self._label_lbl)
        layout.addSpacing(1)
        layout.addWidget(self._value_lbl)
        layout.addWidget(self._unit_lbl)
        layout.addStretch()
        layout.addWidget(self._trend_lbl)

        self._frame.setStyleSheet(card_style())
        track_themed(self, self._frame)
        self.apply_theme()

    def get_native(self): return self._frame

    def set_label(self, label: str) -> None:
        self._label_lbl.setText(label)

    def set_value(self, value: str) -> None:
        self._value_lbl.setText(str(value))

    def set_unit(self, unit: str) -> None:
        self._unit_lbl.setText(unit)
        self._unit_lbl.setVisible(bool(unit))

    def set_trend(self, trend: float) -> None:
        self._trend = float(trend)
        self._apply_trend()

    #: Trend style -> theme token for the trend line's colour.
    _TREND_COLORS = {
        TREND_UP: "ok",
        TREND_DOWN: "error",
        TREND_FLAT: "text_muted",
    }

    def _apply_trend(self) -> None:
        text, style = trend_presentation(self._trend, self._status)
        color = C[self._TREND_COLORS.get(style, style)]
        self._trend_lbl.setText(text)
        self._trend_lbl.setStyleSheet(
            f"color: {color}; font-size: {M['stat_label_size']}px; font-weight: 600; "
            "background: transparent;"
        )

    def set_status(self, status: str) -> None:
        self._status = normalize_card_status(status)
        self._apply_trend()

    def apply_theme(self) -> None:
        self._label_lbl.setStyleSheet(_label_qss())
        self._value_lbl.setStyleSheet(_value_qss())
        self._unit_lbl.setStyleSheet(_unit_qss())
        self._frame.setStyleSheet(card_style())
        self._apply_trend()
