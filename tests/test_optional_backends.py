"""
Smoke tests for optional backends that may or may not be installed.

These tests exercise the core widget surface on Qt, wx, and Jupyter when the
dependencies are available in the current environment.
"""
import importlib

import pytest

from uniui import create_factory

BACKEND_MODULES = {
    "qt": "PySide2",
    "wx": "wx",
    "jupyter": "ipywidgets",
}


def backend_available(framework: str) -> bool:
    """Return whether the optional backend dependency is importable."""
    try:
        importlib.import_module(BACKEND_MODULES[framework])
    except ImportError:
        return False
    return True


@pytest.fixture(params=["qt", "wx", "jupyter"])
def optional_framework(request):
    """Yield each optional framework that is installed locally."""
    framework = request.param
    if not backend_available(framework):
        pytest.skip(f"{framework} backend dependency is not installed")
    return framework


def test_optional_backend_widget_smoke(optional_framework):
    """Create and exercise the core widget surface for optional backends."""
    factory = create_factory(optional_framework)

    label = factory.create_label()
    label.set_text("Label")
    assert label.get_text() == "Label"

    button = factory.create_button()
    button.set_text("Press")
    assert button.get_text() == "Press"
    button.set_enabled(False)
    assert button.is_enabled() is False

    line_edit = factory.create_line_edit()
    line_edit.set_text("12.5")
    assert abs(line_edit.get_value() - 12.5) < 0.001
    line_edit.set_enabled(True)
    assert line_edit.is_enabled() is True

    text_area = factory.create_text_area()
    text_area.set_text("Line 1")
    text_area.append("\nLine 2")
    assert "Line 2" in text_area.get_text()

    combo_box = factory.create_combo_box()
    combo_box.add_item("A")
    combo_box.add_item("B")
    combo_box.set_selection("B")
    assert combo_box.get_text() == "B"

    dropdown = factory.create_dropdown()
    dropdown.add_item("One")
    dropdown.add_item("Two")
    dropdown.set_selection("Two")
    assert dropdown.get_text() == "Two"

    vbox = factory.create_vbox()
    vbox.add_item(factory.create_label())
    group_box = factory.create_group_box()
    group_box.set_title("Settings")
    group_box.set_layout(vbox)

    tab_widget = factory.create_tab_widget()
    tab_widget.add_tab(factory.create_label(), "General")
    assert tab_widget.get_current_index() == 0

    image = factory.create_image()
    image.set_fixed_width(120)
