"""Runtime theme tests for the Qt Admin component set."""

import pytest


pytestmark = pytest.mark.qt


def test_admin_theme_updates_live_widgets_without_replacement():
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.qt_components import (
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
        assert dark["bg"] == "#0b0f19"
        assert dark["surface"] in table._table.styleSheet()
        assert dark["sidebar_bg"] in sidebar.get_native().styleSheet()
        assert sidebar.get_native().currentRow() == 0
        assert native_ids == (
            id(stat.get_native()), id(table.get_native()), id(sidebar.get_native())
        )
    finally:
        set_admin_theme(False)


def test_admin_palette_is_returned_as_a_copy():
    from uniui.qt_components import get_admin_palette

    palette = get_admin_palette()
    palette["bg"] = "changed"
    assert get_admin_palette()["bg"] != "changed"


def test_admin_sidebar_splitter_is_draggable_and_restores_width():
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.qt_components import QtAppShellAdapter, QtSidebarAdapter

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
        assert splitter.handleWidth() == 0

        root.resize(1200, 700)
        app.processEvents()
        assert 300 <= sidebar.get_native().width() <= 340
        assert splitter.handleWidth() == 5
    finally:
        root.close()


def test_admin_footer_uses_shared_height_and_keeps_text_visible():
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.theme import get_admin_metrics
    from uniui.qt_components import QtAppShellAdapter

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    shell = QtAppShellAdapter()
    footer_content = QtWidgets.QWidget()
    footer_layout = QtWidgets.QHBoxLayout(footer_content)
    footer_layout.setContentsMargins(0, 0, 0, 0)
    label = QtWidgets.QLabel("All systems operational")
    label.setMinimumWidth(0)
    label.setSizePolicy(
        QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
    )
    footer_layout.addWidget(label)
    footer_layout.addStretch()
    shell.set_content(QtWidgets.QWidget())
    shell.set_footer(footer_content)
    root = shell.get_native()
    try:
        root.resize(900, 600)
        root.show()
        app.processEvents()

        footer = shell._footer_area
        assert footer.height() == get_admin_metrics()["footer_height"]
        assert footer.layout().contentsMargins().left() == 20
        assert footer.accessibleName() == "Application status bar"
        assert label.isVisible()
        assert label.width() >= label.sizeHint().width()
        assert label.height() > 0
        label_top_left = label.mapTo(footer, label.rect().topLeft())
        label_bottom_right = label.mapTo(footer, label.rect().bottomRight())
        assert footer.contentsRect().contains(label_top_left)
        assert footer.contentsRect().contains(label_bottom_right)
    finally:
        root.close()


def test_admin_sidebar_exposes_navigation_states_and_accessibility():
    pytest.importorskip("PySide2")
    from PySide2 import QtGui, QtWidgets
    from uniui.qt_components import QtSidebarAdapter

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    sidebar = QtSidebarAdapter()
    sidebar.add_item("dashboard", "Dashboard", "dashboard")
    native = sidebar.get_native()
    try:
        sidebar.set_active("dashboard")
        app.processEvents()

        icon = native.item(0).icon()
        assert native.accessibleName() == "Primary navigation"
        assert "QListWidget::item:disabled" in native.styleSheet()
        assert icon.availableSizes(QtGui.QIcon.Normal, QtGui.QIcon.Off)
        assert icon.availableSizes(QtGui.QIcon.Selected, QtGui.QIcon.Off)
    finally:
        native.close()


def test_admin_table_uses_status_pill_delegate_and_web_density():
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.qt_components import QtTableAdapter

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    table = QtTableAdapter()
    table.set_columns([
        {"key": "name", "label": "Name"},
        {"key": "status", "label": "Status", "width": 120},
    ])
    table.set_rows([{"name": "Alice", "status": "Active"}])
    native = table._table
    try:
        native.resize(500, 240)
        native.show()
        app.processEvents()

        from PySide2 import QtCore

        assert native.model().headerData(1, QtCore.Qt.Horizontal) == "STATUS"
        assert native.horizontalHeader().height() == 44
        assert native.rowHeight(0) == 52
        assert type(native.itemDelegateForColumn(1)).__name__ == "_StatusPillDelegate"
        assert native.focusPolicy() != 0
    finally:
        native.close()


def test_qt_admin_icons_render_normal_and_selected_svg_states():
    pytest.importorskip("PySide2")
    from PySide2 import QtGui, QtWidgets
    from uniui.qt_icons import admin_icon

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    icon = admin_icon("dashboard", "#cbd5e1", selected_color="#60a5fa")

    assert icon.availableSizes(QtGui.QIcon.Normal, QtGui.QIcon.Off)
    assert icon.availableSizes(QtGui.QIcon.Selected, QtGui.QIcon.Off)


def test_qt_gauge_and_chart_theme_switch_preserves_streaming_state():
    pytest.importorskip("PySide2")
    from uniui.qt_components import QtChartAdapter, QtGaugeAdapter, set_admin_theme

    gauge = QtGaugeAdapter(); gauge.set_value(72)
    chart = QtChartAdapter()
    chart.set_data([1, 2], [{"name": "Load", "data": [20, 30]}])
    chart.append_data(3, [40])
    native_ids = (id(gauge.get_native()), id(chart.get_native()))
    try:
        set_admin_theme(True)
        assert native_ids == (id(gauge.get_native()), id(chart.get_native()))
        assert chart._widget.x_values == [1, 2, 3]
        assert chart._widget.series[0]["data"] == [20.0, 30.0, 40.0]
    finally:
        set_admin_theme(False)
