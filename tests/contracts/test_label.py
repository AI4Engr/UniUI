"""
Contract Tests for Label Widget

These tests ensure that Label behaves consistently across all platforms.
"""
import pytest
from tests.contract_framework import (
    WidgetContractTest,
    VisibilityContractTest,
)
from uniui import LABEL


class TestLabelContract(VisibilityContractTest):
    """Contract tests for Label widget"""

    widget_kind = LABEL

    def create_widget(self, factory):
        """Create label widget"""
        return factory.create_label()

    @pytest.mark.contract
    def test_set_get_text(self, factory):
        """Test set_text and get_text"""
        label = self.create_widget(factory)

        label.set_text("Hello World")
        assert label.get_text() == "Hello World"

        label.set_text("")
        assert label.get_text() == ""

    @pytest.mark.contract
    def test_text_normalization(self, factory):
        """Test that text is normalized (whitespace trimmed)"""
        label = self.create_widget(factory)

        # Leading/trailing whitespace should be trimmed
        label.set_text("  Hello  ")
        assert label.get_text() == "Hello"

    @pytest.mark.contract
    def test_none_to_empty_string(self, factory):
        """Test that None becomes empty string"""
        label = self.create_widget(factory)

        label.set_text(None)
        assert label.get_text() == ""

    @pytest.mark.contract
    def test_set_fixed_width(self, factory):
        """Test set_fixed_width"""
        label = self.create_widget(factory)

        # Should not crash
        label.set_fixed_width(200)

    @pytest.mark.contract
    def test_unicode_text(self, factory):
        """Test Unicode text handling"""
        label = self.create_widget(factory)

        unicode_text = "Hello 世界 🌍"
        label.set_text(unicode_text)
        assert label.get_text() == unicode_text

    @pytest.mark.contract
    def test_long_text(self, factory):
        """Test handling of very long text"""
        label = self.create_widget(factory)

        long_text = "A" * 1000
        label.set_text(long_text)
        assert label.get_text() == long_text

    @pytest.mark.contract
    def test_multiline_text(self, factory):
        """Test text with newlines"""
        label = self.create_widget(factory)

        multiline = "Line 1\nLine 2\nLine 3"
        label.set_text(multiline)
        result = label.get_text()
        # Result should contain the text (may have normalization)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
