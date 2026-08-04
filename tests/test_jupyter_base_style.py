"""Jupyter counterpart of test_qt_base_style.

jupyter_components scopes its CSS under ``.uniui-admin-shell`` and only injects it
from the AppShell, so plain controls were unstyled in notebooks that build no
shell.  jupyter_style publishes an equivalent rule set scoped to the
``.uniui-widget`` marker class the factory applies to everything it creates.
"""

import pytest


pytestmark = pytest.mark.jupyter


def test_factory_marks_every_widget_it_creates():
    pytest.importorskip("ipywidgets")
    import uniui
    from uniui.jupyter_style import WIDGET_CLASS

    uniui.use("jupyter")
    factory = uniui._get_factory()

    for name in (
        "create_dropdown",
        "create_combo_box",
        "create_tab_widget",
        "create_button",
        "create_line_edit",
        "create_label",
    ):
        native = getattr(factory, name)().get_native()
        assert WIDGET_CLASS in native._dom_classes, f"{name} is unreachable by CSS"


def test_base_css_covers_the_selection_controls():
    pytest.importorskip("ipywidgets")
    from uniui.jupyter_style import base_css

    css = base_css()
    for fragment in ("widget-dropdown", "widget-combobox", "widget-tab", "--uniui-accent"):
        assert fragment in css


def test_style_node_follows_the_admin_theme():
    pytest.importorskip("ipywidgets")
    from uniui.jupyter_components import set_admin_theme
    from uniui.jupyter_style import style_widget_html

    node = style_widget_html()
    try:
        set_admin_theme(False)
        light = node.value
        set_admin_theme(True)

        assert node.value != light, "live stylesheet did not follow the theme"
    finally:
        set_admin_theme(False)
