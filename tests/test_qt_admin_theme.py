"""Runtime theme tests for the Qt Admin component set."""

import pytest


pytestmark = pytest.mark.qt


def test_admin_theme_updates_live_widgets_without_replacement():
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.qt_admin import (
        QtSidebarAdapter,
        QtStatCardAdapter,
        QtTableAdapter,
        get_admin_palette,
        is_admin_dark,
        set_admin_theme,
    )

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    stat = QtStatCardAdapter()
    table = QtTableAdapter()
    sidebar = QtSidebarAdapter()
    table.set_columns([{"key": "status", "label": "Status"}])
    table.set_rows([{"status": "Active"}])
    sidebar.add_item("dashboard", "Dashboard", "dashboard")
    sidebar.set_active("dashboard")

    native_ids = (
        id(stat.get_native()), id(table.get_native()), id(sidebar.get_native())
    )
    try:
        set_admin_theme(True)
        dark = get_admin_palette()
        app.processEvents()

        assert is_admin_dark()
        assert dark["bg"] == "#0b1120"
        assert dark["surface"] in table._table.styleSheet()
        assert dark["sidebar_bg"] in sidebar.get_native().styleSheet()
        assert sidebar.get_native().currentRow() == 0
        assert native_ids == (
            id(stat.get_native()), id(table.get_native()), id(sidebar.get_native())
        )
    finally:
        set_admin_theme(False)


def test_admin_palette_is_returned_as_a_copy():
    from uniui.qt_admin import get_admin_palette

    palette = get_admin_palette()
    palette["bg"] = "changed"
    assert get_admin_palette()["bg"] != "changed"


def test_admin_sidebar_splitter_is_draggable_and_restores_width():
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.qt_admin import QtAppShellAdapter, QtSidebarAdapter

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    shell = QtAppShellAdapter()
    sidebar = QtSidebarAdapter()
    sidebar.add_item("dashboard", "Dashboard", "dashboard")
    shell.set_sidebar(sidebar)
    shell.set_content(QtWidgets.QWidget())
    root = shell.get_native()
    try:
        root.resize(1200, 700)
        root.show()
        app.processEvents()
        splitter = root.findChild(QtWidgets.QSplitter)

        splitter.setSizes([320, 880])
        app.processEvents()
        assert 300 <= sidebar.get_native().width() <= 340

        root.resize(640, 560)
        app.processEvents()
        assert root.width() == 640
        assert sidebar.get_native().width() == 72

        root.resize(1200, 700)
        app.processEvents()
        assert 300 <= sidebar.get_native().width() <= 340
    finally:
        root.close()
