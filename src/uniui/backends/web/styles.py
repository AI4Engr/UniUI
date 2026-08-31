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


def _base_css() -> str:
    """The shell container, stock-control and input rules shared by everything.

    These are not owned by any one component: they style the admin root, the
    Quasar button/field defaults and the label colour that every component
    inherits.
    """
    return """        body:has(.uniui-web-admin) {margin:0;overflow:hidden;background:var(--uniui-bg)}
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
"""


def _input_css() -> str:
    """Quasar field overrides for the plain input controls."""
    return """        .uniui-web-admin .uniui-input {font-size:13px}
        .uniui-web-admin .uniui-input .q-field__control {height:40px;min-height:40px;background:var(--uniui-input_bg)!important;
          color:var(--uniui-text)!important;border-radius:9px!important}
        .uniui-web-admin .uniui-input.q-field--outlined .q-field__control:before {border:1px solid var(--uniui-border_strong)}
        .uniui-web-admin .uniui-input.q-field--focused .q-field__control:after {border:2px solid var(--uniui-accent)}
        .uniui-web-admin .uniui-input .q-field__native {min-height:40px;padding:0 12px;color:var(--uniui-text)}
        .uniui-web-admin .uniui-input .q-field__append {height:40px;color:var(--uniui-text_muted)}
"""






def admin_css() -> str:
    """The full Admin stylesheet, composed from each component's fragment.

    Fragment order is the original rule order and must stay that way: CSS
    resolves ties by source order, so moving a block changes rendering even
    though the text is unchanged.

    Imported inside the function because the component modules import from this
    one (``install_admin_css``); a module-level import would be circular.
    """
    from .components.app_shell import app_shell_css, app_shell_responsive_css
    from .components.breadcrumb import breadcrumb_css
    from .components.card import card_css
    from .components.drawer import drawer_css
    from .components.gauge import gauge_css
    from .components.metric_list import metric_list_css
    from .components.sidebar import sidebar_css
    from .components.stat_card import stat_card_css
    from .components.table import status_pill_css, table_css
    from .components.toast import toast_css
    from .page_styles import _page_and_shell_css, _page_trailer_css

    return (
        shared_icon_css() + "\n"
        + _base_css()
        + app_shell_css()
        + sidebar_css()
        + card_css()
        + stat_card_css()
        + metric_list_css()
        + _input_css()
        + table_css()
        + breadcrumb_css()
        + _page_and_shell_css()
        + gauge_css()
        + drawer_css()
        + status_pill_css()
        + toast_css()
        + _page_trailer_css()
        + app_shell_responsive_css()
    )


def install_admin_css() -> None:
    global _css_installed
    if _css_installed:
        return
    ui.add_css(admin_css(), shared=True)
    _css_installed = True
