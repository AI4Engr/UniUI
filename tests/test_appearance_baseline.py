"""Appearance-regression safety net for the ``src`` refactor.

The normal suite exercises behaviour, not looks: every UI bug found in this
codebase so far (blank content area, unconstrained page width, light mode
rendering dark) passed a fully green test run. These tests pin the *emitted
style output* of each backend so a refactor that is behaviourally neutral but
visually destructive fails loudly.

The assertions are deliberately structural rather than exact-string: they check
that the declarations a rule is supposed to carry are still present. A pure
reformat of the stylesheet should not fail; a dropped rule must.

``docs/src-refactor-plan.md`` requires the refactor to preserve "current light/
dark themes and responsive behavior" - this module is how that is verified.
"""
import re

import pytest


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _decls(css: str, selector: str) -> str:
    """Return the concatenated declaration blocks for ``selector``.

    Matches the selector only when it appears as a complete selector in the
    comma-separated prelude, so ``.uniui-page`` does not match
    ``.uniui-page-header``.
    """
    out = []
    for prelude, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        parts = [p.strip() for p in prelude.split(",")]
        if any(p == selector or p.endswith(" " + selector) for p in parts):
            out.append(body)
    return " ".join(out)


def _norm(text: str) -> str:
    """Collapse whitespace so formatting changes do not break assertions."""
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------------
# Jupyter
# --------------------------------------------------------------------------

class TestJupyterAdminCss:
    """The Jupyter admin stylesheet must keep its layout-critical rules."""

    @pytest.fixture
    def css(self):
        widgets = pytest.importorskip("ipywidgets")  # noqa: F841
        from uniui import jupyter_components
        return jupyter_components._css()

    def test_page_fills_its_flex_parent(self, css):
        """The page root must size from its parent, not cap itself.

        Deliberately the opposite of the web backend: commit 75310ba removed
        ``max-width``/``margin:auto`` here because in the ipywidgets DOM that
        rule constrained shell sizing rather than centering the content. Width
        is bounded by the shell instead. ``test_jupyter_components`` asserts
        the same thing from the other direction - keep both in step.
        """
        decls = _norm(_decls(css, ".uniui-page")).replace(" ", "")
        assert "width:100%" in decls, "page no longer fills its parent"
        assert "max-width" not in decls, (
            "max-width reintroduced on the Jupyter page root; it constrains "
            "shell sizing (see commit 75310ba)"
        )

    def test_shell_body_is_a_flex_row(self, css):
        """The sidebar and content sit side by side; without this they stack."""
        decls = _norm(_decls(css, ".uniui-shell-body"))
        assert "display:flex" in decls.replace(" ", "")

    def test_admin_shell_defines_theme_variables(self, css):
        """Every ``var(--uniui-*)`` reference needs a definition on the shell.

        Catches a refactor that moves variable emission out from under the
        admin shell selector, which is what makes light mode render dark.
        """
        assert "--uniui-bg" in css
        assert "--uniui-text" in css

    def test_no_unresolved_fstring_placeholders(self, css):
        """``jupyter_components._css`` is an f-string; web's CSS is not.

        Moving a rule between the two backends without adjusting the quoting
        emits a literal ``{_M['...']}``. Cheap guard against a real mistake
        already made once during this work.
        """
        assert "{_M[" not in css
        assert "{_C[" not in css


class TestJupyterBaseCss:
    def test_base_css_defines_variables_and_is_wrapped(self):
        pytest.importorskip("ipywidgets")
        from uniui import jupyter_style
        css = jupyter_style.base_css()
        assert css.startswith("<style>") and css.endswith("</style>")
        assert "--uniui-bg" in css


class TestJupyterShellLayout:
    """Sizing that must stay inline on the widget, not in CSS.

    ipywidgets wraps every child in its own DOM node, so a CSS ``flex`` on a
    widget's class never reaches the element that is actually the flex item.
    The content box therefore collapsed to zero width and the page rendered
    blank. These attributes are the fix and must not be refactored into CSS.
    """

    @pytest.fixture
    def shell(self):
        pytest.importorskip("ipywidgets")
        from uniui import create_factory
        factory = create_factory("jupyter")
        shell = factory.create_app_shell()
        shell.set_sidebar(factory.create_sidebar())
        shell.set_content(factory.create_overlay())
        return shell

    def test_mounted_content_keeps_inline_flex_sizing(self, shell):
        """The mounted content must carry ``flex`` inline, not via CSS."""
        content = shell._content
        assert content is not None, "no content mounted"
        assert content.layout.flex == "1 1 0%", (
            "content lost its inline flex; it collapses to zero width"
        )

    def test_body_is_the_flex_row(self, shell):
        assert shell._body.layout.flex == "1 1 auto"

    def test_shell_reserves_minimum_height(self, shell):
        """Without a min-height the shell collapses in a notebook output cell."""
        assert shell.get_native().layout.min_height == "680px"


# --------------------------------------------------------------------------
# Qt
# --------------------------------------------------------------------------

class TestQtStyles:
    @pytest.fixture(autouse=True)
    def _qt(self):
        pytest.importorskip("PySide2")

    def test_component_qss_fragments_are_non_empty(self):
        from uniui import qt_components
        for name in ("_card_style", "_table_style", "_sidebar_style",
                     "_breadcrumb_button_style", "_scrollbar_rules"):
            fragment = getattr(qt_components, name)()
            assert fragment.strip(), f"{name}() produced no QSS"

    def test_base_stylesheet_is_non_empty(self):
        from uniui import qt_style
        assert qt_style.base_stylesheet().strip()

    def test_palette_differs_between_light_and_dark(self):
        """Regression: light mode rendered with the dark palette."""
        from uniui import qt_components
        qt_components.set_theme(False)
        light = dict(qt_components.get_palette())
        qt_components.set_theme(True)
        dark = dict(qt_components.get_palette())
        assert light != dark
        assert light["bg"] != dark["bg"]


# --------------------------------------------------------------------------
# Web
# --------------------------------------------------------------------------

class TestWebAdminCss:
    @pytest.fixture
    def css(self, monkeypatch):
        pytest.importorskip("nicegui")
        from nicegui import ui
        from uniui.backends.web import styles

        captured = []
        monkeypatch.setattr(
            ui, "add_css", lambda text, **kwargs: captured.append(text)
        )
        # The flag is owned by the styles module, not the compat shim - the CSS
        # is emitted once per process, so it must be reset where it lives.
        monkeypatch.setattr(styles, "_css_installed", False)
        styles.install_admin_css()
        assert captured, "no CSS was installed"
        return "\n".join(captured)

    def test_page_is_width_constrained(self, css):
        decls = _norm(_decls(css, ".uniui-page"))
        assert "max-width" in decls

    def test_admin_shell_rule_present(self, css):
        assert ".uniui-web-admin" in css

    def test_css_uses_theme_variables(self, css):
        assert "var(--uniui-" in css

    def test_no_unresolved_fstring_placeholders(self, css):
        """``web_components``' CSS block is a plain string, not an f-string."""
        assert "{_M[" not in css
        assert "{_C[" not in css
