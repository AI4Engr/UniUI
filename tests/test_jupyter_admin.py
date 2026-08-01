"""Focused tests for the Jupyter Admin backend."""
import pytest

pytest.importorskip("ipywidgets")

from uniui import create_factory
from uniui.jupyter_admin import is_admin_dark, set_admin_theme


def test_jupyter_factory_registers_admin_components():
    factory = create_factory("jupyter")
    assert type(factory.create_card()).__name__ == "JupyterCardAdapter"
    assert type(factory.create_stat_card()).__name__ == "JupyterStatCardAdapter"
    assert type(factory.create_table()).__name__ == "JupyterTableAdapter"
    assert type(factory.create_sidebar()).__name__ == "JupyterSidebarAdapter"
    assert type(factory.create_app_shell()).__name__ == "JupyterAppShellAdapter"
    assert type(factory.create_breadcrumb()).__name__ == "JupyterBreadcrumbAdapter"


def test_jupyter_admin_theme_updates_live_shell_without_rebuilding_children():
    factory = create_factory("jupyter")
    shell = factory.create_app_shell()
    children = shell.get_native().children
    set_admin_theme(True)
    try:
        assert is_admin_dark()
        assert "--uniui-bg:#0b1220" in shell._style.value
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

