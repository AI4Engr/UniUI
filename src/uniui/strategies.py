"""
Value parsing helpers.

Simple functions for converting widget text to typed values.
"""
from typing import Optional, Union


def parse_float(text: str, default: float = 0.0) -> float:
    """Parse text to float, returning *default* for empty/whitespace."""
    text = text.strip()
    if not text:
        return default
    return float(text)


def parse_int(text: str, default: int = 0) -> int:
    """Parse text to int, returning *default* for empty/whitespace."""
    text = text.strip()
    if not text:
        return default
    return int(text)


def parse_flexible(text: str) -> Union[float, str]:
    """Try to parse as float; fall back to stripped string."""
    text = text.strip()
    try:
        return float(text)
    except ValueError:
        return text


def normalize_text(text: Optional[str]) -> str:
    """Normalize text: None -> '', otherwise strip whitespace."""
    if text is None:
        return ""
    return str(text).strip()
