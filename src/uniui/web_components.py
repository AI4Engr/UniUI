"""Modern Admin components for the NiceGUI Web backend."""
from __future__ import annotations

from html import escape
from typing import Callable, Dict, List, Optional

from nicegui import ui

from .components import (
    IAppShell, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, ISidebar, IStatCard, ITable,
)
from . import theme_runtime
from .icons import ADMIN_ICON_NAMES, css_mask
from .theme import get_admin_metrics, get_admin_tokens
from .visuals import (
    CHART_TYPES, append_chart_point, normalized_series,
    render_chart_svg, render_gauge_svg,
)
from .web import NiceGUIWidgetFactory, _WebAdapter


_M = get_admin_metrics()

_shells: List["WebAppShellAdapter"] = []
_visuals: List[object] = []
_css_installed = False


def _shared_icon_css() -> str:
    rules = [
        ".uniui-svg-icon{display:inline-block;width:18px;height:18px;"
        "flex:0 0 18px;margin-right:9px;color:inherit;vertical-align:-4px}"
    ]
    for name in ADMIN_ICON_NAMES:
        rules.append(f".uniui-svg-icon.uniui-icon-{name}{{{css_mask(name)}}}")
        rules.append(
            f".uniui-icon-{name} .q-btn__content::before{{content:'';display:inline-block;"
            f"width:18px;height:18px;flex:0 0 18px;margin-right:7px;{css_mask(name)}}}"
        )
    return "".join(rules)


def get_palette() -> Dict[str, str]:
    return get_admin_tokens(theme_runtime.is_dark())


def is_dark() -> bool:
    return theme_runtime.is_dark()


@theme_runtime.register_refresh
def _sync_palette() -> None:
    """Re-render every live shell and visual after a theme change.

    Registered with theme_runtime, so switching from any backend restyles the
    web components too — the per-backend flags used to drift apart.
    """
    for target in (*list(_shells), *list(_visuals)):
        try:
            target.apply_theme()
        except Exception:
            continue


def set_theme(dark: bool) -> bool:
    """Switch every live shell, on this and every other backend."""
    return theme_runtime.set_theme(dark)


# Names used before the admin_ prefix was dropped.
get_admin_palette = get_palette
is_admin_dark = is_dark
set_admin_theme = set_theme


def _install_admin_css() -> None:
    global _css_installed
    if _css_installed:
        return
    ui.add_css(
        _shared_icon_css() + """
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


_native = theme_runtime.native


def _clear(element) -> None:
    element.clear()


class WebCardAdapter(_WebAdapter, ICard):
    def __init__(self):
        _install_admin_css()
        card = ui.card().classes("uniui-web-card")
        with card:
            with ui.row().classes("w-full items-start no-wrap"):
                with ui.column().classes("gap-0 grow"):
                    self._title = ui.label("").classes("uniui-web-card-title")
                    self._subtitle = ui.label("").classes("uniui-web-card-subtitle")
                self._action = ui.row().classes("items-start")
            self._content = ui.column().classes("w-full items-stretch")
        super().__init__(card)

    def set_title(self, title: str) -> None: self._title.set_text(str(title))
    def set_subtitle(self, subtitle: str) -> None: self._subtitle.set_text(str(subtitle))
    def set_content(self, widget) -> None:
        _clear(self._content); _native(widget).move(self._content)
    def set_action(self, widget) -> None:
        _clear(self._action); _native(widget).move(self._action)


class WebStatCardAdapter(_WebAdapter, IStatCard):
    def __init__(self):
        _install_admin_css()
        card = ui.card().classes("uniui-web-stat")
        with card:
            self._label = ui.label("").classes("uniui-web-stat-label")
            self._value = ui.label("—").classes("uniui-web-stat-value")
            self._unit = ui.label("").classes("uniui-web-stat-unit")
            self._trend_label = ui.label("—  No change").classes("uniui-web-stat-trend")
        super().__init__(card)
        self._status = "ok"
        self._trend = 0.0

    def set_label(self, label: str) -> None: self._label.set_text(str(label))
    def set_value(self, value: str) -> None: self._value.set_text(str(value))
    def set_unit(self, unit: str) -> None: self._unit.set_text(str(unit))
    def set_trend(self, trend: float) -> None:
        self._trend = float(trend)
        self._apply_trend()
    def _apply_trend(self) -> None:
        trend = self._trend
        self._trend_label.classes(remove="uniui-up uniui-down uniui-warn uniui-error")
        if self._status != "ok" and trend == 0:
            text = "Needs attention" if self._status == "warn" else "Error"
            self._trend_label.set_text(text); self._trend_label.classes(add=f"uniui-{self._status}")
        elif trend > 0:
            self._trend_label.set_text(f"↗  {trend:.1f}%  vs last period"); self._trend_label.classes(add="uniui-up")
        elif trend < 0:
            self._trend_label.set_text(f"↘  {abs(trend):.1f}%  vs last period"); self._trend_label.classes(add="uniui-down")
        else:
            self._trend_label.set_text("—  No change")
    def set_status(self, status: str) -> None:
        self._status = status if status in {"ok", "warn", "error"} else "ok"
        self._apply_trend()


class WebMetricListAdapter(_WebAdapter, IMetricList):
    """Dense two-column key/value list for secondary metrics."""

    def __init__(self):
        _install_admin_css()
        root = ui.column().classes("w-full items-stretch gap-0")
        super().__init__(root)

    def set_items(self, items: List[Dict]) -> None:
        _clear(self._native)
        with self._native:
            for index, item in enumerate(items):
                classes = "w-full uniui-web-metric-row"
                if index > 0:
                    classes += " uniui-metric-divider"
                with ui.row().classes(classes):
                    ui.label(str(item.get("label", ""))).classes("uniui-web-metric-label")
                    ui.label(str(item.get("value", ""))).classes("uniui-web-metric-value")


class WebTableAdapter(_WebAdapter, ITable):
    def __init__(self):
        _install_admin_css()
        self._columns: List[Dict] = []
        self._rows: List[Dict] = []
        self._row_click_cb: Optional[Callable[[Dict], None]] = None
        root = ui.column().classes("w-full items-stretch gap-0")
        with root:
            self._table = ui.table(columns=[], rows=[], pagination={"rowsPerPage": 0}).classes("uniui-web-table")
            self._message = ui.label("").classes("self-center q-pa-lg")
        self._message.set_visibility(False)
        self._table.on("rowClick", self._on_row_event)
        super().__init__(root)

    def set_columns(self, columns: List[Dict]) -> None:
        self._columns = list(columns)
        self._table.columns = [
            {"name": c.get("key", ""), "label": c.get("label", c.get("key", "")), "field": c.get("key", ""), "align": "right" if c.get("key") in {"amount", "price", "total"} else "left"}
            for c in self._columns
        ]
        if any(c.get("key") == "status" for c in self._columns):
            self._table.add_slot(
                "body-cell-status",
                """
                <q-td :props="props">
                  <span class="uniui-status-pill"
                    :class="{
                      'uniui-status-ok': ['active','delivered','shipped'].includes(String(props.value).toLowerCase()),
                      'uniui-status-warn': ['processing','pending','warning'].includes(String(props.value).toLowerCase()),
                      'uniui-status-error': ['inactive','cancelled','failed','error'].includes(String(props.value).toLowerCase()),
                      'uniui-status-neutral': !['active','delivered','shipped','processing','pending','warning','inactive','cancelled','failed','error'].includes(String(props.value).toLowerCase())
                    }">{{ props.value }}</span>
                </q-td>
                """,
            )
        self._table.update()
    def set_rows(self, rows: List[Dict]) -> None:
        self._rows = list(rows); self._table.rows = self._rows; self._table.update()
    def set_loading(self, loading: bool) -> None:
        self._table.set_visibility(not loading); self._message.set_text("Loading…"); self._message.set_visibility(loading)
    def set_error(self, message: str) -> None:
        self._table.set_visibility(not bool(message)); self._message.set_text(f"⚠  {message}"); self._message.set_visibility(bool(message))
    def on_row_click(self, fn: Callable[[Dict], None]) -> None: self._row_click_cb = fn
    def _on_row_event(self, event) -> None:
        args = getattr(event, "args", None)
        row = args.get("row") if isinstance(args, dict) else None
        if row is None and isinstance(args, (list, tuple)) and args:
            row = args[-1]
        if self._row_click_cb and isinstance(row, dict): self._row_click_cb(row)


class WebGaugeAdapter(_WebAdapter, IGauge):
    def __init__(self):
        _install_admin_css()
        self._label = ""; self._value = 0.0; self._unit = ""
        self._minimum = 0.0; self._maximum = 100.0; self._status = "ok"
        super().__init__(ui.html("", sanitize=False).classes("uniui-web-gauge"))
        _visuals.append(self)
        self._render()
    def set_label(self, label: str) -> None: self._label = str(label); self._render()
    def set_value(self, value: float) -> None: self._value = float(value); self._render()
    def set_range(self, minimum: float, maximum: float) -> None:
        self._minimum = float(minimum); self._maximum = max(float(maximum), self._minimum + 1.0); self._render()
    def set_unit(self, unit: str) -> None: self._unit = str(unit); self._render()
    def set_status(self, status: str) -> None:
        self._status = status if status in {"ok", "warn", "error"} else "ok"; self._render()
    def _render(self) -> None:
        self._native.set_content(render_gauge_svg(
            self._label, self._value, self._unit, self._minimum,
            self._maximum, self._status, get_palette(),
        ))
    def apply_theme(self) -> None: self._render()


class WebChartAdapter(_WebAdapter, IChart):
    def __init__(self):
        _install_admin_css(); self._chart_type = "line"; self._title = ""
        self._x: List = []; self._series: List[Dict] = []; self._max_points = 120
        super().__init__(ui.html("", sanitize=False).classes("uniui-web-chart"))
        _visuals.append(self); self._render()
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
        self._native.set_content(render_chart_svg(
            self._chart_type, self._title, self._x, self._series, get_palette()
        ))
    def apply_theme(self) -> None: self._render()


class WebDrawerAdapter(_WebAdapter, IDrawer):
    def __init__(self):
        _install_admin_css(); self._open = False
        root = ui.element("div").classes("uniui-web-drawer-root")
        with root:
            scrim = ui.element("div").classes("uniui-web-drawer-scrim")
            panel = ui.card().classes("uniui-web-drawer-panel")
            with panel:
                with ui.row().classes("uniui-web-drawer-header"):
                    self._title = ui.label("").classes("uniui-web-drawer-title")
                    close = ui.button("", color=None, on_click=lambda _event: self.close()).props("flat round dense")
                    close.add_slot("default", '<span class="uniui-svg-icon uniui-icon-close"></span>')
                self._content = ui.column().classes("w-full items-stretch")
        scrim.on("click", lambda _event: self.close())
        super().__init__(root)
    def set_title(self, title: str) -> None: self._title.set_text(str(title))
    def set_content(self, widget) -> None: _clear(self._content); _native(widget).move(self._content)
    def open(self) -> None: self._open = True; self._native.classes(add="uniui-open")
    def close(self) -> None: self._open = False; self._native.classes(remove="uniui-open")
    def toggle(self) -> None: self.close() if self._open else self.open()
    def is_open(self) -> bool: return self._open


class WebSidebarAdapter(_WebAdapter, ISidebar):
    def __init__(self):
        _install_admin_css()
        self._keys: List[str] = []; self._buttons = []; self._select_cb = None; self._active = ""; self._collapsed = False
        super().__init__(ui.column().classes("uniui-web-sidebar items-stretch"))
    def add_item(self, key: str, label: str, icon: str = "") -> None:
        with self._native:
            button = ui.button(
                "",
                color=None,
                on_click=lambda _e, k=key: self._emit(k),
            ).props("flat no-caps")
        if icon in ADMIN_ICON_NAMES:
            button.add_slot(
                "default",
                f'<span class="uniui-svg-icon uniui-icon-{icon}"></span>'
                f'<span class="uniui-nav-label">{escape(label)}</span>',
            )
        button.tooltip(label)
        self._keys.append(key); self._buttons.append(button)
    def set_active(self, key: str) -> None:
        self._active = key
        for i, button in enumerate(self._buttons):
            button.classes(add="uniui-active" if self._keys[i] == key else "", remove="" if self._keys[i] == key else "uniui-active")
    def on_select(self, fn: Callable[[str], None]) -> None: self._select_cb = fn
    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = bool(collapsed)
        for button in self._buttons:
            button.classes(
                add="uniui-collapsed" if collapsed else "",
                remove="" if collapsed else "uniui-collapsed",
            )
    def _emit(self, key: str) -> None:
        if self._select_cb: self._select_cb(key)


class WebAppShellAdapter(_WebAdapter, IAppShell):
    def __init__(self):
        _install_admin_css()
        root = ui.column().classes("uniui-web-admin w-full items-stretch gap-0")
        with root:
            self._header = ui.row().classes("uniui-web-header")
            self._splitter = ui.splitter(value=18, limits=(12, 28)).classes("uniui-web-body")
            with self._splitter.before:
                self._sidebar_slot = ui.column().classes("w-full h-full items-stretch gap-0")
            with self._splitter.after:
                self._content = ui.column().classes("uniui-web-content items-stretch gap-0")
            self._footer = ui.row().classes("uniui-web-footer items-center")
        self._header.set_visibility(False); self._footer.set_visibility(False)
        super().__init__(root)
        _shells.append(self)
        self.apply_theme()
    def set_header(self, widget) -> None:
        _clear(self._header); _native(widget).move(self._header); self._header.set_visibility(True)
    def set_sidebar(self, sidebar) -> None:
        _clear(self._sidebar_slot); _native(sidebar).move(self._sidebar_slot)
    def set_content(self, widget) -> None:
        _clear(self._content); _native(widget).move(self._content)
    def set_footer(self, widget) -> None:
        _clear(self._footer); _native(widget).move(self._footer); self._footer.set_visibility(True)
    def apply_theme(self) -> None:
        p = get_palette()
        variables = {f"--uniui-{key}": value for key, value in p.items()}
        variables.update({
            "--uniui-header-height": f"{_M['header_height']}px",
            "--uniui-footer-height": f"{_M['footer_height']}px",
            "--uniui-shell-bars": f"{_M['header_height'] + _M['footer_height']}px",
            "--uniui-sidebar-collapsed": f"{_M['sidebar_collapsed']}px",
            "--uniui-control-height": f"{_M['control_height']}px",
            "--uniui-stat-value-size": f"{_M['stat_value_size']}px",
            "--uniui-stat-label-size": f"{_M['stat_label_size']}px",
            "--uniui-sidebar-edge-width": f"{_M['sidebar_edge_width']}px",
            "--uniui-content-padding": f"{_M['content_padding']}px {_M['content_padding'] + 4}px {_M['content_padding'] + 4}px",
            "--uniui-card-padding": f"{_M['card_padding']}px {_M['card_padding'] + 2}px",
            "--uniui-card-gap": f"{_M['card_gap']}px",
            "--uniui-section-gap": f"{_M['section_gap']}px",
        })
        self._native.style(";".join(f"{key}:{value}" for key, value in variables.items()))


class WebBreadcrumbAdapter(_WebAdapter, IBreadcrumb):
    def __init__(self):
        _install_admin_css(); self._click_cb = None; self._items = []
        super().__init__(ui.row().classes("uniui-web-breadcrumb"))
    def set_items(self, items: List[Dict]) -> None:
        self._items = list(items); _clear(self._native)
        with self._native:
            for index, item in enumerate(self._items):
                if index: ui.label("›").style("color:var(--uniui-text_muted)")
                label, path = str(item.get("label", "")), item.get("path", "")
                if path and index != len(self._items) - 1:
                    ui.button(label, color=None, on_click=lambda _e, p=path: self._emit(p)).props("flat dense no-caps")
                else: ui.label(label).style("color:var(--uniui-text);font-weight:650")
    def on_click(self, fn: Callable[[str], None]) -> None: self._click_cb = fn
    def _emit(self, path: str) -> None:
        if self._click_cb: self._click_cb(path)


def _register(factory_class) -> None:
    factory_class.createCard = lambda self: WebCardAdapter()
    factory_class.createStatCard = lambda self: WebStatCardAdapter()
    factory_class.createMetricList = lambda self: WebMetricListAdapter()
    factory_class.createTable = lambda self: WebTableAdapter()
    factory_class.createSidebar = lambda self: WebSidebarAdapter()
    factory_class.createAppShell = lambda self: WebAppShellAdapter()
    factory_class.createBreadcrumb = lambda self: WebBreadcrumbAdapter()
    factory_class.createGauge = lambda self: WebGaugeAdapter()
    factory_class.createChart = lambda self: WebChartAdapter()
    factory_class.createDrawer = lambda self: WebDrawerAdapter()


_register(NiceGUIWidgetFactory)


__all__ = [
    "WebCardAdapter", "WebStatCardAdapter", "WebTableAdapter", "WebSidebarAdapter",
    "WebAppShellAdapter", "WebBreadcrumbAdapter", "get_palette", "is_dark", "set_theme",
    "get_admin_palette", "is_admin_dark", "set_admin_theme",
    "WebGaugeAdapter", "WebChartAdapter", "WebDrawerAdapter",
]
