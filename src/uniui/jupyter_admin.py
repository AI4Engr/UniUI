"""Modern Admin components for the Jupyter/ipywidgets backend.

The implementation deliberately keeps ordinary responsive work in CSS.  The
sidebar splitter uses pointer events in the browser and sends only the final
width back to Python when the drag ends.
"""
from __future__ import annotations

from html import escape
from typing import Callable, Dict, List, Optional
import weakref

import ipywidgets as widgets

from .admin import IAppShell, IBreadcrumb, ICard, ISidebar, IStatCard, ITable


_LIGHT = {
    "bg": "#f4f7fb",
    "surface": "#ffffff",
    "surface_subtle": "#f8fafc",
    "text": "#172033",
    "text_muted": "#667085",
    "border": "#e4e7ec",
    "border_strong": "#d0d5dd",
    "accent": "#4f46e5",
    "accent_hover": "#4338ca",
    "ok": "#16a34a",
    "warn": "#d97706",
    "error": "#dc2626",
    "sidebar_bg": "#101828",
    "sidebar_fg": "#d0d5dd",
    "sidebar_active": "#344054",
    "header_bg": "#ffffff",
    "input_bg": "#ffffff",
    "shadow": "0 1px 3px rgba(16,24,40,.08), 0 1px 2px rgba(16,24,40,.04)",
}

_DARK = {
    "bg": "#0b1220",
    "surface": "#111827",
    "surface_subtle": "#182235",
    "text": "#f2f4f7",
    "text_muted": "#98a2b3",
    "border": "#263247",
    "border_strong": "#344054",
    "accent": "#818cf8",
    "accent_hover": "#a5b4fc",
    "ok": "#4ade80",
    "warn": "#fbbf24",
    "error": "#fb7185",
    "sidebar_bg": "#080d18",
    "sidebar_fg": "#cbd5e1",
    "sidebar_active": "#263247",
    "header_bg": "#111827",
    "input_bg": "#182235",
    "shadow": "0 1px 3px rgba(0,0,0,.35)",
}

_admin_dark = False
_theme_targets: "weakref.WeakSet[object]" = weakref.WeakSet()


def get_admin_palette() -> Dict[str, str]:
    """Return a copy of the active Jupyter Admin palette."""
    return dict(_DARK if _admin_dark else _LIGHT)


def is_admin_dark() -> bool:
    return _admin_dark


def set_admin_theme(dark: bool) -> bool:
    """Switch all live Jupyter Admin shells between light and dark themes."""
    global _admin_dark
    _admin_dark = bool(dark)
    for target in list(_theme_targets):
        apply_theme = getattr(target, "apply_theme", None)
        if callable(apply_theme):
            apply_theme()
    return _admin_dark


def _native(widget):
    return widget.get_native() if hasattr(widget, "get_native") else widget


def _html(text: str, class_name: str = "") -> widgets.HTML:
    widget = widgets.HTML(value=text)
    if class_name:
        widget.add_class(class_name)
    return widget


def _css() -> str:
    p = get_admin_palette()
    variables = ";".join(f"--uniui-{key}:{value}" for key, value in p.items())
    return f"""
<style>
.uniui-admin-shell {{{variables};
  container-type:inline-size; width:100%; min-width:0; min-height:680px;
  color:var(--uniui-text); background:var(--uniui-bg);
  font-family:Inter,"Segoe UI Variable Text","Segoe UI",sans-serif;
  border:1px solid var(--uniui-border); border-radius:14px; overflow:hidden;
  box-shadow:var(--uniui-shadow); box-sizing:border-box;
}}
.uniui-admin-shell, .uniui-admin-shell * {{box-sizing:border-box}}
.uniui-admin-shell .widget-label {{color:var(--uniui-text)}}
.uniui-admin-shell .widget-text input {{
  color:var(--uniui-text)!important; background:var(--uniui-input_bg)!important;
  border:1px solid var(--uniui-border_strong)!important; border-radius:8px!important;
  min-height:38px; padding:7px 10px;
}}
.uniui-admin-shell .widget-button,
.uniui-admin-shell .widget-button button {{
  background:var(--uniui-accent)!important; color:white!important;
  border:1px solid var(--uniui-accent)!important; border-radius:8px!important;
  min-height:36px; padding:6px 13px; font-weight:600;
}}
.uniui-admin-shell .widget-button:hover,
.uniui-admin-shell .widget-button button:hover {{
  background:var(--uniui-accent_hover)!important;
  border-color:var(--uniui-accent_hover)!important;
}}
.uniui-shell-header {{
  flex:0 0 64px; min-height:64px; padding:0 16px; gap:10px;
  align-items:center; background:var(--uniui-header_bg);
  border-bottom:1px solid var(--uniui-border);
}}
.uniui-shell-body {{display:flex; width:100%; min-width:0; flex:1 1 auto}}
.uniui-shell-content {{
  min-width:0; flex:1 1 0; padding:24px 28px 28px;
  overflow:auto; background:var(--uniui-bg);
}}
.uniui-shell-footer {{
  flex:0 0 auto; min-height:38px; padding:8px 16px;
  background:var(--uniui-surface); border-top:1px solid var(--uniui-border);
}}
.uniui-admin-card {{
  width:100%; min-width:0; padding:18px 20px 20px; gap:12px;
  background:var(--uniui-surface); border:1px solid var(--uniui-border);
  border-radius:12px; box-shadow:var(--uniui-shadow);
}}
.uniui-card-header {{display:flex; flex-flow:row; align-items:flex-start; gap:12px}}
.uniui-card-copy {{min-width:0; flex:1 1 auto; gap:2px}}
.uniui-card-title, .uniui-card-title p {{
  margin:0; color:var(--uniui-text); font-size:16px; font-weight:700;
}}
.uniui-card-subtitle, .uniui-card-subtitle p {{
  margin:0; color:var(--uniui-text_muted); font-size:12px;
}}
.uniui-stat-card {{
  min-width:190px; min-height:136px; padding:15px 18px 14px;
  background:var(--uniui-surface); border:1px solid var(--uniui-border);
  border-top:3px solid var(--uniui-ok); border-radius:12px;
  box-shadow:var(--uniui-shadow); gap:2px; flex:1 1 190px;
}}
.uniui-stat-card.uniui-status-warn {{border-top-color:var(--uniui-warn)}}
.uniui-stat-card.uniui-status-error {{border-top-color:var(--uniui-error)}}
.uniui-stat-label, .uniui-stat-label p {{margin:0;color:var(--uniui-text_muted);font-size:12px;font-weight:600}}
.uniui-stat-value, .uniui-stat-value p {{margin:2px 0 0;color:var(--uniui-text);font-size:29px;line-height:1.15;font-weight:750}}
.uniui-stat-unit, .uniui-stat-unit p {{margin:0;color:var(--uniui-text_muted);font-size:11px}}
.uniui-stat-trend, .uniui-stat-trend p {{margin:9px 0 0;color:var(--uniui-text_muted);font-size:11px;font-weight:650}}
.uniui-stat-trend.uniui-up, .uniui-stat-trend.uniui-up p {{color:var(--uniui-ok)}}
.uniui-stat-trend.uniui-down, .uniui-stat-trend.uniui-down p {{color:var(--uniui-error)}}
.uniui-admin-table {{width:100%; min-width:0}}
.uniui-admin-table table {{width:100%; border-collapse:separate; border-spacing:0; color:var(--uniui-text); font-size:13px}}
.uniui-admin-table th {{
  padding:10px 12px; text-align:left; color:var(--uniui-text_muted);
  background:var(--uniui-surface_subtle); border-bottom:1px solid var(--uniui-border);
  font-size:11px; letter-spacing:.035em; text-transform:uppercase;
}}
.uniui-admin-table td {{padding:11px 12px;border-bottom:1px solid var(--uniui-border)}}
.uniui-admin-table tbody tr {{cursor:pointer}}
.uniui-admin-table tbody tr:hover {{background:var(--uniui-surface_subtle)}}
.uniui-admin-table .uniui-number {{text-align:right}}
.uniui-admin-table .uniui-status {{font-weight:700}}
.uniui-admin-table .uniui-ok {{color:var(--uniui-ok)}}
.uniui-admin-table .uniui-warn {{color:var(--uniui-warn)}}
.uniui-admin-table .uniui-error {{color:var(--uniui-error)}}
.uniui-table-message, .uniui-table-message p {{margin:20px 0;text-align:center;color:var(--uniui-text_muted)}}
.uniui-admin-sidebar {{
  width:236px; min-width:168px; max-width:360px; flex:0 0 236px;
  padding:14px 10px; gap:5px; overflow:auto; background:var(--uniui-sidebar_bg);
}}
.uniui-admin-sidebar .widget-button {{width:100%}}
.uniui-admin-sidebar .widget-button,
.uniui-admin-sidebar .widget-button button {{
  width:100%; min-height:42px; padding:8px 11px; text-align:left;
  background:transparent!important; color:var(--uniui-sidebar_fg)!important;
  border-color:transparent!important; box-shadow:none!important;
}}
.uniui-admin-sidebar .widget-button:hover,
.uniui-admin-sidebar .widget-button button:hover,
.uniui-admin-sidebar .uniui-active,
.uniui-admin-sidebar .uniui-active button {{
  color:white!important; background:var(--uniui-sidebar_active)!important;
}}
.uniui-sidebar-icon {{display:inline-block; width:24px; text-align:center; margin-right:8px}}
.uniui-splitter-widget {{
  width:6px; min-width:6px; flex:0 0 6px; align-self:stretch;
  background:var(--uniui-border); cursor:col-resize; touch-action:none;
}}
.uniui-splitter-widget:hover, .uniui-splitter-widget:active {{background:var(--uniui-accent)}}
.uniui-splitter-handle {{width:100%;height:100%;min-height:520px;touch-action:none}}
.uniui-breadcrumb {{align-items:center;gap:4px;min-width:0}}
.uniui-breadcrumb .widget-button,
.uniui-breadcrumb .widget-button button {{
  min-height:28px;padding:2px 5px;background:transparent!important;
  color:var(--uniui-text_muted)!important;border-color:transparent!important;
}}
.uniui-breadcrumb-current, .uniui-breadcrumb-current p {{margin:0;color:var(--uniui-text);font-weight:650}}
.uniui-breadcrumb-separator, .uniui-breadcrumb-separator p {{margin:0;color:var(--uniui-text_muted)}}
.uniui-demo-page {{gap:18px}}
.uniui-demo-heading {{gap:16px;align-items:center;flex-wrap:nowrap!important}}
.uniui-demo-title .widget-label, .uniui-demo-title {{color:var(--uniui-text)!important;font-size:24px;font-weight:750}}
.uniui-demo-subtitle .widget-label, .uniui-demo-subtitle,
.uniui-demo-hint .widget-label, .uniui-demo-hint {{color:var(--uniui-text_muted)!important}}
.uniui-demo-stats {{display:flex;flex-flow:row wrap;gap:14px;align-items:stretch}}
.uniui-demo-header-content {{width:100%;min-width:0;gap:8px;align-items:center;flex-wrap:nowrap!important}}
@container (max-width:1019px) {{
  .uniui-admin-sidebar {{width:72px!important;min-width:72px!important;max-width:72px!important;flex-basis:72px!important;padding:14px 8px}}
  .uniui-admin-sidebar .widget-button,
  .uniui-admin-sidebar .widget-button button {{font-size:0;text-align:center;padding:8px 4px}}
  .uniui-admin-sidebar .widget-button::first-letter,
  .uniui-admin-sidebar .widget-button button::first-letter {{font-size:16px}}
  .uniui-splitter-widget {{display:none!important}}
  .uniui-shell-content {{padding:22px 18px}}
}}
@container (max-width:719px) {{
  .uniui-shell-header {{padding:0 10px}}
  .uniui-shell-content {{padding:18px 12px}}
  .uniui-shell-footer {{display:none!important}}
}}
</style>
"""


_SPLITTER_HTML = """
<div class="uniui-splitter-handle" title="Drag to resize navigation"
 onpointerdown="const h=this,root=h.closest('.uniui-shell-body'),side=root.querySelector('.uniui-admin-sidebar'),bridge=root.querySelector('.uniui-sidebar-width-bridge input'),sx=event.clientX,sw=side.getBoundingClientRect().width,pid=event.pointerId;h.setPointerCapture(pid);const move=e=>{const w=Math.max(168,Math.min(360,sw+e.clientX-sx));side.style.width=w+'px';side.style.minWidth=w+'px';side.style.maxWidth=w+'px';side.style.flex='0 0 '+w+'px';};const up=e=>{move(e);const w=Math.round(side.getBoundingClientRect().width);if(bridge){bridge.value=String(w);bridge.dispatchEvent(new Event('change',{bubbles:true}));}h.removeEventListener('pointermove',move);};h.addEventListener('pointermove',move);h.addEventListener('pointerup',up,{once:true});h.addEventListener('pointercancel',up,{once:true});">
</div>
"""


class JupyterCardAdapter(ICard):
    def __init__(self):
        self._title = _html("", "uniui-card-title")
        self._subtitle = _html("", "uniui-card-subtitle")
        self._title.layout.display = "none"
        self._subtitle.layout.display = "none"
        self._copy = widgets.VBox([self._title, self._subtitle])
        self._copy.add_class("uniui-card-copy")
        self._action = widgets.Box()
        self._action.layout.display = "none"
        self._header = widgets.HBox([self._copy, self._action])
        self._header.add_class("uniui-card-header")
        self._content = widgets.Box(layout=widgets.Layout(width="100%", min_width="0"))
        self._native = widgets.VBox([self._header, self._content])
        self._native.add_class("uniui-admin-card")

    def get_native(self): return self._native

    def set_title(self, title: str) -> None:
        self._title.value = f"<p>{escape(str(title))}</p>"
        self._title.layout.display = None if title else "none"

    def set_subtitle(self, subtitle: str) -> None:
        self._subtitle.value = f"<p>{escape(str(subtitle))}</p>"
        self._subtitle.layout.display = None if subtitle else "none"

    def set_content(self, widget) -> None:
        self._content.children = (_native(widget),)

    def set_action(self, widget) -> None:
        self._action.children = (_native(widget),)
        self._action.layout.display = None


class JupyterStatCardAdapter(IStatCard):
    def __init__(self):
        self._label = _html("", "uniui-stat-label")
        self._value = _html("<p>—</p>", "uniui-stat-value")
        self._unit = _html("", "uniui-stat-unit")
        self._trend_widget = _html("<p>— &nbsp;No change</p>", "uniui-stat-trend")
        self._native = widgets.VBox([self._label, self._value, self._unit, self._trend_widget])
        self._native.add_class("uniui-stat-card")
        self._status = "ok"
        self._trend = 0.0

    def get_native(self): return self._native

    def set_label(self, label: str) -> None:
        self._label.value = f"<p>{escape(str(label))}</p>"

    def set_value(self, value: str) -> None:
        self._value.value = f"<p>{escape(str(value))}</p>"

    def set_unit(self, unit: str) -> None:
        self._unit.value = f"<p>{escape(str(unit))}</p>" if unit else ""

    def set_trend(self, trend: float) -> None:
        self._trend = float(trend)
        for name in ("uniui-up", "uniui-down"):
            self._trend_widget.remove_class(name)
        if self._trend > 0:
            text = f"↗ &nbsp;{self._trend:.1f}% &nbsp;vs last period"
            self._trend_widget.add_class("uniui-up")
        elif self._trend < 0:
            text = f"↘ &nbsp;{abs(self._trend):.1f}% &nbsp;vs last period"
            self._trend_widget.add_class("uniui-down")
        else:
            text = "— &nbsp;No change"
        self._trend_widget.value = f"<p>{text}</p>"

    def set_status(self, status: str) -> None:
        for name in ("uniui-status-warn", "uniui-status-error"):
            self._native.remove_class(name)
        self._status = status if status in {"ok", "warn", "error"} else "ok"
        if self._status != "ok":
            self._native.add_class(f"uniui-status-{self._status}")


class JupyterTableAdapter(ITable):
    def __init__(self):
        self._columns: List[Dict] = []
        self._rows: List[Dict] = []
        self._row_click_cb: Optional[Callable[[Dict], None]] = None
        self._table = _html("", "uniui-table-html")
        self._message = _html("", "uniui-table-message")
        self._message.layout.display = "none"
        self._bridge = widgets.BoundedIntText(value=-1, min=-1, max=1_000_000)
        self._bridge.layout.display = "none"
        self._bridge.add_class("uniui-table-bridge")
        self._bridge.observe(self._on_bridge, names="value")
        self._native = widgets.VBox([self._table, self._message, self._bridge])
        self._native.add_class("uniui-admin-table")

    def get_native(self): return self._native

    def set_columns(self, columns: List[Dict]) -> None:
        self._columns = list(columns)
        self._render()

    def set_rows(self, rows: List[Dict]) -> None:
        self._rows = list(rows)
        self._render()

    def _render(self) -> None:
        headers = "".join(
            f"<th>{escape(str(col.get('label', col.get('key', ''))))}</th>"
            for col in self._columns
        )
        rendered_rows = []
        for index, row in enumerate(self._rows):
            cells = []
            for col in self._columns:
                key = col.get("key", "")
                value = row.get(key, "")
                classes = []
                if key in {"amount", "price", "total"}:
                    classes.append("uniui-number")
                if key == "status":
                    classes.extend(("uniui-status", self._status_class(value)))
                class_attr = f' class="{" ".join(classes)}"' if classes else ""
                cells.append(f"<td{class_attr}>{escape(str(value))}</td>")
            click = (
                "const root=this.closest('.uniui-admin-table'),input=root.querySelector(" 
                "'.uniui-table-bridge input');if(input){input.value='" + str(index) +
                "';input.dispatchEvent(new Event('change',{bubbles:true}));}"
            )
            rendered_rows.append(f'<tr onclick="{click}">{"".join(cells)}</tr>')
        self._table.value = (
            f'<div class="uniui-admin-table-wrap"><table><thead><tr>{headers}</tr></thead>'
            f'<tbody>{"".join(rendered_rows)}</tbody></table></div>'
        )

    @staticmethod
    def _status_class(value) -> str:
        text = str(value).lower()
        if text in {"active", "delivered", "shipped"}:
            return "uniui-ok"
        if text in {"processing", "pending", "warning"}:
            return "uniui-warn"
        if text in {"cancelled", "failed", "error"}:
            return "uniui-error"
        return ""

    def set_loading(self, loading: bool) -> None:
        if loading:
            self._table.layout.display = "none"
            self._message.value = "<p>Loading…</p>"
            self._message.layout.display = None
        else:
            self._message.layout.display = "none"
            self._table.layout.display = None

    def set_error(self, message: str) -> None:
        if message:
            self._table.layout.display = "none"
            self._message.value = f"<p>⚠ &nbsp;{escape(str(message))}</p>"
            self._message.layout.display = None
        else:
            self._message.layout.display = "none"
            self._table.layout.display = None

    def on_row_click(self, fn: Callable[[Dict], None]) -> None:
        self._row_click_cb = fn

    def _on_bridge(self, change) -> None:
        index = int(change["new"])
        if index >= 0 and index < len(self._rows) and self._row_click_cb:
            self._row_click_cb(self._rows[index])
        if index != -1:
            self._bridge.value = -1


_ICONS = {"dashboard": "▦", "users": "♟", "settings": "⚙"}


class JupyterSidebarAdapter(ISidebar):
    def __init__(self):
        self._native = widgets.VBox()
        self._native.add_class("uniui-admin-sidebar")
        self._keys: List[str] = []
        self._labels: List[str] = []
        self._icons: List[str] = []
        self._buttons: List[widgets.Button] = []
        self._select_cb: Optional[Callable[[str], None]] = None
        self._active = ""
        self._collapsed = False

    def get_native(self): return self._native

    def add_item(self, key: str, label: str, icon: str = "") -> None:
        self._keys.append(key)
        self._labels.append(label)
        self._icons.append(icon)
        button = widgets.Button(layout=widgets.Layout(width="100%"))
        button.tooltip = label
        button.on_click(lambda _button, k=key: self._on_select(k))
        self._buttons.append(button)
        self._native.children = tuple(self._buttons)
        self._refresh_button(len(self._buttons) - 1)

    def set_active(self, key: str) -> None:
        self._active = key
        for index, button in enumerate(self._buttons):
            if self._keys[index] == key:
                button.add_class("uniui-active")
            else:
                button.remove_class("uniui-active")

    def on_select(self, fn: Callable[[str], None]) -> None:
        self._select_cb = fn

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = bool(collapsed)
        for index in range(len(self._buttons)):
            self._refresh_button(index)
        width = 72 if self._collapsed else 236
        self.set_width(width, fixed=self._collapsed)

    def set_width(self, width: int, fixed: bool = False) -> None:
        width = max(72 if fixed else 168, min(360, int(width)))
        px = f"{width}px"
        self._native.layout.width = px
        self._native.layout.flex = f"0 0 {px}"
        self._native.layout.min_width = px if fixed else "168px"
        self._native.layout.max_width = px if fixed else "360px"

    def _refresh_button(self, index: int) -> None:
        icon = _ICONS.get(self._icons[index], self._icons[index] or self._labels[index][:1])
        self._buttons[index].description = icon if self._collapsed else f"{icon}  {self._labels[index]}"

    def _on_select(self, key: str) -> None:
        if self._select_cb:
            self._select_cb(key)


class JupyterAppShellAdapter(IAppShell):
    def __init__(self):
        self._style = widgets.HTML(value=_css())
        self._header = widgets.HBox()
        self._header.add_class("uniui-shell-header")
        self._header.layout.display = "none"
        self._content = widgets.Box()
        self._content.add_class("uniui-shell-content")
        self._handle = widgets.HTML(value=_SPLITTER_HTML)
        self._handle.add_class("uniui-splitter-widget")
        self._width_bridge = widgets.BoundedIntText(value=236, min=168, max=360)
        self._width_bridge.layout.display = "none"
        self._width_bridge.add_class("uniui-sidebar-width-bridge")
        self._width_bridge.observe(self._on_width, names="value")
        self._body = widgets.HBox([self._handle, self._content, self._width_bridge])
        self._body.add_class("uniui-shell-body")
        self._footer = widgets.Box()
        self._footer.add_class("uniui-shell-footer")
        self._footer.layout.display = "none"
        self._native = widgets.VBox([self._style, self._header, self._body, self._footer])
        self._native.add_class("uniui-admin-shell")
        self._native.layout.width = "100%"
        self._sidebar: Optional[JupyterSidebarAdapter] = None
        self._saved_sidebar_width = 236
        _theme_targets.add(self)

    def get_native(self): return self._native

    def set_header(self, widget) -> None:
        self._header.children = (_native(widget),)
        self._header.layout.display = "flex"

    def set_sidebar(self, sidebar) -> None:
        native = _native(sidebar)
        self._sidebar = sidebar if hasattr(sidebar, "set_width") else None
        self._body.children = (native, self._handle, self._content, self._width_bridge)
        if self._sidebar:
            self._sidebar.set_width(self._saved_sidebar_width)

    def set_content(self, widget) -> None:
        self._content.children = (_native(widget),)

    def set_footer(self, widget) -> None:
        self._footer.children = (_native(widget),)
        self._footer.layout.display = None

    def _on_width(self, change) -> None:
        width = max(168, min(360, int(change["new"])))
        self._saved_sidebar_width = width
        if self._sidebar:
            self._sidebar.set_width(width)

    def apply_theme(self) -> None:
        self._style.value = _css()


class JupyterBreadcrumbAdapter(IBreadcrumb):
    def __init__(self):
        self._native = widgets.HBox()
        self._native.add_class("uniui-breadcrumb")
        self._click_cb: Optional[Callable[[str], None]] = None
        self._items: List[Dict] = []

    def get_native(self): return self._native

    def set_items(self, items: List[Dict]) -> None:
        self._items = list(items)
        children = []
        for index, item in enumerate(self._items):
            if index:
                children.append(_html("<p>›</p>", "uniui-breadcrumb-separator"))
            label = str(item.get("label", ""))
            path = item.get("path", "")
            if path and index != len(self._items) - 1:
                button = widgets.Button(description=label, layout=widgets.Layout(width="auto"))
                button.on_click(lambda _button, p=path: self._on_click(p))
                children.append(button)
            else:
                children.append(_html(f"<p>{escape(label)}</p>", "uniui-breadcrumb-current"))
        self._native.children = tuple(children)

    def on_click(self, fn: Callable[[str], None]) -> None:
        self._click_cb = fn

    def _on_click(self, path: str) -> None:
        if self._click_cb:
            self._click_cb(path)


def _register(factory_class) -> None:
    factory_class.createCard = lambda self: JupyterCardAdapter()
    factory_class.createStatCard = lambda self: JupyterStatCardAdapter()
    factory_class.createTable = lambda self: JupyterTableAdapter()
    factory_class.createSidebar = lambda self: JupyterSidebarAdapter()
    factory_class.createAppShell = lambda self: JupyterAppShellAdapter()
    factory_class.createBreadcrumb = lambda self: JupyterBreadcrumbAdapter()


from .jupyter import JupyterWidgetFactory

_register(JupyterWidgetFactory)


__all__ = [
    "JupyterCardAdapter", "JupyterStatCardAdapter", "JupyterTableAdapter",
    "JupyterSidebarAdapter", "JupyterAppShellAdapter", "JupyterBreadcrumbAdapter",
    "get_admin_palette", "is_admin_dark", "set_admin_theme",
]
