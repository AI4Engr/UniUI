"""Unit tests for the shared stat-card presentation model.

The exact-string cases below are the wording the three backends produced
*before* the model existed. They are pinned deliberately: the refactor must not
change what a user sees on the card.
"""
import pytest

from uniui.models.stat_card import (
    CARD_STATUSES,
    TREND_DOWN,
    TREND_FLAT,
    TREND_UP,
    normalize_card_status,
    trend_presentation,
)
from uniui.models.status import STATUS_ERROR, STATUS_OK, STATUS_WARN


class TestTrendText:
    """Wording pinned to the pre-refactor output."""

    def test_positive_trend(self):
        assert trend_presentation(12.5) == ("↗  12.5%  vs last period", TREND_UP)

    def test_negative_trend_shows_magnitude_not_sign(self):
        assert trend_presentation(-3.25) == ("↘  3.2%  vs last period", TREND_DOWN)

    def test_zero_trend(self):
        assert trend_presentation(0) == ("—  No change", TREND_FLAT)

    def test_trend_is_rounded_to_one_decimal(self):
        assert trend_presentation(7).text == "↗  7.0%  vs last period"
        assert trend_presentation(0.04).text == "↗  0.0%  vs last period"

    def test_integer_and_string_inputs_are_accepted(self):
        assert trend_presentation(5).style == TREND_UP
        assert trend_presentation("-5").style == TREND_DOWN


class TestSeparator:
    """HTML backends need ``&nbsp;`` so the gap does not collapse."""

    def test_html_separator_matches_previous_jupyter_output(self):
        assert trend_presentation(4.0, separator=" &nbsp;").text == (
            "↗ &nbsp;4.0% &nbsp;vs last period"
        )

    def test_html_separator_applies_to_no_change_too(self):
        assert trend_presentation(0, separator=" &nbsp;").text == (
            "— &nbsp;No change"
        )


class TestStatusOverride:
    """A non-ok status with no movement replaces the trend line."""

    def test_warn_with_no_movement(self):
        assert trend_presentation(0, STATUS_WARN) == ("Needs attention", STATUS_WARN)

    def test_error_with_no_movement(self):
        assert trend_presentation(0, STATUS_ERROR) == ("Error", STATUS_ERROR)

    @pytest.mark.parametrize("status", [STATUS_WARN, STATUS_ERROR])
    def test_actual_movement_wins_over_status(self, status):
        """Real movement is more informative than a static status word."""
        assert trend_presentation(2.0, status).style == TREND_UP
        assert trend_presentation(-2.0, status).style == TREND_DOWN

    def test_ok_status_never_overrides(self):
        assert trend_presentation(0, STATUS_OK).style == TREND_FLAT


class TestStatusNormalization:
    @pytest.mark.parametrize("status", CARD_STATUSES)
    def test_known_statuses_pass_through(self, status):
        assert normalize_card_status(status) == status

    @pytest.mark.parametrize("status", ["neutral", "", "bogus", None])
    def test_unknown_statuses_fall_back_to_ok(self, status):
        """Preserves the long-standing behaviour of the backend adapters.

        Note ``neutral`` is deliberately included: it is valid for a table
        cell but a card has no neutral rendering.
        """
        assert normalize_card_status(status) == STATUS_OK


class TestBackendsAgree:
    """All three backends must show the same text for the same input."""

    CASES = [(9.5, STATUS_OK), (-4.0, STATUS_OK), (0.0, STATUS_OK),
             (0.0, STATUS_WARN), (0.0, STATUS_ERROR)]

    @pytest.mark.parametrize("trend,status", CASES)
    def test_qt_matches_model(self, trend, status):
        pytest.importorskip("PySide2")
        from uniui import create_factory

        card = create_factory("qt").create_stat_card()
        card.set_status(status)
        card.set_trend(trend)
        assert card._trend_lbl.text() == trend_presentation(trend, status).text

    @pytest.mark.parametrize("trend,status", CASES)
    def test_jupyter_matches_model(self, trend, status):
        pytest.importorskip("ipywidgets")
        from uniui import create_factory

        card = create_factory("jupyter").create_stat_card()
        card.set_status(status)
        card.set_trend(trend)
        expected = trend_presentation(trend, status, " &nbsp;").text
        assert card._trend_widget.value == f"<p>{expected}</p>"

    @pytest.mark.parametrize("trend,status", CASES)
    def test_web_matches_model(self, trend, status):
        pytest.importorskip("nicegui")
        from uniui import create_factory, use

        use("web")
        card = create_factory("web").create_stat_card()
        card.set_status(status)
        card.set_trend(trend)
        assert card._trend_label.text == trend_presentation(trend, status).text


class TestTrendClassesAreExclusive:
    """Switching trend direction must not leave the old class behind."""

    def test_jupyter_clears_previous_class(self):
        pytest.importorskip("ipywidgets")
        from uniui import create_factory

        card = create_factory("jupyter").create_stat_card()
        card.set_trend(5.0)
        assert "uniui-up" in card._trend_widget._dom_classes
        card.set_trend(-5.0)
        classes = card._trend_widget._dom_classes
        assert "uniui-down" in classes and "uniui-up" not in classes

    def test_jupyter_clears_status_class_when_trend_moves(self):
        pytest.importorskip("ipywidgets")
        from uniui import create_factory

        card = create_factory("jupyter").create_stat_card()
        card.set_status(STATUS_ERROR)
        assert "uniui-status-error" in card._trend_widget._dom_classes
        card.set_trend(3.0)
        classes = card._trend_widget._dom_classes
        assert "uniui-up" in classes and "uniui-status-error" not in classes

    def test_web_clears_previous_class(self):
        pytest.importorskip("nicegui")
        from uniui import create_factory, use

        use("web")
        card = create_factory("web").create_stat_card()
        card.set_trend(5.0)
        assert "uniui-up" in card._trend_label.classes
        card.set_trend(-5.0)
        assert "uniui-down" in card._trend_label.classes
        assert "uniui-up" not in card._trend_label.classes
