"""
Contract test base classes for UniUI widgets.

Provides reusable mixin classes that define the behavioral contract
every platform implementation must satisfy.
"""
import pytest
from uniui.core import InvalidValueError


def simulate_click(button) -> None:
    """Trigger a Button's click callback via its native widget, backend-agnostically.

    Skips the test if the current backend's native widget exposes none of
    the known click-trigger mechanisms.
    """
    native = button.get_native()
    if hasattr(native, "animateClick"):
        native.animateClick(0)
    elif hasattr(native, "_callback") and callable(native._callback):
        native._callback()
    elif hasattr(native, "click") and callable(native.click):
        native.click()  # ipywidgets Button: calls registered handlers as handler(self)
    else:
        pytest.skip("Cannot trigger click on this backend's native widget")


def skip_unless_available(framework: str) -> None:
    """Skip the current test if ``framework``'s toolkit isn't installed.

    ``framework`` is one of "qt" / "jupyter" / "web" - the values used to
    parametrize a factory-per-backend test. Also activates the Web backend
    state so a Web widget created for the first time in a process behaves
    the same as one created after a normal ``use("web")`` call.
    """
    module = {"qt": "PySide2", "jupyter": "ipywidgets", "web": "nicegui"}[framework]
    pytest.importorskip(module)
    if framework == "web":
        from uniui import use
        use(framework)


class WidgetContractTest:
    """Base class for all widget contract tests.

    Subclasses must define:
        widget_kind: str  - the LABEL / LINE_EDIT / ... constant
        create_widget(factory) -> widget instance
    """

    widget_kind: str = ""

    def create_widget(self, factory):
        raise NotImplementedError

    @pytest.mark.contract
    def test_create_widget(self, factory):
        """Widget can be created without error"""
        widget = self.create_widget(factory)
        assert widget is not None

    @pytest.mark.contract
    def test_get_native(self, factory):
        """get_native() returns a non-None object"""
        widget = self.create_widget(factory)
        assert widget.get_native() is not None


class VisibilityContractTest(WidgetContractTest):
    """Contract for widgets that support show/hide."""

    @pytest.mark.contract
    def test_show_hide(self, factory):
        """show() and hide() must not raise"""
        widget = self.create_widget(factory)
        widget.show()
        widget.hide()
        widget.show()


class CommonCapabilitiesContractTest(WidgetContractTest):
    """Contract for show/hide/is_visible, set_enabled/is_enabled, and fixed/
    minimum sizing — every widget interface now provides these (see
    IWidget's defaults in contracts/widgets.py), except the Qt QLayout-backed
    IVBoxLayout/IHBoxLayout/IGrid, which raise NotSupportedError instead and
    are exercised separately in test_layout.py.
    """

    @pytest.mark.contract
    def test_visibility(self, factory):
        """hide()/show() must toggle is_visible(). Not asserting the initial
        state: Qt widgets report is_visible() == False until actually shown
        in a window (real Qt windowing behavior), while Jupyter/Web widgets
        are visible from construction — both are correct for their platform.
        """
        widget = self.create_widget(factory)
        widget.show()
        assert widget.is_visible() is True
        widget.hide()
        assert widget.is_visible() is False
        widget.show()
        assert widget.is_visible() is True

    @pytest.mark.contract
    def test_enabled(self, factory):
        widget = self.create_widget(factory)
        assert widget.is_enabled() is True
        widget.set_enabled(False)
        assert widget.is_enabled() is False
        widget.set_enabled(True)
        assert widget.is_enabled() is True

    @pytest.mark.contract
    def test_sizing(self, factory):
        """Fixed/minimum sizing must not raise."""
        widget = self.create_widget(factory)
        widget.set_fixed_width(200)
        widget.set_fixed_height(100)
        widget.set_minimum_width(50)
        widget.set_minimum_height(30)


class ValueWidgetContractTest(WidgetContractTest):
    """Contract for widgets that expose a numeric value via get_value()."""

    @pytest.mark.contract
    def test_empty_value(self, factory):
        """Empty text returns default (0.0)"""
        widget = self.create_widget(factory)
        widget.set_text("")
        value = widget.get_value()
        assert abs(value) < 0.001

    @pytest.mark.contract
    def test_float_value(self, factory):
        """Float text is parsed correctly"""
        widget = self.create_widget(factory)
        widget.set_text("3.14")
        value = widget.get_value()
        assert abs(value - 3.14) < 0.001

    @pytest.mark.contract
    def test_negative_value(self, factory):
        """Negative numbers are parsed correctly"""
        widget = self.create_widget(factory)
        widget.set_text("-42.5")
        value = widget.get_value()
        assert abs(value - (-42.5)) < 0.001

    @pytest.mark.contract
    def test_invalid_value_raises(self, factory):
        """Non-numeric text raises InvalidValueError"""
        widget = self.create_widget(factory)
        widget.set_text("not_a_number")
        with pytest.raises(InvalidValueError):
            widget.get_value()

    @pytest.mark.contract
    def test_value_roundtrip(self, factory):
        """set_value then get_value returns the same number"""
        widget = self.create_widget(factory)
        widget.set_value(99.9)
        value = widget.get_value()
        assert abs(value - 99.9) < 0.001
