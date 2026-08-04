"""Themed CSS for the plain ipywidgets created by the Jupyter factory.

`jupyter_components` styles the Admin components and scopes its rules under
``.uniui-admin-shell``.  That leaves ordinary controls unstyled whenever an app
does not build an AppShell, so this module publishes an equivalent rule set
scoped to ``.uniui-widget`` — a marker class the factory puts on every widget
it creates.

The stylesheet is emitted once per notebook via :func:`style_widget_html`, and
:func:`refresh` rewrites the live copies when the theme flips.
"""
from __future__ import annotations

import weakref
from typing import Optional

import ipywidgets as widgets

from .jupyter_components import get_admin_palette


WIDGET_CLASS = "uniui-widget"

_STYLE_NODES: "weakref.WeakSet[widgets.HTML]" = weakref.WeakSet()


def mark(widget) -> None:
    """Tag a widget so the base stylesheet applies to it."""
    native = widget.get_native() if hasattr(widget, "get_native") else widget
    add_class = getattr(native, "add_class", None)
    if callable(add_class):
        add_class(WIDGET_CLASS)


def base_css() -> str:
    """Return the base widget CSS for the active theme, wrapped in <style>."""
    palette = get_admin_palette()
    variables = ";".join(f"--uniui-{key}:{value}" for key, value in palette.items())
    return f"<style>\n.{WIDGET_CLASS} {{{variables}}}\n{_BASE_RULES}</style>"


def style_widget_html() -> widgets.HTML:
    """Return an HTML widget carrying the stylesheet, tracked for theme changes.

    Display this once alongside your widgets; ``uniui.display.show_ui`` does it
    for you.
    """
    node = widgets.HTML(value=base_css())
    _STYLE_NODES.add(node)
    return node


def refresh() -> None:
    """Rewrite every live stylesheet node after a theme change."""
    css = base_css()
    for node in list(_STYLE_NODES):
        try:
            node.value = css
        except Exception:
            _STYLE_NODES.discard(node)


# Scoped to .uniui-widget so these never fight the admin shell's own rules.
# ipywidgets ships its own inline styles, hence the !important flags.
_BASE_RULES = f"""
.{WIDGET_CLASS} {{box-sizing:border-box}}
.{WIDGET_CLASS} .widget-label {{color:var(--uniui-text)}}
.{WIDGET_CLASS}.widget-text input,
.{WIDGET_CLASS} .widget-text input {{
  color:var(--uniui-text)!important; background:var(--uniui-input_bg)!important;
  border:1px solid var(--uniui-border_strong)!important; border-radius:9px!important;
  min-height:38px; padding:7px 10px;
}}
.{WIDGET_CLASS}.widget-button button,
.{WIDGET_CLASS} .widget-button button {{
  background:var(--uniui-accent)!important; color:white!important;
  border:1px solid var(--uniui-accent)!important; border-radius:9px!important;
  min-height:36px; padding:6px 13px; font-weight:600;
}}
.{WIDGET_CLASS}.widget-button button:hover,
.{WIDGET_CLASS} .widget-button button:hover {{
  background:var(--uniui-accent_hover)!important;
  border-color:var(--uniui-accent_hover)!important;
}}
.{WIDGET_CLASS}.widget-dropdown > select,
.{WIDGET_CLASS} .widget-dropdown > select,
.{WIDGET_CLASS}.widget-combobox input,
.{WIDGET_CLASS} .widget-combobox input {{
  color:var(--uniui-text)!important; background:var(--uniui-input_bg)!important;
  border:1px solid var(--uniui-border_strong)!important; border-radius:9px!important;
  min-height:38px; padding:7px 30px 7px 10px; font-size:13px;
}}
.{WIDGET_CLASS}.widget-dropdown > select:focus,
.{WIDGET_CLASS} .widget-dropdown > select:focus,
.{WIDGET_CLASS}.widget-combobox input:focus,
.{WIDGET_CLASS} .widget-combobox input:focus {{
  border:2px solid var(--uniui-accent)!important; outline:none;
}}
.{WIDGET_CLASS}.widget-tab, .{WIDGET_CLASS} .widget-tab {{background:transparent; border:none}}
.{WIDGET_CLASS}.widget-tab .p-TabBar, .{WIDGET_CLASS} .widget-tab .p-TabBar,
.{WIDGET_CLASS}.widget-tab .lm-TabBar, .{WIDGET_CLASS} .widget-tab .lm-TabBar {{
  border-bottom:1px solid var(--uniui-border); overflow:visible;
}}
.{WIDGET_CLASS}.widget-tab .p-TabBar-tab, .{WIDGET_CLASS} .widget-tab .p-TabBar-tab,
.{WIDGET_CLASS}.widget-tab .lm-TabBar-tab, .{WIDGET_CLASS} .widget-tab .lm-TabBar-tab {{
  background:transparent!important; border:none!important;
  color:var(--uniui-text_muted)!important; font-weight:600; font-size:13px;
  padding:9px 16px; min-height:0;
}}
.{WIDGET_CLASS}.widget-tab .p-TabBar-tab.p-mod-current,
.{WIDGET_CLASS} .widget-tab .p-TabBar-tab.p-mod-current,
.{WIDGET_CLASS}.widget-tab .lm-TabBar-tab.lm-mod-current,
.{WIDGET_CLASS} .widget-tab .lm-TabBar-tab.lm-mod-current {{
  color:var(--uniui-accent)!important;
  box-shadow:inset 0 -2px 0 var(--uniui-accent);
}}
"""


__all__ = ["WIDGET_CLASS", "base_css", "mark", "refresh", "style_widget_html"]
