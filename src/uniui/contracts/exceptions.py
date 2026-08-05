"""UniUI exception hierarchy."""

from __future__ import annotations


class UniUIException(Exception):
    """Base exception for all UniUI errors"""
    pass
class NotSupportedError(UniUIException):
    """Raised when a widget type is not supported on a specific platform."""
    pass
class WidgetCreationError(UniUIException):
    """Raised when widget creation fails."""
    pass
class InvalidValueError(UniUIException):
    """Raised when a value cannot be parsed or is invalid"""
    pass
class ConfigurationError(UniUIException):
    """Raised when there's a configuration problem"""
    pass
