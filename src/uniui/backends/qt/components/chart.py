"""Qt IChart: line, area, and bar charts painted with QPainter."""
from __future__ import annotations

from typing import Dict, List

from PySide2 import QtCore, QtGui, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import IChart
from ....models.chart import ChartModel
from ..runtime import C, track_themed


class _ChartWidget(QtWidgets.QWidget):
    """Line/area/bar chart painted with QPainter.

    State lives in a shared :class:`ChartModel`; the attributes below stay as
    plain properties so ``paintEvent`` reads them directly.
    """

    def __init__(self):
        super().__init__()
        self.model = ChartModel()
        self.setMinimumSize(320, 210)
        self.setAccessibleName("Data chart")

    chart_type = property(lambda self: self.model.chart_type,
                          lambda self, v: self.model.set_type(v))
    title = property(lambda self: self.model.title,
                     lambda self, v: self.model.set_title(v))
    x_values = property(lambda self: self.model.x_values)
    series = property(lambda self: self.model.series)

    def paintEvent(self, _event) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        title_height = 28 if self.title else 10
        plot = QtCore.QRectF(48, title_height, max(40, self.width() - 64),
                             max(40, self.height() - title_height - 28))
        if self.title:
            font = QtGui.QFont(self.font()); font.setPixelSize(13); font.setBold(True)
            painter.setFont(font); painter.setPen(QtGui.QColor(C["text"]))
            painter.drawText(QtCore.QRectF(8, 2, self.width() - 16, 22),
                             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, self.title)
        message = self.model.overlay_text()
        if message:
            painter.setPen(QtGui.QColor(C["text_muted"]))
            painter.drawText(plot, QtCore.Qt.AlignCenter, message)
            return
        values = [value for item in self.series for value in item.get("data", [])]
        low, high = min(values), max(values)
        if low == high:
            low -= 1.0; high += 1.0
        padding = (high - low) * 0.08
        low -= padding; high += padding
        grid_pen = QtGui.QPen(QtGui.QColor(C["border"]), 1)
        painter.setPen(grid_pen)
        for index in range(5):
            y = plot.top() + plot.height() * index / 4
            painter.drawLine(QtCore.QPointF(plot.left(), y), QtCore.QPointF(plot.right(), y))
        colors = [C["accent"], C["ok"], C["warn"], C["error"]]
        for series_index, item in enumerate(self.series):
            data = item.get("data", [])
            if not data:
                continue
            color = QtGui.QColor(colors[series_index % len(colors)])
            points = []
            for index, value in enumerate(data):
                x = plot.left() + plot.width() * index / max(1, len(data) - 1)
                y = plot.bottom() - ((value - low) / (high - low)) * plot.height()
                points.append(QtCore.QPointF(x, y))
            if self.chart_type == "bar":
                slot = plot.width() / max(1, len(data))
                bar_width = max(3.0, slot * 0.62 / max(1, len(self.series)))
                painter.setPen(QtCore.Qt.NoPen); painter.setBrush(color)
                for index, point in enumerate(points):
                    x = plot.left() + index * slot + slot * 0.19 + series_index * bar_width
                    painter.drawRoundedRect(
                        QtCore.QRectF(x, point.y(), bar_width, plot.bottom() - point.y()), 3, 3
                    )
                continue
            path = QtGui.QPainterPath(points[0])
            for point in points[1:]:
                path.lineTo(point)
            if self.chart_type == "area":
                area = QtGui.QPainterPath(path)
                area.lineTo(points[-1].x(), plot.bottom())
                area.lineTo(points[0].x(), plot.bottom())
                area.closeSubpath()
                fill = QtGui.QColor(color); fill.setAlpha(38)
                painter.fillPath(area, fill)
            pen = QtGui.QPen(color, 2.4)
            pen.setCapStyle(QtCore.Qt.RoundCap); pen.setJoinStyle(QtCore.Qt.RoundJoin)
            painter.setPen(pen); painter.setBrush(QtCore.Qt.NoBrush); painter.drawPath(path)


class QtChartAdapter(VisibilityMixin, EnableMixin, SizeMixin, IChart):
    def __init__(self):
        self._widget = _ChartWidget()
        track_themed(self, self._widget)

    def get_native(self): return self._widget
    def set_type(self, chart_type: str) -> None:
        self._widget.model.set_type(chart_type); self._widget.update()
    def set_title(self, title: str) -> None:
        self._widget.model.set_title(title); self._widget.update()
    def set_data(self, x: List, series: List[Dict]) -> None:
        self._widget.model.set_data(x, series); self._widget.update()
    def append_data(self, x, values) -> None:
        self._widget.model.append_data(x, values); self._widget.update()
    def set_max_points(self, max_points: int) -> None:
        self._widget.model.set_max_points(max_points); self._widget.update()
    def set_loading(self, loading: bool) -> None:
        self._widget.model.set_loading(loading); self._widget.update()
    def set_error(self, message: str) -> None:
        self._widget.model.set_error(message); self._widget.update()
    def apply_theme(self) -> None: self._widget.update()
