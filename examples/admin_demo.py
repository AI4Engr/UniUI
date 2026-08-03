"""
Admin Dashboard Demo — UniUI M3 admin skeleton showcase.

Run:
    python examples/admin_demo.py --ui qt
    %run examples/admin_demo.py --ui jupyter   # inside a notebook cell
    python examples/admin_demo.py --ui web
"""
import sys
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uniui import (
    use, parse_args_ui, show_ui, State, Computed, bind_text, TaskRunner,
    LayoutSpec, LayoutItem,
)
import uniui


_ADMIN_THEME = State("Light")
_THEME_TOGGLE = None


def _toggle_admin_theme():
    if _THEME_TOGGLE is not None:
        _THEME_TOGGLE()

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
# Small Qt composition helpers used by this desktop showcase
# ---------------------------------------------------------------------------

class _NativeWrap:
    """Adapt a native QWidget to the tiny get_native() protocol UniUI expects."""

    def __init__(self, widget):
        self._widget = widget

    def get_native(self):
        return self._widget


def _header_icon(name, color):
    """Render a toolbar icon from the cross-backend Admin SVG source."""
    from uniui.qt_icons import admin_icon

    aliases = {"back": "arrow_back", "forward": "arrow_forward"}
    return admin_icon(aliases.get(name, name), color, size=20)


def _page_frame(title, subtitle, action_text=""):
    """Return (UniUI wrapper, body layout, optional primary action button)."""
    from PySide2 import QtWidgets, QtCore

    page = QtWidgets.QWidget()
    page.setProperty("adminPage", "1")
    page.setAccessibleName(title)
    page.setMinimumWidth(0)
    page.setSizePolicy(
        QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding
    )
    layout = QtWidgets.QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(18)

    heading = QtWidgets.QWidget()
    heading.setProperty("pageHeading", "1")
    heading_layout = QtWidgets.QHBoxLayout(heading)
    heading_layout.setContentsMargins(0, 0, 0, 0)
    heading_layout.setSpacing(16)

    copy = QtWidgets.QWidget()
    copy_layout = QtWidgets.QVBoxLayout(copy)
    copy_layout.setContentsMargins(0, 0, 0, 0)
    copy_layout.setSpacing(4)
    # The breadcrumb in the header bar already names the page; the H1 here
    # would just repeat it, so only the descriptive subtitle is shown.
    subtitle_label = QtWidgets.QLabel(subtitle)
    subtitle_label.setProperty("pageSubtitle", "1")
    subtitle_label.setWordWrap(True)
    subtitle_label.setMinimumWidth(0)
    subtitle_label.setSizePolicy(
        QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred
    )
    copy_layout.addWidget(subtitle_label)
    heading_layout.addWidget(copy, stretch=1)

    action = None
    if action_text:
        action = QtWidgets.QPushButton(action_text)
        action.setProperty("buttonRole", "primary")
        action.setCursor(QtCore.Qt.PointingHandCursor)
        heading_layout.addWidget(action, alignment=QtCore.Qt.AlignVCenter)

    layout.addWidget(heading)
    return _NativeWrap(page), layout, action


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def dashboard_page(ctx):
    f = uniui._get_factory()
    from PySide2 import QtWidgets, QtCore

    root, layout, refresh_btn = _page_frame(
        "Dashboard",
        "Monitor the signals that need your attention today.",
        "Refresh data",
    )

    # Stat cards
    sc_users   = f.create_stat_card()
    sc_orders  = f.create_stat_card()
    sc_revenue = f.create_stat_card()
    sc_errors  = f.create_stat_card()

    sc_users.set_label("Active Users");  sc_users.set_value("…");   sc_users.set_trend(0); sc_users.set_status("ok")
    sc_orders.set_label("Orders");       sc_orders.set_value("…");  sc_orders.set_trend(0); sc_orders.set_status("ok")
    sc_revenue.set_label("Revenue");     sc_revenue.set_value("…"); sc_revenue.set_trend(0); sc_revenue.set_status("ok")
    sc_errors.set_label("Open Errors");  sc_errors.set_value("…");  sc_errors.set_trend(0); sc_errors.set_status("warn")

    class _ResponsiveStats(QtWidgets.QWidget):
        def __init__(self, cards):
            super().__init__()
            self._cards = cards
            self._columns = 0
            self._grid = QtWidgets.QGridLayout(self)
            self._grid.setContentsMargins(0, 0, 0, 0)
            self._grid.setHorizontalSpacing(14)
            self._grid.setVerticalSpacing(14)
            self._reflow(4)

        def minimumSizeHint(self):
            # Report the compact one-column minimum so the parent window can
            # shrink far enough for resizeEvent() to trigger a reflow.
            return QtCore.QSize(190, 136)

        def resizeEvent(self, event):
            super().resizeEvent(event)
            width = event.size().width()
            columns = 1 if width < 440 else 2 if width < 720 else 4
            self._reflow(columns)

        def _reflow(self, columns):
            if columns == self._columns:
                return
            self._columns = columns
            for card in self._cards:
                self._grid.removeWidget(card)
            for index, card in enumerate(self._cards):
                self._grid.addWidget(card, index // columns, index % columns)
            for column in range(4):
                self._grid.setColumnStretch(column, 0)
            for column in range(columns):
                self._grid.setColumnStretch(column, 1)
            rows = (len(self._cards) + columns - 1) // columns
            self.setFixedHeight(rows * 136 + (rows - 1) * 14)

    stat_row = _ResponsiveStats([
        sc_users.get_native(), sc_orders.get_native(),
        sc_revenue.get_native(), sc_errors.get_native(),
    ])

    gauge = f.create_gauge()
    gauge.set_label("Service health")
    gauge.set_range(0, 100)
    gauge.set_unit("%")
    gauge.set_status("ok")
    gauge.set_value(82)
    chart = f.create_chart()
    chart.set_type("area")
    chart.set_title("Live activity")
    chart.set_max_points(24)
    chart.set_data(
        ["-4", "-3", "-2", "-1", "now"],
        [{"name": "Requests", "data": [42, 58, 51, 67, 62]}],
    )
    gauge_card = f.create_card()
    gauge_card.set_title("Health")
    gauge_card.set_subtitle("Animated radial progress")
    gauge_card.set_content(gauge)
    chart_card = f.create_card()
    chart_card.set_title("Realtime")
    chart_card.set_subtitle("append_data() keeps the latest 24 points")
    chart_card.set_content(chart)

    metrics = f.create_metric_list()
    metrics.set_items(_DETAIL_METRICS)
    metrics_card = f.create_card()
    metrics_card.set_title("Process")
    metrics_card.set_subtitle("Runtime signals at a glance")
    metrics_card.set_content(metrics)

    visual_row = QtWidgets.QWidget()
    visual_layout = QtWidgets.QHBoxLayout(visual_row)
    visual_layout.setContentsMargins(0, 0, 0, 0)
    visual_layout.setSpacing(14)
    visual_layout.addWidget(gauge_card.get_native(), stretch=1)
    visual_layout.addWidget(chart_card.get_native(), stretch=2)
    visual_layout.addWidget(metrics_card.get_native(), stretch=1)
    visual_row.setFixedHeight(250)

    runner = TaskRunner()

    def _fetch(_cancelled: threading.Event):
        time.sleep(0.5)
        active = sum(1 for u in _USERS if u["status"] == "Active")
        revenue = sum(
            float(o["amount"].replace("$", "").replace(",", ""))
            for o in _ORDERS if o["status"] != "Cancelled"
        )
        return {"users": active, "orders": len(_ORDERS), "revenue": revenue, "errors": 2}

    def _on_done(data):
        sc_users.set_value(str(data["users"]));      sc_users.set_trend(5.2)
        sc_orders.set_value(str(data["orders"]));    sc_orders.set_trend(-1.4)
        sc_revenue.set_value(f"${data['revenue']:,.0f}"); sc_revenue.set_trend(12.0)
        sc_errors.set_value(str(data["errors"]));    sc_errors.set_status("error"); sc_errors.set_trend(0)
        health = max(0, 100 - data["errors"] * 7)
        gauge.set_value(health)
        gauge.set_status("ok" if health >= 80 else "warn")
        chart.append_data(time.strftime("%H:%M:%S"), [data["users"] * 14 + data["orders"]])
        refresh_btn.setEnabled(True)
        refresh_btn.setText("Refresh data")

    def _refresh():
        refresh_btn.setEnabled(False)
        refresh_btn.setText("Refreshing…")
        runner.run(_fetch, on_done=_on_done, on_error=lambda _exc: _on_done({
            "users": "—", "orders": "—", "revenue": 0, "errors": "—"
        }))

    refresh_btn.clicked.connect(_refresh)
    _refresh()

    # Orders table
    tbl = f.create_table()
    tbl.set_columns([
        {"key": "id",       "label": "Order",    "width": 80},
        {"key": "customer", "label": "Customer", "width": 180},
        {"key": "amount",   "label": "Amount",   "width": 100},
        {"key": "status",   "label": "Status",   "width": 120},
    ])
    tbl.set_rows(_ORDERS)

    selected = State("Click a row to inspect")
    status_lbl = f.create_label()
    bind_text(status_lbl, selected)
    status_lbl.get_native().setProperty("tableHint", "1")
    tbl.on_row_click(lambda row: selected.set(
        f"  {row['id']}  ·  {row['customer']}  ·  {row['status']}"
    ))

    card = f.create_card()
    card.set_title("Recent Orders")
    card.set_subtitle("Click a row to inspect it")
    inner = f.create_vbox()
    inner.add_item(tbl)
    inner.add_item(status_lbl)
    card.set_content(inner)

    layout.addWidget(stat_row)
    layout.addWidget(visual_row)
    layout.addWidget(card.get_native(), stretch=1)
    return root


def users_page(ctx):
    f = uniui._get_factory()
    from PySide2 import QtWidgets

    root, layout, add_btn = _page_frame(
        "Users",
        "Manage access, roles, and account status.",
        "Add user",
    )
    add_btn.clicked.connect(lambda: None)

    search = State("")
    search_input = f.create_line_edit()
    search_input.set_text("")
    search_input.on_change(search.set)
    search_input.get_native().setPlaceholderText("Search by name or email…")
    search_input.get_native().setClearButtonEnabled(True)
    search_input.get_native().setMaximumWidth(420)

    tbl = f.create_table()
    tbl.set_columns([
        {"key": "id",     "label": "ID",     "width": 50},
        {"key": "name",   "label": "Name",   "width": 180},
        {"key": "email",  "label": "Email"},
        {"key": "role",   "label": "Role",   "width": 90},
        {"key": "status", "label": "Status", "width": 90},
    ])
    tbl.set_rows(_USERS)

    search.subscribe(lambda q: tbl.set_rows([
        u for u in _USERS
        if not q.strip() or q.lower() in u["name"].lower() or q.lower() in u["email"].lower()
    ]))

    card = f.create_card()
    card.set_title("All Users")
    card.set_subtitle("Type to filter by name or email")
    content = QtWidgets.QWidget()
    content_layout = QtWidgets.QVBoxLayout(content)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(14)
    content_layout.addWidget(search_input.get_native())
    content_layout.addWidget(tbl.get_native(), stretch=1)
    card.set_content(_NativeWrap(content))
    layout.addWidget(card.get_native(), stretch=1)
    return root


def settings_page(_ctx):
    f = uniui._get_factory()
    root, layout, open_drawer = _page_frame(
        "Settings",
        "Choose how the workspace looks and behaves.",
        "Open drawer",
    )

    info = f.create_label()
    bind_text(info, Computed(
        lambda: f"Current theme: {_ADMIN_THEME.value}", _ADMIN_THEME
    ))
    drawer_theme = f.create_button()
    bind_text(drawer_theme, Computed(
        lambda: (
            "Switch to Light" if _ADMIN_THEME.value == "Dark" else "Switch to Dark"
        ),
        _ADMIN_THEME,
    ))
    drawer_theme.connect(_toggle_admin_theme)

    drawer = f.create_drawer()
    drawer.set_title("Workspace settings")
    drawer_content = f.create_vbox()
    drawer_hint = f.create_label()
    drawer_hint.set_text("Changes apply immediately without rebuilding the current route.")
    drawer_content.add_item(drawer_hint)
    drawer_content.add_item(drawer_theme)
    drawer.set_content(drawer_content)
    open_drawer.clicked.connect(drawer.open)

    card = f.create_card()
    card.set_title("Appearance")
    card.set_subtitle("Theme changes preserve routes, table state, and loaded data")
    inner = f.create_vbox()
    inner.add_item(info)
    open_button = f.create_button()
    open_button.set_text("Open settings drawer")
    open_button.connect(drawer.open)
    inner.add_item(open_button)
    card.set_content(inner)
    layout.addWidget(card.get_native())
    layout.addStretch()
    return root


def not_found_page(ctx):
    f = uniui._get_factory()
    lbl = f.create_label()
    lbl.set_text(f"404 — No page at: {ctx.path}")
    return lbl


# ---------------------------------------------------------------------------
# Browser composition (shared by Jupyter and the NiceGUI Web backend)
# ---------------------------------------------------------------------------

def _add_class(widget, class_name):
    """Add a semantic CSS class without exposing a backend in page code."""
    native = widget.get_native() if hasattr(widget, "get_native") else widget
    if hasattr(native, "add_class"):
        native.add_class(class_name)
    elif hasattr(native, "classes"):
        native.classes(add=class_name)
    return widget


def _set_props(widget, props):
    """Apply optional browser-native presentation props when available."""
    native = widget.get_native() if hasattr(widget, "get_native") else widget
    if hasattr(native, "props"):
        native.props(props)
    return widget


def _set_icon_class(widget, icon_name):
    """Switch a shared SVG icon class on a browser-backed control."""
    from uniui.admin_icons import ADMIN_ICON_NAMES

    native = widget.get_native() if hasattr(widget, "get_native") else widget
    for name in ADMIN_ICON_NAMES:
        class_name = f"uniui-icon-{name}"
        if hasattr(native, "remove_class"):
            native.remove_class(class_name)
        elif hasattr(native, "classes"):
            native.classes(remove=class_name)
    _add_class(widget, f"uniui-icon-{icon_name}")
    return widget


def _browser_page_frame(title, subtitle, action_text=""):
    f = uniui._get_factory()
    page = f.create_vbox()
    page.set_spec(LayoutSpec(gap=18))
    _add_class(page, "uniui-demo-page")
    page_native = page.get_native() if hasattr(page, "get_native") else page
    if hasattr(page_native, "tooltip"):
        page_native.tooltip(title)

    heading = f.create_hbox()
    heading.set_spec(LayoutSpec(gap=16))
    _add_class(heading, "uniui-demo-heading")
    copy = f.create_vbox()
    copy.set_spec(LayoutSpec(gap=4))
    # The breadcrumb in the header bar already names the page; the H1 here
    # would just repeat it, so only the descriptive subtitle is shown.
    subtitle_label = f.create_label()
    subtitle_label.set_text(subtitle)
    _add_class(subtitle_label, "uniui-demo-subtitle")
    copy.add_item(subtitle_label)
    heading.add_item_with_spec(copy, LayoutItem(copy, grow=1))

    action = None
    if action_text:
        action = f.create_button()
        action.set_text(action_text)
        _add_class(action, "uniui-demo-primary-action")
        _set_props(action, "no-caps unelevated")
        heading.add_item(action)

    page.add_item(heading)
    return page, action


def _browser_dashboard_page(_ctx):
    f = uniui._get_factory()
    page, refresh_btn = _browser_page_frame(
        "Dashboard",
        "Monitor the signals that need your attention today.",
        "Refresh data",
    )

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
    _add_class(stats, "uniui-demo-stats")
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
    metrics_card = f.create_card(); metrics_card.set_title("Process")
    metrics_card.set_subtitle("Runtime signals at a glance"); metrics_card.set_content(metrics)

    visuals = f.create_wrap(); visuals.set_spec(LayoutSpec(gap=14))
    visuals.add_item(gauge_card); visuals.add_item(chart_card); visuals.add_item(metrics_card)

    def refresh():
        refresh_btn.set_enabled(False)
        refresh_btn.set_text("Refreshing…")
        active = sum(1 for user in _USERS if user["status"] == "Active")
        revenue = sum(
            float(order["amount"].replace("$", "").replace(",", ""))
            for order in _ORDERS if order["status"] != "Cancelled"
        )
        values = (str(active), str(len(_ORDERS)), f"${revenue:,.0f}", "2")
        trends = (5.2, -1.4, 12.0, 0.0)
        for card, value, trend in zip(cards, values, trends):
            card.set_value(value)
            card.set_trend(trend)
        cards[-1].set_status("error")
        health = max(0, 100 - 2 * 7)
        gauge.set_value(health)
        chart.append_data(time.strftime("%H:%M:%S"), [active * 14 + len(_ORDERS)])
        refresh_btn.set_text("Refresh data")
        refresh_btn.set_enabled(True)

    refresh_btn.connect(refresh)
    refresh()

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
    _add_class(hint, "uniui-demo-hint")
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


def _browser_users_page(_ctx):
    f = uniui._get_factory()
    page, add_btn = _browser_page_frame(
        "Users", "Manage access, roles, and account status.", "Add user"
    )
    add_btn.connect(lambda: None)

    search_input = f.create_line_edit()
    native_input = search_input.get_native()
    if hasattr(native_input, "placeholder"):
        native_input.placeholder = "Search by name or email…"
    elif hasattr(native_input, "props"):
        native_input.props('placeholder="Search by name or email…" clearable outlined dense')
    if hasattr(native_input, "layout"):
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


def _browser_settings_page(_ctx):
    f = uniui._get_factory()
    page, open_drawer = _browser_page_frame(
        "Settings", "Choose how the workspace looks and behaves.", "Open drawer"
    )
    info = f.create_label()
    bind_text(info, Computed(lambda: f"Current theme: {_ADMIN_THEME.value}", _ADMIN_THEME))
    drawer_button = f.create_button()
    bind_text(drawer_button, Computed(
        lambda: "Switch to Light" if _ADMIN_THEME.value == "Dark" else "Switch to Dark",
        _ADMIN_THEME,
    ))
    drawer_button.connect(_toggle_admin_theme)
    drawer = f.create_drawer(); drawer.set_title("Workspace settings")
    drawer_content = f.create_vbox(); drawer_hint = f.create_label()
    drawer_hint.set_text("Changes apply immediately without rebuilding the current route.")
    drawer_content.add_item(drawer_hint); drawer_content.add_item(drawer_button)
    drawer.set_content(drawer_content)
    open_drawer.connect(drawer.open)
    content = f.create_vbox()
    content.set_spec(LayoutSpec(gap=12))
    content.add_item(info)
    open_button = f.create_button(); open_button.set_text("Open settings drawer")
    open_button.connect(drawer.open); content.add_item(open_button)
    card = f.create_card()
    card.set_title("Appearance")
    card.set_subtitle("Theme changes preserve routes, table state, and loaded data")
    card.set_content(content)
    page.add_item(card)
    page.add_item(drawer)
    return page


def _browser_not_found_page(ctx):
    label = uniui._get_factory().create_label()
    label.set_text(f"404 — No page at: {ctx.path}")
    return label


def _main_browser(framework):
    """Build the same Admin workflow for Jupyter and standalone Web."""
    global _THEME_TOGGLE

    from uniui.routing import Router, Route, RouterView, sync_breadcrumb
    if framework == "jupyter":
        from uniui import jupyter_admin as admin_backend
    else:
        from uniui import web_admin as admin_backend

    _ADMIN_THEME.set("Light")
    admin_backend.set_admin_theme(False)
    f = uniui._get_factory()
    router = Router(
        Route("/dashboard", _browser_dashboard_page, name="dashboard"),
        Route("/users", _browser_users_page, name="users"),
        Route("/settings", _browser_settings_page, name="settings"),
        not_found=_browser_not_found_page,
    )

    header = f.create_hbox()
    _add_class(header, "uniui-demo-header-content")
    header.set_spec(LayoutSpec(gap=8))
    logo = f.create_label(); logo.set_text("U"); _add_class(logo, "uniui-demo-logo-mark")
    product = f.create_label(); product.set_text("UniUI Admin"); _add_class(product, "uniui-demo-product")
    back = f.create_button()
    forward = f.create_button()
    back.set_text(""); forward.set_text("")
    _set_props(back, "flat round dense")
    _set_props(forward, "flat round dense")
    _set_icon_class(back, "arrow_back")
    _set_icon_class(forward, "arrow_forward")
    _add_class(back, "uniui-demo-icon-button")
    _add_class(forward, "uniui-demo-icon-button")
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
    _add_class(theme_button, "uniui-demo-theme-button")
    _set_props(theme_button, "flat no-caps")
    _set_icon_class(theme_button, "dark_mode")
    header.add_item(logo)
    header.add_item(product)
    header.add_item(back)
    header.add_item(forward)
    header.add_item_with_spec(breadcrumb, LayoutItem(breadcrumb, grow=1))
    header.add_item(theme_button)
    avatar = f.create_label(); avatar.set_text("AJ"); _add_class(avatar, "uniui-demo-avatar")
    header.add_item(avatar)

    sidebar = f.create_sidebar()
    for key, label, icon in (
        ("dashboard", "Dashboard", "dashboard"),
        ("users", "Users", "users"),
        ("settings", "Settings", "settings"),
    ):
        sidebar.add_item(key, label, icon)
    sidebar.on_select(router.push_named)
    router.on_navigate(lambda ctx: sidebar.set_active(ctx.name)
                       if ctx.name and ctx.name != "__not_found__" else None)

    content = RouterView(router)
    shell = f.create_app_shell()
    shell.set_header(header)
    shell.set_sidebar(sidebar)
    shell.set_content(content)
    footer = f.create_hbox()
    ready = f.create_label(); ready.set_text("●  All systems operational"); _add_class(ready, "uniui-web-status-ok")
    version = f.create_label(); version.set_text("UniUI admin preview · v0.1"); _add_class(version, "uniui-web-footer-meta")
    footer.add_item(ready); footer.add_stretch(); footer.add_item(version)
    shell.set_footer(footer)

    def apply_theme(dark):
        admin_backend.set_admin_theme(dark)
        _ADMIN_THEME.set("Dark" if dark else "Light")
        theme_button.set_text("Light mode" if dark else "Dark mode")
        _set_icon_class(theme_button, "light_mode" if dark else "dark_mode")

    def toggle():
        apply_theme(_ADMIN_THEME.value != "Dark")

    _THEME_TOGGLE = toggle
    theme_button.connect(toggle)
    apply_theme(False)
    router.push("/dashboard")
    show_ui(shell, title="UniUI Admin Demo", width=1180, height=780)


# ---------------------------------------------------------------------------
# Admin stylesheet
# ---------------------------------------------------------------------------

def _admin_stylesheet():
    from uniui.qt_admin import get_admin_palette

    p = get_admin_palette()
    return """
QWidget {
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
    font-size: 13px;
    color: %(text)s;
}
QWidget[adminPage="1"], QWidget[pageHeading="1"] { background: transparent; }
QLabel { background: transparent; color: %(text)s; }
QLabel[pageSubtitle="1"] {
    color: %(text)s;
    font-size: 18px;
    font-weight: 650;
}
QLabel[tableHint="1"] {
    color: %(text_muted)s;
    background: %(surface_subtle)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
    padding: 8px 10px;
}
QWidget[topBar="1"] { background: %(header_bg)s; }
QLabel[logoMark="1"] {
    background: %(accent)s; color: white; border-radius: 8px;
    font-size: 15px; font-weight: 800;
}
QLabel[productName="1"] { color: %(text)s; font-size: 15px; font-weight: 700; }
QFrame[headerSeparator="1"] { color: %(header_border)s; background: transparent; }
QLabel[avatar="1"] {
    background: %(avatar_bg)s; color: %(avatar_fg)s;
    border-radius: 16px; font-size: 11px; font-weight: 700;
}
QLabel[systemStatus="1"] { color: %(ok)s; font-size: 11px; }
QLabel[footerMeta="1"] { color: %(text_muted)s; font-size: 11px; }
QToolButton[headerButton="1"] {
    background: transparent; color: %(text_muted)s; border: none;
    border-radius: 7px; padding: 5px 8px; min-width: 18px; min-height: 18px;
}
QToolButton[headerButton="1"]:hover { background: %(surface_subtle)s; color: %(text)s; }

QLineEdit {
    background: %(input_bg)s;
    border: 1px solid %(border_strong)s;
    border-radius: 9px;
    padding: 8px 11px;
    color: %(text)s;
    font-size: 13px;
    min-height: 20px;
}
QLineEdit:focus { border: 2px solid %(accent)s; padding: 7px 10px; }
QLineEdit:hover { border-color: %(text_muted)s; }
QLineEdit:disabled {
    color: %(text_muted)s;
    background: %(surface_subtle)s;
    border-color: %(border)s;
}

QPushButton {
    background: %(accent)s;
    color: #ffffff;
    border: 1px solid %(accent)s;
    border-radius: 9px;
    padding: 7px 14px;
    font-size: 13px;
    font-weight: 600;
    min-height: 20px;
    qproperty-iconSize: 18px 18px;
}
QPushButton:hover { background: %(accent_hover)s; border-color: %(accent_hover)s; }
QPushButton:pressed { background: %(accent_press)s; }
QPushButton:focus { border: 2px solid %(accent_hover)s; padding: 6px 13px; }
QPushButton:disabled {
    color: %(text_muted)s;
    background: %(disabled)s;
    border-color: %(disabled)s;
}
QPushButton[buttonRole="secondary"] {
    background: %(surface)s;
    color: %(text)s;
    border: 1px solid %(border_strong)s;
}
QPushButton[buttonRole="secondary"]:hover { background: %(surface_subtle)s; }
QPushButton:flat {
    background: transparent;
    color: %(text_muted)s;
    border: none;
    min-height: 0;
    padding: 5px 7px;
}
QPushButton:flat:hover { color: %(text)s; background: %(surface_subtle)s; }

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: %(scrollbar)s;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
""" % p


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global _THEME_TOGGLE

    framework = parse_args_ui()
    use(framework if framework != "auto" else "qt")

    if framework in {"jupyter", "web"}:
        _main_browser(framework)
        return

    from uniui.routing import Router, Route, RouterView, sync_breadcrumb
    from uniui.qt_admin import get_admin_palette, set_admin_theme
    from PySide2 import QtWidgets, QtCore

    _ADMIN_THEME.set("Light")
    set_admin_theme(False)

    router = Router(
        Route("/dashboard", dashboard_page, name="dashboard"),
        Route("/users",     users_page,     name="users"),
        Route("/settings",  settings_page,  name="settings"),
        not_found=not_found_page,
    )

    f = uniui._get_factory()

    # ── Product header ────────────────────────────────────────────────────────
    class _ResponsiveTopBar(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self._responsive_widgets = None

        def set_responsive_widgets(self, product, search, theme):
            self._responsive_widgets = (product, search, theme)

        def resizeEvent(self, event):
            super().resizeEvent(event)
            if self._responsive_widgets is None:
                return
            product, search, theme = self._responsive_widgets
            width = event.size().width()
            product.setVisible(width >= 650)
            theme.setVisible(width >= 720)
            search.setVisible(width >= 850)

    header_w = _ResponsiveTopBar()
    header_w.setProperty("topBar", "1")
    header_w.setMinimumWidth(0)
    header_w.setSizePolicy(
        QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred
    )
    hl = QtWidgets.QHBoxLayout(header_w)
    hl.setContentsMargins(4, 0, 4, 0)
    hl.setSpacing(7)

    logo_mark = QtWidgets.QLabel("U")
    logo_mark.setProperty("logoMark", "1")
    logo_mark.setAlignment(QtCore.Qt.AlignCenter)
    logo_mark.setFixedSize(32, 32)
    hl.addWidget(logo_mark)
    logo = QtWidgets.QLabel("UniUI Admin")
    logo.setProperty("productName", "1")
    hl.addWidget(logo)

    sep = QtWidgets.QFrame()
    sep.setProperty("headerSeparator", "1")
    sep.setFrameShape(QtWidgets.QFrame.VLine)
    hl.addWidget(sep)

    back_btn = QtWidgets.QToolButton()
    fwd_btn = QtWidgets.QToolButton()
    for button, tip in ((back_btn, "Go back"), (fwd_btn, "Go forward")):
        button.setProperty("headerButton", "1")
        button.setToolTip(tip)
        button.setCursor(QtCore.Qt.PointingHandCursor)
    back_btn.clicked.connect(router.back)
    fwd_btn.clicked.connect(router.forward)
    hl.addWidget(back_btn)
    hl.addWidget(fwd_btn)

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

    global_search = QtWidgets.QLineEdit()
    global_search.setPlaceholderText("Search…")
    global_search.setMaximumWidth(210)
    search_action = global_search.addAction(
        _header_icon("search", get_admin_palette()["text_muted"]),
        QtWidgets.QLineEdit.LeadingPosition,
    )
    hl.addWidget(global_search)

    theme_btn = QtWidgets.QPushButton("Dark mode")
    theme_btn.setProperty("buttonRole", "secondary")
    theme_btn.setCursor(QtCore.Qt.PointingHandCursor)
    hl.addWidget(theme_btn)
    header_w.set_responsive_widgets(logo, global_search, theme_btn)

    bell = QtWidgets.QToolButton()
    bell.setProperty("headerButton", "1")
    bell.setToolTip("Notifications")
    bell.setCursor(QtCore.Qt.PointingHandCursor)
    hl.addWidget(bell)

    avatar = QtWidgets.QLabel("AJ")
    avatar.setProperty("avatar", "1")
    avatar.setAlignment(QtCore.Qt.AlignCenter)
    avatar.setFixedSize(32, 32)
    avatar.setToolTip("Alice Johnson · Administrator")
    hl.addWidget(avatar)

    # ── Sidebar + content ─────────────────────────────────────────────────────
    sidebar = f.create_sidebar()
    for key, label, icon in (
        ("dashboard", "Dashboard", "dashboard"),
        ("users", "Users", "users"),
        ("settings", "Settings", "settings"),
    ):
        sidebar.add_item(key, label, icon)
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
    ready = QtWidgets.QLabel("●  All systems operational")
    ready.setProperty("systemStatus", "1")
    version = QtWidgets.QLabel("UniUI admin preview · v0.1")
    version.setProperty("footerMeta", "1")
    for label in (ready, version):
        label.setMinimumWidth(0)
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred
        )
    ready.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    version.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    footer_layout.addWidget(ready, stretch=1)
    footer_layout.addWidget(version, stretch=1)
    shell.set_footer(_NativeWrap(footer))

    def _apply_theme(dark: bool):
        set_admin_theme(dark)
        palette = get_admin_palette()
        icon_color = palette["text_muted"]
        back_btn.setIcon(_header_icon("back", icon_color))
        fwd_btn.setIcon(_header_icon("forward", icon_color))
        bell.setIcon(_header_icon("notifications", icon_color))
        search_action.setIcon(_header_icon("search", icon_color))
        theme_btn.setIcon(_header_icon(
            "light_mode" if dark else "dark_mode", icon_color
        ))
        shell.get_native().setStyleSheet(_admin_stylesheet())
        name = "Dark" if dark else "Light"
        _ADMIN_THEME.set(name)
        theme_btn.setText("Light mode" if dark else "Dark mode")

    def _toggle_theme():
        _apply_theme(_ADMIN_THEME.value != "Dark")

    _THEME_TOGGLE = _toggle_theme
    theme_btn.clicked.connect(_toggle_theme)
    _apply_theme(False)

    router.push("/dashboard")

    show_ui(shell, title="UniUI Admin Demo", width=1180, height=780,
            stylesheet=_admin_stylesheet())


if __name__ == "__main__":
    main()
