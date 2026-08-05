"""CSS for the Web Admin backend.

The stylesheet is a **plain string**, unlike the Jupyter backend's ``css()``
which is an f-string. Moving a rule between the two without adjusting the
quoting either emits a literal ``{M['...']}`` or raises on a bare ``{``.
``tests/test_appearance_baseline.py`` guards both directions.

Sizing comes from CSS custom properties rather than interpolated metrics; the
shell writes them onto its own element in ``WebAppShellAdapter.apply_theme``,
which is what lets a theme switch restyle without re-emitting this block.

``_css_installed`` lives here with the function that owns it. It is module
state, so a test that needs the CSS re-emitted must reset it on *this* module.
"""
from __future__ import annotations

from nicegui import ui

from ...browser_css import icon_mask_rules


_css_installed = False


#: Base geometry for the standalone icon span this backend renders into
#: Quasar button slots. Jupyter has no equivalent - it styles ``button::before``
#: directly, because ipywidgets gives it no span to target.
_ICON_BASE_RULE = (
    ".uniui-svg-icon{display:inline-block;width:18px;height:18px;"
    "flex:0 0 18px;margin-right:9px;color:inherit;vertical-align:-4px}"
)

#: Two rules per icon: the standalone span, and Quasar's button content slot.
_ICON_RULES = (
    ".uniui-svg-icon.uniui-icon-{name}{{{mask}}}"
    ".uniui-icon-{name} .q-btn__content::before{{content:'';display:inline-block;"
    "width:18px;height:18px;flex:0 0 18px;margin-right:7px;{mask}}}"
)


def shared_icon_css() -> str:
    return _ICON_BASE_RULE + icon_mask_rules(_ICON_RULES)


def install_admin_css() -> None:
    global _css_installed
    if _css_installed:
        return
    ui.add_css(
        shared_icon_css() + """
        body:has(.uniui-web-admin) {margin:0;overflow:hidden;background:var(--uniui-bg)}
        .nicegui-content:has(.uniui-web-admin) {width:100%!important;max-width:none!important;padding:0!important;margin:0!important}
        .uniui-web-admin {container-type:inline-size;width:100%;height:100dvh;min-width:0;min-height:0;overflow:hidden;
          color:var(--uniui-text);background:var(--uniui-bg);font-family:Inter,"Segoe UI Variable Text","Segoe UI",sans-serif;
          font-size:14px;line-height:1.45;-webkit-font-smoothing:antialiased}
        .uniui-web-admin.uniui-root {padding:0!important;gap:0!important;max-width:none!important;margin:0!important}
        .uniui-web-admin * {box-sizing:border-box}
        .uniui-web-admin .uniui-label {color:var(--uniui-text_muted)!important}
        .uniui-web-admin .q-btn {text-transform:none;letter-spacing:0;font-weight:600}
        .uniui-web-admin .uniui-button {min-height:var(--uniui-control-height);padding:0 15px;background:var(--uniui-accent)!important;
          color:#fff!important;border-radius:9px!important;box-shadow:0 1px 2px rgba(37,99,235,.18)}
        .uniui-web-admin .uniui-button:hover {background:var(--uniui-accent_hover)!important}
        .uniui-web-header {height:var(--uniui-header-height);min-height:var(--uniui-header-height);width:100%;padding:0 20px!important;gap:10px!important;
          flex-wrap:nowrap!important;align-items:center!important;background:var(--uniui-header_bg);
          border-bottom:1px solid var(--uniui-border);box-shadow:0 1px 2px rgba(16,24,40,.025);z-index:2}
        .uniui-web-body {width:100%;height:calc(100dvh - var(--uniui-shell-bars));min-height:0;background:var(--uniui-bg)}
        .uniui-web-body .q-splitter__separator {width:5px!important;background:var(--uniui-border);transition:.15s}
        .uniui-web-body .q-splitter__separator:hover {background:var(--uniui-accent)}
        .uniui-web-content {width:100%;min-width:0;height:100%;padding:var(--uniui-content-padding);overflow:auto;background:var(--uniui-bg);
          scrollbar-width:thin;scrollbar-color:var(--uniui-border_strong) transparent}
        .uniui-web-footer {height:var(--uniui-footer-height);min-height:var(--uniui-footer-height);width:100%;padding:7px 20px;background:var(--uniui-surface);
          border-top:1px solid var(--uniui-border)}
        .uniui-web-sidebar {width:100%;height:100%;padding:18px 12px;gap:6px!important;overflow:auto;background:var(--uniui-sidebar_bg)}
        .uniui-web-sidebar .q-btn {position:relative;width:100%;min-height:42px;justify-content:flex-start;padding:8px 12px;
          color:var(--uniui-sidebar_fg)!important;background:transparent!important;border-radius:8px;font-size:13px;font-weight:500}
        .uniui-web-sidebar .q-btn .q-icon {width:22px;margin-right:10px;color:#94a3b8;font-size:19px}
        .uniui-web-sidebar .q-btn:hover {color:#fff!important;background:rgba(255,255,255,.055)!important}
        .uniui-web-sidebar .uniui-active {color:#fff!important;background:var(--uniui-sidebar_active)!important;box-shadow:inset var(--uniui-sidebar-edge-width) 0 0 var(--uniui-accent)}
        .uniui-web-sidebar .uniui-active .uniui-svg-icon {color:var(--uniui-accent)}
        .uniui-web-sidebar .uniui-collapsed .uniui-nav-label {display:none}
        .uniui-web-sidebar .uniui-collapsed .uniui-svg-icon {margin-right:0}
        .uniui-web-card {width:100%;min-width:0;padding:var(--uniui-card-padding);border:1px solid var(--uniui-border)!important;
          border-radius:14px!important;background:var(--uniui-surface)!important;color:var(--uniui-text);box-shadow:none!important}
        .uniui-web-card-title {color:var(--uniui-text);font-size:16px;font-weight:700;line-height:1.3}
        .uniui-web-card-subtitle {margin-top:2px;color:var(--uniui-text_muted);font-size:12px}
        .uniui-web-card .uniui-vbox {gap:var(--uniui-card-gap)!important}
        .uniui-web-stat {min-width:190px;min-height:136px;flex:1 1 190px;padding:15px 18px!important;gap:1px!important;
          border:1px solid var(--uniui-border)!important;
          border-radius:14px!important;background:var(--uniui-surface)!important;box-shadow:none!important}
        .uniui-web-stat-label {color:var(--uniui-text_muted);font-size:var(--uniui-stat-label-size);font-weight:600}
        .uniui-web-stat-value {color:var(--uniui-text);font-size:var(--uniui-stat-value-size);line-height:1.15;font-weight:750}
        .uniui-web-stat-unit {color:var(--uniui-text_muted);font-size:11px}
        .uniui-web-stat-trend {margin-top:auto;color:var(--uniui-text_muted);font-size:11px;font-weight:650}
        .uniui-web-stat-trend.uniui-up {color:var(--uniui-ok)} .uniui-web-stat-trend.uniui-down {color:var(--uniui-error)}
        .uniui-web-stat-trend.uniui-warn {color:var(--uniui-warn)} .uniui-web-stat-trend.uniui-error {color:var(--uniui-error)}
        .uniui-web-metric-row {padding:8px 0!important;justify-content:space-between!important;align-items:center!important}
        .uniui-web-metric-row.uniui-metric-divider {border-top:1px solid var(--uniui-border)}
        .uniui-web-metric-label {color:var(--uniui-text_muted)!important;font-size:var(--uniui-stat-label-size)}
        .uniui-web-metric-value {color:var(--uniui-text)!important;font-size:13px;font-weight:600}
        .uniui-web-admin .uniui-input {font-size:13px}
        .uniui-web-admin .uniui-input .q-field__control {height:40px;min-height:40px;background:var(--uniui-input_bg)!important;
          color:var(--uniui-text)!important;border-radius:9px!important}
        .uniui-web-admin .uniui-input.q-field--outlined .q-field__control:before {border:1px solid var(--uniui-border_strong)}
        .uniui-web-admin .uniui-input.q-field--focused .q-field__control:after {border:2px solid var(--uniui-accent)}
        .uniui-web-admin .uniui-input .q-field__native {min-height:40px;padding:0 12px;color:var(--uniui-text)}
        .uniui-web-admin .uniui-input .q-field__append {height:40px;color:var(--uniui-text_muted)}
        .uniui-web-table {width:100%;color:var(--uniui-text);background:var(--uniui-surface);border:1px solid var(--uniui-border);
          border-radius:10px;box-shadow:none!important;overflow:hidden;font-family:inherit}
        .uniui-web-table .q-table__container,.uniui-web-table .q-table__card {box-shadow:none!important;background:transparent}
        .uniui-web-table thead tr {height:44px;background:var(--uniui-surface);color:var(--uniui-text_muted);
          border-bottom:1px solid var(--uniui-border)}
        .uniui-web-table thead th {font-size:var(--uniui-stat-label-size);font-weight:600}
        .uniui-web-table tbody td {height:52px;font-size:13px;border-color:var(--uniui-border)}
        .uniui-web-table tbody tr:hover {background:var(--uniui-surface_subtle)}
        .uniui-web-table .q-table__bottom {min-height:42px;border-top:1px solid var(--uniui-border);color:var(--uniui-text_muted);font-size:12px}
        .uniui-web-breadcrumb {gap:4px!important;flex:1 1 auto;flex-wrap:nowrap!important;align-items:center!important;min-width:0}
        .uniui-web-breadcrumb .q-btn {min-height:28px;padding:2px 4px;color:var(--uniui-text_muted)!important;background:transparent!important;font-weight:500}
        .uniui-demo-page {width:100%;max-width:1180px;margin:0 auto;gap:var(--uniui-section-gap)!important}
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
        .uniui-web-gauge,.uniui-web-chart {width:100%;min-width:0}
        .uniui-web-gauge svg,.uniui-web-chart svg {display:block;width:100%;height:auto;max-height:250px}
        .uniui-web-drawer-root {position:fixed;inset:0;z-index:5000;pointer-events:none;visibility:hidden}
        .uniui-web-drawer-root.uniui-open {pointer-events:auto;visibility:visible}
        .uniui-web-drawer-scrim {position:absolute;inset:0;background:rgba(2,6,23,.34);opacity:0;transition:opacity .18s ease}
        .uniui-web-drawer-panel {position:absolute;right:0;top:0;height:100%;width:min(380px,92vw);margin:0!important;
          padding:20px 22px!important;border-radius:0!important;background:var(--uniui-surface)!important;
          border-left:1px solid var(--uniui-border)!important;transform:translateX(100%);transition:transform .2s ease}
        .uniui-web-drawer-root.uniui-open .uniui-web-drawer-scrim {opacity:1}
        .uniui-web-drawer-root.uniui-open .uniui-web-drawer-panel {transform:none}
        .uniui-web-drawer-header {width:100%;align-items:center;gap:10px!important}
        .uniui-web-drawer-title {flex:1 1 auto;color:var(--uniui-text)!important;font-size:18px;font-weight:700}
        .uniui-status-pill {display:inline-flex;align-items:center;min-height:24px;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:700}
        .uniui-status-pill.uniui-status-ok {color:var(--uniui-status_ok_fg);background:var(--uniui-status_ok_bg)}
        .uniui-status-pill.uniui-status-warn {color:var(--uniui-status_warn_fg);background:var(--uniui-status_warn_bg)}
        .uniui-status-pill.uniui-status-error {color:var(--uniui-status_error_fg);background:var(--uniui-status_error_bg)}
        .uniui-status-pill.uniui-status-neutral {color:var(--uniui-status_neutral_fg);background:var(--uniui-status_neutral_bg)}
        .uniui-demo-subtitle {color:var(--uniui-text)!important;font-size:18px!important;line-height:1.3;font-weight:650!important}
        .uniui-demo-hint {color:var(--uniui-text_muted)!important;font-size:13px}
        .uniui-demo-stats {gap:var(--uniui-card-gap)!important;align-items:stretch!important}
        @media(max-width:1019px) {
          .uniui-web-body .q-splitter__before {width:var(--uniui-sidebar-collapsed)!important}
          .uniui-web-body .q-splitter__after {width:calc(100% - var(--uniui-sidebar-collapsed))!important}
          .uniui-web-body .q-splitter__separator {display:none!important}
          .uniui-web-sidebar {padding:16px 8px}.uniui-web-sidebar .q-btn{font-size:0;justify-content:center;padding:8px 4px}
          .uniui-web-sidebar .uniui-svg-icon {margin:0;width:20px;height:20px;flex-basis:20px}
          .uniui-web-content {padding:24px 20px}
          .uniui-demo-product {display:none}
        }
        @media(max-width:719px) {
          .uniui-web-body {height:calc(100dvh - 60px)}.uniui-web-content{padding:20px 14px}.uniui-web-footer{display:none}
          .uniui-web-header{padding:0 12px!important}.uniui-demo-theme-button{font-size:0;min-width:34px!important;padding:0!important}
          .uniui-demo-heading{align-items:flex-start!important}.uniui-demo-subtitle{font-size:16px!important}
        }
        """,
        shared=True,
    )
    _css_installed = True
