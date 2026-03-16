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
        """Test whitespace handling in text"""
        line_edit = self.create_widget(factory)

        line_edit.set_text("  Hello World  ")
        # Whitespace should be trimmed
        assert line_edit.get_text() == "Hello World"

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
    @pytest.mark.skip("Event testing requires platform-specific triggers")
    def test_on_change_callback(self, factory):
        """Test on_change event"""
        line_edit = self.create_widget(factory)
        called = []

        line_edit.on_change(lambda: called.append(1))

        # Change text programmatically
        line_edit.set_text("Hello")

        # Note: Programmatic changes may not trigger events on all platforms
        # This test may need platform-specific implementation
