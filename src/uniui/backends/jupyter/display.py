"""Jupyter display and theme refresh.

Moved out of the root ``display.py``, which is now a thin dispatcher.

The theme refresh itself lives in ``primitives/theming.py`` — it is part of the
primitive layer because plain controls need it even when the app builds no
AppShell.  This module re-exports it under the dispatcher's naming convention
so ``display.py`` can treat all three backends the same way.
"""
from __future__ import annotations

from .primitives.theming import refresh_theme_jupyter as refresh_theme


def show(native, set_refresh_root=None) -> bool:
    """Jupyter display method.  Returns True when it took ownership."""
    try:
        from IPython.display import display
        import ipywidgets

        # Check if it's an ipywidgets widget
        if isinstance(native, (ipywidgets.Widget, ipywidgets.Box)):
            # Store root widget reference for theme refresh
            if set_refresh_root:
                set_refresh_root(native)

            # Apply initial theme
            refresh_theme(native)

            # Publish the base widget stylesheet so plain controls are
            # styled even when the app builds no AppShell.
            try:
                from .primitives.styles import style_widget_html
                display(style_widget_html())
            except ImportError:
                pass

            display(native)
            return True

    except (ImportError, AttributeError):
        pass

    return False


def show_forced(container) -> None:
    """Force display using Jupyter, bypassing framework detection."""
    from IPython.display import display
    display(container.get_native())


# Jupyter scheduling stays in the root dispatcher on purpose.  It is a plain
# ``asyncio`` running-loop check with no ipywidgets involvement, and this module
# imports ipywidgets at import time — delegating here would drag the toolkit
# into every Qt and fallback schedule.


__all__ = ["refresh_theme", "show", "show_forced"]
