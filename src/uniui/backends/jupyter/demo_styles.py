"""Demo-page CSS for the Jupyter Admin backend.

These rules style the markup in ``examples/`` — field wrappers, colour
swatches, the demo header chrome — not any UniUI widget, so no component module
owns them and they do not belong in the shared stylesheet either.

They are still emitted as part of :func:`.styles.css`, in their original
position: CSS resolves ties by source order, so moving the block would change
rendering even though the text is unchanged.
"""
from __future__ import annotations

from .runtime import M


def _demo_css() -> str:
    """Field/swatch/badge helpers used by the demo pages, not by any component.

    These style example markup rather than a UniUI widget, so no component
    module owns them; they stay here rather than acquiring a fake home.
    """
    return """.uniui-demo-field {gap:6px; min-width:190px}
.uniui-demo-field-label, .uniui-demo-field-label .widget-label {
  color:var(--uniui-text_muted)!important; font-size:12px; font-weight:650;
}
.uniui-demo-swatch-row {gap:10px; align-items:center; flex-wrap:wrap!important}
.uniui-demo-swatch {
  width:34px; height:34px; border-radius:9px; border:1px solid var(--uniui-border);
  flex:0 0 34px;
}
.uniui-demo-badge-row {gap:8px; flex-wrap:wrap!important}"""


def _demo_page_css() -> str:
    """Demo page chrome: headings, logo, avatar and the header action buttons."""
    return f""".uniui-demo-page {{gap:{M['section_gap']}px;width:100%;min-width:0}}
.uniui-demo-heading {{gap:16px;align-items:center;flex-wrap:nowrap!important}}
.uniui-demo-subtitle .widget-label, .uniui-demo-subtitle {{color:var(--uniui-text)!important;font-size:17px;font-weight:650}}
.uniui-demo-hint .widget-label, .uniui-demo-hint {{color:var(--uniui-text_muted)!important}}
.uniui-demo-stats {{display:flex;flex-flow:row wrap;gap:{M['card_gap']}px;align-items:stretch}}
.uniui-demo-header-content {{width:100%;min-width:0;gap:8px;align-items:center;flex-wrap:nowrap!important}}
.uniui-demo-logo-mark, .uniui-demo-logo-mark .widget-label {{
  width:32px!important;min-width:32px;height:32px;display:grid;place-items:center;
  border-radius:9px;background:var(--uniui-accent);color:#fff!important;
  font-size:14px;font-weight:800;
}}
.uniui-demo-product, .uniui-demo-product .widget-label {{
  color:var(--uniui-text)!important;font-size:14px;font-weight:700;white-space:nowrap;
}}
.uniui-demo-avatar, .uniui-demo-avatar .widget-label {{
  width:32px!important;min-width:32px;height:32px;display:grid;place-items:center;
  border-radius:50%;background:var(--uniui-avatar_bg);color:var(--uniui-avatar_fg)!important;
  font-size:11px;font-weight:750;
}}
.uniui-admin-shell .uniui-demo-icon-button,
.uniui-admin-shell .uniui-demo-icon-button button {{
  width:32px!important;min-width:32px!important;height:32px;min-height:32px!important;
  padding:0!important;background:transparent!important;
  color:var(--uniui-text_muted)!important;border:1px solid transparent!important;
}}
.uniui-admin-shell .uniui-demo-icon-button button:hover {{
  background:var(--uniui-surface_subtle)!important;
  border-color:var(--uniui-border)!important;color:var(--uniui-text)!important;
}}
.uniui-admin-shell .uniui-demo-theme-button,
.uniui-admin-shell .uniui-demo-theme-button button {{
  min-height:34px!important;padding:0 12px!important;background:var(--uniui-surface)!important;
  color:var(--uniui-text)!important;border:1px solid var(--uniui-border_strong)!important;
}}
.uniui-admin-shell .uniui-demo-theme-button button:hover {{
  background:var(--uniui-surface_subtle)!important;
}}
.uniui-admin-shell .uniui-demo-primary-action,
.uniui-admin-shell .uniui-demo-primary-action button {{
  white-space:nowrap;background:var(--uniui-accent)!important;color:#fff!important;
  border-color:var(--uniui-accent)!important;
}}
.uniui-web-status-ok, .uniui-web-status-ok .widget-label {{
  color:var(--uniui-ok)!important;font-size:12px;font-weight:600;
}}
.uniui-web-footer-meta, .uniui-web-footer-meta .widget-label {{
  color:var(--uniui-text_muted)!important;font-size:12px;
}}"""
