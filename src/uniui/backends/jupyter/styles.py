"""CSS, splitter markup and debug probes for the Jupyter Admin backend.

:func:`css` is an **f-string**. The web backend's equivalent block is a plain
string, so moving a rule between the two without adjusting the quoting emits a
literal ``{M['...']}`` into the stylesheet. ``tests/test_appearance_baseline.py``
guards both directions.

Every rule is scoped under ``.uniui-admin-shell``; the theme variables are
defined on that same selector, so moving variable emission out from under it is
what makes light mode render dark.
"""
from __future__ import annotations

from html import escape

from ...browser_css import icon_mask_rules, palette_declarations
from .runtime import M, get_palette


#: The icon sits on the ipywidgets ``button`` element, which is nested inside
#: the widget's own wrapper - hence ``button::before`` rather than the Web
#: backend's standalone span.
_ICON_RULE = (
    ".uniui-icon-{name} button::before{{content:'';display:inline-block;"
    "width:18px;height:18px;flex:0 0 18px;margin-right:8px;"
    "vertical-align:-4px;{mask}}}"
)


def shared_icon_css() -> str:
    return icon_mask_rules(_ICON_RULE)


def _selectors(scope: str, suffix: str, nested: bool) -> str:
    """Build the selector list for one base-control rule.

    ``nested`` scopes (the Admin shell) only ever match descendants, because the
    shell class sits on a container.  The plain-widget scope also has to match
    the element *itself*: the factory puts ``.uniui-widget`` on each widget, so
    ``.uniui-widget.widget-text`` and ``.uniui-widget .widget-text`` are both
    real cases depending on how ipywidgets nested that particular control.
    """
    parts = [f"{scope} {part.strip()}" for part in suffix.split(",")]
    if not nested:
        parts = [
            f"{scope}{part.strip()},\n{scope} {part.strip()}"
            for part in suffix.split(",")
        ]
    return ",\n".join(parts)


def base_control_rules(scope: str, nested: bool = True) -> str:
    """Return the themed rules for stock ipywidgets controls under ``scope``.

    One builder serves both scopes: ``.uniui-admin-shell`` (nested, emitted
    inside :func:`css`) and ``.uniui-widget`` (not nested, emitted by
    ``primitives.styles`` for apps that never build an AppShell).  The two
    stylesheets still reach the DOM by different routes and on different
    schedules - only the rule *text* is shared.

    ipywidgets ships inline styles of its own, hence the ``!important`` flags.
    """
    sel = lambda suffix: _selectors(scope, suffix, nested)
    # The Admin shell paints the wrapper as well as the button; the plain scope
    # historically only painted the button, and widening it here would restyle
    # every stock button in a plain notebook.
    button_suffix = ".widget-button,.widget-button button" if nested else ".widget-button button"
    # A label is always a child node, never the marked widget itself, so this
    # one stays descendant-only in both scopes.
    rules = f"""{scope} .widget-label {{color:var(--uniui-text)}}
{sel(".widget-text input")} {{
  color:var(--uniui-text)!important; background:var(--uniui-input_bg)!important;
  border:1px solid var(--uniui-border_strong)!important; border-radius:9px!important;
  min-height:38px; padding:7px 10px;
}}
{sel(button_suffix)} {{
  background:var(--uniui-accent)!important; color:white!important;
  border:1px solid var(--uniui-accent)!important; border-radius:9px!important;
  min-height:36px; padding:6px 13px; font-weight:600;
}}
{sel(button_suffix.replace(",", ":hover,") + ":hover")} {{
  background:var(--uniui-accent_hover)!important;
  border-color:var(--uniui-accent_hover)!important;
}}
{sel(".widget-dropdown > select,.widget-combobox input")} {{
  color:var(--uniui-text)!important; background:var(--uniui-input_bg)!important;
  border:1px solid var(--uniui-border_strong)!important; border-radius:9px!important;
  min-height:38px; padding:7px 30px 7px 10px; font-size:13px;
}}
"""
    if nested:
        rules += f"""{sel(".widget-dropdown > select:hover,.widget-combobox input:hover")} {{border-color:var(--uniui-text_muted)!important}}
"""
    rules += f"""{sel(".widget-dropdown > select:focus,.widget-combobox input:focus")} {{
  border:2px solid var(--uniui-accent)!important; outline:none;
}}"""
    return rules


def css() -> str:
    """The Admin shell stylesheet, composed from each component's fragment.

    This function owns only what is genuinely shared: the theme variables, the
    shell container, the stock-ipywidgets base rules, and the tab chrome. Every
    component's own rules come from that component's module, so a rule and the
    markup it targets stay together.

    Imported inside the function because the component modules import from this
    one (``base_control_rules``); a module-level import would be circular.
    """
    from .components.app_shell import app_shell_css, app_shell_responsive_css
    from .components.breadcrumb import breadcrumb_css
    from .components.card import card_css
    from .components.drawer import drawer_css
    from .components.gauge import gauge_css
    from .components.metric_list import metric_list_css
    from .components.sidebar import sidebar_css
    from .components.stat_card import stat_card_css
    from .components.table import table_css
    from .components.toast import toast_css
    from .demo_styles import _demo_css, _demo_page_css

    p = get_palette()
    variables = palette_declarations(p)
    return f"""
<style>
{shared_icon_css()}
.uniui-admin-shell {{{variables};
  container-type:inline-size; width:100%; min-width:0; min-height:680px;
  color:var(--uniui-text); background:var(--uniui-bg);
  font-family:Inter,"Segoe UI Variable Text","Segoe UI",sans-serif;
  border:1px solid var(--uniui-border); border-radius:14px; overflow:hidden;
  box-shadow:var(--uniui-shadow); box-sizing:border-box;
}}
.uniui-admin-shell, .uniui-admin-shell * {{box-sizing:border-box}}
{base_control_rules(".uniui-admin-shell", nested=True)}
.uniui-admin-shell .widget-tab {{background:transparent; border:none}}
.uniui-admin-shell .widget-tab > .p-TabBar,
.uniui-admin-shell .widget-tab .lm-TabBar {{
  border-bottom:1px solid var(--uniui-border); overflow:visible;
}}
.uniui-admin-shell .widget-tab .p-TabBar-tab,
.uniui-admin-shell .widget-tab .lm-TabBar-tab {{
  background:transparent!important; border:none!important;
  color:var(--uniui-text_muted)!important; font-weight:600; font-size:13px;
  padding:9px 16px; min-height:0;
}}
.uniui-admin-shell .widget-tab .p-TabBar-tab.p-mod-current,
.uniui-admin-shell .widget-tab .lm-TabBar-tab.lm-mod-current {{
  color:var(--uniui-accent)!important;
  box-shadow:inset 0 -2px 0 var(--uniui-accent);
}}
.uniui-admin-shell .widget-tab .p-TabBar-tabLabel,
.uniui-admin-shell .widget-tab .lm-TabBar-tabLabel {{color:inherit}}
.uniui-admin-shell .widget-tab > .widget-tab-contents,
.uniui-admin-shell .widget-tab .p-StackedPanel,
.uniui-admin-shell .widget-tab .lm-StackedPanel {{
  border:none; background:transparent; padding:16px 2px 0;
}}
{_demo_css()}
{app_shell_css()}
{card_css()}
{stat_card_css()}
{metric_list_css()}
{table_css()}
{toast_css()}
{gauge_css()}
{drawer_css()}
{sidebar_css()}
{breadcrumb_css()}
{_demo_page_css()}
{app_shell_responsive_css()}
</style>
"""


# ---------------------------------------------------------------------------
# Compatibility re-exports.
#
# SPLITTER_HTML, debug_html and DEBUG_MEASURE_JS moved to
# components/app_shell_assets.py - they are shell markup and probes, not
# stylesheet rules. jupyter_components re-exports them from here, so the names
# stay importable at their old location.
#
# Imported from the submodule directly, NOT via ``.components``: the components
# package __init__ imports every adapter, and app_shell.py imports ``css`` from
# this module, so going through the package would be circular. app_shell_assets
# itself imports nothing from this package, so reaching it directly is safe.
# ---------------------------------------------------------------------------
from .components.app_shell_assets import (  # noqa: E402
    DEBUG_MEASURE_JS, SPLITTER_HTML, debug_html,
)
