"""
Contract Tests for LineEdit Widget

These tests ensure that LineEdit behaves consistently across all platforms.
"""
import pytest
from tests.contract_framework import (
    WidgetContractTest,
    ValueWidgetContractTest,
    VisibilityContractTest,
)
from uniui import LINE_EDIT
from uniui.core import InvalidValueError


class TestLineEditContract(
    ValueWidgetContractTest,
    VisibilityContractTest
):
    """Contract tests for LineEdit widget"""

    widget_kind = LINE_EDIT

    def create_widget(self, factory):
        """Create line edit widget"""
        return factory.create_line_edit()

    # Text capability tests
    @pytest.mark.contract
    def test_set_get_text(self, factory):
        """Test set_text and get_text"""
        line_edit = self.create_widget(factory)

        line_edit.set_text("Hello")
        assert line_edit.get_text() == "Hello"

        line_edit.set_text("")
        assert line_edit.get_text() == ""

    @pytest.mark.contract
    def test_text_whitespace(self, factory):
        """Test whitespace round-trips unchanged — LineEdit is an input field, not a display label."""
        line_edit = self.create_widget(factory)

        line_edit.set_text("  Hello World  ")
        assert "Hello World" in line_edit.get_text()

    # Value capability tests (inherited from ValueWidgetContractTest)
    # - test_empty_value
    # - test_float_value
    # - test_negative_value
    # - test_invalid_value_raises
    # - test_value_roundtrip

    @pytest.mark.contract
    def test_integer_value(self, factory):
        """Test integer value parsing"""
        line_edit = self.create_widget(factory)

        line_edit.set_text("42")
        value = line_edit.get_value()
        assert abs(value - 42.0) < 0.001

    @pytest.mark.contract
    def test_scientific_notation(self, factory):
        """Test scientific notation parsing"""
        line_edit = self.create_widget(factory)

        line_edit.set_text("1.5e3")
        value = line_edit.get_value()
        assert abs(value - 1500.0) < 0.001

    @pytest.mark.contract
    def test_zero_values(self, factory):
        """Test various zero representations"""
        line_edit = self.create_widget(factory)

        test_cases = ["0", "0.0", "0.00", "-0", "-0.0"]

        for text in test_cases:
            line_edit.set_text(text)
            value = line_edit.get_value()
            assert abs(value) < 0.001, f"'{text}' should parse to 0.0, got {value}"

    @pytest.mark.contract
    def test_leading_zeros(self, factory):
        """Test numbers with leading zeros"""
        line_edit = self.create_widget(factory)

        line_edit.set_text("007")
        value = line_edit.get_value()
        assert abs(value - 7.0) < 0.001

    @pytest.mark.contract
    def test_special_characters_invalid(self, factory):
        """Test that special characters raise InvalidValueError"""
        line_edit = self.create_widget(factory)

        invalid_inputs = ["abc", "12.34.56", "$100", "1,000"]

        for text in invalid_inputs:
            line_edit.set_text(text)
            with pytest.raises(InvalidValueError):
                line_edit.get_value()

    # Enable/disable tests
    @pytest.mark.contract
    def test_set_enabled(self, factory):
        """Test set_enabled and is_enabled"""
        line_edit = self.create_widget(factory)

        line_edit.set_enabled(True)
        assert line_edit.is_enabled() is True

        line_edit.set_enabled(False)
        assert line_edit.is_enabled() is False

    # Size tests
    @pytest.mark.contract
    def test_set_fixed_width(self, factory):
        """Test set_fixed_width"""
        line_edit = self.create_widget(factory)

        # Should not crash
        line_edit.set_fixed_width(200)
        line_edit.set_fixed_width(100)

    # Change event tests
    @pytest.mark.contract
    def test_on_change_callback(self, factory):
        """Test on_change event"""
        line_edit = self.create_widget(factory)
        called = []

        line_edit.on_change(lambda: called.append(1))

        # Change text programmatically
        line_edit.set_text("Hello")
        assert called, "expected on_change callback to fire"

    @pytest.mark.contract
    def test_on_change_dispose_stops_callback(self, factory):
        """Disposing the Handle returned by on_change() unregisters the callback."""
        line_edit = self.create_widget(factory)
        called = []

        handle = line_edit.on_change(lambda: called.append(1))
        line_edit.set_text("Hello")
        assert called == [1]

        handle.dispose()
        line_edit.set_text("World")
        assert called == [1]

    @pytest.mark.contract
    def test_on_change_callback_exception_does_not_propagate(self, factory):
        """A raising on_change callback must not stop sibling callbacks or crash set_text()."""
        line_edit = self.create_widget(factory)
        called = []

        def bad():
            raise ValueError("boom")

        line_edit.on_change(bad)
        line_edit.on_change(lambda: called.append(1))

        line_edit.set_text("Hello")  # must not raise
        assert called == [1]

    @pytest.mark.contract
    def test_set_leading_icon(self, factory):
        """set_leading_icon() must not raise on any backend (default no-op
        on backends without an icon slot, e.g. Jupyter)."""
        line_edit = self.create_widget(factory)
        line_edit.set_leading_icon("search")


class TestLineEditLeadingIconRendering:
    """Backend-specific assertions that set_leading_icon() actually renders
    something, not just that it's a silent no-op everywhere."""

    def test_qt_leading_icon_adds_a_real_action_with_a_non_null_icon(self):
        from tests.contract_framework import skip_unless_available
        skip_unless_available("qt")
        from uniui import create_factory

        line_edit = create_factory("qt").create_line_edit()
        line_edit.set_leading_icon("search")

        actions = line_edit.get_native().actions()
        assert actions, "expected addAction() to have registered a leading icon action"
        assert not actions[0].icon().isNull()

    def test_web_leading_icon_adds_a_prepend_slot_with_the_icon_class(self):
        from tests.contract_framework import skip_unless_available
        skip_unless_available("web")
        from uniui import create_factory

        line_edit = create_factory("web").create_line_edit()
        line_edit.set_leading_icon("search")

        native = line_edit.get_native()
        assert "prepend" in native.slots
        assert "uniui-icon-search" in native.slots["prepend"].template

    def test_qt_leading_icon_retints_automatically_on_theme_change(self):
        from tests.contract_framework import skip_unless_available
        skip_unless_available("qt")
        from uniui import create_factory, theme_runtime

        line_edit = create_factory("qt").create_line_edit()
        line_edit.set_leading_icon("search")

        theme_runtime.set_theme(False)
        try:
            action = line_edit.get_native().actions()[0]
            before = action.icon().pixmap(20, 20).toImage()
            before_px = [before.pixel(x, 10) for x in range(20)]

            theme_runtime.set_theme(True)
            action_after = line_edit.get_native().actions()[0]
            after = action_after.icon().pixmap(20, 20).toImage()
            after_px = [after.pixel(x, 10) for x in range(20)]

            assert before_px != after_px, (
                "leading icon color must change automatically on theme change"
            )
        finally:
            theme_runtime.set_theme(False)
