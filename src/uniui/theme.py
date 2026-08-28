"""The design tokens every backend renders from.

This is the single source of truth.  It used to be split in two: this module
held a calculator-flavoured palette (``fg``/``bg_input``/``accent_op``) while
``admin_theme`` held a second, more complete one (``text``/``input_bg``/
``surface``).  The two disagreed on shared names — ``accent`` was indigo here
and blue there — and fought each other at runtime.

The tokens below are the former Admin set, which is the more complete of the
two.  The older names are kept as aliases pointing at the same values, so
existing backends keep working unchanged:

    fg -> text        fg_muted -> text_muted
    bg_input -> input_bg          border_radius -> radius_medium

Public API:
- THEME: the active palette, **mutated in place** so that modules which did
  ``from .theme import THEME`` see theme switches without re-importing.
  Never rebind this name.
- toggle_theme() -> bool  (returns True if now dark)
- set_theme(dark) -> bool
- is_dark() -> bool

Beyond the built-in light/dark pair, additional named themes can be
registered (from a dict or a JSON file) and switched to by name:
- register_theme(name, palette, *, dark, metrics=None) -> None
- set_active_theme(name) -> str
- get_active_theme_name() -> str
- list_themes() -> List[str]

``set_theme``/``toggle_theme``/``is_dark`` are unchanged and keep working
exactly as before — they are a boolean-typed special case of the same
mechanism, not a separate code path: ``set_theme(dark)`` just calls
``set_active_theme("dark" if dark else "light")``.
"""
from __future__ import annotations

import json
import warnings
from typing import Any, Dict, List

from . import theme_registry

try:
    from importlib.resources import read_text as _read_resource_text
except ImportError:  # pragma: no cover - importlib.resources always exists on 3.8+
    from importlib_resources import read_text as _read_resource_text


# ---------------------------------------------------------------------------
# Colour tokens
# ---------------------------------------------------------------------------
#
# Every built-in theme -- including light/dark -- is stored as JSON in the
# uniui.themes package, not as a Python dict literal here. That keeps "ship a
# new built-in theme" a data change (add a .json file, list it below) rather
# than a code change, and means a theme registered by a user
# (uniui.register_theme) and a theme shipped with the library go through the
# exact same validation path in theme_registry.register_theme.
#
# read_text() rather than the newer files()/as_file() API: this package
# targets Python 3.8, and files() needs 3.9+. read_text is deprecated (not
# removed) starting 3.11 in favour of files() -- the warning is suppressed
# here rather than left to leak into every importing application's console.

#: (registry name, filename in uniui/themes/, is this theme dark-leaning)
_BUILTIN_THEMES = (
    ("light", "light.json", False),
    ("dark", "dark.json", True),
    ("ocean", "ocean.json", True),
    ("midnight", "midnight.json", True),
    ("sand", "sand.json", False),
    ("sunset", "sunset.json", False),
)


def _load_bundled_colors(filename: str) -> Dict[str, str]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        text = _read_resource_text("uniui.themes", filename)
    return json.loads(text)


LIGHT: Dict[str, str] = _load_bundled_colors("light.json")
DARK: Dict[str, str] = _load_bundled_colors("dark.json")


# ---------------------------------------------------------------------------
# Sizing and typography
# ---------------------------------------------------------------------------

METRICS: Dict[str, Any] = {
    "font_family": '"Segoe UI Variable Text", "Segoe UI", sans-serif',
    "font_size": 13,
    "radius_small": 8,
    "radius_medium": 10,
    "radius_large": 14,
    "header_height": 60,
    "footer_height": 36,
    "sidebar_expanded": 212,
    "sidebar_collapsed": 72,
    "sidebar_min": 168,
    "sidebar_max": 360,
    "sidebar_edge_width": 2,
    "content_padding": 32,
    "section_gap": 32,
    "card_gap": 12,
    "card_padding": 18,
    "control_height": 38,
    "stat_value_size": 26,
    "stat_label_size": 12,

    # -- Systematic spacing scale -----------------------------------------
    # Widget-level margins/gaps should reference these instead of a literal
    # pixel count, so the whole Admin surface moves together when the scale
    # changes rather than needing a per-widget hunt.
    "space_1": 4,
    "space_2": 8,
    "space_3": 12,
    "space_4": 16,
    "space_5": 24,
    "space_6": 32,

    # -- Typography scale ---------------------------------------------------
    # Secondary/muted text defaulted to whatever a widget's author picked
    # (9-12px scattered across components); this gives them one shared floor.
    "text_xs": 11,
    "text_sm": 12,
    "text_base": 13,
    "text_lg": 15,
}


# Names the pre-merge palette used, mapped onto their current equivalents.
# Keeping them means qt.py / jupyter.py / web.py / display.py need no edits.
_ALIASES = {
    "fg": "text",
    "fg_muted": "text_muted",
    "bg_input": "input_bg",
    "border_radius": "radius_medium",
}

# Tokens the old palette had that have no counterpart in the current design
# tokens.  All four are still live: `fg_button` (text on an accent-filled
# button) and the spacing values are read by the Qt, Jupyter and Web
# renderers alike, so they are not removable without a palette redesign.
_LEGACY_EXTRAS = {
    "fg_button": "#ffffff",
    "padding": 14,
    "padding_inner": 4,
    "spacing": 4,
}


def _build_palette(colors: Dict[str, str], metrics: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build a full palette from color tokens: colors + metrics + legacy aliases.

    ``metrics`` defaults to the shared ``METRICS`` — sizing/typography is a
    layout concern, not a palette one, so every theme shares it unless it
    explicitly opts into an override.
    """
    palette: Dict[str, Any] = dict(colors)
    palette.update(metrics if metrics is not None else METRICS)
    palette.update(_LEGACY_EXTRAS)
    for old_name, current_name in _ALIASES.items():
        palette[old_name] = palette[current_name]
    return palette


def _palette(dark: bool) -> Dict[str, Any]:
    """Build a full palette: tokens + metrics + legacy aliases."""
    return _build_palette(DARK if dark else LIGHT)


THEME_LIGHT = _palette(False)
THEME_DARK = _palette(True)

# Start in dark mode by default for a modern feel.
THEME = dict(THEME_DARK)

_is_dark = True
_active_theme_name = "dark"

theme_registry._set_required_keys(LIGHT.keys())

# light/dark go through register_built_theme: their palettes are already
# built above (THEME_LIGHT/THEME_DARK), so re-validating and rebuilding them
# from the same JSON a second time would be redundant work for no benefit.
# Every other built-in theme goes through the same register_theme() path a
# user's own uniui.register_theme() call would use, proving a bundled theme
# gets no special treatment beyond being listed in _BUILTIN_THEMES.
theme_registry.register_built_theme("light", THEME_LIGHT, dark=False)
theme_registry.register_built_theme("dark", THEME_DARK, dark=True)
for _name, _filename, _dark in _BUILTIN_THEMES:
    if _name in ("light", "dark"):
        continue
    theme_registry.register_theme(
        _name, _load_bundled_colors(_filename), dark=_dark, _build=_build_palette
    )
del _name, _filename, _dark


def set_active_theme(name: str) -> str:
    """Switch the active palette to the named theme. Returns ``name``.

    THEME is updated in place, same as ``set_theme`` — modules holding a
    reference to it see the new values immediately.  ``is_dark()`` is
    updated from the theme's own registered ``dark`` flag, so it stays
    truthful for any theme, not just the built-in light/dark pair; this is
    also what lets the Web backend's ``ui.dark_mode()`` call stay correct
    for a custom theme without any Web-specific code change.
    """
    global _is_dark, _active_theme_name
    palette = theme_registry.get_theme(name)
    THEME.update(palette)
    _active_theme_name = name
    _is_dark = theme_registry.is_theme_dark(name)
    return _active_theme_name


def get_active_theme_name() -> str:
    """Return the name of the currently active theme."""
    return _active_theme_name


def register_theme(
    name: str, palette: Any, *, dark: bool, metrics: Dict[str, Any] = None
) -> None:
    """Register a named theme so it can be passed to ``set_active_theme``.

    ``palette`` is a dict of color tokens (the same shape as ``LIGHT``/
    ``DARK``) or a path to a JSON file holding that shape.  Raises
    ``ValueError`` naming any missing required tokens.
    """
    theme_registry.register_theme(name, palette, dark=dark, metrics=metrics, _build=_build_palette)


def list_themes() -> List[str]:
    """Return every registered theme name, sorted."""
    return theme_registry.list_themes()


def set_theme(dark: bool) -> bool:
    """Switch between the built-in light and dark themes. Returns True if now dark.

    THEME is updated in place; modules holding a reference to it see the new
    values immediately.  A special case of ``set_active_theme`` — the
    boolean API and the named API can never disagree about what ended up in
    THEME because they are the same code path.
    """
    set_active_theme("dark" if dark else "light")
    return _is_dark


def toggle_theme() -> bool:
    """Toggle between light and dark theme. Returns True if now dark."""
    return set_theme(not _is_dark)


def is_dark() -> bool:
    """Return True if current theme is dark."""
    return _is_dark


def get_tokens(dark: bool = False) -> Dict[str, str]:
    """Return a mutable copy of the selected colour palette."""
    return dict(DARK if dark else LIGHT)


def get_metrics() -> Dict[str, Any]:
    """Return a mutable copy of the sizing and typography tokens."""
    return dict(METRICS)


# Names from when these tokens lived in a separate `admin_theme` module.
ADMIN_LIGHT = LIGHT
ADMIN_DARK = DARK
ADMIN_METRICS = METRICS
get_admin_tokens = get_tokens
get_admin_metrics = get_metrics


__all__ = [
    "ADMIN_DARK",
    "ADMIN_LIGHT",
    "ADMIN_METRICS",
    "DARK",
    "LIGHT",
    "METRICS",
    "THEME",
    "THEME_DARK",
    "THEME_LIGHT",
    "get_active_theme_name",
    "get_admin_metrics",
    "get_admin_tokens",
    "get_metrics",
    "get_tokens",
    "is_dark",
    "list_themes",
    "register_theme",
    "set_active_theme",
    "set_theme",
    "toggle_theme",
]
