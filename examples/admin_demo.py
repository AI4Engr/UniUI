"""
Admin Dashboard Demo — UniUI M3 admin skeleton showcase.

Run:
    python examples/admin_demo.py --ui qt
    %run examples/admin_demo.py --ui jupyter   # inside a notebook cell
    python examples/admin_demo.py --ui web
"""
import sys
import os
import random
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uniui import (
    use, parse_args_ui, show_ui, State, Computed, bind_text, TaskRunner,
    LayoutSpec, LayoutItem, schedule_after,
)
import uniui
from uniui import theme_runtime


_ADMIN_THEME = State("light")
_THEME_TOGGLE = None


def _toggle_admin_theme():
    if _THEME_TOGGLE is not None:
        _THEME_TOGGLE()


#: Set by main()'s Qt path to its _apply_theme(dark) closure. Qt's
#: stylesheet is a one-shot string baked into setStyleSheet() at apply
#: time, not a live binding like Web's CSS variables or Jupyter's re-emitted
#: <style> node -- theme_runtime.set_active_theme() alone updates THEME but
#: never repaints an already-built Qt widget tree. Web/Jupyter don't need
#: this hook: their refresh_theme_* already reads THEME live.
_QT_RESTYLE_HOOK = None


def _apply_named_theme(name: str) -> None:
    """Switch to any registered theme by name, refreshing every backend.

    Additive alongside the light/dark quick-toggle (_toggle_admin_theme):
    the picker calls this, the header's toggle button keeps flipping
    between the two defaults exactly as before.
    """
    theme_runtime.set_active_theme(name)
    _ADMIN_THEME.set(name)
    if _QT_RESTYLE_HOOK is not None:
        _QT_RESTYLE_HOOK(uniui.is_dark())

# ---------------------------------------------------------------------------
# Fake data
# ---------------------------------------------------------------------------

_USERS = [
    {"id": "1", "name": "Alice Johnson", "email": "alice@example.com",  "role": "Admin",  "status": "Active"},
    {"id": "2", "name": "Bob Smith",     "email": "bob@example.com",    "role": "Editor", "status": "Inactive"},
    {"id": "3", "name": "Carol White",   "email": "carol@example.com",  "role": "Viewer", "status": "Active"},
    {"id": "4", "name": "David Lee",     "email": "david@example.com",  "role": "Editor", "status": "Active"},
    {"id": "5", "name": "Eve Martinez",  "email": "eve@example.com",    "role": "Admin",  "status": "Active"},
]

_ORDERS = [
    {"id": "#1042", "customer": "Alice Johnson", "amount": "$120.00", "status": "Shipped"},
    {"id": "#1041", "customer": "Carol White",   "amount": "$89.50",  "status": "Processing"},
    {"id": "#1040", "customer": "David Lee",     "amount": "$340.00", "status": "Delivered"},
    {"id": "#1039", "customer": "Eve Martinez",  "amount": "$55.00",  "status": "Cancelled"},
]

_DETAIL_METRICS = [
    {"label": "Active handles",   "value": "4"},
    {"label": "Event loop latency", "value": "0.3 ms"},
    {"label": "Heap size",        "value": "13.5 MiB"},
    {"label": "Used heap",        "value": "12.3 MiB"},
    {"label": "HTTP p95 latency", "value": "7.3 ms"},
]


# ---------------------------------------------------------------------------
# Cross-backend composition helpers (shared by Qt, Jupyter, and Web)
# ---------------------------------------------------------------------------

def _set_props(widget, props):
    """Apply optional browser-native presentation props when available."""
    native = widget.get_native() if hasattr(widget, "get_native") else widget
    if hasattr(native, "props"):
        native.props(props)
    return widget


def _set_icon_class(widget, icon_name):
    """Switch a shared SVG icon class on the widget."""
    from uniui.icons import ADMIN_ICON_NAMES

    for name in ADMIN_ICON_NAMES:
        widget.remove_class(f"uniui-icon-{name}")
    widget.add_class(f"uniui-icon-{icon_name}")
    # ipywidgets Buttons carry the generic theme's accent colour as an
    # inline style, which outranks any stylesheet. Clear it so the admin
    # palette can style this button through its semantic class.
    native = widget.get_native() if hasattr(widget, "get_native") else widget
    style = getattr(native, "style", None)
    if style is not None and hasattr(style, "button_color"):
        style.button_color = None
        style.text_color = None
    return widget


def _page_frame(title, subtitle, action_text=""):
    f = uniui._get_factory()
    page = f.create_vbox()
    page.set_spec(LayoutSpec(gap=18))
    page.add_class("uniui-page")
    page_native = page.get_native() if hasattr(page, "get_native") else page
    if callable(getattr(page_native, "tooltip", None)):
        page_native.tooltip(title)  # NiceGUI element
    elif hasattr(page_native, "tooltip"):
        page_native.tooltip = title  # ipywidgets trait

    heading = f.create_hbox()
    heading.set_spec(LayoutSpec(gap=16))
    heading.add_class("uniui-page-heading")
    copy = f.create_vbox()
    copy.set_spec(LayoutSpec(gap=4))
    # The breadcrumb in the header bar already names the page; the H1 here
    # would just repeat it, so only the descriptive subtitle is shown.
    subtitle_label = f.create_label()
    subtitle_label.set_text(subtitle)
    subtitle_label.add_class("uniui-page-subtitle")
    copy.add_item(subtitle_label)
    heading.add_item_with_spec(copy, LayoutItem(copy, grow=1))

    action = None
    if action_text:
        action = f.create_button()
        action.set_text(action_text)
        action.add_class("uniui-shell-primary-action")
        _set_props(action, "no-caps unelevated")
        heading.add_item(action)

    page.add_item(heading)
    return page, action


def dashboard_page(_ctx):
    f = uniui._get_factory()
    page, refresh_btn = _page_frame(
        "Dashboard",
        "Monitor the signals that need your attention today.",
        "Refresh data",
    )

    live_updates = f.create_switch()
    live_updates.set_checked(True)
    live_label = f.create_label()
    live_label.set_text("Live updates")
    live_row = f.create_hbox()
    live_row.set_spec(LayoutSpec(gap=8))
    live_row.add_item(live_updates)
    live_row.add_item(live_label)
    page.add_item(live_row)

    cards = []
    for label, status in (
        ("Active Users", "ok"), ("Orders", "ok"),
        ("Revenue", "ok"), ("Open Errors", "warn"),
    ):
        card = f.create_stat_card()
        card.set_label(label)
        card.set_value("…")
        card.set_trend(0)
        card.set_status(status)
        cards.append(card)

    stats = f.create_wrap()
    stats.set_spec(LayoutSpec(gap=14))
    stats.add_class("uniui-page-stats")
    for card in cards:
        stats.add_item(card)

    gauge = f.create_gauge()
    gauge.set_label("Service health"); gauge.set_range(0, 100)
    gauge.set_unit("%"); gauge.set_status("ok"); gauge.set_value(82)
    chart = f.create_chart()
    chart.set_type("area"); chart.set_title("Live activity"); chart.set_max_points(24)
    chart.set_data(
        ["-4", "-3", "-2", "-1", "now"],
        [{"name": "Requests", "data": [42, 58, 51, 67, 62]}],
    )
    gauge_card = f.create_card(); gauge_card.set_title("Health")
    gauge_card.set_subtitle("Animated radial progress"); gauge_card.set_content(gauge)
    chart_card = f.create_card(); chart_card.set_title("Realtime")
    chart_card.set_subtitle("Keeps the latest 24 points"); chart_card.set_content(chart)

    metrics = f.create_metric_list(); metrics.set_items(_DETAIL_METRICS)
    disk_usage = f.create_progress_bar(); disk_usage.set_value(62); disk_usage.set_status("warn")
    metrics_body = f.create_vbox(); metrics_body.set_spec(LayoutSpec(gap=10))
    metrics_body.add_item(metrics); metrics_body.add_item(disk_usage)
    metrics_card = f.create_card(); metrics_card.set_title("Process")
    metrics_card.set_subtitle("Runtime signals at a glance"); metrics_card.set_content(metrics_body)

    visuals = f.create_wrap(); visuals.set_spec(LayoutSpec(gap=14))
    visuals.add_item(gauge_card); visuals.add_item(chart_card); visuals.add_item(metrics_card)

    # Runs the "fetch" on a worker thread via TaskRunner so the UI stays
    # responsive during the simulated network delay - cross-backend
    # (uniui.state.TaskRunner), unlike a plain synchronous refresh.
    runner = TaskRunner()

    def _fetch(_cancelled: threading.Event):
        time.sleep(0.5)
        active = sum(1 for user in _USERS if user["status"] == "Active")
        revenue = sum(
            float(order["amount"].replace("$", "").replace(",", ""))
            for order in _ORDERS if order["status"] != "Cancelled"
        )
        return {"users": active, "orders": len(_ORDERS), "revenue": revenue, "errors": 2}

    def _on_done(data):
        values = (str(data["users"]), str(data["orders"]), f"${data['revenue']:,.0f}", str(data["errors"]))
        trends = (5.2, -1.4, 12.0, 0.0)
        for card, value, trend in zip(cards, values, trends):
            card.set_value(value)
            card.set_trend(trend)
        cards[-1].set_status("error")
        health = max(0, 100 - data["errors"] * 7)
        gauge.set_value(health)
        gauge.set_status("ok" if health >= 80 else "warn")
        chart.append_data(time.strftime("%H:%M:%S"), [data["users"] * 14 + data["orders"]])
        refresh_btn.set_text("Refresh data")
        refresh_btn.set_enabled(True)

    def refresh():
        refresh_btn.set_enabled(False)
        refresh_btn.set_text("Refreshing…")
        runner.run(_fetch, on_done=_on_done, on_error=lambda _exc: _on_done({
            "users": "—", "orders": "—", "revenue": 0, "errors": "—"
        }))

    refresh_btn.connect(refresh)
    refresh()

    _live_state = {"value": 62}

    def _live_tick():
        try:
            if live_updates.is_checked():
                _live_state["value"] = max(20, min(120, _live_state["value"] + random.randint(-6, 8)))
                chart.append_data(time.strftime("%H:%M:%S"), [_live_state["value"]])
        except Exception:
            return  # page/chart was torn down; stop rescheduling
        schedule_after(1500, _live_tick)

    schedule_after(1500, _live_tick)

    table = f.create_table()
    table.set_columns([
        {"key": "id", "label": "Order", "width": 80},
        {"key": "customer", "label": "Customer", "width": 180},
        {"key": "amount", "label": "Amount", "width": 100},
        {"key": "status", "label": "Status", "width": 120},
    ])
    table.set_rows(_ORDERS)
    selected = State("Click a row to inspect")
    hint = f.create_label()
    bind_text(hint, selected)
    hint.add_class("uniui-page-hint")
    table.on_row_click(lambda row: selected.set(
        f"{row['id']}  ·  {row['customer']}  ·  {row['status']}"
    ))
    table_content = f.create_vbox()
    table_content.set_spec(LayoutSpec(gap=12))
    table_content.add_item(table)
    table_content.add_item(hint)
    table_card = f.create_card()
    table_card.set_title("Recent Orders")
    table_card.set_subtitle("Click a row to inspect it")
    table_card.set_content(table_content)

    page.add_item(stats)
    page.add_item(visuals)
    page.add_item_with_spec(table_card, LayoutItem(table_card, grow=1))
    return page


def users_page(_ctx):
    f = uniui._get_factory()
    page, add_btn = _page_frame(
        "Users", "Manage access, roles, and account status.", "Add user"
    )
    add_btn.connect(lambda: None)

    search_input = f.create_line_edit()
    native_input = search_input.get_native()
    if hasattr(native_input, "setPlaceholderText"):
        # Qt: QLineEdit
        native_input.setPlaceholderText("Search by name or email…")
        native_input.setClearButtonEnabled(True)
        native_input.setMaximumWidth(420)
    elif hasattr(native_input, "props"):
        # Web: NiceGUI element
        native_input.props('placeholder="Search by name or email…" clearable outlined dense')
    elif hasattr(native_input, "placeholder"):
        # Jupyter: ipywidgets Text - .layout is a real settable trait here,
        # unlike Qt's QWidget.layout() method or NiceGUI's absent attribute.
        native_input.placeholder = "Search by name or email…"
        native_input.layout.width = "100%"
        native_input.layout.max_width = "420px"

    table = f.create_table()
    table.set_columns([
        {"key": "id", "label": "ID", "width": 50},
        {"key": "name", "label": "Name", "width": 180},
        {"key": "email", "label": "Email"},
        {"key": "role", "label": "Role", "width": 90},
        {"key": "status", "label": "Status", "width": 90},
    ])
    table.set_rows(_USERS)

    def filter_users():
        query = search_input.get_text().strip().lower()
        table.set_rows([
            user for user in _USERS
            if not query or query in user["name"].lower() or query in user["email"].lower()
        ])

    search_input.on_change(filter_users)
    content = f.create_vbox()
    content.set_spec(LayoutSpec(gap=14))
    content.add_item(search_input)
    content.add_item(table)
    card = f.create_card()
    card.set_title("All Users")
    card.set_subtitle("Type to filter by name or email")
    card.set_content(content)
    page.add_item_with_spec(card, LayoutItem(card, grow=1))
    return page


def settings_page(_ctx):
    f = uniui._get_factory()
    page, open_drawer = _page_frame(
        "Settings", "Choose how the workspace looks and behaves.", "Open drawer"
    )
    info = f.create_label()
    bind_text(info, Computed(lambda: f"Current theme: {_ADMIN_THEME.value.title()}", _ADMIN_THEME))
    drawer_button = f.create_button()
    bind_text(drawer_button, Computed(
        # _ADMIN_THEME is the reactive trigger; the label reads the real
        # is_dark() flag so it stays correct after the picker below
        # switches to a named theme, not just after the quick toggle.
        lambda: "Switch to Light" if uniui.is_dark() else "Switch to Dark",
        _ADMIN_THEME,
    ))
    drawer_button.connect(_toggle_admin_theme)

    # Theme picker: every registered theme, not just the light/dark pair the
    # header's quick-toggle button flips between.
    theme_picker = f.create_combo_box()
    for name in uniui.list_themes():
        theme_picker.add_item(name)
    theme_picker.set_selection(_ADMIN_THEME.value)
    theme_picker.on_change(lambda: _apply_named_theme(theme_picker.get_text()))

    drawer = f.create_drawer(); drawer.set_title("Workspace settings")
    drawer_content = f.create_vbox(); drawer_hint = f.create_label()
    drawer_hint.set_text("Changes apply immediately without rebuilding the current route.")
    drawer_content.add_item(drawer_hint); drawer_content.add_item(drawer_button)
    drawer.set_content(drawer_content)
    open_drawer.connect(drawer.open)
    content = f.create_vbox()
    content.set_spec(LayoutSpec(gap=12))
    content.add_item(info)
    content.add_item(theme_picker)
    open_button = f.create_button(); open_button.set_text("Open settings drawer")
    open_button.connect(drawer.open); content.add_item(open_button)
    card = f.create_card()
    card.set_title("Appearance")
    card.set_subtitle("Theme changes preserve routes, table state, and loaded data")
    card.set_content(content)
    page.add_item(card)
    page.add_item(drawer)
    return page


def _labeled_field(label_text, control):
    f = uniui._get_factory()
    field = f.create_vbox()
    field.set_spec(LayoutSpec(gap=6))
    field.add_class("uniui-page-field")
    label = f.create_label()
    label.set_text(label_text)
    label.add_class("uniui-page-field-label")
    field.add_item(label)
    field.add_item(control)
    return field


def components_page(_ctx):
    f = uniui._get_factory()
    page, _ = _page_frame(
        "Components",
        "A quick reference for the form and navigation controls available in every backend.",
    )

    role_dropdown = f.create_dropdown()
    for role in ("Admin", "Editor", "Viewer"):
        role_dropdown.add_item(role)
    role_dropdown.set_selection("Editor")
    role_field = _labeled_field("Role (dropdown)", role_dropdown)

    theme_combo = f.create_combo_box()
    for option in ("System", "Light", "Dark", "High contrast"):
        theme_combo.add_item(option)
    theme_combo.set_selection("System")
    theme_field = _labeled_field("Theme (editable combo box)", theme_combo)

    status_dropdown = f.create_dropdown()
    for status in ("Active", "Inactive", "Pending"):
        status_dropdown.add_item(status)
    status_dropdown.set_selection("Active")
    status_field = _labeled_field("Status (dropdown)", status_dropdown)

    selection_hint = f.create_label()
    selection_hint.set_text("Editor · Active")
    selection_hint.add_class("uniui-page-hint")

    def _update_hint():
        selection_hint.set_text(f"{role_dropdown.get_text()} · {status_dropdown.get_text()}")

    role_dropdown.on_change(_update_hint)
    status_dropdown.on_change(_update_hint)

    fields_row = f.create_wrap()
    fields_row.set_spec(LayoutSpec(gap=16))
    fields_row.add_item(role_field)
    fields_row.add_item(theme_field)
    fields_row.add_item(status_field)

    inputs_content = f.create_vbox()
    inputs_content.set_spec(LayoutSpec(gap=14))
    inputs_content.add_item(fields_row)
    inputs_content.add_item(selection_hint)

    inputs_card = f.create_card()
    inputs_card.set_title("Selection controls")
    inputs_card.set_subtitle("Dropdown and combo box, wired to a shared change handler")
    inputs_card.set_content(inputs_content)

    overview_tab = f.create_vbox()
    overview_tab.set_spec(LayoutSpec(gap=10))
    overview_label = f.create_label()
    overview_label.set_text(
        "Tabs mount every pane up front and only toggle visibility, so state "
        "in inactive tabs is preserved when you switch back."
    )
    overview_tab.add_item(overview_label)

    activity_tab = f.create_vbox()
    activity_tab.set_spec(LayoutSpec(gap=8))
    for entry in (
        "Alice Johnson updated the Dashboard layout",
        "Bob Smith invited a new Editor",
        "Nightly export completed without errors",
    ):
        row = f.create_label()
        row.set_text(f"•  {entry}")
        activity_tab.add_item(row)

    notify_switch = f.create_switch()
    notify_switch.set_checked(True)
    notify_label = f.create_label()
    notify_label.set_text("Notifications")
    notify_row = f.create_hbox()
    notify_row.set_spec(LayoutSpec(gap=8))
    notify_row.add_item(notify_switch)
    notify_row.add_item(notify_label)
    # Without a trailing stretch, a bare HBox stretched to the tab's full
    # width divides ALL leftover space between its two zero-stretch
    # children instead of letting them hug together on the left - the
    # switch and its own label ended up ~500px apart (caught by actually
    # clicking into this nested Settings sub-tab and looking, not by any
    # test).
    notify_row.add_stretch()

    compact_checkbox = f.create_checkbox()
    compact_checkbox.set_checked(False)
    compact_label = f.create_label()
    compact_label.set_text("Compact density")
    compact_row = f.create_hbox()
    compact_row.set_spec(LayoutSpec(gap=8))
    compact_row.add_item(compact_checkbox)
    compact_row.add_item(compact_label)
    compact_row.add_stretch()

    settings_tab = f.create_vbox()
    settings_tab.set_spec(LayoutSpec(gap=8))
    settings_tab.add_item(notify_row)
    settings_tab.add_item(compact_row)

    tabs = f.create_tab_widget()
    tabs.add_tab(overview_tab, "Overview")
    tabs.add_tab(activity_tab, "Activity")
    tabs.add_tab(settings_tab, "Settings")

    tabs_card = f.create_card()
    tabs_card.set_title("Tabs")
    tabs_card.set_subtitle("Three panes sharing one tab strip")
    tabs_card.set_content(tabs)

    # More controls: RadioGroup, NumberInput, and Slider, each wired to a
    # live label via on_change - matching the gallery's "real interaction,
    # not a screenshot" principle.
    density_hint = f.create_label()
    density_hint.set_text("Density: Comfortable")
    density_radio = f.create_radio_group()
    density_radio.set_options(["Comfortable", "Compact", "Spacious"])
    density_radio.set_selected("Comfortable")
    density_radio.on_change(lambda: density_hint.set_text(
        f"Density: {density_radio.get_selected()}"
    ))
    density_box = f.create_vbox()
    density_box.set_spec(LayoutSpec(gap=6))
    density_box.add_item(density_radio)
    density_box.add_item(density_hint)
    density_field = _labeled_field("Table density", density_box)

    rows_hint = f.create_label()
    rows_hint.set_text("25 rows per page")
    rows_input = f.create_number_input()
    rows_input.set_range(5, 100)
    rows_input.set_step(5)
    rows_input.set_value(25)
    rows_input.on_change(lambda: rows_hint.set_text(
        f"{int(rows_input.get_value())} rows per page"
    ))
    rows_box = f.create_vbox()
    rows_box.set_spec(LayoutSpec(gap=6))
    rows_box.add_item(rows_input)
    rows_box.add_item(rows_hint)
    rows_field = _labeled_field("Rows per page", rows_box)

    interval_hint = f.create_label()
    interval_hint.set_text("Every 5s")
    interval_slider = f.create_slider()
    interval_slider.set_range(1, 30)
    interval_slider.set_step(1)
    interval_slider.set_value(5)
    interval_slider.on_change(lambda: interval_hint.set_text(
        f"Every {int(interval_slider.get_value())}s"
    ))
    interval_box = f.create_vbox()
    interval_box.set_spec(LayoutSpec(gap=6))
    interval_box.add_item(interval_slider)
    interval_box.add_item(interval_hint)
    interval_field = _labeled_field("Refresh interval", interval_box)

    more_controls_row = f.create_wrap()
    more_controls_row.set_spec(LayoutSpec(gap=16))
    more_controls_row.add_item(density_field)
    more_controls_row.add_item(rows_field)
    more_controls_row.add_item(interval_field)

    more_controls_card = f.create_card()
    more_controls_card.set_title("More controls")
    more_controls_card.set_subtitle("RadioGroup, NumberInput, and Slider, each driving a live label")
    more_controls_card.set_content(more_controls_row)

    page.add_item(inputs_card)
    page.add_item(more_controls_card)
    page.add_item_with_spec(tabs_card, LayoutItem(tabs_card, grow=1))
    return page


def not_found_page(ctx):
    label = uniui._get_factory().create_label()
    label.set_text(f"404 — No page at: {ctx.path}")
    return label


def _build_router():
    """The shared route table, built fresh per call since Route/Router hold
    per-instance navigation state - split out so a test can build one
    without also going through show_ui()'s blocking event loop, and so Qt,
    Jupyter, and Web all navigate through the exact same page functions."""
    from uniui.routing import Router, Route

    return Router(
        Route("/dashboard",   dashboard_page,   name="dashboard"),
        Route("/users",       users_page,       name="users"),
        Route("/components",  components_page,  name="components"),
        # Cached: settings_page binds labels to the module-level, permanent
        # _ADMIN_THEME state. Rebuilding it on every visit (the default for
        # uncached routes) would leak one bind_text subscription per visit,
        # each pointing at a widget that gets deleted the moment the route
        # is left - the next theme toggle after that throws "Internal C++
        # object already deleted" on Qt for every leaked visit. Caching
        # means the page (and its one subscription) is built exactly once.
        Route("/settings",    settings_page,    name="settings", cache=True),
        not_found=not_found_page,
    )


def create_admin_ui(framework="auto", debug=False):
    """Build the Admin dashboard shell and return it (Jupyter and Web only).

    Mirrors the create_*_ui(framework) -> show_ui(layout, ...) pattern used
    by the other examples (create_bmi_ui, create_sysmon_ui, ...).
    """
    global _THEME_TOGGLE

    use(framework)

    from uniui.routing import RouterView, sync_breadcrumb
    if framework == "jupyter":
        from uniui import jupyter_components as admin_backend
    else:
        from uniui import web_components as admin_backend

    _ADMIN_THEME.set("light")
    admin_backend.set_admin_theme(False)
    f = uniui._get_factory()
    router = _build_router()

    header = f.create_hbox()
    header.add_class("uniui-shell-header-content")
    header.set_spec(LayoutSpec(gap=8))
    logo = f.create_label(); logo.set_text("U"); logo.add_class("uniui-shell-logo-mark")
    product = f.create_label(); product.set_text("UniUI Admin"); product.add_class("uniui-shell-product")
    beta_badge = f.create_badge(); beta_badge.set_text("Beta"); beta_badge.set_status("warn")
    back = f.create_button()
    forward = f.create_button()
    back.set_text(""); forward.set_text("")
    _set_props(back, "flat round dense")
    _set_props(forward, "flat round dense")
    _set_icon_class(back, "arrow_back")
    _set_icon_class(forward, "arrow_forward")
    back.add_class("uniui-shell-icon-button")
    forward.add_class("uniui-shell-icon-button")
    back.connect(router.back)
    forward.connect(router.forward)
    breadcrumb = f.create_breadcrumb()
    sync_breadcrumb(breadcrumb, router, trail_fn=lambda ctx: (
        [{"label": "Dashboard"}] if ctx.name == "dashboard" else
        [{"label": "Dashboard", "path": "/dashboard"},
         {"label": ctx.name.replace("-", " ").title()}]
    ))
    breadcrumb.on_click(router.push)
    theme_button = f.create_button()
    theme_button.set_text("Dark mode")
    theme_button.add_class("uniui-shell-theme-button")
    _set_props(theme_button, "flat no-caps")
    _set_icon_class(theme_button, "dark_mode")
    header.add_item(logo)
    header.add_item(product)
    header.add_item(beta_badge)
    header.add_item(back)
    header.add_item(forward)
    header.add_item_with_spec(breadcrumb, LayoutItem(breadcrumb, grow=1))
    header.add_item(theme_button)
    avatar = f.create_label(); avatar.set_text("AJ"); avatar.add_class("uniui-shell-avatar")
    header.add_item(avatar)

    sidebar = f.create_sidebar()
    sidebar.add_group("Workspace")
    for key, label, icon in (
        ("dashboard", "Dashboard", "dashboard"),
        ("users", "Users", "users"),
        ("components", "Components", "components"),
    ):
        sidebar.add_item(key, label, icon)
    sidebar.add_group("Admin")
    sidebar.add_item("settings", "Settings", "settings")
    sidebar.on_select(router.push_named)
    router.on_navigate(lambda ctx: sidebar.set_active(ctx.name)
                       if ctx.name and ctx.name != "__not_found__" else None)

    content = RouterView(router)
    shell = f.create_app_shell()
    shell.set_header(header)
    shell.set_sidebar(sidebar)
    shell.set_content(content)
    if debug and hasattr(shell, "set_debug"):
        shell.set_debug(True)
    footer = f.create_hbox()
    ready = f.create_label(); ready.set_text("●  All systems operational"); ready.add_class("uniui-web-status-ok")
    version = f.create_label(); version.set_text("UniUI admin preview · v0.1"); version.add_class("uniui-web-footer-meta")
    footer.add_item(ready); footer.add_stretch(); footer.add_item(version)
    shell.set_footer(footer)

    def apply_theme(dark):
        admin_backend.set_admin_theme(dark)
        _ADMIN_THEME.set("dark" if dark else "light")
        theme_button.set_text("Light mode" if dark else "Dark mode")
        _set_icon_class(theme_button, "light_mode" if dark else "dark_mode")

    def toggle():
        # Read the real active-theme flag, not the display-name string: if
        # the settings-page picker has switched to a named theme like
        # "sunset", _ADMIN_THEME.value is no longer "Light"/"Dark" and a
        # string comparison here would silently toggle the wrong direction.
        apply_theme(not uniui.is_dark())

    _THEME_TOGGLE = toggle
    theme_button.connect(toggle)
    apply_theme(False)
    router.push("/dashboard")
    return shell


def _main_browser(framework):
    """Standalone entrypoint: build the Admin shell and display it."""
    from uniui.display import show_ui

    shell = create_admin_ui(framework)
    show_ui(shell, title="UniUI Admin Demo", width=1280, height=780)


# ---------------------------------------------------------------------------
# Admin stylesheet
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Main (Qt shell only - the pages above are cross-backend; the shell is not
# unified yet, see notes/admin_demo_unification_plan.md Step 3)
# ---------------------------------------------------------------------------

class _NativeWrap:
    """Adapt a native QWidget to the tiny get_native() protocol UniUI expects.

    Only used by the Qt-only shell below (header/footer built from raw
    QtWidgets) - the pages themselves no longer need it."""

    def __init__(self, widget):
        self._widget = widget

    def get_native(self):
        return self._widget


def _header_icon(name, color):
    """Render a toolbar icon from the cross-backend Admin SVG source."""
    from uniui.qt_icons import admin_icon

    aliases = {"back": "arrow_back", "forward": "arrow_forward"}
    return admin_icon(aliases.get(name, name), color, size=20)


def main():
    global _THEME_TOGGLE

    framework = parse_args_ui()
    use(framework if framework != "auto" else "qt")

    if framework in {"jupyter", "web"}:
        _main_browser(framework)
        return

    from uniui.routing import RouterView, sync_breadcrumb
    from uniui.qt_components import get_admin_palette, set_admin_theme
    from uniui.qt_style import base_stylesheet, tag_native
    from PySide2 import QtWidgets, QtCore

    _ADMIN_THEME.set("light")
    set_admin_theme(False)

    router = _build_router()

    f = uniui._get_factory()

    # ── Product header ────────────────────────────────────────────────────────
    class _ResponsiveTopBar(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self._responsive_widgets = None

        def set_responsive_widgets(self, product, search):
            self._responsive_widgets = (product, search)

        def resizeEvent(self, event):
            super().resizeEvent(event)
            if self._responsive_widgets is None:
                return
            product, search = self._responsive_widgets
            width = event.size().width()
            product.setVisible(width >= 650)
            search.setVisible(width >= 850)

    header_w = _ResponsiveTopBar()
    tag_native(header_w, "uniui-shell-topbar")
    header_w.setMinimumWidth(0)
    header_w.setSizePolicy(
        QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred
    )
    hl = QtWidgets.QHBoxLayout(header_w)
    hl.setContentsMargins(4, 0, 4, 0)
    hl.setSpacing(7)

    logo_mark = f.create_label()
    logo_mark.set_text("U")
    logo_mark.add_class("uniui-shell-logo-mark")
    logo_mark_native = logo_mark.get_native()
    logo_mark_native.setAlignment(QtCore.Qt.AlignCenter)
    logo_mark_native.setFixedSize(32, 32)
    hl.addWidget(logo_mark_native)
    logo = f.create_label()
    logo.set_text("UniUI Admin")
    logo.add_class("uniui-shell-product")
    logo_native = logo.get_native()
    hl.addWidget(logo_native)

    beta_badge = f.create_badge(); beta_badge.set_text("Beta"); beta_badge.set_status("warn")
    hl.addWidget(beta_badge.get_native())

    sep = f.create_separator("vertical")
    sep.add_class("uniui-shell-separator")
    hl.addWidget(sep.get_native())

    back = f.create_button(); forward = f.create_button()
    for btn, icon_name, tip in (
        (back, "arrow_back", "Go back"),
        (forward, "arrow_forward", "Go forward"),
    ):
        btn.set_text("")
        _set_icon_class(btn, icon_name)
        btn.add_class("uniui-shell-icon-button")
        btn_native = btn.get_native()
        btn_native.setToolTip(tip)
        btn_native.setCursor(QtCore.Qt.PointingHandCursor)
    back.connect(router.back)
    forward.connect(router.forward)
    back_native, fwd_native = back.get_native(), forward.get_native()
    hl.addWidget(back_native)
    hl.addWidget(fwd_native)

    # Breadcrumb in header
    breadcrumb = f.create_breadcrumb()
    sync_breadcrumb(breadcrumb, router, trail_fn=lambda ctx: (
        [{"label": "Dashboard"}]
        if ctx.name == "dashboard" else
        [{"label": "Dashboard", "path": "/dashboard"},
         {"label": ctx.name.replace("-", " ").title()}]
    ))
    breadcrumb.on_click(router.push)
    hl.addWidget(breadcrumb.get_native(), stretch=1)

    global_search = f.create_line_edit()
    global_search.add_class("uniui-shell-header-search")
    global_search_native = global_search.get_native()
    global_search_native.setPlaceholderText("Search…")
    global_search_native.setMaximumWidth(180)
    search_action = global_search_native.addAction(
        _header_icon("search", get_admin_palette()["text_muted"]),
        QtWidgets.QLineEdit.LeadingPosition,
    )
    hl.addWidget(global_search_native)

    theme_btn = f.create_button()
    theme_btn.set_text("")
    _set_icon_class(theme_btn, "dark_mode")
    theme_btn.add_class("uniui-shell-icon-button")
    theme_btn_native = theme_btn.get_native()
    theme_btn_native.setToolTip("Toggle dark mode")
    theme_btn_native.setCursor(QtCore.Qt.PointingHandCursor)
    hl.addWidget(theme_btn_native)
    header_w.set_responsive_widgets(logo_native, global_search_native)

    bell = f.create_button()
    bell.set_text("")
    _set_icon_class(bell, "notifications")
    bell.add_class("uniui-shell-icon-button")
    bell_native = bell.get_native()
    bell_native.setToolTip("Notifications")
    bell_native.setCursor(QtCore.Qt.PointingHandCursor)
    hl.addWidget(bell_native)

    avatar = f.create_label()
    avatar.set_text("AJ")
    avatar.add_class("uniui-shell-avatar")
    avatar_native = avatar.get_native()
    avatar_native.setAlignment(QtCore.Qt.AlignCenter)
    avatar_native.setFixedSize(32, 32)
    avatar_native.setToolTip("Alice Johnson · Administrator")
    hl.addWidget(avatar_native)

    # ── Sidebar + content ─────────────────────────────────────────────────────
    sidebar = f.create_sidebar()
    sidebar.add_group("Workspace")
    for key, label, icon in (
        ("dashboard", "Dashboard", "dashboard"),
        ("users", "Users", "users"),
        ("components", "Components", "components"),
    ):
        sidebar.add_item(key, label, icon)
    sidebar.add_group("Admin")
    sidebar.add_item("settings", "Settings", "settings")
    sidebar.on_select(router.push_named)

    def _sync_sidebar(ctx):
        if ctx.name and ctx.name != "__not_found__":
            sidebar.set_active(ctx.name)

    router.on_navigate(_sync_sidebar)
    content = RouterView(router)

    # ── AppShell ──────────────────────────────────────────────────────────────
    shell = f.create_app_shell()
    shell.set_header(_NativeWrap(header_w))
    shell.set_sidebar(sidebar)
    shell.set_content(content)

    footer = QtWidgets.QWidget()
    footer_layout = QtWidgets.QHBoxLayout(footer)
    footer_layout.setContentsMargins(0, 0, 0, 0)
    ready = f.create_label(); ready.set_text("●  All systems operational")
    ready.add_class("uniui-shell-status-ok")
    version = f.create_label(); version.set_text("UniUI admin preview · v0.1")
    version.add_class("uniui-shell-footer-meta")
    ready_native, version_native = ready.get_native(), version.get_native()
    for label in (ready_native, version_native):
        label.setMinimumWidth(0)
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred
        )
    ready_native.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    version_native.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    footer_layout.addWidget(ready_native, stretch=1)
    footer_layout.addWidget(version_native, stretch=1)
    shell.set_footer(_NativeWrap(footer))

    def _restyle_shell(dark: bool):
        """Repaint chrome (icons, stylesheet, toggle label) from THEME as it
        stands right now. Does not touch THEME itself -- set_admin_theme()
        would force it back to the plain light/dark palette, clobbering a
        named theme picked from the settings-page dropdown."""
        _set_icon_class(back, "arrow_back")
        _set_icon_class(forward, "arrow_forward")
        _set_icon_class(bell, "notifications")
        search_action.setIcon(_header_icon("search", get_admin_palette()["text_muted"]))
        _set_icon_class(theme_btn, "light_mode" if dark else "dark_mode")
        theme_btn_native.setToolTip("Switch to light mode" if dark else "Switch to dark mode")
        shell.get_native().setStyleSheet(base_stylesheet())

    def _apply_theme(dark: bool):
        set_admin_theme(dark)
        _restyle_shell(dark)
        _ADMIN_THEME.set("dark" if dark else "light")

    def _toggle_theme():
        # See the matching comment on the Jupyter/Web toggle() above: read
        # the real flag, not the display-name string, so a named theme
        # picked from the settings page doesn't desync the quick toggle.
        _apply_theme(not uniui.is_dark())

    _THEME_TOGGLE = _toggle_theme
    theme_btn.connect(_toggle_theme)
    _apply_theme(False)

    global _QT_RESTYLE_HOOK
    _QT_RESTYLE_HOOK = _restyle_shell

    router.push("/dashboard")

    show_ui(shell, title="UniUI Admin Demo", width=1280, height=780,
            stylesheet=base_stylesheet())


if __name__ == "__main__":
    main()
