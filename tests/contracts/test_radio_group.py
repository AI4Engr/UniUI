"""
Contract Tests for RadioGroup Widget

These tests ensure that RadioGroup behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import CommonCapabilitiesContractTest
from uniui import RADIO_GROUP


class TestRadioGroupContract(CommonCapabilitiesContractTest):
    """Contract tests for RadioGroup widget."""

    widget_kind = RADIO_GROUP

    def create_widget(self, factory):
        """Create radio group widget."""
        return factory.create_radio_group()

    @pytest.mark.contract
    def test_set_options_selects_the_first_one(self, factory):
        radio_group = self.create_widget(factory)
        radio_group.set_options(["Small", "Medium", "Large"])
        assert radio_group.get_selected() == "Small"

    @pytest.mark.contract
    def test_set_selected_roundtrip(self, factory):
        radio_group = self.create_widget(factory)
        radio_group.set_options(["Small", "Medium", "Large"])
        radio_group.set_selected("Large")
        assert radio_group.get_selected() == "Large"

    @pytest.mark.contract
    def test_set_options_replaces_previous_options(self, factory):
        radio_group = self.create_widget(factory)
        radio_group.set_options(["Old"])
        radio_group.set_options(["New", "Newer"])
        assert radio_group.get_selected() == "New"

    @pytest.mark.contract
    def test_on_change_callback(self, factory):
        radio_group = self.create_widget(factory)
        radio_group.set_options(["A", "B", "C"])
        called = []
        radio_group.on_change(lambda: called.append(1))

        radio_group.set_selected("B")
        radio_group.set_selected("C")

        assert len(called) >= 1

    @pytest.mark.contract
    def test_on_change_dispose_stops_callback(self, factory):
        radio_group = self.create_widget(factory)
        radio_group.set_options(["A", "B"])
        called = []
        handle = radio_group.on_change(lambda: called.append(1))
        handle.dispose()

        radio_group.set_selected("B")

        assert called == []
