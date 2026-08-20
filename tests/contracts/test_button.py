"""
Contract Tests for Button Widget

These tests ensure that Button behaves consistently across all platforms.
"""
import pytest

from tests.contract_framework import CommonCapabilitiesContractTest
from uniui import BUTTON


class TestButtonContract(CommonCapabilitiesContractTest):
    """Contract tests for Button widget."""

    widget_kind = BUTTON

    def create_widget(self, factory):
        """Create button widget."""
        return factory.create_button()

    @pytest.mark.contract
    def test_set_get_text(self, factory):
        """Test set_text and get_text."""
        button = self.create_widget(factory)

        button.set_text("Click Me")
        assert button.get_text() == "Click Me"

        button.set_text("")
        assert button.get_text() == ""

    @pytest.mark.contract
    def test_text_normalization(self, factory):
        """Test that surrounding whitespace is normalized."""
        button = self.create_widget(factory)

        button.set_text("  Run  ")
        assert button.get_text() == "Run"

    @pytest.mark.contract
    def test_none_to_empty_string(self, factory):
        """Test that None becomes an empty label."""
        button = self.create_widget(factory)

        button.set_text(None)
        assert button.get_text() == ""

    @pytest.mark.contract
    def test_unicode_text(self, factory):
        """Test Unicode text handling."""
        button = self.create_widget(factory)

        button.set_text("提交 世界")
        assert button.get_text() == "提交 世界"

    @pytest.mark.contract
    def test_set_enabled(self, factory):
        """Test set_enabled and is_enabled when available."""
        button = self.create_widget(factory)

        button.set_enabled(True)
        assert button.is_enabled() is True

        button.set_enabled(False)
        assert button.is_enabled() is False

    @pytest.mark.contract
    def test_connect_callback(self, factory):
        """Test click callback registration."""
        button = self.create_widget(factory)
        called = []

        button.connect(lambda: called.append(1))

        # Trigger via the native widget's click mechanism, backend-agnostically.
        native = button.get_native()
        if hasattr(native, "animateClick"):
            native.animateClick(0)
        elif hasattr(native, "_callback") and callable(native._callback):
            native._callback()
        elif hasattr(native, "click") and callable(native.click):
            native.click()  # ipywidgets Button: calls registered handlers as handler(self)
        else:
            pytest.skip("Cannot trigger click on this backend's native widget")

        assert called == [1]

    @pytest.mark.contract
    def test_connect_dispose_stops_callback(self, factory):
        """Disposing the Handle returned by connect() unregisters the callback."""
        button = self.create_widget(factory)
        called = []

        handle = button.connect(lambda: called.append(1))
        handle.dispose()

        native = button.get_native()
        if hasattr(native, "animateClick"):
            native.animateClick(0)
        elif hasattr(native, "_callback") and callable(native._callback):
            native._callback()
        elif hasattr(native, "click") and callable(native.click):
            native.click()  # ipywidgets Button: calls registered handlers as handler(self)
        else:
            pytest.skip("Cannot trigger click on this backend's native widget")

        assert called == []

    @pytest.mark.contract
    def test_connect_callback_exception_does_not_propagate(self, factory):
        """A raising connect() callback must not stop sibling callbacks or crash the trigger."""
        button = self.create_widget(factory)
        called = []

        def bad():
            raise ValueError("boom")

        button.connect(bad)
        button.connect(lambda: called.append(1))

        native = button.get_native()
        if hasattr(native, "animateClick"):
            native.animateClick(0)
        elif hasattr(native, "_callback") and callable(native._callback):
            native._callback()
        elif hasattr(native, "click") and callable(native.click):
            native.click()  # ipywidgets Button: calls registered handlers as handler(self)
        else:
            pytest.skip("Cannot trigger click on this backend's native widget")

        assert called == [1]
