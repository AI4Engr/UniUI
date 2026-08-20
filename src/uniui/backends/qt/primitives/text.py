"""Text and display primitives: labels, images, group boxes."""
from __future__ import annotations

from typing import Callable, List, Optional
from urllib.request import urlopen

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSplitter, QStackedWidget, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget,
)

from ....core import *
from ...._adapter_mixins import (
    ClearMixin, EnableMixin, NativeMixin, SelectionMixin, SizeMixin, TextMixin,
    VisibilityMixin,
)
from ....strategies import normalize_text, parse_float
from .helpers import check_connection


class QTLabel(QtWidgets.QLabel):
    """Qt Label Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def setText(self, text):
        super().setText(text)

    def getText(self):
        return super().text()

    def setTextColor(self, text_color, background):
        color_string = 'color: ' + text_color + ';  background-color: ' + background
        super().setStyleSheet(color_string)

    def setFixedWidth(self, width):
        super().setFixedWidth(width)

    def hide(self):
        super().hide()

    def show(self):
        super().show()
class QTImage(QtWidgets.QLabel):
    """Qt Image Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def setImage(self, source):
        """Set image from binary data or file path"""
        if isinstance(source, bytes):
            image = QtGui.QImage()
            image.loadFromData(source, 'PNG')
            self.setPixmap(QtGui.QPixmap.fromImage(image))
        else:
            # Assume it's a file path
            pixmap = QtGui.QPixmap(source)
            super().setPixmap(pixmap)
        self.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

    def setImageFromUrl(self, url_str):
        has_internet = check_connection()

        if has_internet:
            url = urlopen(url_str)
            data = url.read()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            super().setPixmap(pixmap)

    def setFixedWidth(self, width):
        super().setFixedWidth(width)
class QTGroupBox(QtWidgets.QGroupBox):
    """Qt Group Box Widget - native implementation"""
    def __init__(self):
        super().__init__()

    def setTitle(self, title):
        super().setTitle(title)

    def setLayout(self, layout):
        super().setLayout(layout)
class QtLabelAdapter(NativeMixin, TextMixin, VisibilityMixin, EnableMixin, SizeMixin, ILabel):
    """Qt Label adapter - implements snake_case interface convention"""
class QtImageAdapter(VisibilityMixin, EnableMixin, IImage):
    """Qt Image adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTImage):
        self._native = native_widget

    def get_native(self):
        return self._native

    # IImageCapable
    def set_image(self, path: str):
        self._native.setImage(path)

    def set_image_from_url(self, url: str):
        self._native.setImageFromUrl(url)

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)
class QtGroupBoxAdapter(VisibilityMixin, EnableMixin, SizeMixin, IGroupBox):
    """Qt GroupBox adapter - implements snake_case interface convention"""

    def __init__(self, native_widget: QTGroupBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # IContainerCapable
    def set_layout(self, layout: IWidget):
        self._native.setLayout(layout.get_native())

    # ITitleCapable
    def set_title(self, title: str):
        self._native.setTitle(title)
