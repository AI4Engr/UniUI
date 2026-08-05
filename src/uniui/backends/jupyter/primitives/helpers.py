"""Text coercion shared by the Jupyter primitive adapters."""
from __future__ import annotations


def convert_control_text(text):
    """Convert control text to appropriate type"""
    try:
        return float(text)
    except ValueError:
        return text
