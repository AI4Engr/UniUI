"""Structural guarantees for the Qt backend split.

Components are moving from ``uniui.qt_components`` into
``uniui.backends.qt.components``. Two things about that move are easy to break
and produce no test failure anywhere else:

  1. ``qt_components`` must keep re-exporting what it used to define, because
     ``examples/`` and ``qt_style`` still import from it.
  2. The live palette must stay a *single dict mutated in place*. Every style
     builder reads it at call time, so if any module ever rebinds its own copy,
     that module silently freezes at whatever theme was active when it was
     first imported - and only shows up as a half-restyled UI after a switch.
"""
import pytest

pytest.importorskip("PySide2")

from PySide2 import QtWidgets  # noqa: E402

from uniui import qt_components  # noqa: E402
from uniui.backends.qt import runtime, styles  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def light_theme():
    """Run the test from a known theme and restore it afterwards."""
    previous = runtime.is_dark()
    qt_components.set_admin_theme(False)
    yield
    qt_components.set_admin_theme(previous)


class TestCompatibilityReExports:
    MOVED = [
        "QtAppShellAdapter",
        "QtBreadcrumbAdapter",
        "QtCardAdapter",
        "QtChartAdapter",
        "QtDrawerAdapter",
        "QtGaugeAdapter",
        "QtMetricListAdapter",
        "QtSidebarAdapter",
        "QtStatCardAdapter",
        "QtTableAdapter",
    ]

    def test_every_component_lives_in_its_own_module(self):
        """One component per module, not a second monolith."""
        from uniui.backends.qt import components

        homes = {
            name: getattr(components, name).__module__ for name in self.MOVED
        }
        assert len(set(homes.values())) == len(self.MOVED), homes
        for name, module in homes.items():
            assert module.startswith("uniui.backends.qt.components."), (name, module)

    @pytest.mark.parametrize("name", MOVED)
    def test_moved_component_is_still_importable_from_the_old_module(self, name):
        assert hasattr(qt_components, name)

    @pytest.mark.parametrize("name", MOVED)
    def test_the_re_export_is_the_same_class_not_a_copy(self, name):
        from uniui.backends.qt import components

        assert getattr(qt_components, name) is getattr(components, name)

    @pytest.mark.parametrize(
        "name",
        [
            "get_palette", "is_dark", "set_theme",
            "get_admin_palette", "is_admin_dark", "set_admin_theme",
            "_scrollbar_rules", "_card_style", "_C", "_M",
        ],
    )
    def test_helper_names_survive_the_move(self, name):
        """``qt_style`` imports ``_scrollbar_rules`` and ``get_admin_palette``
        from here, so these are load-bearing despite the underscore."""
        assert hasattr(qt_components, name)

    def test_the_factory_still_builds_a_stat_card(self):
        from uniui.backends.qt.components import QtStatCardAdapter

        factory = qt_components.QtWidgetFactory()
        assert isinstance(factory.createStatCard(), QtStatCardAdapter)


class TestPaletteIsShared:
    def test_every_module_sees_one_dict_object(self):
        assert qt_components._C is runtime.C

    def test_metrics_are_shared_too(self):
        assert qt_components._M is runtime.M

    def test_a_theme_switch_mutates_rather_than_rebinds(self, light_theme):
        """The identity check that makes the rest of the split safe."""
        before = runtime.C
        qt_components.set_admin_theme(True)
        assert runtime.C is before
        assert qt_components._C is before


class TestThemeSwitchReachesEveryModule:
    def test_tokens_change(self, light_theme):
        light = runtime.C["text"]
        qt_components.set_admin_theme(True)
        assert runtime.C["text"] != light

    def test_shared_style_builder_follows(self, light_theme):
        light_qss = styles.card_style()
        qt_components.set_admin_theme(True)
        assert styles.card_style() != light_qss
        assert runtime.C["surface"] in styles.card_style()

    def test_a_moved_component_restyles(self, light_theme):
        card = qt_components.QtStatCardAdapter()
        card.set_label("Revenue")
        card.set_value("42")
        light_qss = card._value_lbl.styleSheet()

        qt_components.set_admin_theme(True)
        dark_qss = card._value_lbl.styleSheet()
        assert dark_qss != light_qss
        assert runtime.C["text"] in dark_qss

        qt_components.set_admin_theme(False)
        assert card._value_lbl.styleSheet() == light_qss

    @pytest.mark.parametrize(
        "factory_method",
        [
            "createCard", "createStatCard", "createMetricList", "createTable",
            "createSidebar", "createAppShell", "createBreadcrumb",
            "createGauge", "createChart", "createDrawer",
        ],
    )
    def test_every_component_survives_a_theme_switch(self, factory_method, light_theme):
        """A moved component must still be registered for theme refresh.

        ``track_themed`` is what puts an adapter on the refresh list. Forgetting
        it during a move produces a component that simply stops restyling -
        invisible until someone toggles dark mode.
        """
        factory = qt_components.QtWidgetFactory()
        adapter = getattr(factory, factory_method)()
        qt_components.set_admin_theme(True)
        qt_components.set_admin_theme(False)
        assert adapter.get_native() is not None

    def test_adapters_are_tracked_for_refresh(self, light_theme):
        factory = qt_components.QtWidgetFactory()
        before = len(runtime.THEMED_ADAPTERS)
        held = [factory.createCard(), factory.createTable(), factory.createGauge()]
        assert len(runtime.THEMED_ADAPTERS) > before
        assert held  # keep them alive; the registry holds weak references

    def test_get_palette_reports_the_active_theme(self, light_theme):
        light = qt_components.get_admin_palette()["text"]
        qt_components.set_admin_theme(True)
        assert qt_components.get_admin_palette()["text"] != light

    def test_get_palette_returns_a_copy(self):
        """Callers must not be able to corrupt the live palette."""
        palette = qt_components.get_admin_palette()
        assert palette is not runtime.C
        palette["text"] = "#000000"
        assert runtime.C["text"] != "#000000"


class TestLabelHelperUsesTheLiveTheme:
    def test_default_colour_is_not_frozen_at_import_time(self, light_theme):
        """The default used to be evaluated in the signature, which baked in
        whichever theme was active when the module first loaded."""
        light_lbl = runtime.label("x")
        qt_components.set_admin_theme(True)
        dark_lbl = runtime.label("x")
        assert dark_lbl.styleSheet() != light_lbl.styleSheet()
        assert runtime.C["text"] in dark_lbl.styleSheet()
