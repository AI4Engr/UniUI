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

from .admin import (
    IAppShell, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, ISidebar, IStatCard, ITable,
)
from .admin_icons import ADMIN_ICON_NAMES, css_mask
from .admin_theme import get_admin_metrics, get_admin_tokens
from .admin_visuals import (
    CHART_TYPES, append_chart_point, normalized_series,
    render_chart_svg, render_gauge_svg,
)


_LIGHT = get_admin_tokens(False)
_DARK = get_admin_tokens(True)
_M = get_admin_metrics()

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


def _shared_icon_css() -> str:
    rules = []
    for name in ADMIN_ICON_NAMES:
        rules.append(
            f".uniui-icon-{name} button::before{{content:'';display:inline-block;"
            f"width:18px;height:18px;flex:0 0 18px;margin-right:8px;"
            f"vertical-align:-4px;{css_mask(name)}}}"
        )
    return "".join(rules)


def _css() -> str:
    p = get_admin_palette()
    variables = ";".join(f"--uniui-{key}:{value}" for key, value in p.items())
    return f"""
<style>
{_shared_icon_css()}
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
  border:1px solid var(--uniui-border_strong)!important; border-radius:9px!important;
  min-height:38px; padding:7px 10px;
}}
.uniui-admin-shell .widget-button,
.uniui-admin-shell .widget-button button {{
  background:var(--uniui-accent)!important; color:white!important;
  border:1px solid var(--uniui-accent)!important; border-radius:9px!important;
  min-height:36px; padding:6px 13px; font-weight:600;
}}
.uniui-admin-shell .widget-button:hover,
.uniui-admin-shell .widget-button button:hover {{
  background:var(--uniui-accent_hover)!important;
  border-color:var(--uniui-accent_hover)!important;
}}
.uniui-shell-header {{
  flex:0 0 {_M['header_height']}px; min-height:{_M['header_height']}px; padding:0 16px; gap:10px;
  align-items:center; background:var(--uniui-header_bg);
  border-bottom:1px solid var(--uniui-border);
}}
.uniui-shell-body {{display:flex; width:100%; min-width:0; flex:1 1 auto}}
.uniui-shell-content {{
  min-width:0; flex:1 1 0; padding:{_M['content_padding']}px {_M['content_padding'] + 4}px {_M['content_padding'] + 4}px;
  overflow:auto; background:var(--uniui-bg);
}}
.uniui-shell-footer {{
  flex:0 0 auto; min-height:{_M['footer_height']}px; padding:8px 16px;
  background:var(--uniui-surface); border-top:1px solid var(--uniui-border);
}}
.uniui-admin-card {{
  width:100%; min-width:0; padding:{_M['card_padding']}px {_M['card_padding'] + 2}px; gap:{_M['card_gap']}px;
  background:var(--uniui-surface); border:1px solid var(--uniui-border);
  border-radius:14px; box-shadow:none;
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
  border-radius:14px;
  box-shadow:none; gap:1px; flex:1 1 190px;
}}
.uniui-stat-label, .uniui-stat-label p {{margin:0;color:var(--uniui-text_muted);font-size:{_M['stat_label_size']}px;font-weight:600}}
.uniui-stat-value, .uniui-stat-value p {{margin:2px 0 0;color:var(--uniui-text);font-size:{_M['stat_value_size']}px;line-height:1.15;font-weight:750}}
.uniui-stat-unit, .uniui-stat-unit p {{margin:0;color:var(--uniui-text_muted);font-size:11px}}
.uniui-stat-trend, .uniui-stat-trend p {{margin:9px 0 0;color:var(--uniui-text_muted);font-size:11px;font-weight:650}}
.uniui-stat-trend.uniui-up, .uniui-stat-trend.uniui-up p {{color:var(--uniui-ok)}}
.uniui-stat-trend.uniui-down, .uniui-stat-trend.uniui-down p {{color:var(--uniui-error)}}
.uniui-stat-trend.uniui-status-warn, .uniui-stat-trend.uniui-status-warn p {{color:var(--uniui-warn)}}
.uniui-stat-trend.uniui-status-error, .uniui-stat-trend.uniui-status-error p {{color:var(--uniui-error)}}
.uniui-metric-list-wrap {{width:100%; min-width:0}}
.uniui-metric-row {{display:flex; justify-content:space-between; align-items:center; padding:8px 0}}
.uniui-metric-row.uniui-metric-divider {{border-top:1px solid var(--uniui-border)}}
.uniui-metric-label {{color:var(--uniui-text_muted); font-size:{_M['stat_label_size']}px}}
.uniui-metric-value {{color:var(--uniui-text); font-size:13px; font-weight:600}}
.uniui-admin-table {{width:100%; min-width:0}}
.uniui-admin-table table {{width:100%; border-collapse:separate; border-spacing:0; color:var(--uniui-text); font-size:13px}}
.uniui-admin-table th {{
  padding:10px 12px; text-align:left; color:var(--uniui-text_muted);
  background:var(--uniui-surface); border-bottom:1px solid var(--uniui-border);
  font-size:{_M['stat_label_size']}px; font-weight:600;
}}
.uniui-admin-table td {{padding:11px 12px;border-bottom:1px solid var(--uniui-border)}}
.uniui-admin-table tbody tr {{cursor:pointer}}
.uniui-admin-table tbody tr:hover {{background:var(--uniui-surface_subtle)}}
.uniui-admin-table .uniui-number {{text-align:right}}
.uniui-status-pill {{display:inline-flex;align-items:center;min-height:24px;padding:3px 9px;
  border-radius:999px;font-size:11px;font-weight:700}}
.uniui-status-pill.uniui-status-ok {{color:var(--uniui-status_ok_fg);background:var(--uniui-status_ok_bg)}}
.uniui-status-pill.uniui-status-warn {{color:var(--uniui-status_warn_fg);background:var(--uniui-status_warn_bg)}}
.uniui-status-pill.uniui-status-error {{color:var(--uniui-status_error_fg);background:var(--uniui-status_error_bg)}}
.uniui-status-pill.uniui-status-neutral {{color:var(--uniui-status_neutral_fg);background:var(--uniui-status_neutral_bg)}}
.uniui-table-message, .uniui-table-message p {{margin:20px 0;text-align:center;color:var(--uniui-text_muted)}}
.uniui-admin-gauge,.uniui-admin-chart {{width:100%;min-width:0}}
.uniui-admin-gauge svg,.uniui-admin-chart svg {{display:block;width:100%;height:auto;max-height:250px}}
.uniui-admin-drawer {{max-height:0;opacity:0;overflow:hidden;transform:translateX(24px);
  pointer-events:none;padding:0 20px;background:var(--uniui-surface);border:1px solid transparent;
  border-radius:14px;transition:max-height .2s ease,opacity .18s ease,transform .2s ease,padding .2s ease}}
.uniui-admin-drawer.uniui-open {{max-height:520px;opacity:1;transform:none;pointer-events:auto;
  padding:18px 20px;border-color:var(--uniui-border);box-shadow:var(--uniui-shadow)}}
.uniui-drawer-header {{align-items:center}}
.uniui-drawer-title,.uniui-drawer-title p {{margin:0;color:var(--uniui-text);font-size:18px;font-weight:700}}
.uniui-admin-sidebar {{
  width:{_M['sidebar_expanded']}px; min-width:{_M['sidebar_min']}px;
  max-width:{_M['sidebar_max']}px; flex:0 0 {_M['sidebar_expanded']}px;
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
.uniui-admin-sidebar .uniui-active {{box-shadow:inset {_M['sidebar_edge_width']}px 0 0 var(--uniui-sidebar_edge)}}
.uniui-admin-sidebar .uniui-active button::before {{background:var(--uniui-accent)}}
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
.uniui-demo-page {{gap:{_M['section_gap']}px}}
.uniui-demo-heading {{gap:16px;align-items:center;flex-wrap:nowrap!important}}
.uniui-demo-subtitle .widget-label, .uniui-demo-subtitle {{color:var(--uniui-text)!important;font-size:17px;font-weight:650}}
.uniui-demo-hint .widget-label, .uniui-demo-hint {{color:var(--uniui-text_muted)!important}}
.uniui-demo-stats {{display:flex;flex-flow:row wrap;gap:{_M['card_gap']}px;align-items:stretch}}
.uniui-demo-header-content {{width:100%;min-width:0;gap:8px;align-items:center;flex-wrap:nowrap!important}}
@container (max-width:1019px) {{
  .uniui-admin-sidebar {{width:{_M['sidebar_collapsed']}px!important;min-width:{_M['sidebar_collapsed']}px!important;max-width:{_M['sidebar_collapsed']}px!important;flex-basis:{_M['sidebar_collapsed']}px!important;padding:14px 8px}}
  .uniui-admin-sidebar .widget-button,
  .uniui-admin-sidebar .widget-button button {{font-size:0;text-align:center;padding:8px 4px}}
  .uniui-admin-sidebar .widget-button button::before {{margin-right:0}}
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
        self._apply_trend()

    def _apply_trend(self) -> None:
        for name in ("uniui-up", "uniui-down", "uniui-status-warn", "uniui-status-error"):
            self._trend_widget.remove_class(name)
        if self._status != "ok" and self._trend == 0:
            text = "Needs attention" if self._status == "warn" else "Error"
            self._trend_widget.add_class(f"uniui-status-{self._status}")
        elif self._trend > 0:
            text = f"↗ &nbsp;{self._trend:.1f}% &nbsp;vs last period"
            self._trend_widget.add_class("uniui-up")
        elif self._trend < 0:
            text = f"↘ &nbsp;{abs(self._trend):.1f}% &nbsp;vs last period"
            self._trend_widget.add_class("uniui-down")
        else:
            text = "— &nbsp;No change"
        self._trend_widget.value = f"<p>{text}</p>"

    def set_status(self, status: str) -> None:
        self._status = status if status in {"ok", "warn", "error"} else "ok"
        self._apply_trend()


class JupyterMetricListAdapter(IMetricList):
    """Dense two-column key/value list for secondary metrics."""

    def __init__(self):
        self._html = _html("", "uniui-metric-list")
        self._native = widgets.VBox([self._html])
        self._native.add_class("uniui-metric-list-wrap")

    def get_native(self): return self._native

    def set_items(self, items: List[Dict]) -> None:
        rows = []
        for index, item in enumerate(items):
            classes = "uniui-metric-row" + (" uniui-metric-divider" if index > 0 else "")
            label = escape(str(item.get("label", "")))
            value = escape(str(item.get("value", "")))
            rows.append(
                f'<div class="{classes}"><span class="uniui-metric-label">{label}</span>'
                f'<span class="uniui-metric-value">{value}</span></div>'
            )
        self._html.value = "".join(rows)


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
                rendered_value = escape(str(value))
                if key in {"amount", "price", "total"}:
                    classes.append("uniui-number")
                if key == "status":
                    rendered_value = (
                        f'<span class="uniui-status-pill {self._status_class(value)}">'
                        f"{rendered_value}</span>"
                    )
                class_attr = f' class="{" ".join(classes)}"' if classes else ""
                cells.append(f"<td{class_attr}>{rendered_value}</td>")
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
            return "uniui-status-ok"
        if text in {"processing", "pending", "warning"}:
            return "uniui-status-warn"
        if text in {"inactive", "cancelled", "failed", "error"}:
            return "uniui-status-error"
        return "uniui-status-neutral"

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


class JupyterGaugeAdapter(IGauge):
    def __init__(self):
        self._label = ""; self._value = 0.0; self._unit = ""
        self._minimum = 0.0; self._maximum = 100.0; self._status = "ok"
        self._native = _html("", "uniui-admin-gauge")
        _theme_targets.add(self)
        self._render()
    def get_native(self): return self._native
    def set_label(self, label: str) -> None: self._label = str(label); self._render()
    def set_value(self, value: float) -> None: self._value = float(value); self._render()
    def set_range(self, minimum: float, maximum: float) -> None:
        self._minimum = float(minimum); self._maximum = max(float(maximum), self._minimum + 1.0); self._render()
    def set_unit(self, unit: str) -> None: self._unit = str(unit); self._render()
    def set_status(self, status: str) -> None:
        self._status = status if status in {"ok", "warn", "error"} else "ok"; self._render()
    def _render(self) -> None:
        self._native.value = render_gauge_svg(
            self._label, self._value, self._unit, self._minimum,
            self._maximum, self._status, get_admin_palette(),
        )
    def apply_theme(self) -> None: self._render()


class JupyterChartAdapter(IChart):
    def __init__(self):
        self._chart_type = "line"; self._title = ""; self._x: List = []
        self._series: List[Dict] = []; self._max_points = 120
        self._native = _html("", "uniui-admin-chart")
        _theme_targets.add(self); self._render()
    def get_native(self): return self._native
    def set_type(self, chart_type: str) -> None:
        self._chart_type = chart_type if chart_type in CHART_TYPES else "line"; self._render()
    def set_title(self, title: str) -> None: self._title = str(title); self._render()
    def set_data(self, x: List, series: List[Dict]) -> None:
        self._x = list(x)[-self._max_points:]; self._series = normalized_series(series)
        for item in self._series: item["data"] = item["data"][-self._max_points:]
        self._render()
    def append_data(self, x, values) -> None:
        append_chart_point(self._x, self._series, x, values, self._max_points); self._render()
    def set_max_points(self, max_points: int) -> None:
        self._max_points = max(2, int(max_points)); self._x = self._x[-self._max_points:]
        for item in self._series: item["data"] = item["data"][-self._max_points:]
        self._render()
    def _render(self) -> None:
        self._native.value = render_chart_svg(
            self._chart_type, self._title, self._x, self._series, get_admin_palette()
        )
    def apply_theme(self) -> None: self._render()


class JupyterDrawerAdapter(IDrawer):
    def __init__(self):
        self._title = _html("", "uniui-drawer-title")
        close = widgets.Button(description="", tooltip="Close drawer", layout=widgets.Layout(width="36px"))
        close.add_class("uniui-icon-close"); close.on_click(lambda _button: self.close())
        header = widgets.HBox([self._title, close]); header.add_class("uniui-drawer-header")
        self._content = widgets.Box()
        self._native = widgets.VBox([header, self._content]); self._native.add_class("uniui-admin-drawer")
        self._open = False
    def get_native(self): return self._native
    def set_title(self, title: str) -> None: self._title.value = f"<p>{escape(str(title))}</p>"
    def set_content(self, widget) -> None: self._content.children = (_native(widget),)
    def open(self) -> None: self._open = True; self._native.add_class("uniui-open")
    def close(self) -> None: self._open = False; self._native.remove_class("uniui-open")
    def toggle(self) -> None: self.close() if self._open else self.open()
    def is_open(self) -> bool: return self._open


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
        if icon in ADMIN_ICON_NAMES:
            button.add_class(f"uniui-icon-{icon}")
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
        width = _M["sidebar_collapsed"] if self._collapsed else _M["sidebar_expanded"]
        self.set_width(width, fixed=self._collapsed)

    def set_width(self, width: int, fixed: bool = False) -> None:
        minimum = _M["sidebar_collapsed"] if fixed else _M["sidebar_min"]
        width = max(minimum, min(_M["sidebar_max"], int(width)))
        px = f"{width}px"
        self._native.layout.width = px
        self._native.layout.flex = f"0 0 {px}"
        self._native.layout.min_width = px if fixed else f"{_M['sidebar_min']}px"
        self._native.layout.max_width = px if fixed else f"{_M['sidebar_max']}px"

    def _refresh_button(self, index: int) -> None:
        self._buttons[index].description = "" if self._collapsed else self._labels[index]

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
        self._width_bridge = widgets.BoundedIntText(
            value=_M["sidebar_expanded"],
            min=_M["sidebar_min"],
            max=_M["sidebar_max"],
        )
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
        self._saved_sidebar_width = _M["sidebar_expanded"]
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
        width = max(_M["sidebar_min"], min(_M["sidebar_max"], int(change["new"])))
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
    factory_class.createMetricList = lambda self: JupyterMetricListAdapter()
    factory_class.createTable = lambda self: JupyterTableAdapter()
    factory_class.createSidebar = lambda self: JupyterSidebarAdapter()
    factory_class.createAppShell = lambda self: JupyterAppShellAdapter()
    factory_class.createBreadcrumb = lambda self: JupyterBreadcrumbAdapter()
    factory_class.createGauge = lambda self: JupyterGaugeAdapter()
    factory_class.createChart = lambda self: JupyterChartAdapter()
    factory_class.createDrawer = lambda self: JupyterDrawerAdapter()


from .jupyter import JupyterWidgetFactory

_register(JupyterWidgetFactory)


__all__ = [
    "JupyterCardAdapter", "JupyterStatCardAdapter", "JupyterTableAdapter",
    "JupyterSidebarAdapter", "JupyterAppShellAdapter", "JupyterBreadcrumbAdapter",
    "JupyterGaugeAdapter", "JupyterChartAdapter", "JupyterDrawerAdapter",
    "get_admin_palette", "is_admin_dark", "set_admin_theme",
]
