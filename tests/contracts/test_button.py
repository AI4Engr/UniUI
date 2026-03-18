"""
Contract Tests for Button Widget

These tests ensure that Button behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import WidgetContractTest
from uniui import BUTTON


class TestButtonContract(WidgetContractTest):
    """Contract tests for Button widget."""

    widget_kind = BUTTON

    def create_widget(self, factory):
        """Create button widget."""
        return factory.create_button()

    @pytest.mark.contract
    def test_set_get_text(self, factory):
        """Test set_text and get_text."""
        button = self.create_widget(factory)

        button.set_text("Click Me")
        assert button.get_text() == "Click Me"

        button.set_text("")
        assert button.get_text() == ""

    @pytest.mark.contract
    def test_text_normalization(self, factory):
        """Test that surrounding whitespace is normalized."""
        button = self.create_widget(factory)

        button.set_text("  Run  ")
        assert button.get_text() == "Run"

    @pytest.mark.contract
    def test_none_to_empty_string(self, factory):
        """Test that None becomes an empty label."""
        button = self.create_widget(factory)

        button.set_text(None)
        assert button.get_text() == ""

    @pytest.mark.contract
    def test_unicode_text(self, factory):
        """Test Unicode text handling."""
        button = self.create_widget(factory)

        button.set_text("提交 世界")
        assert button.get_text() == "提交 世界"

    @pytest.mark.contract
    def test_set_enabled(self, factory):
        """Test set_enabled and is_enabled when available."""
        button = self.create_widget(factory)

        button.set_enabled(True)
        assert button.is_enabled() is True

        button.set_enabled(False)
        assert button.is_enabled() is False

    @pytest.mark.contract
    def test_connect_callback(self, factory):
        """Test click callback registration."""
        button = self.create_widget(factory)
        called = []

        button.connect(lambda: called.append(1))
        native = button.get_native()

        native._callback()

        assert called == [1]
