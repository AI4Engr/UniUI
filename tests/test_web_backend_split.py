"""Structural guarantees for the Web backend split.

Components moved from ``uniui.web_components`` into
``uniui.backends.web.components``. The failure modes this pins:

  1. ``web_components`` must keep re-exporting what it used to define -
     ``examples/admin_demo.py`` imports it as its admin backend and the tests
     import the theme helpers from it.
  2. The gauge and chart render SVG *server-side*, so unlike the rest of the
     backend they cannot be restyled by CSS alone. They must be registered via
     ``track_visual`` or they keep the old palette after a theme switch while
     everything around them updates.
  3. ``_css_installed`` is mutable state owned by ``backends.web.styles``. A
     compat re-export would copy the value, so resetting it on the shim would
     not reach the module that actually guards the emission.
"""
import pytest

pytest.importorskip("nicegui")

from uniui import web_components  # noqa: E402
from uniui.backends.web import runtime, styles  # noqa: E402


@pytest.fixture
def light_theme():
    previous = runtime.is_dark()
    web_components.set_admin_theme(False)
    yield
    web_components.set_admin_theme(previous)


class TestCompatibilityReExports:
    MOVED = [
        "WebAppShellAdapter",
        "WebBreadcrumbAdapter",
        "WebCardAdapter",
        "WebChartAdapter",
        "WebDrawerAdapter",
        "WebGaugeAdapter",
        "WebMetricListAdapter",
        "WebSidebarAdapter",
        "WebStatCardAdapter",
        "WebTableAdapter",
    ]

    def test_every_component_lives_in_its_own_module(self):
        from uniui.backends.web import components

        homes = {
            name: getattr(components, name).__module__ for name in self.MOVED
        }
        assert len(set(homes.values())) == len(self.MOVED), homes
        for name, module in homes.items():
            assert module.startswith("uniui.backends.web.components."), (name, module)

    @pytest.mark.parametrize("name", MOVED)
    def test_moved_component_is_still_importable_from_the_old_module(self, name):
        assert hasattr(web_components, name)

    @pytest.mark.parametrize("name", MOVED)
    def test_the_re_export_is_the_same_class_not_a_copy(self, name):
        from uniui.backends.web import components

        assert getattr(web_components, name) is getattr(components, name)

    @pytest.mark.parametrize(
        "name",
        [
            "get_palette", "is_dark", "set_theme",
            "get_admin_palette", "is_admin_dark", "set_admin_theme",
            "_M", "_native", "_clear", "_install_admin_css", "_shared_icon_css",
            "_shells", "_visuals",
        ],
    )
    def test_helper_names_survive_the_move(self, name):
        assert hasattr(web_components, name)

    def test_the_factory_still_builds_a_stat_card(self):
        from uniui.backends.web.components import WebStatCardAdapter

        factory = web_components.NiceGUIWidgetFactory()
        assert isinstance(factory.createStatCard(), WebStatCardAdapter)


class TestSelfRenderingVisualsAreTracked:
    """The gauge and chart paint the palette into their own SVG."""

    @pytest.mark.parametrize("factory_method", ["createGauge", "createChart"])
    def test_visual_is_registered(self, factory_method):
        factory = web_components.NiceGUIWidgetFactory()
        adapter = getattr(factory, factory_method)()
        assert adapter in runtime.VISUALS
        assert callable(getattr(adapter, "apply_theme", None))

    def test_the_shell_is_registered(self):
        shell = web_components.NiceGUIWidgetFactory().createAppShell()
        assert shell in runtime.SHELLS

    def test_a_gauge_restyles_on_a_theme_switch(self, light_theme):
        gauge = web_components.NiceGUIWidgetFactory().createGauge()
        gauge.set_value(42)
        light = gauge.get_native().content

        web_components.set_admin_theme(True)
        assert gauge.get_native().content != light, (
            "gauge kept its light-theme SVG; it is not being re-rendered"
        )

        web_components.set_admin_theme(False)
        assert gauge.get_native().content == light

    @pytest.mark.parametrize(
        "factory_method",
        [
            "createCard", "createStatCard", "createMetricList", "createTable",
            "createSidebar", "createAppShell", "createBreadcrumb",
            "createGauge", "createChart", "createDrawer",
        ],
    )
    def test_every_component_survives_a_theme_switch(self, factory_method, light_theme):
        factory = web_components.NiceGUIWidgetFactory()
        adapter = getattr(factory, factory_method)()
        web_components.set_admin_theme(True)
        web_components.set_admin_theme(False)
        assert adapter.get_native() is not None


class TestThemeTokens:
    def test_palette_changes(self, light_theme):
        light = runtime.get_palette()["text"]
        web_components.set_admin_theme(True)
        assert runtime.get_palette()["text"] != light

    def test_get_palette_returns_a_fresh_copy(self):
        palette = web_components.get_admin_palette()
        palette["text"] = "#000000"
        assert web_components.get_admin_palette()["text"] != "#000000"

    def test_the_shell_emits_metrics_as_css_variables(self):
        """Sizing comes from custom properties, not interpolated metrics - the
        shell writes them onto its own element."""
        shell = web_components.NiceGUIWidgetFactory().createAppShell()
        shell.apply_theme()
        style = shell.get_native()._style
        rendered = style if isinstance(style, str) else ";".join(
            f"{k}:{v}" for k, v in style.items()
        )
        assert "--uniui-header-height" in rendered
        assert "--uniui-bg" in rendered

    def test_metrics_are_shared(self):
        assert web_components._M is runtime.M


class TestCssInstallFlagOwnership:
    def test_the_flag_lives_on_the_styles_module(self):
        assert hasattr(styles, "_css_installed")

    def test_the_shim_does_not_shadow_the_flag(self):
        """A re-export here would copy the value at import time, so resetting
        it on the shim would silently fail to re-emit the CSS."""
        assert "_css_installed" not in vars(web_components)

    def test_resetting_the_flag_re_emits_the_css(self, monkeypatch):
        from nicegui import ui

        captured = []
        monkeypatch.setattr(ui, "add_css", lambda text, **kw: captured.append(text))
        monkeypatch.setattr(styles, "_css_installed", False)
        styles.install_admin_css()
        assert captured, "CSS was not re-emitted after the flag was reset"
        assert ".uniui-web-admin" in captured[0]

    def test_css_has_no_unresolved_placeholders(self, monkeypatch):
        """The web CSS block is a plain string; Jupyter's is an f-string."""
        from nicegui import ui

        captured = []
        monkeypatch.setattr(ui, "add_css", lambda text, **kw: captured.append(text))
        monkeypatch.setattr(styles, "_css_installed", False)
        styles.install_admin_css()
        assert "{_M[" not in captured[0]
        assert "{M[" not in captured[0]
