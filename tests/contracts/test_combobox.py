"""
Contract Tests for ComboBox Widget

These tests ensure that ComboBox behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import WidgetContractTest
from uniui import COMBO_BOX


class TestComboBoxContract(WidgetContractTest):
    """Contract tests for ComboBox widget."""

    widget_kind = COMBO_BOX

    def create_widget(self, factory):
        """Create combo box widget."""
        return factory.create_combo_box()

    @pytest.mark.contract
    def test_add_items_and_select(self, factory):
        """Test adding items and selecting a value."""
        combo_box = self.create_widget(factory)

        combo_box.add_item("Alpha")
        combo_box.add_item("Beta")
        combo_box.set_selection("Beta")

        assert combo_box.get_text() == "Beta"

    @pytest.mark.contract
    def test_clear_and_repopulate(self, factory):
        """Test clearing items and reusing the widget."""
        combo_box = self.create_widget(factory)

        combo_box.add_item("Old")
        combo_box.clear()
        combo_box.add_item("New")
        combo_box.set_selection("New")

        assert combo_box.get_text() == "New"

    @pytest.mark.contract
    def test_unicode_items(self, factory):
        """Test Unicode item handling."""
        combo_box = self.create_widget(factory)

        combo_box.add_item("简体中文")
        combo_box.add_item("Español")
        combo_box.set_selection("简体中文")

        assert combo_box.get_text() == "简体中文"

    @pytest.mark.contract
    def test_set_enabled(self, factory):
        """Test set_enabled and is_enabled."""
        combo_box = self.create_widget(factory)

        combo_box.set_enabled(True)
        assert combo_box.is_enabled() is True

        combo_box.set_enabled(False)
        assert combo_box.is_enabled() is False

    @pytest.mark.contract
    def test_on_change_callback(self, factory):
        """Test change callback registration."""
        combo_box = self.create_widget(factory)
        called = []

        combo_box.add_item("Alpha")
        combo_box.add_item("Beta")
        combo_box.on_change(lambda: called.append(1))

        # Trigger change via the adapter interface — backend-agnostic.
        # Qt fires the signal synchronously; Tk/wx go through their own paths.
        combo_box.set_selection("Beta")
        combo_box.set_selection("Alpha")

        # At least one change event must have fired.
        assert len(called) >= 1
