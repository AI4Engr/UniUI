"""Focused tests for the Jupyter Admin backend."""
import pytest

pytest.importorskip("ipywidgets")

from uniui import create_factory
from uniui.jupyter_components import is_admin_dark, set_admin_theme
from uniui.routing import Route, Router, RouterView


def test_jupyter_factory_registers_admin_components():
    factory = create_factory("jupyter")
    assert type(factory.create_card()).__name__ == "JupyterCardAdapter"
    assert type(factory.create_stat_card()).__name__ == "JupyterStatCardAdapter"
    assert type(factory.create_table()).__name__ == "JupyterTableAdapter"
    assert type(factory.create_sidebar()).__name__ == "JupyterSidebarAdapter"
    assert type(factory.create_app_shell()).__name__ == "JupyterAppShellAdapter"
    assert type(factory.create_breadcrumb()).__name__ == "JupyterBreadcrumbAdapter"
    wrap = factory.create_wrap().get_native()
    assert type(wrap).__name__ == "Box"
    assert type(wrap).__module__.startswith("ipywidgets.")


def test_jupyter_admin_theme_updates_live_shell_without_rebuilding_children():
    factory = create_factory("jupyter")
    shell = factory.create_app_shell()
    children = shell.get_native().children
    set_admin_theme(True)
    try:
        assert is_admin_dark()
        assert "--uniui-bg:#0b0f19" in shell._style.value
        assert shell.get_native().children == children
    finally:
        set_admin_theme(False)


def test_jupyter_table_row_bridge_calls_python_once_and_resets():
    factory = create_factory("jupyter")
    table = factory.create_table()
    table.set_columns([{"key": "id", "label": "ID"}])
    table.set_rows([{"id": 7}])
    selected = []
    table.on_row_click(selected.append)

    table._bridge.value = 0

    assert selected == [{"id": 7}]
    assert table._bridge.value == -1
    assert "dispatchEvent(new Event('change'" in table._table.value


def test_jupyter_admin_uses_shared_svg_icons_and_status_pills():
    factory = create_factory("jupyter")
    sidebar = factory.create_sidebar()
    sidebar.add_item("dashboard", "Dashboard", "dashboard")
    button = sidebar._buttons[0]
    table = factory.create_table()
    table.set_columns([{"key": "status", "label": "Status"}])
    table.set_rows([{"status": "Active"}])

    assert "uniui-icon-dashboard" in button._dom_classes
    assert button.description == "Dashboard"
    assert "uniui-status-pill uniui-status-ok" in table._table.value
    assert "▦" not in button.description


def test_jupyter_gauge_chart_and_drawer_update_in_place():
    factory = create_factory("jupyter")
    gauge = factory.create_gauge(); native_gauge = gauge.get_native()
    gauge.set_label("Load"); gauge.set_unit("%"); gauge.set_value(72)
    chart = factory.create_chart(); native_chart = chart.get_native()
    chart.set_max_points(3)
    chart.set_data([1, 2], [{"name": "Load", "data": [20, 30]}])
    chart.append_data(3, [40]); chart.append_data(4, [50])
    drawer = factory.create_drawer(); drawer.set_title("Details")
    drawer.set_content(factory.create_label()); drawer.open()

    assert gauge.get_native() is native_gauge
    assert chart.get_native() is native_chart
    assert "uniui-gauge-svg" in native_gauge.value
    assert len(chart._model.x_values) == 3
    assert drawer.is_open()
    drawer.close(); assert not drawer.is_open()


def test_jupyter_sidebar_and_shell_keep_drag_width_state():
    factory = create_factory("jupyter")
    sidebar = factory.create_sidebar()
    sidebar.add_item("dashboard", "Dashboard", "dashboard")
    selected = []
    sidebar.on_select(selected.append)
    sidebar._buttons[0].click()
    assert selected == ["dashboard"]

    shell = factory.create_app_shell()
    shell.set_sidebar(sidebar)
    shell._width_bridge.value = 320

    assert shell._saved_sidebar_width == 320
    assert sidebar.get_native().layout.width == "320px"
    assert "onpointerdown" in shell._handle.value
    assert "@container (max-width:1019px)" in shell._style.value


def test_jupyter_shell_mounts_content_as_direct_flex_child():
    factory = create_factory("jupyter")
    shell = factory.create_app_shell()
    sidebar = factory.create_sidebar()
    content = factory.create_overlay()

    shell.set_sidebar(sidebar)
    shell.set_content(content)

    native = content.get_native()
    assert shell._content is native
    assert native in shell._body.children
    assert native.layout.flex == "1 1 0%"
    assert native.layout.width == "auto"
    assert shell._body.layout.flex == "1 1 auto"
    assert shell.get_native().layout.min_height == "680px"
    assert "max-width:1180px;margin:0 auto" not in shell._style.value


def test_jupyter_shell_debug_probe_reports_python_tree_and_dom_targets():
    factory = create_factory("jupyter")
    shell = factory.create_app_shell()
    content = factory.create_overlay()
    page = factory.create_vbox()
    page.add_item(factory.create_label())
    content.add_layer(page)
    shell.set_content(content)
    shell.set_debug(True)

    assert shell._debug.layout.display == "block"
    assert "active=0 layers=1 mounted=1 page=VBox wrapped=True page_children=1" in shell._debug.value
    assert "active=0 layers=1 mounted=1 page=VBox wrapped=True page_children=1" in shell.debug_report()
    assert "Measure DOM" in shell._debug.value
    assert "getBoundingClientRect" in shell._debug.value
    assert "querySelectorAll('.uniui-admin-shell')" in shell._debug.value
    assert "uniui-shell-content" in shell._debug.value
    assert "UniUI browser DOM measurements" in shell.debug_script()
    assert "insertAdjacentElement('beforebegin'" in shell.debug_script()


def test_jupyter_split_pane_has_local_pointer_drag_bridge():
    factory = create_factory("jupyter")
    split = factory.create_split_pane("horizontal")
    split.set_first(factory.create_label())
    split.set_second(factory.create_label())
    split.set_sizes(0.3)

    native = split.get_native()
    assert len(native.children) == 4
    assert "onpointerdown" in native._handle.value
    assert native.children[0].layout.flex == "0 0 30.0000%"


def test_jupyter_router_mounts_only_active_page_and_preserves_cached_state():
    factory = create_factory("jupyter")
    pages = {}

    def make_page(name):
        def build(_ctx):
            page = factory.create_line_edit()
            page.set_text(name)
            pages[name] = page.get_native()
            return page
        return build

    router = Router(
        Route("/a", make_page("a"), name="a", cache=True),
        Route("/b", make_page("b"), name="b", cache=True),
    )
    view = RouterView(router, factory)
    overlay = view.get_native()

    router.push("/a")
    first = pages["a"]
    first.value = "edited"
    router.push("/b")
    second = pages["b"]

    assert overlay._layers == [first, second]
    assert type(overlay).__name__ == "VBox"
    assert type(overlay).__module__.startswith("ipywidgets.")
    assert overlay.children == (second,)

    router.push("/a")
    assert overlay.children == (first,)
    assert first.value == "edited"


def test_jupyter_router_rewraps_composite_page_in_clean_stock_vbox():
    factory = create_factory("jupyter")
    page = factory.create_vbox()
    label = factory.create_label()
    label.set_text("Visible child")
    page.add_item(label)

    router = Router(Route("/page", lambda _ctx: page, name="page", cache=True))
    view = RouterView(router, factory)
    router.push("/page")

    overlay = view.get_native()
    source = page.get_native()
    rendered = overlay.children[0]
    assert overlay._layers == [source]
    assert rendered is not source
    assert type(rendered).__name__ == "VBox"
    assert type(rendered).__module__.startswith("ipywidgets.")
    assert rendered.children == source.children

    extra = factory.create_label()
    extra.set_text("Added later")
    page.add_item(extra)
    assert rendered.children == source.children
