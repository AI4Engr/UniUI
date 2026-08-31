"""Page and shell-chrome CSS for the Jupyter Admin backend.

These rules style generic page content (``uniui-page-*``: headings,
subtitles, hints, field labels, stat rows) and admin-shell chrome
(``uniui-shell-*``: logo, avatar, header buttons) - vocabulary any app
built on UniUI's widgets can use via ``add_class()``, not markup specific
to any one example. No component module owns them (they aren't part of one
widget's own rules) and they aren't part of the shell container itself, so
they stay in their own functions.

They are still emitted as part of :func:`.styles.css`, in their original
position: CSS resolves ties by source order, so moving the block would change
rendering even though the text is unchanged.
"""
from __future__ import annotations

from .runtime import M


def _page_field_css() -> str:
    """Field/swatch/badge helpers for form-style page layouts."""
    return """.uniui-page-field {gap:6px; min-width:190px}
.uniui-page-field-label, .uniui-page-field-label .widget-label {
  color:var(--uniui-text_muted)!important; font-size:12px; font-weight:650;
}
.uniui-shell-swatch-row {gap:10px; align-items:center; flex-wrap:wrap!important}
.uniui-shell-swatch {
  width:34px; height:34px; border-radius:9px; border:1px solid var(--uniui-border);
  flex:0 0 34px;
}
.uniui-shell-badge-row {gap:8px; flex-wrap:wrap!important}"""


def _page_and_shell_css() -> str:
    """Page typography plus admin-shell chrome: headings, logo, avatar, header buttons."""
    return f""".uniui-page {{gap:{M['section_gap']}px;width:100%;min-width:0}}
.uniui-page-heading {{gap:16px;align-items:center;flex-wrap:nowrap!important}}
.uniui-page-subtitle .widget-label, .uniui-page-subtitle {{color:var(--uniui-text)!important;font-size:17px;font-weight:650}}
.uniui-page-hint .widget-label, .uniui-page-hint {{color:var(--uniui-text_muted)!important}}
.uniui-page-stats {{display:flex;flex-flow:row wrap;gap:{M['card_gap']}px;align-items:stretch}}
.uniui-shell-header-content {{width:100%;min-width:0;gap:8px;align-items:center;flex-wrap:nowrap!important}}
.uniui-shell-logo-mark, .uniui-shell-logo-mark .widget-label {{
  width:32px!important;min-width:32px;height:32px;display:grid;place-items:center;
  border-radius:9px;background:var(--uniui-accent);color:#fff!important;
  font-size:14px;font-weight:800;
}}
.uniui-shell-product, .uniui-shell-product .widget-label {{
  color:var(--uniui-text)!important;font-size:14px;font-weight:700;white-space:nowrap;
}}
.uniui-shell-avatar, .uniui-shell-avatar .widget-label {{
  width:32px!important;min-width:32px;height:32px;display:grid;place-items:center;
  border-radius:50%;background:var(--uniui-avatar_bg);color:var(--uniui-avatar_fg)!important;
  font-size:11px;font-weight:750;
}}
.uniui-admin-shell .uniui-shell-icon-button,
.uniui-admin-shell .uniui-shell-icon-button button {{
  width:32px!important;min-width:32px!important;height:32px;min-height:32px!important;
  padding:0!important;background:transparent!important;
  color:var(--uniui-text_muted)!important;border:1px solid transparent!important;
}}
.uniui-admin-shell .uniui-shell-icon-button button:hover {{
  background:var(--uniui-surface_subtle)!important;
  border-color:var(--uniui-border)!important;color:var(--uniui-text)!important;
}}
.uniui-admin-shell .uniui-shell-theme-button,
.uniui-admin-shell .uniui-shell-theme-button button {{
  min-height:34px!important;padding:0 12px!important;background:var(--uniui-surface)!important;
  color:var(--uniui-text)!important;border:1px solid var(--uniui-border_strong)!important;
}}
.uniui-admin-shell .uniui-shell-theme-button button:hover {{
  background:var(--uniui-surface_subtle)!important;
}}
.uniui-admin-shell .uniui-shell-primary-action,
.uniui-admin-shell .uniui-shell-primary-action button {{
  white-space:nowrap;background:var(--uniui-accent)!important;color:#fff!important;
  border-color:var(--uniui-accent)!important;
}}
.uniui-web-status-ok, .uniui-web-status-ok .widget-label {{
  color:var(--uniui-ok)!important;font-size:12px;font-weight:600;
}}
.uniui-web-footer-meta, .uniui-web-footer-meta .widget-label {{
  color:var(--uniui-text_muted)!important;font-size:12px;
}}"""
