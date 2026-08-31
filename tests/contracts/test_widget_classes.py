"""
Contract tests for IWidget.add_class() / remove_class().

Tagging a widget with a semantic class name is a uniform IWidget capability
(see notes/add_class_design_plan.md) backed per-backend by:
  - Web: real DOM classes via NiceGUI's element.classes(add=/remove=)
  - Jupyter: real DOM classes via ipywidgets' own add_class/remove_class
  - Qt: a boolean dynamic property + QSS attribute selector ([name="true"]),
    repolished via unpolish()/polish() so an already-applied stylesheet
    picks up the change immediately

VBox/HBox/Grid are a deliberate exception to the "raise NotSupportedError"
convention used for show/hide/set_enabled/sizing on those three: unlike
those, a CSS-style class is NOT universally meaningless on a layout-only
native - Web's and Jupyter's VBox/HBox/Grid are real DOM/ipywidgets
elements that can carry a class same as any other widget, and
admin_demo.py's uniui-demo-page/uniui-demo-heading classes are genuinely
load-bearing there. Only Qt's native is a bare QLayout with nothing to
tag, so it falls through to IWidget's inherited no-op rather than raising.
"""
import pytest

from tests.contract_framework import WidgetContractTest, skip_unless_available
from uniui import LABEL


class TestLabelClassContract(WidgetContractTest):
    """add_class/remove_class on a representative primitive, across all
    three backends via the existing `factory` fixture parametrization."""

    widget_kind = LABEL

    def create_widget(self, factory):
        return factory.create_label()

    @pytest.mark.contract
    def test_add_class_does_not_raise(self, factory):
        label = self.create_widget(factory)
        label.add_class("uniui-demo-subtitle")

    @pytest.mark.contract
    def test_remove_class_does_not_raise(self, factory):
        label = self.create_widget(factory)
        label.add_class("uniui-demo-subtitle")
        label.remove_class("uniui-demo-subtitle")

    @pytest.mark.contract
    def test_remove_class_without_prior_add_does_not_raise(self, factory):
        """remove_class() on a class that was never added must be a no-op,
        not an error - every backend's underlying mechanism (NiceGUI
        classes(remove=...), ipywidgets remove_class, Qt setProperty(False))
        tolerates removing an absent class."""
        label = self.create_widget(factory)
        label.remove_class("never-added")

    @pytest.mark.contract
    def test_multiple_classes_coexist(self, factory):
        """Tagging the same widget with two classes must not collide -
        each is independent, same as a real multi-class CSS element."""
        label = self.create_widget(factory)
        label.add_class("uniui-class-a")
        label.add_class("uniui-class-b")
        label.remove_class("uniui-class-a")
        label.remove_class("uniui-class-b")


class TestQtClassMixinNative:
    """Qt-specific: the dynamic property actually reflects add_class/
    remove_class calls, so a QSS attribute selector has something to match
    against."""

    def test_add_class_sets_boolean_property_true(self):
        skip_unless_available("qt")
        from uniui import create_factory

        label = create_factory("qt").create_label()
        native = label.get_native()
        label.add_class("uniui-demo-subtitle")
        assert native.property("uniui-demo-subtitle") is True

    def test_remove_class_sets_boolean_property_false(self):
        skip_unless_available("qt")
        from uniui import create_factory

        label = create_factory("qt").create_label()
        native = label.get_native()
        label.add_class("uniui-demo-subtitle")
        label.remove_class("uniui-demo-subtitle")
        assert native.property("uniui-demo-subtitle") is False

    def test_multiple_classes_are_independent_properties(self):
        skip_unless_available("qt")
        from uniui import create_factory

        label = create_factory("qt").create_label()
        native = label.get_native()
        label.add_class("uniui-class-a")
        label.add_class("uniui-class-b")
        assert native.property("uniui-class-a") is True
        assert native.property("uniui-class-b") is True
        label.remove_class("uniui-class-a")
        assert native.property("uniui-class-a") is False
        assert native.property("uniui-class-b") is True

    def test_qss_attribute_selector_round_trip(self):
        """Manual Qt QSS round-trip: tag a real QtLabelAdapter, apply a
        stylesheet matching the class, assert the visual property (font
        size/weight) actually changed - not just that the property was set.

        Polishes the widget *before* calling add_class, matching the real
        "late-tagging" scenario the design plan calls out: a dynamic
        property set after the widget is already polished doesn't
        retroactively match QSS attribute selectors without an explicit
        unpolish()/polish() - without forcing that initial polish first,
        this test can't tell "add_class's repolish works" apart from "the
        widget just happened to polish for the first time on its own"."""
        skip_unless_available("qt")
        from PySide2 import QtWidgets
        from uniui import create_factory

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        label = create_factory("qt").create_label()
        native = label.get_native()
        native.setStyleSheet(
            'QLabel[uniui-demo-subtitle="true"] { font-size: 30pt; font-weight: 700; }'
        )
        native.ensurePolished()  # force the initial polish before tagging
        before = native.font().bold()
        label.add_class("uniui-demo-subtitle")
        native.ensurePolished()
        assert before is False
        assert native.font().bold() is True

    def test_qss_attribute_selector_removal_round_trip(self):
        """The inverse: removing the class must retroactively stop matching
        the QSS rule too, not just adding it."""
        skip_unless_available("qt")
        from PySide2 import QtWidgets
        from uniui import create_factory

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        label = create_factory("qt").create_label()
        native = label.get_native()
        native.setStyleSheet(
            'QLabel[uniui-demo-subtitle="true"] { font-size: 30pt; font-weight: 700; }'
        )
        label.add_class("uniui-demo-subtitle")
        native.ensurePolished()
        assert native.font().bold() is True
        label.remove_class("uniui-demo-subtitle")
        native.ensurePolished()
        assert native.font().bold() is False


class TestWebAndJupyterClassNative:
    """Web/Jupyter-specific: add_class/remove_class reach the real DOM/
    ipywidgets class list, unlike Qt's dynamic-property bridge."""

    def test_web_add_class_reaches_nicegui_classes(self):
        skip_unless_available("web")
        from uniui import create_factory

        label = create_factory("web").create_label()
        native = label.get_native()
        label.add_class("uniui-demo-subtitle")
        assert "uniui-demo-subtitle" in native._classes
        label.remove_class("uniui-demo-subtitle")
        assert "uniui-demo-subtitle" not in native._classes

    def test_jupyter_add_class_reaches_dom_classes(self):
        skip_unless_available("jupyter")
        from uniui import create_factory

        label = create_factory("jupyter").create_label()
        native = label.get_native()
        label.add_class("uniui-demo-subtitle")
        assert "uniui-demo-subtitle" in native._dom_classes
        label.remove_class("uniui-demo-subtitle")
        assert "uniui-demo-subtitle" not in native._dom_classes


class TestLayoutOnlyClassBehavior:
    """VBox/HBox/Grid: Qt's bare-QLayout native has no add_class/remove_class
    surface at all, so it inherits IWidget's silent no-op - it must NOT
    raise NotSupportedError, unlike show/hide/set_enabled/sizing on the same
    three interfaces (see test_layout.py for those). Web and Jupyter, whose
    VBox/HBox/Grid wrap a real DOM/ipywidgets element, get a fully working
    implementation instead.
    """

    def test_qt_vbox_add_class_does_not_raise(self):
        skip_unless_available("qt")
        from uniui import create_factory

        vbox = create_factory("qt").create_vbox()
        vbox.add_class("uniui-demo-page")  # must not raise
        vbox.remove_class("uniui-demo-page")  # must not raise

    def test_qt_hbox_add_class_does_not_raise(self):
        skip_unless_available("qt")
        from uniui import create_factory

        hbox = create_factory("qt").create_hbox()
        hbox.add_class("uniui-demo-heading")  # must not raise
        hbox.remove_class("uniui-demo-heading")  # must not raise

    def test_qt_grid_add_class_does_not_raise(self):
        skip_unless_available("qt")
        from uniui import create_factory

        grid = create_factory("qt").create_grid()
        grid.add_class("some-class")  # must not raise
        grid.remove_class("some-class")  # must not raise

    def test_qt_vbox_add_class_is_a_true_no_op(self):
        """Not just "doesn't raise" - confirm it has no side effect either,
        since QVBoxLayout has no .style()/paintable surface to tag."""
        skip_unless_available("qt")
        from uniui import create_factory

        vbox = create_factory("qt").create_vbox()
        native = vbox.get_native()
        assert not hasattr(native, "setProperty") or native.property("x") in (None, False)
        vbox.add_class("x")
        # QLayout (a QObject) does still technically have setProperty, but
        # IWidget's inherited no-op never calls it - confirm no property
        # was set as a side effect of add_class going through the real Qt
        # bridge instead of the no-op.
        assert native.property("x") in (None, False)

    def test_qt_vbox_still_raises_for_show(self):
        """Contrast case: show()/hide()/set_enabled()/sizing on the exact
        same QtVBoxAdapter still raise NotSupportedError as before - only
        add_class/remove_class got the exception carved out."""
        skip_unless_available("qt")
        from uniui import create_factory
        from uniui.contracts.exceptions import NotSupportedError

        vbox = create_factory("qt").create_vbox()
        with pytest.raises(NotSupportedError):
            vbox.show()

    def test_web_vbox_add_class_reaches_real_dom_class(self):
        skip_unless_available("web")
        from uniui import create_factory

        vbox = create_factory("web").create_vbox()
        native = vbox.get_native()
        vbox.add_class("uniui-demo-page")
        assert "uniui-demo-page" in native._classes

    def test_jupyter_vbox_add_class_reaches_real_dom_class(self):
        skip_unless_available("jupyter")
        from uniui import create_factory

        vbox = create_factory("jupyter").create_vbox()
        native = vbox.get_native()
        vbox.add_class("uniui-demo-page")
        assert "uniui-demo-page" in native._dom_classes
