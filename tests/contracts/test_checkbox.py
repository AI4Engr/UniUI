"""
Contract Tests for Checkbox Widget

These tests ensure that Checkbox behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import CheckedWidgetContractTest, CommonCapabilitiesContractTest
from uniui import CHECKBOX


class TestCheckboxContract(CheckedWidgetContractTest, CommonCapabilitiesContractTest):
    """Contract tests for Checkbox widget."""

    widget_kind = CHECKBOX

    def create_widget(self, factory):
        """Create checkbox widget."""
        return factory.create_checkbox()
