"""Shared design tokens for Admin interfaces across all primary backends.

Backends are free to render these tokens differently (QSS, CSS variables,
inline styles), but they should not invent separate colors or layout metrics.
"""
from __future__ import annotations

from typing import Any, Dict


ADMIN_LIGHT: Dict[str, str] = {
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


ADMIN_DARK: Dict[str, str] = {
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
    "ok": "#4ade80",
    "warn": "#fbbf24",
    "error": "#fb7185",
    "sidebar_bg": "#080c14",
    "sidebar_fg": "#cbd5e1",
    "sidebar_active": "#141c2b",
    "sidebar_hover": "#111827",
    "sidebar_edge": "#60a5fa",
    "sidebar_active_fg": "#ffffff",
    "header_bg": "#121826",
    "header_border": "#263244",
    "input_bg": "#182131",
    "row_alt": "#182131",
    "row_selected": "#172554",
    "row_selected_fg": "#dbeafe",
    "disabled": "#334155",
    "scrollbar": "#475569",
    "avatar_bg": "#172554",
    "avatar_fg": "#dbeafe",
    "status_ok_bg": "#143322",
    "status_ok_fg": "#86efac",
    "status_warn_bg": "#3a2a0c",
    "status_warn_fg": "#fcd34d",
    "status_error_bg": "#3b1720",
    "status_error_fg": "#fda4af",
    "status_neutral_bg": "#1e293b",
    "status_neutral_fg": "#cbd5e1",
    "shadow": "0 1px 2px rgba(0,0,0,.25),0 8px 24px rgba(0,0,0,.16)",
}


ADMIN_METRICS: Dict[str, Any] = {
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


def get_admin_tokens(dark: bool = False) -> Dict[str, str]:
    """Return a mutable copy of the selected shared Admin palette."""
    return dict(ADMIN_DARK if dark else ADMIN_LIGHT)


def get_admin_metrics() -> Dict[str, Any]:
    """Return a mutable copy of shared Admin sizing and typography tokens."""
    return dict(ADMIN_METRICS)


__all__ = [
    "ADMIN_LIGHT",
    "ADMIN_DARK",
    "ADMIN_METRICS",
    "get_admin_tokens",
    "get_admin_metrics",
]
