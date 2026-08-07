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
"""
from __future__ import annotations

from typing import Any, Dict


# ---------------------------------------------------------------------------
# Colour tokens
# ---------------------------------------------------------------------------

LIGHT: Dict[str, str] = {
    "bg": "#f6f8fc",
    "surface": "#ffffff",
    "surface_subtle": "#f8fafc",
    "text": "#182230",
    "text_muted": "#667085",
    "border": "#e7ebf0",
    "border_strong": "#d5dae1",
    "accent": "#2563eb",
    "accent_hover": "#1d4ed8",
    "accent_press": "#1e40af",
    "accent_soft": "#eff6ff",
    "accent_op": "#0891b2",
    "accent_op_hover": "#0e7490",
    "accent_op_press": "#155e75",
    "accent_sci": "#059669",
    "accent_sci_hover": "#047857",
    "accent_sci_press": "#065f46",
    "accent_action": "#ea580c",
    "accent_action_hover": "#c2410c",
    "accent_action_press": "#9a3412",
    "accent_neutral": "#374151",
    "accent_neutral_hover": "#1f2937",
    "accent_neutral_press": "#111827",
    "ok": "#16a34a",
    "warn": "#d97706",
    "error": "#dc2626",
    "sidebar_bg": "#111827",
    "sidebar_fg": "#cbd5e1",
    "sidebar_active": "#182235",
    "sidebar_hover": "#182235",
    "sidebar_edge": "#2563eb",
    "sidebar_active_fg": "#ffffff",
    "header_bg": "#ffffff",
    "header_border": "#e7ebf0",
    "input_bg": "#ffffff",
    "row_alt": "#f8fafc",
    "row_selected": "#eff6ff",
    "row_selected_fg": "#1d4ed8",
    "disabled": "#bfdbfe",
    "scrollbar": "#cbd5e1",
    "avatar_bg": "#dbeafe",
    "avatar_fg": "#1d4ed8",
    "status_ok_bg": "#dcfce7",
    "status_ok_fg": "#15803d",
    "status_warn_bg": "#fef3c7",
    "status_warn_fg": "#b45309",
    "status_error_bg": "#fee2e2",
    "status_error_fg": "#b91c1c",
    "status_neutral_bg": "#f1f5f9",
    "status_neutral_fg": "#475569",
    "shadow": "0 1px 2px rgba(16,24,40,.04),0 4px 12px rgba(16,24,40,.04)",
}

DARK: Dict[str, str] = {
    "bg": "#0b0f19",
    "surface": "#121826",
    "surface_subtle": "#182131",
    "text": "#f1f5f9",
    "text_muted": "#94a3b8",
    "border": "#263244",
    "border_strong": "#344154",
    "accent": "#60a5fa",
    "accent_hover": "#93c5fd",
    "accent_press": "#3b82f6",
    "accent_soft": "#172554",
    "accent_op": "#0891b2",
    "accent_op_hover": "#22d3ee",
    "accent_op_press": "#67e8f9",
    "accent_sci": "#059669",
    "accent_sci_hover": "#10b981",
    "accent_sci_press": "#34d399",
    "accent_action": "#ea580c",
    "accent_action_hover": "#f97316",
    "accent_action_press": "#fb923c",
    "accent_neutral": "#334155",
    "accent_neutral_hover": "#475569",
    "accent_neutral_press": "#64748b",
    "ok": "#4ade80",
    "warn": "#fbbf24",
    "error": "#f87171",
    "sidebar_bg": "#0d1220",
    "sidebar_fg": "#94a3b8",
    "sidebar_active": "#1b2740",
    "sidebar_hover": "#161f33",
    "sidebar_edge": "#60a5fa",
    "sidebar_active_fg": "#ffffff",
    "header_bg": "#111726",
    "header_border": "#1f2a3c",
    "input_bg": "#182131",
    "row_alt": "#141b2a",
    "row_selected": "#172554",
    "row_selected_fg": "#bfdbfe",
    "disabled": "#1e293b",
    "scrollbar": "#475569",
    "avatar_bg": "#1e3a8a",
    "avatar_fg": "#dbeafe",
    "status_ok_bg": "#0f2a1d",
    "status_ok_fg": "#86efac",
    "status_warn_bg": "#2a2010",
    "status_warn_fg": "#fcd34d",
    "status_error_bg": "#3b1720",
    "status_error_fg": "#fda4af",
    "status_neutral_bg": "#1e293b",
    "status_neutral_fg": "#cbd5e1",
    "shadow": "0 1px 2px rgba(0,0,0,.25),0 8px 24px rgba(0,0,0,.16)",
}


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
    "sidebar_expanded": 236,
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
    "stat_label_size": 11,
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


def _palette(dark: bool) -> Dict[str, Any]:
    """Build a full palette: tokens + metrics + legacy aliases."""
    palette: Dict[str, Any] = dict(DARK if dark else LIGHT)
    palette.update(METRICS)
    palette.update(_LEGACY_EXTRAS)
    for old_name, current_name in _ALIASES.items():
        palette[old_name] = palette[current_name]
    return palette


THEME_LIGHT = _palette(False)
THEME_DARK = _palette(True)

# Start in dark mode by default for a modern feel.
THEME = dict(THEME_DARK)

_is_dark = True


def set_theme(dark: bool) -> bool:
    """Switch the active palette. Returns True if now dark.

    THEME is updated in place; modules holding a reference to it see the new
    values immediately.
    """
    global _is_dark
    _is_dark = bool(dark)
    THEME.update(THEME_DARK if _is_dark else THEME_LIGHT)
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
    "get_admin_metrics",
    "get_admin_tokens",
    "get_metrics",
    "get_tokens",
    "is_dark",
    "set_theme",
    "toggle_theme",
]
