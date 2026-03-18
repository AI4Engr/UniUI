"""
Contract Tests for GroupBox Widget

These tests ensure that GroupBox behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import WidgetContractTest
from uniui import GROUP_BOX, Label, VBox


class TestGroupBoxContract(WidgetContractTest):
    """Contract tests for GroupBox widget."""

    widget_kind = GROUP_BOX

    def create_widget(self, factory):
        """Create group box widget."""
        return factory.create_group_box()

    @pytest.mark.contract
    def test_set_title(self, factory):
        """Test that titles can be updated."""
        group_box = self.create_widget(factory)

        group_box.set_title("Settings")
        group_box.set_title("")

    @pytest.mark.contract
    def test_set_title_none(self, factory):
        """Test that None titles are handled gracefully."""
        group_box = self.create_widget(factory)

        group_box.set_title(None)

    @pytest.mark.contract
    def test_set_layout(self, factory):
        """Test attaching a layout with child widgets."""
        group_box = self.create_widget(factory)

        group_box.set_layout(VBox(Label("Inside Group")))

    @pytest.mark.contract
    def test_replace_layout(self, factory):
        """Test replacing an existing layout."""
        group_box = self.create_widget(factory)

        group_box.set_layout(VBox(Label("First")))
        group_box.set_layout(VBox(Label("Second")))
