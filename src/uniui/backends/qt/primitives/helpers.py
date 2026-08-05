"""Small shared helpers for the Qt primitive adapters."""
from __future__ import annotations

import socket
from urllib.request import urlopen


def has_method(o, name):
    """Check if object has a callable method"""
    return callable(getattr(o, name, None))
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
