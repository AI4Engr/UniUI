"""
Theme configuration.

Defines THEME_LIGHT and THEME_DARK color palettes.
THEME is the active palette dict, modified in-place by toggle_theme().
All platform modules reference THEME for colors, fonts, spacing.

Public API:
- toggle_theme() -> bool  (returns True if now dark)
- is_dark() -> bool
"""

THEME_LIGHT = {
    # Colors
    "bg":               "#f0f2f5",    # panel/container background
    "bg_input":         "#ffffff",    # input field background
    "fg":               "#1a1a2e",    # primary text color
    "fg_button":        "#ffffff",    # button text color
    "fg_muted":         "#6b7280",    # muted text (labels, titles)
    "accent":           "#4f46e5",    # primary accent (num buttons)
    "accent_hover":     "#4338ca",    # num button hover
    "accent_press":     "#3730a3",    # num button pressed
    # Operator buttons (teal)
    "accent_op":        "#0891b2",
    "accent_op_hover":  "#0e7490",
    "accent_op_press":  "#155e75",
    # Scientific function buttons (emerald green)
    "accent_sci":       "#059669",
    "accent_sci_hover": "#047857",
    "accent_sci_press": "#065f46",
    # Action buttons (= and C) — amber/orange
    "accent_action":       "#ea580c",
    "accent_action_hover": "#c2410c",
    "accent_action_press": "#9a3412",
    # Neutral (dark mode toggle)
    "accent_neutral":       "#374151",
    "accent_neutral_hover": "#1f2937",
    "accent_neutral_press": "#111827",
    "border":           "#d1d5db",    # border color

    # Font
    "font_family":  "Segoe UI",
    "font_size":    10,

    # Spacing (pixels)
    "padding":       14,          # root container padding
    "padding_inner":  4,          # inner widget padding
    "spacing":        4,          # layout spacing
    "border_radius":  8,          # border radius (Qt only)
}

THEME_DARK = {
    # Colors
    "bg":               "#0f1117",    # deep navy background
    "bg_input":         "#1a1d2e",    # slightly lighter input bg
    "fg":               "#e2e8f0",    # primary text color
    "fg_button":        "#ffffff",    # button text color
    "fg_muted":         "#94a3b8",    # muted labels
    "accent":           "#4f46e5",    # indigo — num buttons
    "accent_hover":     "#6366f1",
    "accent_press":     "#818cf8",
    # Operator buttons (cyan/teal)
    "accent_op":        "#0891b2",
    "accent_op_hover":  "#22d3ee",
    "accent_op_press":  "#67e8f9",
    # Scientific function buttons (emerald green)
    "accent_sci":       "#059669",
    "accent_sci_hover": "#10b981",
    "accent_sci_press": "#34d399",
    # Action buttons (= and C) — orange
    "accent_action":       "#ea580c",
    "accent_action_hover": "#f97316",
    "accent_action_press": "#fb923c",
    # Neutral (dark mode toggle)
    "accent_neutral":       "#334155",
    "accent_neutral_hover": "#475569",
    "accent_neutral_press": "#64748b",
    "border":           "#1e293b",    # subtle border

    # Font
    "font_family":  "Segoe UI",
    "font_size":    10,

    # Spacing (pixels)
    "padding":       14,          # root container padding
    "padding_inner":  4,          # inner widget padding
    "spacing":        4,          # layout spacing
    "border_radius":  8,          # border radius (Qt only)
}

# Start in dark mode by default for a modern feel
THEME = dict(THEME_DARK)

_is_dark = True


def toggle_theme():
    """Toggle between light and dark theme. Returns True if now dark."""
    global _is_dark
    _is_dark = not _is_dark
    THEME.update(THEME_DARK if _is_dark else THEME_LIGHT)
    return _is_dark


def is_dark():
    """Return True if current theme is dark."""
    return _is_dark
