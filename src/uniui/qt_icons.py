"""Qt renderer for the backend-neutral Admin SVG icon set."""
from __future__ import annotations

from typing import Optional

from PySide2 import QtCore, QtGui, QtSvg

from .icons import svg_icon


def admin_pixmap(name: str, color: str, size: int = 20) -> QtGui.QPixmap:
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)
    renderer = QtSvg.QSvgRenderer(
        QtCore.QByteArray(svg_icon(name, color=color, size=size).encode("utf-8"))
    )
    painter = QtGui.QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def admin_icon(name: str, color: str, size: int = 20,
               selected_color: Optional[str] = None) -> QtGui.QIcon:
    icon = QtGui.QIcon()
    icon.addPixmap(
        admin_pixmap(name, color, size), QtGui.QIcon.Normal, QtGui.QIcon.Off
    )
    if selected_color:
        icon.addPixmap(
            admin_pixmap(name, selected_color, size),
            QtGui.QIcon.Selected,
            QtGui.QIcon.Off,
        )
    return icon


__all__ = ["admin_icon", "admin_pixmap"]
