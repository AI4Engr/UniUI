"""
Contract Tests for NumberInput Widget

These tests ensure that NumberInput behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import CommonCapabilitiesContractTest
from uniui import NUMBER_INPUT


class TestNumberInputContract(CommonCapabilitiesContractTest):
    """Contract tests for NumberInput widget."""

    widget_kind = NUMBER_INPUT

    def create_widget(self, factory):
        """Create number input widget."""
        return factory.create_number_input()

    @pytest.mark.contract
    def test_set_value_roundtrip(self, factory):
        number_input = self.create_widget(factory)
        number_input.set_range(0, 100)
        number_input.set_value(42)
        assert number_input.get_value() == 42

    @pytest.mark.contract
    def test_set_range_clamps_out_of_range_value(self, factory):
        number_input = self.create_widget(factory)
        number_input.set_range(0, 10)
        number_input.set_value(5)
        number_input.set_range(0, 3)
        assert number_input.get_value() <= 3

    @pytest.mark.contract
    def test_set_step_does_not_raise(self, factory):
        number_input = self.create_widget(factory)
        number_input.set_step(0.5)

    @pytest.mark.contract
    def test_on_change_callback(self, factory):
        number_input = self.create_widget(factory)
        number_input.set_range(0, 100)
        called = []
        number_input.on_change(lambda: called.append(1))

        number_input.set_value(10)
        number_input.set_value(20)

        assert len(called) >= 1

    @pytest.mark.contract
    def test_on_change_dispose_stops_callback(self, factory):
        number_input = self.create_widget(factory)
        number_input.set_range(0, 100)
        called = []
        handle = number_input.on_change(lambda: called.append(1))
        handle.dispose()

        number_input.set_value(10)

        assert called == []
