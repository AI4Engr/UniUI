"""
Contract Tests for Switch Widget

These tests ensure that Switch behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import CheckedWidgetContractTest, CommonCapabilitiesContractTest
from uniui import SWITCH


class TestSwitchContract(CheckedWidgetContractTest, CommonCapabilitiesContractTest):
    """Contract tests for Switch widget."""

    widget_kind = SWITCH

    def create_widget(self, factory):
        """Create switch widget."""
        return factory.create_switch()
