"""
Contract Tests for TabWidget

These tests ensure that TabWidget behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import VisibilityContractTest
from uniui import TAB_WIDGET, Label, VBox


class TestTabWidgetContract(VisibilityContractTest):
    """Contract tests for TabWidget."""

    widget_kind = TAB_WIDGET

    def create_widget(self, factory):
        """Create tab widget."""
        return factory.create_tab_widget()

    @pytest.mark.contract
    def test_add_first_tab_selects_valid_index(self, factory):
        """Test adding a first tab results in a valid active tab."""
        tab_widget = self.create_widget(factory)

        tab_widget.add_tab(Label("General"), "General")

        assert tab_widget.get_current_index() == 0

    @pytest.mark.contract
    def test_add_layout_tab(self, factory):
        """Test adding a layout-based tab."""
        tab_widget = self.create_widget(factory)

        tab_widget.add_tab(VBox(Label("Inside Layout")), "Layout")

        assert tab_widget.get_current_index() == 0

    @pytest.mark.contract
    def test_remove_tabs_allows_reuse(self, factory):
        """Test removing tabs and adding new ones again."""
        tab_widget = self.create_widget(factory)

        tab_widget.add_tab(Label("First"), "First")
        tab_widget.add_tab(Label("Second"), "Second")
        tab_widget.remove_tabs()
        tab_widget.add_tab(Label("Third"), "Third")

        assert tab_widget.get_current_index() == 0

    @pytest.mark.contract
    def test_multiple_tabs_have_valid_index(self, factory):
        """Test multiple tabs keep the current index in bounds."""
        tab_widget = self.create_widget(factory)

        tab_widget.add_tab(Label("One"), "One")
        tab_widget.add_tab(Label("Two"), "Two")

        assert tab_widget.get_current_index() in (0, 1)
