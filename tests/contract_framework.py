"""
Contract test base classes for UniUI widgets.

Provides reusable mixin classes that define the behavioral contract
every platform implementation must satisfy.
"""
import pytest
from uniui.core import InvalidValueError


class WidgetContractTest:
    """Base class for all widget contract tests.

    Subclasses must define:
        widget_kind: str  - the LABEL / LINE_EDIT / ... constant
        create_widget(factory) -> widget instance
    """

    widget_kind: str = ""

    def create_widget(self, factory):
        raise NotImplementedError

    @pytest.mark.contract
    def test_create_widget(self, factory):
        """Widget can be created without error"""
        widget = self.create_widget(factory)
        assert widget is not None

    @pytest.mark.contract
    def test_get_native(self, factory):
        """get_native() returns a non-None object"""
        widget = self.create_widget(factory)
        assert widget.get_native() is not None


class VisibilityContractTest(WidgetContractTest):
    """Contract for widgets that support show/hide."""

    @pytest.mark.contract
    def test_show_hide(self, factory):
        """show() and hide() must not raise"""
        widget = self.create_widget(factory)
        widget.show()
        widget.hide()
        widget.show()


class ValueWidgetContractTest(WidgetContractTest):
    """Contract for widgets that expose a numeric value via get_value()."""

    @pytest.mark.contract
    def test_empty_value(self, factory):
        """Empty text returns default (0.0)"""
        widget = self.create_widget(factory)
        widget.set_text("")
        value = widget.get_value()
        assert abs(value) < 0.001

    @pytest.mark.contract
    def test_float_value(self, factory):
        """Float text is parsed correctly"""
        widget = self.create_widget(factory)
        widget.set_text("3.14")
        value = widget.get_value()
        assert abs(value - 3.14) < 0.001

    @pytest.mark.contract
    def test_negative_value(self, factory):
        """Negative numbers are parsed correctly"""
        widget = self.create_widget(factory)
        widget.set_text("-42.5")
        value = widget.get_value()
        assert abs(value - (-42.5)) < 0.001

    @pytest.mark.contract
    def test_invalid_value_raises(self, factory):
        """Non-numeric text raises InvalidValueError"""
        widget = self.create_widget(factory)
        widget.set_text("not_a_number")
        with pytest.raises(InvalidValueError):
            widget.get_value()

    @pytest.mark.contract
    def test_value_roundtrip(self, factory):
        """set_value then get_value returns the same number"""
        widget = self.create_widget(factory)
        widget.set_value(99.9)
        value = widget.get_value()
        assert abs(value - 99.9) < 0.001
