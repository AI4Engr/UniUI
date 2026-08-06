"""Qt IGauge: a radial gauge painted with QPainter."""
from __future__ import annotations

from PySide2 import QtCore, QtGui, QtWidgets

from ....components import IGauge
from ....models.gauge import GaugeModel
from ..effects import animate_value
from ..runtime import C, track_themed


class _GaugeWidget(QtWidgets.QWidget):
    """Radial gauge painted with QPainter.

    State lives in a shared :class:`GaugeModel`; the attributes below stay as
    plain properties so ``paintEvent`` reads them directly.
    """

    def __init__(self):
        super().__init__()
        self.model = GaugeModel()
        self.setMinimumSize(190, 180)
        self.setAccessibleName("Radial gauge")

    label = property(lambda self: self.model.label,
                     lambda self, v: self.model.set_label(v))
    unit = property(lambda self: self.model.unit,
                    lambda self, v: self.model.set_unit(v))
    status = property(lambda self: self.model.status,
                      lambda self, v: self.model.set_status(v))
    minimum = property(lambda self: self.model.minimum)
    maximum = property(lambda self: self.model.maximum)

    @property
    def value(self) -> float:
        return self.model.value

    @value.setter
    def value(self, value: float) -> None:
        # Set directly rather than through the model so the animation can push
        # intermediate values without them being treated as a new target.
        self.model.value = float(value)

    def paintEvent(self, _event) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        side = min(self.width(), self.height() - 28)
        arc_size = max(80.0, min(150.0, side - 28.0))
        rect = QtCore.QRectF(
            (self.width() - arc_size) / 2,
            10,
            arc_size,
            arc_size,
        )
        pen = QtGui.QPen(QtGui.QColor(C["border"]), 13)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, -225 * 16, -270 * 16)

        ratio = self.model.ratio
        pen.setColor(QtGui.QColor(C.get(self.status, C["accent"])))
        painter.setPen(pen)
        painter.drawArc(rect, -225 * 16, int(-270 * 16 * ratio))

        value_font = QtGui.QFont(self.font())
        value_font.setPixelSize(25)
        value_font.setBold(True)
        painter.setFont(value_font)
        painter.setPen(QtGui.QColor(C["text"]))
        center = rect.adjusted(0, 32, 0, -20)
        painter.drawText(center, QtCore.Qt.AlignCenter, f"{self.value:g}")

        unit_font = QtGui.QFont(self.font())
        unit_font.setPixelSize(11)
        painter.setFont(unit_font)
        painter.setPen(QtGui.QColor(C["text_muted"]))
        painter.drawText(
            QtCore.QRectF(rect.left(), rect.center().y() + 17, rect.width(), 20),
            QtCore.Qt.AlignCenter,
            self.unit,
        )
        label_font = QtGui.QFont(self.font())
        label_font.setPixelSize(12)
        label_font.setWeight(QtGui.QFont.DemiBold)
        painter.setFont(label_font)
        painter.drawText(
            QtCore.QRectF(8, self.height() - 28, self.width() - 16, 20),
            QtCore.Qt.AlignCenter,
            self.label,
        )


class QtGaugeAdapter(IGauge):
    def __init__(self):
        self._widget = _GaugeWidget()
        self._target_value = 0.0
        track_themed(self, self._widget)

    def get_native(self): return self._widget
    def set_label(self, label: str) -> None:
        self._widget.label = str(label); self._widget.update()
    def set_unit(self, unit: str) -> None:
        self._widget.unit = str(unit); self._widget.update()
    def set_range(self, minimum: float, maximum: float) -> None:
        self._widget.model.set_range(minimum, maximum)
        self._widget.update()
    def set_status(self, status: str) -> None:
        self._widget.status = status
        self._widget.update()
    def set_value(self, value: float) -> None:
        self._target_value = float(value)
        animate_value(
            self._widget,
            self._widget.value,
            self._target_value,
            self._set_display_value,
        )
    def _set_display_value(self, value: float) -> None:
        self._widget.value = value
        self._widget.setAccessibleDescription(
            self._widget.model.accessible_description()
        )
        self._widget.update()
    def apply_theme(self) -> None: self._widget.update()
