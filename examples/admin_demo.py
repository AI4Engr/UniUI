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
    disk_usage = f.create_progress_bar(); disk_usage.set_value(62); disk_usage.set_status("warn")
    metrics_body = f.create_vbox()
    metrics_body.add_item(metrics)
    metrics_body.add_item(disk_usage)
    metrics_card = f.create_card()
    metrics_card.set_title("Process")
    metrics_card.set_subtitle("Runtime signals at a glance")
    metrics_card.set_content(metrics_body)

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
        lambda: f"Current theme: {_ADMIN_THEME.value.title()}", _ADMIN_THEME
    ))
    drawer_theme = f.create_button()
    bind_text(drawer_theme, Computed(
        # _ADMIN_THEME is the reactive trigger; the label itself reads the
        # real is_dark() flag so it stays correct after the picker below
        # switches to a named theme, not just after the quick toggle.
        lambda: "Switch to Light" if uniui.is_dark() else "Switch to Dark",
        _ADMIN_THEME,
    ))
    drawer_theme.connect(_toggle_admin_theme)

    # Theme picker: every registered theme, not just the light/dark pair the
    # header's quick-toggle button flips between.
    theme_picker = f.create_combo_box()
    for name in uniui.list_themes():
        theme_picker.add_item(name)
    theme_picker.set_selection(_ADMIN_THEME.value)
    theme_picker.on_change(lambda: _apply_named_theme(theme_picker.get_text()))

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
    inner.add_item(theme_picker)
    open_button = f.create_button()
    open_button.set_text("Open settings drawer")
    open_button.connect(drawer.open)
    inner.add_item(open_button)
    card.set_content(inner)
    layout.addWidget(card.get_native())
    layout.addStretch()
    return root


def _qt_labeled_field(title, control_native):
    from PySide2 import QtWidgets

    field = QtWidgets.QWidget()
    field_layout = QtWidgets.QVBoxLayout(field)
    field_layout.setContentsMargins(0, 0, 0, 0)
    field_layout.setSpacing(6)
    label = QtWidgets.QLabel(title)
    label.setProperty("fieldLabel", "1")
    field_layout.addWidget(label)
    field_layout.addWidget(control_native)
    return field


def components_page(ctx):
    f = uniui._get_factory()
    from PySide2 import QtWidgets

    root, layout, _ = _page_frame(
        "Components",
        "A quick reference for the form and navigation controls available in every backend.",
    )

    role_dropdown = f.create_dropdown()
    for role in ("Admin", "Editor", "Viewer"):
        role_dropdown.add_item(role)
    role_dropdown.set_selection("Editor")

    theme_combo = f.create_combo_box()
    for option in ("System", "Light", "Dark", "High contrast"):
        theme_combo.add_item(option)
    theme_combo.set_selection("System")

    status_dropdown = f.create_dropdown()
    for status in ("Active", "Inactive", "Pending"):
        status_dropdown.add_item(status)
    status_dropdown.set_selection("Active")

    hint = QtWidgets.QLabel("Editor · Active")
    hint.setProperty("tableHint", "1")

    def _update_hint():
        hint.setText(f"{role_dropdown.get_text()}  ·  {status_dropdown.get_text()}")

    role_dropdown.on_change(_update_hint)
    status_dropdown.on_change(_update_hint)

    fields_row = QtWidgets.QWidget()
    fields_layout = QtWidgets.QHBoxLayout(fields_row)
    fields_layout.setContentsMargins(0, 0, 0, 0)
    fields_layout.setSpacing(16)
    fields_layout.addWidget(_qt_labeled_field("Role (dropdown)", role_dropdown.get_native()))
    fields_layout.addWidget(_qt_labeled_field("Theme (editable combo box)", theme_combo.get_native()))
    fields_layout.addWidget(_qt_labeled_field("Status (dropdown)", status_dropdown.get_native()))
    fields_layout.addStretch()

    inputs_content = QtWidgets.QWidget()
    inputs_layout = QtWidgets.QVBoxLayout(inputs_content)
    inputs_layout.setContentsMargins(0, 0, 0, 0)
    inputs_layout.setSpacing(14)
    inputs_layout.addWidget(fields_row)
    inputs_layout.addWidget(hint)

    inputs_card = f.create_card()
    inputs_card.set_title("Selection controls")
    inputs_card.set_subtitle("Dropdown and combo box, wired to a shared change handler")
    inputs_card.set_content(_NativeWrap(inputs_content))

    overview_tab = QtWidgets.QLabel(
        "Tabs mount every pane up front and only toggle visibility, so state "
        "in inactive tabs is preserved when you switch back."
    )
    overview_tab.setWordWrap(True)

    activity_tab = QtWidgets.QWidget()
    activity_layout = QtWidgets.QVBoxLayout(activity_tab)
    activity_layout.setContentsMargins(12, 12, 12, 12)
    activity_layout.setSpacing(8)
    for entry in (
        "Alice Johnson updated the Dashboard layout",
        "Bob Smith invited a new Editor",
        "Nightly export completed without errors",
    ):
        activity_layout.addWidget(QtWidgets.QLabel(f"•  {entry}"))
    activity_layout.addStretch()

    settings_tab = QtWidgets.QWidget()
    settings_tab_layout = QtWidgets.QVBoxLayout(settings_tab)
    settings_tab_layout.setContentsMargins(12, 12, 12, 12)
    settings_tab_layout.setSpacing(8)
    notify_toggle = QtWidgets.QPushButton("Notifications: On")
    notify_toggle.setProperty("buttonRole", "secondary")
    settings_tab_layout.addWidget(notify_toggle)
    compact_toggle = QtWidgets.QPushButton("Compact density: Off")
    compact_toggle.setProperty("buttonRole", "secondary")
    settings_tab_layout.addWidget(compact_toggle)
    settings_tab_layout.addStretch()

    tabs = f.create_tab_widget()
    tabs.add_tab(_NativeWrap(overview_tab), "Overview")
    tabs.add_tab(_NativeWrap(activity_tab), "Activity")
    tabs.add_tab(_NativeWrap(settings_tab), "Settings")

    tabs_card = f.create_card()
    tabs_card.set_title("Tabs")
    tabs_card.set_subtitle("Three panes sharing one tab strip")
    tabs_card.set_content(tabs)

    layout.addWidget(inputs_card.get_native())
    layout.addWidget(tabs_card.get_native(), stretch=1)
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
        # ipywidgets Buttons carry the generic theme's accent colour as an
        # inline style, which outranks any stylesheet. Clear it so the admin
        # palette can style this button through its semantic class.
        style = getattr(native, "style", None)
        if style is not None and hasattr(style, "button_color"):
            style.button_color = None
            style.text_color = None
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
    from uniui.icons import ADMIN_ICON_NAMES

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
    if callable(getattr(page_native, "tooltip", None)):
        page_native.tooltip(title)  # NiceGUI element
    elif hasattr(page_native, "tooltip"):
        page_native.tooltip = title  # ipywidgets trait

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
    disk_usage = f.create_progress_bar(); disk_usage.set_value(62); disk_usage.set_status("warn")
    metrics_body = f.create_vbox(); metrics_body.add_item(metrics); metrics_body.add_item(disk_usage)
    metrics_card = f.create_card(); metrics_card.set_title("Process")
    metrics_card.set_subtitle("Runtime signals at a glance"); metrics_card.set_content(metrics_body)

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
    _add_class(field, "uniui-demo-field")
    label = f.create_label()
    label.set_text(label_text)
    _add_class(label, "uniui-demo-field-label")
    field.add_item(label)
    field.add_item(control)
    return field


def _browser_components_page(_ctx):
    f = uniui._get_factory()
    page, _ = _browser_page_frame(
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
    _add_class(selection_hint, "uniui-demo-hint")

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

    settings_tab = f.create_vbox()
    settings_tab.set_spec(LayoutSpec(gap=8))
    notify_toggle = f.create_button()
    notify_toggle.set_text("Notifications: On")
    settings_tab.add_item(notify_toggle)
    compact_toggle = f.create_button()
    compact_toggle.set_text("Compact density: Off")
    settings_tab.add_item(compact_toggle)

    tabs = f.create_tab_widget()
    tabs.add_tab(overview_tab, "Overview")
    tabs.add_tab(activity_tab, "Activity")
    tabs.add_tab(settings_tab, "Settings")

    tabs_card = f.create_card()
    tabs_card.set_title("Tabs")
    tabs_card.set_subtitle("Three panes sharing one tab strip")
    tabs_card.set_content(tabs)

    page.add_item(inputs_card)
    page.add_item_with_spec(tabs_card, LayoutItem(tabs_card, grow=1))
    return page


def _browser_not_found_page(ctx):
    label = uniui._get_factory().create_label()
    label.set_text(f"404 — No page at: {ctx.path}")
    return label


def create_admin_ui(framework="auto", debug=False):
    """Build the Admin dashboard shell and return it (Jupyter and Web only).

    Mirrors the create_*_ui(framework) -> show_ui(layout, ...) pattern used
    by the other examples (create_bmi_ui, create_sysmon_ui, ...).
    """
    global _THEME_TOGGLE

    use(framework)

    from uniui.routing import Router, Route, RouterView, sync_breadcrumb
    if framework == "jupyter":
        from uniui import jupyter_components as admin_backend
    else:
        from uniui import web_components as admin_backend

    _ADMIN_THEME.set("light")
    admin_backend.set_admin_theme(False)
    f = uniui._get_factory()
    router = Router(
        Route("/dashboard", _browser_dashboard_page, name="dashboard"),
        Route("/users", _browser_users_page, name="users"),
        Route("/components", _browser_components_page, name="components"),
        Route("/settings", _browser_settings_page, name="settings"),
        not_found=_browser_not_found_page,
    )

    header = f.create_hbox()
    _add_class(header, "uniui-demo-header-content")
    header.set_spec(LayoutSpec(gap=8))
    logo = f.create_label(); logo.set_text("U"); _add_class(logo, "uniui-demo-logo-mark")
    product = f.create_label(); product.set_text("UniUI Admin"); _add_class(product, "uniui-demo-product")
    beta_badge = f.create_badge(); beta_badge.set_text("Beta"); beta_badge.set_status("warn")
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
    header.add_item(beta_badge)
    header.add_item(back)
    header.add_item(forward)
    header.add_item_with_spec(breadcrumb, LayoutItem(breadcrumb, grow=1))
    header.add_item(theme_button)
    avatar = f.create_label(); avatar.set_text("AJ"); _add_class(avatar, "uniui-demo-avatar")
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
    ready = f.create_label(); ready.set_text("●  All systems operational"); _add_class(ready, "uniui-web-status-ok")
    version = f.create_label(); version.set_text("UniUI admin preview · v0.1"); _add_class(version, "uniui-web-footer-meta")
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

def _admin_stylesheet():
    """Demo-only chrome, layered on top of the library's base widget style.

    Ordinary controls (QPushButton, QLineEdit, QComboBox, QTabWidget, ...) are
    styled by uniui.qt_style so any Qt app gets them, not just this demo.
    Only the demo's own property-tagged widgets are defined here.
    """
    from uniui.qt_components import get_admin_palette
    from uniui.qt_style import base_stylesheet

    p = get_admin_palette()
    return base_stylesheet() + """
QWidget[adminPage="1"], QWidget[pageHeading="1"] { background: transparent; }
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
QLabel[fieldLabel="1"] {
    color: %(text_muted)s;
    font-size: 12px;
    font-weight: 650;
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
    from uniui.qt_components import get_admin_palette, set_admin_theme
    from PySide2 import QtWidgets, QtCore

    _ADMIN_THEME.set("light")
    set_admin_theme(False)

    router = Router(
        Route("/dashboard",   dashboard_page,   name="dashboard"),
        Route("/users",       users_page,       name="users"),
        Route("/components",  components_page,  name="components"),
        Route("/settings",    settings_page,    name="settings"),
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

    beta_badge = f.create_badge(); beta_badge.set_text("Beta"); beta_badge.set_status("warn")
    hl.addWidget(beta_badge.get_native())

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

    def _restyle_shell(dark: bool):
        """Repaint chrome (icons, stylesheet, toggle label) from THEME as it
        stands right now. Does not touch THEME itself -- set_admin_theme()
        would force it back to the plain light/dark palette, clobbering a
        named theme picked from the settings-page dropdown."""
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
        theme_btn.setText("Light mode" if dark else "Dark mode")

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
    theme_btn.clicked.connect(_toggle_theme)
    _apply_theme(False)

    global _QT_RESTYLE_HOOK
    _QT_RESTYLE_HOOK = _restyle_shell

    router.push("/dashboard")

    show_ui(shell, title="UniUI Admin Demo", width=1280, height=780,
            stylesheet=_admin_stylesheet())


if __name__ == "__main__":
    main()
