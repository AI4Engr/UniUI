"""
Contract Tests for Dropdown Widget

These tests ensure that Dropdown behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import VisibilityContractTest
from uniui import DROPDOWN


class TestDropdownContract(VisibilityContractTest):
    """Contract tests for Dropdown widget."""

    widget_kind = DROPDOWN

    def create_widget(self, factory):
        """Create dropdown widget."""
        return factory.create_dropdown()

    @pytest.mark.contract
    def test_add_items_and_select(self, factory):
        """Test adding items and reading the selected value."""
        dropdown = self.create_widget(factory)

        dropdown.add_item("Alpha")
        dropdown.add_item("Beta")
        dropdown.set_selection("Beta")

        assert dropdown.get_text() == "Beta"

    @pytest.mark.contract
    def test_clear_and_repopulate(self, factory):
        """Test clearing items and reusing the widget."""
        dropdown = self.create_widget(factory)

        dropdown.add_item("Old")
        dropdown.clear()
        dropdown.add_item("New")
        dropdown.set_selection("New")

        assert dropdown.get_text() == "New"

    @pytest.mark.contract
    def test_unicode_items(self, factory):
        """Test Unicode item handling."""
        dropdown = self.create_widget(factory)

        dropdown.add_item("简体中文")
        dropdown.add_item("Español")
        dropdown.set_selection("Español")

        assert dropdown.get_text() == "Español"

    @pytest.mark.contract
    def test_set_enabled(self, factory):
        """Test set_enabled and is_enabled."""
        dropdown = self.create_widget(factory)

        dropdown.set_enabled(True)
        assert dropdown.is_enabled() is True

        dropdown.set_enabled(False)
        assert dropdown.is_enabled() is False

    @pytest.mark.contract
    def test_on_change_callback(self, factory):
        """Test change callback registration."""
        dropdown = self.create_widget(factory)
        called = []

        dropdown.add_item("Alpha")
        dropdown.add_item("Beta")
        dropdown.on_change(lambda: called.append(1))
        native = dropdown.get_native()
        dropdown.set_selection("Beta")
        native.event_generate("<<ComboboxSelected>>")

        assert called == [1]
