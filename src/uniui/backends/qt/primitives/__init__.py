"""Qt primitive widgets: the controls every Qt app gets, split by category.

The Admin components live one level up in ``backends.qt.components``. The split
between the two is what ``_BaseQtWidgetFactory`` marks: a plain Qt app never
imports the Admin adapters, and neither layer reaches into the other.

``uniui.qt`` re-exports everything here, so existing imports keep working.
"""
from __future__ import annotations

from .factory import _BaseQtWidgetFactory
from .helpers import check_connection, convert_control_text, has_method
from .inputs import (
    QTComboBox, QTDropdown, QTLineEdit, QTPushButton, QTTextarea,
    QtButtonAdapter, QtComboBoxAdapter, QtDropdownAdapter, QtLineEditAdapter,
    QtTextAreaAdapter,
)
from .layouts import (
    QTHBoxLayout, QTTabWidget, QTVBoxLayout, _QFlowLayout, _ResizeNotifier,
    QtGridAdapter, QtHBoxAdapter, QtOverlayAdapter, QtScrollViewAdapter,
    QtSplitPaneAdapter, QtTabWidgetAdapter, QtVBoxAdapter, QtWrapAdapter,
)
from .text import (
    QTGroupBox, QTImage, QTLabel, QtGroupBoxAdapter, QtImageAdapter,
    QtLabelAdapter,
)

__all__ = [
    "_BaseQtWidgetFactory",
    "_QFlowLayout",
    "_ResizeNotifier",
    "QTComboBox",
    "QTDropdown",
    "QTGroupBox",
    "QTHBoxLayout",
    "QTImage",
    "QTLabel",
    "QTLineEdit",
    "QTPushButton",
    "QTTabWidget",
    "QTTextarea",
    "QTVBoxLayout",
    "QtButtonAdapter",
    "QtComboBoxAdapter",
    "QtDropdownAdapter",
    "QtGridAdapter",
    "QtGroupBoxAdapter",
    "QtHBoxAdapter",
    "QtImageAdapter",
    "QtLabelAdapter",
    "QtLineEditAdapter",
    "QtOverlayAdapter",
    "QtScrollViewAdapter",
    "QtSplitPaneAdapter",
    "QtTabWidgetAdapter",
    "QtTextAreaAdapter",
    "QtVBoxAdapter",
    "QtWrapAdapter",
    "check_connection",
    "convert_control_text",
    "has_method",
]
