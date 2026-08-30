"""Responsive, DPI, motion, performance, and render checks for Qt Admin."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


pytestmark = pytest.mark.qt


@pytest.mark.parametrize(
    ("width", "sidebar_width", "handle_width"),
    [(1440, 212, 5), (1180, 72, 0), (900, 72, 0), (640, 72, 0)],
)
def test_qt_shell_responsive_geometry(width, sidebar_width, handle_width):
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.qt_components import QtAppShellAdapter, QtSidebarAdapter

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    shell = QtAppShellAdapter()
    sidebar = QtSidebarAdapter(); sidebar.add_item("dashboard", "Dashboard", "dashboard")
    content = QtWidgets.QWidget(); content.setMinimumHeight(1200)
    shell.set_sidebar(sidebar); shell.set_content(content)
    root = shell.get_native()
    content_id = id(content)
    try:
        root.resize(width, 700); root.show(); app.processEvents()
        assert root.width() == width
        assert sidebar.get_native().width() == sidebar_width
        assert shell._splitter.handleWidth() == handle_width
        assert shell._content_scroll.verticalScrollBar().maximum() > 0
        assert id(shell._content_scroll.widget()) == content_id
    finally:
        root.close()


def test_qt_chart_streaming_performance_and_gauge_animation_toggle():
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.qt_components import QtChartAdapter, QtGaugeAdapter
    from uniui.qt_effects import set_motion_enabled

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    chart = QtChartAdapter(); chart.set_max_points(120)
    chart.set_data([], [{"name": "Load", "data": []}])
    started = time.perf_counter()
    for index in range(5000):
        chart.append_data(index, [index % 100])
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0
    assert len(chart._widget.x_values) == 120
    assert len(chart._widget.series[0]["data"]) == 120

    gauge = QtGaugeAdapter()
    try:
        set_motion_enabled(False)
        gauge.set_value(88)
        app.processEvents()
        assert gauge._widget.value == pytest.approx(88)
    finally:
        set_motion_enabled(True)


def test_qt_drawer_and_offscreen_visual_render_smoke():
    pytest.importorskip("PySide2")
    from PySide2 import QtCore, QtGui, QtWidgets
    from uniui.qt_components import QtChartAdapter, QtDrawerAdapter, QtGaugeAdapter
    from uniui.qt_effects import set_motion_enabled

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    root = QtWidgets.QWidget(); layout = QtWidgets.QHBoxLayout(root)
    gauge = QtGaugeAdapter(); gauge.set_label("Load"); gauge.set_value(72)
    chart = QtChartAdapter(); chart.set_title("Live")
    chart.set_data([1, 2, 3], [{"name": "Load", "data": [20, 45, 32]}])
    layout.addWidget(gauge.get_native()); layout.addWidget(chart.get_native())
    drawer = QtDrawerAdapter(); drawer.set_title("Details")
    drawer.set_content(QtWidgets.QLabel("Settings"))
    try:
        root.resize(900, 360); root.show(); app.processEvents()
        image = QtGui.QImage(root.size(), QtGui.QImage.Format_ARGB32)
        image.fill(QtCore.Qt.transparent); root.render(image)
        sampled_colors = {
            image.pixelColor(x, y).rgba()
            for x in range(0, image.width(), 12)
            for y in range(0, image.height(), 12)
        }
        assert not image.isNull()
        assert len(sampled_colors) >= 8

        set_motion_enabled(False); drawer.open(); app.processEvents()
        assert drawer.is_open()
        assert drawer.get_native().width() == 360
        drawer.close(); app.processEvents()
        assert not drawer.is_open()
    finally:
        set_motion_enabled(True); drawer.get_native().hide(); root.close()


def test_qt_combo_popup_window_is_translucent_to_avoid_square_corners():
    """The popup's rounded QSS corners only render correctly if the popup's
    own top-level window is translucent - otherwise Qt paints an opaque
    rectangular window surface behind it, showing as black slivers in the
    corners the border-radius clips. See styles.apply_combo_popup_style."""
    pytest.importorskip("PySide2")
    from PySide2 import QtCore, QtWidgets
    from uniui import create_factory

    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    combo = create_factory("qt").create_combo_box()
    native = combo.get_native()
    view = native.view()
    assert view.testAttribute(QtCore.Qt.WA_TranslucentBackground)
    assert view.window().testAttribute(QtCore.Qt.WA_TranslucentBackground)


def test_qt_tab_widget_gets_its_own_stylesheet_even_when_nested_in_a_card():
    """A QTabWidget nested inside Card's locally-styled QFrame doesn't
    receive the app-wide stylesheet cascade (same issue as the combo popup)
    -- it must carry its own QSS so QTabBar::tab padding/font aren't left to
    the native style's tighter sizeHint, which clips tab labels."""
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets

    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    from uniui import create_factory

    card = create_factory("qt").create_card()
    tabs = create_factory("qt").create_tab_widget()
    label = create_factory("qt").create_label()
    label.set_text("Activity")
    tabs.add_tab(label, "Activity")
    card.set_content(tabs)

    assert tabs.get_native().styleSheet() != ""


def test_qt_factory_enables_high_dpi_before_application_creation():
    repo_root = Path(__file__).resolve().parents[1]
    for scale in ("1", "1.25", "1.5", "2"):
        env = os.environ.copy(); env["PYTHONPATH"] = str(repo_root / "src")
        env["QT_QPA_PLATFORM"] = "offscreen"; env["QT_SCALE_FACTOR"] = scale
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from uniui import create_factory; create_factory('qt'); "
                "from PySide2 import QtCore, QtWidgets; "
                "from uniui.qt_components import QtAppShellAdapter; "
                "from uniui.qt_icons import admin_pixmap; "
                "app=QtWidgets.QApplication.instance(); shell=QtAppShellAdapter(); "
                "root=shell.get_native(); root.resize(640,480); root.show(); app.processEvents(); "
                "assert root.width()==640 and admin_pixmap('dashboard','#fff',20).width()==20; "
                "assert QtWidgets.QApplication.testAttribute(QtCore.Qt.AA_EnableHighDpiScaling); "
                "assert QtWidgets.QApplication.testAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)",
            ],
            cwd=repo_root, env=env, capture_output=True, text=True,
        )
        assert result.returncode == 0, f"scale={scale}: {result.stderr}"
