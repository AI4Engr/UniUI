"""A registry of named palettes, keyed by name rather than a light/dark bool.

``theme.py`` owns the two shipped themes (``"light"``, ``"dark"``) and the
boolean API built on top of them.  This module owns the mechanism that lets
more themes be registered alongside those two — from a Python dict or a JSON
file — without changing what a "theme" *is*: the same flat set of color
tokens ``LIGHT``/``DARK`` already use, plus the shared sizing/typography
tokens and legacy aliases every backend expects to find.

A theme is validated against ``REQUIRED_KEYS`` before it is stored, so a
palette missing a token fails at registration time with the name of every
missing key — not later, as a ``KeyError`` in the middle of QSS or CSS
interpolation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Union

_REGISTRY: Dict[str, Dict[str, Any]] = {}
_DARK_FLAGS: Dict[str, bool] = {}

#: The color-token keys every theme must supply, derived from ``LIGHT`` by
#: the caller (``theme.py``) so this module never hand-duplicates the list
#: and cannot drift from the source of truth.
REQUIRED_KEYS: FrozenSet[str] = frozenset()


def _set_required_keys(keys) -> None:
    """Called once by ``theme.py`` at import time to seed ``REQUIRED_KEYS``."""
    global REQUIRED_KEYS
    REQUIRED_KEYS = frozenset(keys)


def _load_json(path: Union[str, Path]) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not load theme JSON from {path!r}: {exc}") from exc


def register_theme(
    name: str,
    palette: Union[Dict[str, Any], str, Path],
    *,
    dark: bool,
    metrics: Dict[str, Any] = None,
    _build: Any = None,
) -> None:
    """Register a named theme, validating it against ``REQUIRED_KEYS``.

    ``palette`` is either a dict of color tokens or a path to a JSON file
    holding the same flat shape.  ``dark`` marks whether this theme should be
    treated as dark-leaning — the Web backend needs this to drive NiceGUI's
    own dark-mode baseline, since ``ui.dark_mode()`` is inherently a boolean
    toggle regardless of how many named themes exist above it.

    Raises ``ValueError`` naming every missing required key and leaves the
    registry unchanged if validation fails — a partially registered theme
    would otherwise surface as a ``KeyError`` deep inside stylesheet
    generation, far from the actual mistake.

    ``_build`` is an internal hook: ``theme.py`` passes its palette builder
    so a registered theme gets the same METRICS/alias/legacy-extras
    treatment as the built-in light/dark themes, without this module
    depending on ``theme.py``'s internals directly (avoiding a circular
    import — ``theme.py`` imports this module, not the other way round).
    """
    if isinstance(palette, (str, Path)):
        colors = _load_json(palette)
    else:
        colors = dict(palette)

    missing = REQUIRED_KEYS - set(colors.keys())
    if missing:
        raise ValueError(
            f"theme {name!r} is missing required tokens: {sorted(missing)}"
        )

    built = _build(colors, metrics) if _build is not None else dict(colors)
    _REGISTRY[name] = built
    _DARK_FLAGS[name] = bool(dark)


def register_built_theme(name: str, built_palette: Dict[str, Any], *, dark: bool) -> None:
    """Register an already-fully-built palette (METRICS/aliases included).

    Used internally to seed the registry with ``THEME_LIGHT``/``THEME_DARK``,
    which are built once at ``theme.py`` import time and should not be
    re-validated or rebuilt.
    """
    _REGISTRY[name] = dict(built_palette)
    _DARK_FLAGS[name] = bool(dark)


def get_theme(name: str) -> Dict[str, Any]:
    """Return a copy of the named theme's fully-built palette."""
    if name not in _REGISTRY:
        raise KeyError(f"no theme registered as {name!r}; known: {sorted(_REGISTRY)}")
    return dict(_REGISTRY[name])


def list_themes() -> List[str]:
    """Return every registered theme name, sorted."""
    return sorted(_REGISTRY)


def is_theme_dark(name: str) -> bool:
    """Return the ``dark`` flag a theme was registered with."""
    if name not in _DARK_FLAGS:
        raise KeyError(f"no theme registered as {name!r}; known: {sorted(_REGISTRY)}")
    return _DARK_FLAGS[name]


__all__ = [
    "REQUIRED_KEYS",
    "get_theme",
    "is_theme_dark",
    "list_themes",
    "register_built_theme",
    "register_theme",
]
