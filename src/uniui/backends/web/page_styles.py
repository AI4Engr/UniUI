"""Page and shell-chrome CSS for the Web Admin backend.

These rules style generic page content (``uniui-page-*``: headings,
subtitles, hints, stat rows) and admin-shell chrome (``uniui-shell-*``:
logo, avatar, action buttons) - vocabulary any app built on UniUI's widgets
can use via ``add_class()``, not markup specific to any one example. No
component module owns them (they aren't part of one widget's own rules).

They are still emitted as part of :func:`.styles.admin_css`, in their original
positions: CSS resolves ties by source order, so moving either block would
change rendering even though the text is unchanged.
"""
from __future__ import annotations


def _page_and_shell_css() -> str:
    """Page structure plus shell chrome: headings, logo, avatar, header buttons."""
    return """        .uniui-page {width:100%;max-width:1180px;margin:0 auto;gap:var(--uniui-section-gap)!important}
        .uniui-page-heading {gap:18px!important;flex-wrap:nowrap!important;align-items:center!important}
        .uniui-shell-header-content {width:100%;min-width:0;gap:8px!important;flex-wrap:nowrap!important;align-items:center!important}
        .uniui-shell-logo-mark {width:32px!important;height:32px;min-width:32px;display:grid;place-items:center;border-radius:9px;
          background:var(--uniui-accent);color:#fff!important;font-size:14px;font-weight:800;box-shadow:0 2px 6px rgba(37,99,235,.24)}
        .uniui-shell-product {color:var(--uniui-text)!important;font-size:14px;font-weight:700;white-space:nowrap}
        .uniui-web-admin .uniui-shell-icon-button {width:32px!important;min-width:32px!important;height:32px!important;min-height:32px!important;padding:0!important;
          color:var(--uniui-text_muted)!important;background:transparent!important;border:1px solid transparent!important;box-shadow:none!important}
        .uniui-web-admin .uniui-shell-icon-button:hover {color:var(--uniui-text)!important;background:var(--uniui-surface_subtle)!important;border-color:var(--uniui-border)!important}
        .uniui-web-admin .uniui-shell-theme-button {min-height:34px!important;padding:0 12px!important;color:var(--uniui-text)!important;
          background:var(--uniui-surface)!important;border:1px solid var(--uniui-border_strong)!important;box-shadow:none!important}
        .uniui-web-admin .uniui-shell-theme-button:hover {background:var(--uniui-surface_subtle)!important}
        .uniui-shell-avatar {width:32px!important;height:32px;min-width:32px;display:grid;place-items:center;border-radius:50%;
          background:#dbeafe;color:#1d4ed8!important;font-size:11px;font-weight:750}
        .uniui-web-admin .uniui-shell-primary-action {white-space:nowrap;min-width:max-content;background:var(--uniui-accent)!important;color:#fff!important}
        .uniui-web-admin .uniui-web-status-ok {color:var(--uniui-ok)!important;font-size:12px;font-weight:600}
        .uniui-web-admin .uniui-web-footer-meta {color:var(--uniui-text_muted)!important;font-size:12px}
"""

def _page_trailer_css() -> str:
    """Page typography emitted after the status pills, preserving rule order."""
    return """        .uniui-page-subtitle {color:var(--uniui-text)!important;font-size:18px!important;line-height:1.3;font-weight:650!important}
        .uniui-page-hint {color:var(--uniui-text_muted)!important;font-size:13px}
        .uniui-page-stats {gap:var(--uniui-card-gap)!important;align-items:stretch!important}
"""
