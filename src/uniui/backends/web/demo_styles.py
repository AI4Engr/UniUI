"""Demo-page CSS for the Web Admin backend.

These rules style the markup in ``examples/`` — the demo header chrome, logo,
avatar and action buttons — not any UniUI widget, so no component module owns
them and they do not belong in the shared stylesheet either.

They are still emitted as part of :func:`.styles.admin_css`, in their original
positions: CSS resolves ties by source order, so moving either block would
change rendering even though the text is unchanged.
"""
from __future__ import annotations


def _demo_css() -> str:
    """Demo page chrome: headings, logo, avatar and the header action buttons.

    These style example markup rather than a UniUI widget, so no component
    module owns them.
    """
    return """        .uniui-demo-page {width:100%;max-width:1180px;margin:0 auto;gap:var(--uniui-section-gap)!important}
        .uniui-demo-heading {gap:18px!important;flex-wrap:nowrap!important;align-items:center!important}
        .uniui-demo-header-content {width:100%;min-width:0;gap:8px!important;flex-wrap:nowrap!important;align-items:center!important}
        .uniui-demo-logo-mark {width:32px!important;height:32px;min-width:32px;display:grid;place-items:center;border-radius:9px;
          background:var(--uniui-accent);color:#fff!important;font-size:14px;font-weight:800;box-shadow:0 2px 6px rgba(37,99,235,.24)}
        .uniui-demo-product {color:var(--uniui-text)!important;font-size:14px;font-weight:700;white-space:nowrap}
        .uniui-web-admin .uniui-demo-icon-button {width:32px!important;min-width:32px!important;height:32px!important;min-height:32px!important;padding:0!important;
          color:var(--uniui-text_muted)!important;background:transparent!important;border:1px solid transparent!important;box-shadow:none!important}
        .uniui-web-admin .uniui-demo-icon-button:hover {color:var(--uniui-text)!important;background:var(--uniui-surface_subtle)!important;border-color:var(--uniui-border)!important}
        .uniui-web-admin .uniui-demo-theme-button {min-height:34px!important;padding:0 12px!important;color:var(--uniui-text)!important;
          background:var(--uniui-surface)!important;border:1px solid var(--uniui-border_strong)!important;box-shadow:none!important}
        .uniui-web-admin .uniui-demo-theme-button:hover {background:var(--uniui-surface_subtle)!important}
        .uniui-demo-avatar {width:32px!important;height:32px;min-width:32px;display:grid;place-items:center;border-radius:50%;
          background:#dbeafe;color:#1d4ed8!important;font-size:11px;font-weight:750}
        .uniui-web-admin .uniui-demo-primary-action {white-space:nowrap;min-width:max-content;background:var(--uniui-accent)!important;color:#fff!important}
        .uniui-web-admin .uniui-web-status-ok {color:var(--uniui-ok)!important;font-size:12px;font-weight:600}
        .uniui-web-admin .uniui-web-footer-meta {color:var(--uniui-text_muted)!important;font-size:12px}
"""

def _demo_trailer_css() -> str:
    """Demo typography emitted after the status pills, preserving rule order."""
    return """        .uniui-demo-subtitle {color:var(--uniui-text)!important;font-size:18px!important;line-height:1.3;font-weight:650!important}
        .uniui-demo-hint {color:var(--uniui-text_muted)!important;font-size:13px}
        .uniui-demo-stats {gap:var(--uniui-card-gap)!important;align-items:stretch!important}
"""
