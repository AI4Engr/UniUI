"""
UniUI Component Gallery — a live, running showcase of shipped components,
organized by category. Every example below is a real widget wired to real
behavior (a click updates something visible), not a static screenshot.

This is Phase 1 of TODO.md's "P1: Components Showcase": only components that
already exist in UniUI. Components UniUI doesn't have yet (Toast, Dialog,
Checkbox, Tabs beyond TabWidget, ...) are deliberately absent rather than
faked - see TODO.md for the phased plan to add them.

Run:
    python examples/component_gallery.py --ui qt
    python examples/component_gallery.py --ui web
    %run examples/component_gallery.py --ui jupyter   # inside a notebook cell

Written entirely against the cross-backend declarative API (Card, Button,
Table, ...) rather than a Qt-specific hand-built path like admin_demo.py -
the point of this page is exactly that the same code runs on all three
backends unmodified.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uniui import (
    use, parse_args_ui, show_ui, State, bind_text,
    Router, Route, RouterView, sync_breadcrumb,
    AppShell, Card, Badge, ProgressBar, StatCard, MetricList, Table, Chart, Gauge,
    Breadcrumb, Button, Label, LineEdit, TextArea, ComboBox, Dropdown,
    TabWidget, GroupBox, VBox, HBox, Wrap, LayoutSpec,
)
import uniui

_CATEGORIES = [
    ("overview", "Overview", "dashboard"),
    ("buttons", "Buttons", "components"),
    ("inputs", "Inputs", "components"),
    ("data-display", "Data Display", "components"),
    ("navigation", "Navigation", "components"),
    ("layout", "Layout", "components"),
]


def _section(title, subtitle, *widgets):
    """A titled Card wrapping one demo - the repeating unit of every page."""
    card = Card(title=title, subtitle=subtitle)
    body = VBox(*widgets)
    body.set_spec(LayoutSpec(gap=12))
    card.set_content(body)
    return card


def _page(title, subtitle, *sections):
    header = VBox(Label(title), Label(subtitle))
    header.set_spec(LayoutSpec(gap=2))
    body = VBox(header, *sections)
    body.set_spec(LayoutSpec(gap=16, padding=24))
    return body


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

def overview_page(ctx):
    stats = Wrap()
    stats.set_spec(LayoutSpec(gap=14))
    for label, value, status in [
        ("Categories", str(len(_CATEGORIES) - 1), "ok"),
        ("Components shown", "16", "ok"),
        ("Backends", "3", "ok"),
    ]:
        sc = StatCard(label=label, value=value, status=status)
        stats.add_item(sc)

    intro = Label(
        "Every widget on this page is the real UniUI component, running "
        "live under whichever backend you launched with --ui. Pick a "
        "category from the sidebar to see it in action."
    )
    return _page(
        "Component Gallery", "A live showcase of UniUI's shipped components",
        _section("At a glance", "", stats),
        _section("About this page", "", intro),
    )


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------

def buttons_page(ctx):
    click_count = State(0)
    click_label = Label("Clicked 0 times")

    def on_click():
        click_count.set(click_count.value + 1)
        click_label.set_text(f"Clicked {click_count.value} times")

    row = HBox(
        Button("Click me", on_click=on_click),
        click_label,
    )
    row.set_spec(LayoutSpec(gap=12))

    disabled_btn = Button("Disabled")
    disabled_btn.set_enabled(False)
    states_row = HBox(Button("Enabled"), disabled_btn)
    states_row.set_spec(LayoutSpec(gap=12))

    return _page(
        "Buttons", "IButton — a click callback, text, and enabled state",
        _section(
            "Interactive", "Click actually updates the label on the right",
            row,
        ),
        _section(
            "States", "Enabled vs. disabled",
            states_row,
        ),
        _section(
            "Note", "",
            Label(
                "Visual variants (primary/secondary/outline/danger) aren't "
                "a separate UniUI API yet - they're applied via "
                "backend-specific styling hooks (see admin_demo.py's "
                "buttonRole property). One real component, many looks."
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def inputs_page(ctx):
    echo = Label("(nothing typed yet)")
    line = LineEdit(on_change=lambda: echo.set_text(f"You typed: {line.get_text()}"))
    line_row = VBox(line, echo)
    line_row.set_spec(LayoutSpec(gap=6))

    text_area = TextArea("Multi-line text goes here.")

    combo = ComboBox(items=["Small", "Medium", "Large"])
    dropdown = Dropdown(items=["Light", "Dark", "System"])
    pickers = HBox(combo, dropdown)
    pickers.set_spec(LayoutSpec(gap=12))

    disabled = LineEdit("Read-only value")
    disabled.set_enabled(False)

    return _page(
        "Inputs", "LineEdit, TextArea, ComboBox, Dropdown",
        _section("Text input", "on_change fires on every keystroke", line_row),
        _section("Text area", "", text_area),
        _section("Choice controls", "ComboBox (editable) and Dropdown (fixed list)", pickers),
        _section("Disabled state", "Same widget, set_enabled(False)", disabled),
    )


# ---------------------------------------------------------------------------
# Data Display
# ---------------------------------------------------------------------------

def data_display_page(ctx):
    badges = HBox(
        Badge("Active", status="ok"),
        Badge("Pending", status="warn"),
        Badge("Failed", status="error"),
        Badge("Draft", status="neutral"),
    )
    badges.set_spec(LayoutSpec(gap=8))

    progress = ProgressBar(value=68, status="ok")

    metrics = MetricList()
    metrics.set_items([
        {"label": "Rows shown", "value": "6"},
        {"label": "Sortable columns", "value": "2"},
    ])

    table = Table(
        columns=[
            {"key": "name", "label": "Name", "sortable": True},
            {"key": "role", "label": "Role"},
            {"key": "status", "label": "Status", "sortable": True},
        ],
        rows=[
            {"name": "Alice Johnson", "role": "Admin", "status": "Active"},
            {"name": "Bob Smith", "role": "Editor", "status": "Inactive"},
            {"name": "Carol White", "role": "Viewer", "status": "Active"},
            {"name": "David Lee", "role": "Editor", "status": "Pending"},
            {"name": "Eve Martinez", "role": "Admin", "status": "Active"},
            {"name": "Frank Nguyen", "role": "Viewer", "status": "Failed"},
        ],
    )
    selected = Label("Click a row to select it")
    table.on_row_click(lambda row: selected.set_text(f"Selected: {row['name']}"))
    table_box = VBox(table, selected)
    table_box.set_spec(LayoutSpec(gap=8))

    chart = Chart(
        chart_type="area", title="Sample series",
        x=["Mon", "Tue", "Wed", "Thu", "Fri"],
        series=[{"name": "Visits", "data": [120, 160, 150, 210, 240]}],
    )

    gauge = Gauge(label="Health", value=86, unit="%", status="ok")

    return _page(
        "Data Display", "Badge, ProgressBar, MetricList, Table, Chart, Gauge",
        _section("Badge", "Reuses the same status vocabulary as Table's status column", badges),
        _section("Progress bar", "", progress),
        _section("Metric list", "", metrics),
        _section(
            "Table", "Click a sortable column header to sort; click a row to select it",
            table_box,
        ),
        _section("Chart", "Line/bar/area, redraws on theme switch", chart),
        _section("Gauge", "Animated radial progress", gauge),
    )


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

def navigation_page(ctx):
    breadcrumb = Breadcrumb([
        {"label": "Home", "path": "/"},
        {"label": "Components", "path": "/components"},
        {"label": "Navigation"},
    ])

    tabs = TabWidget()
    tabs.add_tab(Label("First tab's content."), "Tab One")
    tabs.add_tab(Label("Second tab's content."), "Tab Two")
    tabs.add_tab(Label("Third tab's content."), "Tab Three")

    return _page(
        "Navigation", "Breadcrumb, TabWidget — Sidebar is the one on your left",
        _section("Breadcrumb", "Non-last crumbs with a path are clickable links", breadcrumb),
        _section("Tabs", "", tabs),
        _section(
            "Sidebar", "",
            Label(
                "You're already looking at it: grouped sections "
                "(add_group), active-item highlighting, and "
                "collapse/expand at the AppShell breakpoint."
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout_page(ctx):
    grid_demo = uniui.Grid(columns=4)
    grid_demo.set_spec(LayoutSpec(gap=8))
    for i in range(8):
        grid_demo.add_item(GroupBox(f"Cell {i + 1}", layout=VBox(Label("Grid cell"))))

    wrap_demo = Wrap()
    wrap_demo.set_spec(LayoutSpec(gap=8))
    for i in range(6):
        wrap_demo.add_item(GroupBox(f"Item {i + 1}", layout=VBox(Label("Wraps at any width"))))

    split = uniui.SplitPane(
        first=GroupBox("Left pane", layout=VBox(Label("Drag the divider"))),
        second=GroupBox("Right pane", layout=VBox(Label("Resizes both sides"))),
    )

    return _page(
        "Layout", "Grid, Wrap, SplitPane — resize the window to see them reflow",
        _section("Grid (4 columns, fixed span)", "", grid_demo),
        _section("Wrap (flows to the next line when out of room)", "", wrap_demo),
        _section("SplitPane (draggable divider)", "", split),
    )


def not_found_page(ctx):
    return _page("Not found", f"No gallery page matches {ctx.path!r}.")


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------

def build_gallery(framework="auto"):
    use(framework)

    router = Router(
        Route("/overview", overview_page, name="overview"),
        Route("/buttons", buttons_page, name="buttons"),
        Route("/inputs", inputs_page, name="inputs"),
        Route("/data-display", data_display_page, name="data-display"),
        Route("/navigation", navigation_page, name="navigation"),
        Route("/layout", layout_page, name="layout"),
        not_found=not_found_page,
        default="/overview",
    )

    f = uniui._get_factory()
    sidebar = f.create_sidebar()
    sidebar.add_group("Categories")
    for key, label, icon in _CATEGORIES:
        sidebar.add_item(key, label, icon)
    sidebar.on_select(router.push_named)

    def _sync_sidebar(ctx):
        if ctx.name and ctx.name != "__not_found__":
            sidebar.set_active(ctx.name)

    router.on_navigate(_sync_sidebar)

    breadcrumb = Breadcrumb()

    def _trail(ctx):
        if not ctx.name or ctx.name == "__not_found__":
            return [{"label": "Component Gallery"}]
        return [
            {"label": "Component Gallery", "path": "/overview"},
            {"label": ctx.name.replace("-", " ").title()},
        ]

    sync_breadcrumb(breadcrumb, router, trail_fn=_trail)
    breadcrumb.on_click(router.push)

    product = Label("UniUI Component Gallery")
    live_badge = Badge("Live Demo", status="ok")
    header = HBox(product, live_badge, breadcrumb)
    header.set_spec(LayoutSpec(gap=16))

    footer = Label("UniUI Component Gallery · Phase 1 (existing components only)")

    content = RouterView(router)
    shell = AppShell(header=header, sidebar=sidebar, content=content, footer=footer)

    router.push_named("overview")
    return shell


def main():
    framework = parse_args_ui()
    shell = build_gallery(framework)
    show_ui(shell, title="UniUI Component Gallery", width=1200, height=800)


if __name__ == "__main__":
    main()
