"""Cross-backend behaviour parity for the shared adapter mixins.

The Qt and Jupyter adapters forward through _adapter_mixins, so the same
sequence of calls has to behave identically on both.  Emptying a selection
widget is covered explicitly: clearing options/children leaves ipywidgets with
no valid index, and the native wrappers used to force index 0, which raised
"Invalid selection: index out of bounds".
"""

import pytest


BACKENDS = ("qt", "jupyter")


def _factory(framework):
    if framework == "qt":
        pytest.importorskip("PySide2")
    else:
        pytest.importorskip("ipywidgets")

    import uniui

    uniui.use(framework)
    return uniui._get_factory()


@pytest.mark.parametrize("framework", BACKENDS)
def test_label_text_roundtrip_and_none_normalisation(framework):
    label = _factory(framework).create_label()

    label.set_text("hello")
    assert label.get_text() == "hello"

    label.set_text(None)
    assert label.get_text() == ""


@pytest.mark.parametrize("framework", BACKENDS)
def test_label_visibility_toggles(framework):
    label = _factory(framework).create_label()

    label.hide()
    assert label.is_visible() is False

    label.show()
    assert label.is_visible() is True


@pytest.mark.parametrize("framework", BACKENDS)
def test_button_text_and_enabled_state(framework):
    button = _factory(framework).create_button()

    button.set_text("Go")
    assert button.get_text() == "Go"

    button.set_enabled(False)
    assert button.is_enabled() is False

    button.set_enabled(True)
    assert button.is_enabled() is True


@pytest.mark.parametrize("framework", BACKENDS)
@pytest.mark.parametrize("maker", ("create_combo_box", "create_dropdown"))
def test_selection_widgets_survive_being_cleared(framework, maker):
    widget = getattr(_factory(framework), maker)()

    widget.add_item("A")
    widget.add_item("B")
    widget.set_selection("B")
    assert widget.get_text() == "B"

    widget.clear()  # used to raise TraitError on the Jupyter backend

    widget.add_item("X")
    widget.set_selection("X")
    assert widget.get_text() == "X"


@pytest.mark.parametrize("framework", BACKENDS)
def test_tabs_survive_being_emptied(framework):
    factory = _factory(framework)
    tabs = factory.create_tab_widget()

    tabs.add_tab(factory.create_label(), "One")
    tabs.add_tab(factory.create_label(), "Two")
    assert tabs.get_current_index() == 0

    tabs.remove_tabs()  # used to raise TraitError on the Jupyter backend

    tabs.add_tab(factory.create_label(), "Fresh")
