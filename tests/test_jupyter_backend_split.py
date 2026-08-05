"""Structural guarantees for the Jupyter backend split.

Components moved from ``uniui.jupyter_components`` into
``uniui.backends.jupyter.components``. Three things about that move are easy to
break and produce no failure at the point of the mistake:

  1. ``jupyter_components`` must keep re-exporting what it used to define -
     ``jupyter_style`` imports ``get_admin_palette`` from it and
     ``examples/admin_demo.py`` imports the module as its admin backend.
  2. An adapter that renders theme colours itself must be registered via
     ``track_themed``. Unlike Qt there is no live palette dict to freeze here;
     the failure mode is subtler - the component keeps its old colours after a
     switch while everything around it updates.
  3. The CSS builder is an f-string, so a rule moved in from the web backend
     (whose CSS block is a plain string) silently emits a literal ``{M['...']}``.
"""
import pytest

pytest.importorskip("ipywidgets")

from uniui import jupyter_components  # noqa: E402
from uniui.backends.jupyter import runtime, styles  # noqa: E402


@pytest.fixture
def light_theme():
    """Run the test from a known theme and restore it afterwards."""
    previous = runtime.is_dark()
    jupyter_components.set_admin_theme(False)
    yield
    jupyter_components.set_admin_theme(previous)


class TestCompatibilityReExports:
    MOVED = [
        "JupyterAppShellAdapter",
        "JupyterBreadcrumbAdapter",
        "JupyterCardAdapter",
        "JupyterChartAdapter",
        "JupyterDrawerAdapter",
        "JupyterGaugeAdapter",
        "JupyterMetricListAdapter",
        "JupyterSidebarAdapter",
        "JupyterStatCardAdapter",
        "JupyterTableAdapter",
    ]

    def test_every_component_lives_in_its_own_module(self):
        """One component per module, not a second monolith."""
        from uniui.backends.jupyter import components

        homes = {
            name: getattr(components, name).__module__ for name in self.MOVED
        }
        assert len(set(homes.values())) == len(self.MOVED), homes
        for name, module in homes.items():
            assert module.startswith("uniui.backends.jupyter.components."), (
                name, module,
            )

    @pytest.mark.parametrize("name", MOVED)
    def test_moved_component_is_still_importable_from_the_old_module(self, name):
        assert hasattr(jupyter_components, name)

    @pytest.mark.parametrize("name", MOVED)
    def test_the_re_export_is_the_same_class_not_a_copy(self, name):
        from uniui.backends.jupyter import components

        assert getattr(jupyter_components, name) is getattr(components, name)

    @pytest.mark.parametrize(
        "name",
        [
            "get_palette", "is_dark", "set_theme",
            "get_admin_palette", "is_admin_dark", "set_admin_theme",
            "_css", "_M", "_html", "_native", "_SPLITTER_HTML",
            "_DEBUG_MEASURE_JS", "_debug_html", "_shared_icon_css",
        ],
    )
    def test_helper_names_survive_the_move(self, name):
        """``jupyter_style`` and the appearance tests reach for these, so they
        are load-bearing despite the underscore."""
        assert hasattr(jupyter_components, name)

    def test_the_factory_still_builds_a_stat_card(self):
        from uniui.backends.jupyter.components import JupyterStatCardAdapter

        factory = jupyter_components.JupyterWidgetFactory()
        assert isinstance(factory.createStatCard(), JupyterStatCardAdapter)

    def test_jupyter_style_can_still_import_the_palette(self):
        """The import that would break first on a circular-import mistake:
        jupyter_style -> jupyter_components -> backends.jupyter.runtime, while
        runtime imports jupyter_style lazily inside sync_palette."""
        from uniui import jupyter_style

        assert jupyter_style.get_admin_palette() is not None
        assert "--uniui-bg" in jupyter_style.base_css()


class TestThemeSwitchReachesEveryModule:
    def test_palette_changes(self, light_theme):
        light = runtime.get_palette()["text"]
        jupyter_components.set_admin_theme(True)
        assert runtime.get_palette()["text"] != light

    def test_get_palette_returns_a_fresh_copy(self):
        """Callers must not be able to corrupt the palette for everyone else."""
        palette = jupyter_components.get_admin_palette()
        palette["text"] = "#000000"
        assert jupyter_components.get_admin_palette()["text"] != "#000000"

    def test_the_stylesheet_follows_the_theme(self, light_theme):
        light_css = styles.css()
        jupyter_components.set_admin_theme(True)
        assert styles.css() != light_css
        assert runtime.get_palette()["bg"] in styles.css()

    def test_a_moved_component_restyles(self, light_theme):
        """The gauge renders colours into its own SVG, so it has to re-render
        rather than rely on the stylesheet."""
        gauge = jupyter_components.JupyterGaugeAdapter()
        gauge.set_value(42)
        light_svg = gauge.get_native().value

        jupyter_components.set_admin_theme(True)
        assert gauge.get_native().value != light_svg

        jupyter_components.set_admin_theme(False)
        assert gauge.get_native().value == light_svg

    @pytest.mark.parametrize(
        "factory_method",
        [
            "createCard", "createStatCard", "createMetricList", "createTable",
            "createSidebar", "createAppShell", "createBreadcrumb",
            "createGauge", "createChart", "createDrawer",
        ],
    )
    def test_every_component_survives_a_theme_switch(self, factory_method, light_theme):
        factory = jupyter_components.JupyterWidgetFactory()
        adapter = getattr(factory, factory_method)()
        jupyter_components.set_admin_theme(True)
        jupyter_components.set_admin_theme(False)
        assert adapter.get_native() is not None

    @pytest.mark.parametrize(
        "factory_method", ["createGauge", "createChart", "createAppShell"],
    )
    def test_self_rendering_components_are_tracked_for_refresh(self, factory_method):
        """These three paint theme colours themselves. Forgetting
        ``track_themed`` during a move leaves them stale after a switch."""
        factory = jupyter_components.JupyterWidgetFactory()
        adapter = getattr(factory, factory_method)()
        assert adapter in runtime.THEME_TARGETS
        assert callable(getattr(adapter, "apply_theme", None))

    def test_the_shell_restyles_itself(self, light_theme):
        shell = jupyter_components.JupyterAppShellAdapter()
        light = shell._style.value
        jupyter_components.set_admin_theme(True)
        assert shell._style.value != light


class TestStylesModuleOutput:
    def test_css_has_no_unresolved_placeholders(self):
        """``styles.css`` is an f-string; the web backend's is not."""
        css = styles.css()
        assert "{M[" not in css
        assert "{_M[" not in css

    def test_the_shim_exposes_the_same_builder(self):
        assert jupyter_components._css is styles.css

    def test_metrics_are_shared(self):
        assert jupyter_components._M is runtime.M


class TestBaseControlScopes:
    """One builder emits the stock-control rules for both Jupyter scopes.

    The two scopes are not interchangeable, and the difference is invisible in
    a rendered notebook until a control silently loses its styling - so it is
    pinned here rather than left to review.
    """

    def test_the_admin_scope_only_matches_descendants(self):
        """``.uniui-admin-shell`` sits on a container, so a self-matching
        selector like ``.uniui-admin-shell.widget-text`` can never match."""
        rules = styles.base_control_rules(".uniui-admin-shell", nested=True)
        assert ".uniui-admin-shell.widget" not in rules
        assert ".uniui-admin-shell .widget-text input" in rules

    def test_the_widget_scope_also_matches_the_element_itself(self):
        """The factory marks each widget, so ``.uniui-widget`` lands *on* the
        control for flat widgets and on an ancestor for nested ones. Emitting
        only the descendant form leaves flat controls unstyled."""
        rules = styles.base_control_rules(".uniui-widget", nested=False)
        assert ".uniui-widget.widget-text input" in rules
        assert ".uniui-widget .widget-text input" in rules

    def test_labels_stay_descendant_only_in_both_scopes(self):
        """A label is always a child node, never the marked widget."""
        for scope, nested in ((".uniui-admin-shell", True), (".uniui-widget", False)):
            rules = styles.base_control_rules(scope, nested=nested)
            assert f"{scope} .widget-label" in rules
            assert f"{scope}.widget-label" not in rules

    def test_only_the_admin_scope_paints_the_button_wrapper(self):
        """Widening this to the plain scope would restyle every stock button
        in a notebook, not just UniUI's."""
        admin = styles.base_control_rules(".uniui-admin-shell", nested=True)
        widget = styles.base_control_rules(".uniui-widget", nested=False)
        assert ".uniui-admin-shell .widget-button,\n" in admin
        assert ".uniui-widget .widget-button button" in widget
        # The wrapper must not appear as a selector in its own right - check
        # every selector line, since a stray one hides inside a comma list.
        selectors = [
            line.rstrip(",{ ").strip()
            for line in widget.splitlines()
            if line.strip().startswith(".uniui-widget")
        ]
        assert ".uniui-widget .widget-button" not in selectors
        assert ".uniui-widget.widget-button" not in selectors

    def test_both_stylesheets_use_the_shared_builder(self):
        """Guards against a future edit re-inlining one copy and letting the
        two scopes drift apart again."""
        from uniui import jupyter_style

        assert styles.base_control_rules(".uniui-widget", nested=False) in (
            jupyter_style._BASE_RULES
        )
        assert styles.base_control_rules(".uniui-admin-shell", nested=True) in styles.css()
