"""
Contract Tests for Slider Widget

These tests ensure that Slider behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import CommonCapabilitiesContractTest
from uniui import SLIDER


class TestSliderContract(CommonCapabilitiesContractTest):
    """Contract tests for Slider widget."""

    widget_kind = SLIDER

    def create_widget(self, factory):
        """Create slider widget."""
        return factory.create_slider()

    @pytest.mark.contract
    def test_set_value_roundtrip(self, factory):
        slider = self.create_widget(factory)
        slider.set_range(0, 100)
        slider.set_value(42)
        assert slider.get_value() == 42

    @pytest.mark.contract
    def test_set_range_clamps_out_of_range_value(self, factory):
        slider = self.create_widget(factory)
        slider.set_range(0, 10)
        slider.set_value(5)
        slider.set_range(0, 3)
        assert slider.get_value() <= 3

    @pytest.mark.contract
    def test_set_step_does_not_raise(self, factory):
        slider = self.create_widget(factory)
        slider.set_step(0.5)

    @pytest.mark.contract
    def test_fractional_step_value_roundtrip(self, factory):
        slider = self.create_widget(factory)
        slider.set_range(0, 10)
        slider.set_step(0.5)
        slider.set_value(7.5)
        assert abs(slider.get_value() - 7.5) < 0.01

    @pytest.mark.contract
    def test_on_change_callback(self, factory):
        slider = self.create_widget(factory)
        slider.set_range(0, 100)
        called = []
        slider.on_change(lambda: called.append(1))

        slider.set_value(10)
        slider.set_value(20)

        assert len(called) >= 1

    @pytest.mark.contract
    def test_on_change_dispose_stops_callback(self, factory):
        slider = self.create_widget(factory)
        slider.set_range(0, 100)
        called = []
        handle = slider.on_change(lambda: called.append(1))
        handle.dispose()

        slider.set_value(10)

        assert called == []
