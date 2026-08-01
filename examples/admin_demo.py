"""
Admin Dashboard Demo — M3 Admin Skeleton example.

Run with:
    python examples/admin_demo.py --ui qt
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import uniui
from uniui import (
    use, parse_args_ui,
    Label, Button, VBox, HBox,
    Card, StatCard, Table, Sidebar, AppShell,
    show_ui,
)
from uniui.routing import Router, Route, RouterView, NavMenu


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def dashboard_page(ctx):
    col = uniui._get_factory().create_vbox()

    title = Label("Dashboard")

    stats = uniui._get_factory().create_hbox()
    for label, value, trend in [
        ("Active Users", "1,280", 5.2),
        ("Orders Today", "320", -1.4),
        ("Revenue", "$48,200", 12.0),
        ("Errors", "3", -80.0),
    ]:
        sc = StatCard(label=label, value=value, trend=trend,
                      status="error" if label == "Errors" else "ok")
        stats.add_item(sc)

    # Sample table
    tbl = Table(
        columns=[
            {"key": "id", "label": "ID", "width": 60},
            {"key": "name", "label": "Name"},
            {"key": "status", "label": "Status", "width": 100},
        ],
        rows=[
            {"id": "1", "name": "Alice Johnson", "status": "Active"},
            {"id": "2", "name": "Bob Smith", "status": "Inactive"},
            {"id": "3", "name": "Carol White", "status": "Active"},
        ],
    )

    card = Card(title="Recent Users")
    card.set_content(tbl)

    col.add_item(title)
    col.add_item(stats)
    col.add_item(card)
    return col


def users_page(ctx):
    col = uniui._get_factory().create_vbox()
    label = Label("Users — page " + ctx.query.get("page", "1"))

    tbl = Table(
        columns=[
            {"key": "id", "label": "ID", "width": 60},
            {"key": "name", "label": "Name"},
            {"key": "email", "label": "Email"},
        ],
        rows=[
            {"id": "1", "name": "Alice Johnson", "email": "alice@example.com"},
            {"id": "2", "name": "Bob Smith", "email": "bob@example.com"},
        ],
    )

    col.add_item(label)
    col.add_item(tbl)
    return col


def not_found_page(ctx):
    col = uniui._get_factory().create_vbox()
    col.add_item(Label(f"404 — Page not found: {ctx.path}"))
    return col


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    framework = parse_args_ui()
    use(framework if framework != "auto" else "qt")

    router = Router(
        Route("/dashboard", dashboard_page, name="dashboard"),
        Route("/users", users_page, name="users"),
        not_found=not_found_page,
    )

    sidebar = NavMenu.from_router(router)

    content = RouterView(router)

    shell = AppShell(
        header=Label("  UniUI Admin Demo"),
        sidebar=sidebar,
        content=content,
    )

    # Navigate to default page
    router.push("/dashboard")

    show_ui(shell, title="UniUI Admin Demo", width=1024, height=700)


if __name__ == "__main__":
    main()
