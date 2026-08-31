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


def test_qt_wrap_sizes_ignored_policy_children_to_their_real_width():
    """Regression: QtWrapAdapter's _QFlowLayout used to size children via
    QWidgetItem.sizeHint(), which Qt zeroes out on any axis where the
    widget's size policy is QSizePolicy.Ignored - several UniUI Qt
    components (StatCard, Card, Table, MetricList labels) use Ignored
    horizontally so an ordinary QVBoxLayout/QHBoxLayout parent can shrink
    them below their natural width. Placed inside a Wrap instead, every
    such child collapsed to width 0 and effectively disappeared (caught by
    actually looking at admin_demo's dashboard, not by any prior test)."""
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.qt_components import QtStatCardAdapter
    from uniui.backends.qt.primitives.layouts import QtWrapAdapter
    from uniui.core import LayoutSpec

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    wrap = QtWrapAdapter()
    wrap.set_spec(LayoutSpec(gap=14))
    cards = []
    for label in ("Active Users", "Orders", "Revenue", "Open Errors"):
        card = QtStatCardAdapter()
        card.set_label(label)
        card.set_value("42")
        wrap.add_item(card)
        cards.append(card)

    root = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(root)
    layout.addWidget(wrap.get_native())
    try:
        root.resize(1000, 300)
        root.show()
        for _ in range(5):
            app.processEvents()
        for card in cards:
            geo = card.get_native().geometry()
            assert geo.width() > 0, f"{card.get_native().property('card')} collapsed to width 0"
            assert geo.height() == 136
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


def test_qt_combo_popup_has_no_border_radius_and_no_translucency():
    """The popup is a Qt::Popup top-level window - WA_TranslucentBackground
    on that combination is a known-bad interaction on Windows without
    desktop composition (confirmed by hands-on repro: the whole popup
    rendered solid black instead of showing rounded transparent corners).
    Square corners avoid the problem entirely, so neither the QSS nor the
    widget attribute should reappear. See styles.apply_combo_popup_style."""
    pytest.importorskip("PySide2")
    from PySide2 import QtCore, QtWidgets
    from uniui import create_factory

    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    combo = create_factory("qt").create_combo_box()
    native = combo.get_native()
    view = native.view()
    assert "border-radius" not in native.styleSheet()
    assert not view.testAttribute(QtCore.Qt.WA_TranslucentBackground)
    assert not view.window().testAttribute(QtCore.Qt.WA_TranslucentBackground)


def test_qt_tab_widget_gets_its_own_stylesheet_even_when_nested_in_a_card():
    """A QTabWidget nested inside Card's locally-styled QFrame doesn't
    receive the app-wide stylesheet cascade (same issue as the combo popup)
    -- it must carry its own QSS so QTabBar::tab font/border aren't left to
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


def test_qt_tab_bar_qss_has_no_padding_property_that_clips_labels():
    """PySide2's Windows-style tab painting computes the text-drawing rect
    differently from the sizeHint contents rect once a QSS `padding` is set
    on QTabBar::tab, clipping both edges of the label - confirmed by
    hands-on repro: "Activity" rendered with both its leading "A" and
    trailing "y" cut off. min-width/height give equivalent visual spacing
    without touching that broken code path, so `padding` must not come
    back here."""
    import re

    from uniui.backends.qt.primitives.styles import base_stylesheet

    qss = re.sub(r"/\*.*?\*/", "", base_stylesheet(), flags=re.DOTALL)
    tab_bar_rule = qss.split("QTabBar::tab {", 1)[1].split("}", 1)[0]
    assert "padding" not in tab_bar_rule


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


def test_qt_admin_demo_settings_route_survives_repeated_visits_and_theme_toggle():
    """Regression: settings_page binds labels to the module-level, permanent
    _ADMIN_THEME state. Before the /settings route was marked cache=True,
    every visit rebuilt the page and leaked one bind_text subscription
    pointing at a QTLabel that gets deleted the moment the route is left --
    the next theme toggle after that raised "Internal C++ object (QTLabel)
    already deleted" for every leaked visit. Reproduced by visiting
    /settings then navigating away twice (so a pre-fix run leaks two
    subscriptions), forcing Qt's deferred deletion to actually run, then
    toggling the theme and asserting nothing was logged to stderr."""
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + str(repo_root)
    env["QT_QPA_PLATFORM"] = "offscreen"
    script = """
import sys
sys.path.insert(0, "examples")
from PySide2 import QtWidgets, QtCore
import examples.admin_demo as demo
from uniui.routing import RouterView

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
router = demo._build_router()
view = RouterView(router)
for _ in range(2):
    router.push_named("settings")
    router.push_named("dashboard")
for _ in range(5):
    app.processEvents()
QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
app.processEvents()
demo._ADMIN_THEME.set("dark")
print("OK")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo_root, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "already deleted" not in result.stderr, result.stderr
    assert "OK" in result.stdout


def test_qt_admin_demo_semantic_classes_still_style_real_widgets():
    """Regression: admin_demo.py's pages style themselves via
    widget.add_class("uniui-demo-...") - a real IWidget capability
    (src/uniui/_adapter_mixins.py ClassMixin) backed on Qt by a boolean
    dynamic property + QSS attribute selector ([name="true"]), repolished
    via unpolish()/polish() so it takes effect immediately.
    _admin_stylesheet() selects on the same class names, so page subtitles
    should render as an 18px/650-weight heading, not fall back to plain
    13px body text (caught by measuring the real widget's rendered font,
    not by eyeballing a screenshot - the visual difference is easy to
    miss)."""
    pytest.importorskip("PySide2")
    import uniui
    from PySide2 import QtWidgets
    import examples.admin_demo as demo
    from uniui.routing import RouterView

    # use("qt") first, matching main()'s real order - creating the Qt
    # factory lazily on first _get_factory() call (e.g. inside
    # push_named() below) re-applies the base stylesheet and would
    # clobber a custom one set beforehand.
    uniui.use("qt")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setStyleSheet(demo._admin_stylesheet())
    router = demo._build_router()
    view = RouterView(router)
    root = view.get_native()
    try:
        router.push_named("dashboard")
        app.processEvents()
        subtitle = next(
            lbl for lbl in root.findChildren(QtWidgets.QLabel)
            if lbl.property("uniui-demo-subtitle") is True
        )
        assert subtitle.font().pixelSize() == 18
        assert subtitle.font().bold()
    finally:
        root.close()
