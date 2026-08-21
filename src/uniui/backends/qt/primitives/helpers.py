"""Small shared helpers for the Qt primitive adapters."""
from __future__ import annotations

import socket
from urllib.request import urlopen

from PySide2 import QtWidgets


def has_method(o, name):
    """Check if object has a callable method"""
    return callable(getattr(o, name, None))


def is_qlayout(native) -> bool:
    """True if ``native`` is a Qt layout manager, not a widget.

    A UniUI widget's ``get_native()`` can return either — Qt's pure-layout
    interfaces (``IVBoxLayout``/``IHBoxLayout``/``IGrid``) hand back a raw
    ``QLayout``, which has no widget-level API (no ``show``/``setEnabled``/
    Qt composition methods that expect a widget). Every composition point
    that can't accept a layout directly needs to check this first.
    """
    return isinstance(native, QtWidgets.QLayout)


def ensure_qwidget(native) -> QtWidgets.QWidget:
    """Return ``native`` unchanged if it's already a widget; otherwise wrap
    the ``QLayout`` in a plain container ``QWidget``.

    Use this at any composition point that requires a real widget
    (``QScrollArea.setWidget``, ``QStackedWidget.addWidget``, ``QSplitter``,
    a top-level window) — as opposed to points that can add a layout
    natively (``QVBoxLayout.addLayout``), which should branch on
    :func:`is_qlayout` themselves rather than always wrapping.
    """
    if is_qlayout(native):
        wrapper = QtWidgets.QWidget()
        wrapper.setLayout(native)
        return wrapper
    return native
def convert_control_text(text):
    """Convert control text to appropriate type"""
    try:
        return float(text)
    except ValueError:
        return text
def check_connection():
    """Check if internet connection is available"""
    try:
        host = socket.gethostbyname('www.google.com')
        s = socket.create_connection((host, 80), 2)
        return True
    except:
        return False
