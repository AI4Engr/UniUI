"""
Qt/PySide2 backend.

Native widgets, adapters, and factory for the Qt platform.
Each widget class wraps a PySide2 widget and exposes the IWidget interface.

The implementation now lives in :mod:`uniui.backends.qt.primitives`, split by
category (text, inputs, layouts, factory). This module stays as the public
import surface: ``from uniui.qt import QtLabelAdapter`` and friends keep
working, and so do the names this module has always re-exported incidentally -
the ``core`` interfaces, the adapter mixins, and the bare ``QtWidgets`` /
``QtCore`` / ``QtGui`` modules, which callers have been reaching through.
"""
from __future__ import annotations
from typing import List, Optional, Callable
from urllib.request import urlopen
import socket

# Import capability interfaces from core
from .core import *
from ._adapter_mixins import (
    ClearMixin, EnableMixin, NativeMixin, SelectionMixin, SizeMixin,
    TextMixin, VisibilityMixin,
)
from .strategies import normalize_text, parse_float

# Qt imports
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import (
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QVBoxLayout, QHBoxLayout, QWidget,
    QTabWidget, QGroupBox, QScrollArea, QSplitter, QStackedWidget
)
from PySide2.QtCore import Qt

from .backends.qt.primitives import (
    QTCheckbox, QTComboBox, QTDropdown, QTGroupBox, QTHBoxLayout, QTImage,
    QTLabel, QTLineEdit, QTNumberInput, QTPushButton, QTRadioGroup, QTSwitch,
    QTTabWidget, QTTextarea, QTVBoxLayout, QtButtonAdapter, QtCheckboxAdapter,
    QtComboBoxAdapter, QtDropdownAdapter, QtGridAdapter, QtGroupBoxAdapter,
    QtHBoxAdapter, QtImageAdapter, QtLabelAdapter, QtLineEditAdapter,
    QtNumberInputAdapter, QtOverlayAdapter, QtRadioGroupAdapter,
    QtScrollViewAdapter, QtSplitPaneAdapter, QtSwitchAdapter,
    QtTabWidgetAdapter, QtTextAreaAdapter, QtVBoxAdapter, QtWrapAdapter,
    _BaseQtWidgetFactory, _QFlowLayout, _ResizeNotifier,
    check_connection, convert_control_text, has_method,
)
