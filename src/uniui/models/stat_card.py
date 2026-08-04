"""Shared presentation model for stat cards.

Trend formatting and the status/trend interaction were implemented three times
- once per backend - with identical rules but three copies of the thresholds
and wording. This model owns those rules and returns plain text plus a
semantic style name; the backend decides how to render it (QSS colour, CSS
class, NiceGUI class) and is responsible for escaping.

The separator between the arrow and the percentage is a parameter because the
HTML backends need ``&nbsp;`` to keep the gap from collapsing, while Qt uses
ordinary spaces.
"""
from typing import NamedTuple

from .status import STATUS_ERROR, STATUS_OK, STATUS_WARN

#: Statuses a stat card accepts. Unlike table cells a card has no "neutral"
#: state: anything unrecognised falls back to ``ok``.
CARD_STATUSES = (STATUS_OK, STATUS_WARN, STATUS_ERROR)

#: Semantic style names a backend must be able to render for the trend line.
TREND_UP = "up"
TREND_DOWN = "down"
TREND_FLAT = "flat"

_STATUS_TEXT = {
    STATUS_WARN: "Needs attention",
    STATUS_ERROR: "Error",
}

_NO_CHANGE = "No change"


class TrendPresentation(NamedTuple):
    """What a backend needs to render the trend line.

    ``style`` is either a trend direction (``up``/``down``/``flat``) or a
    semantic status (``warn``/``error``) when the status overrides the trend.
    """

    text: str
    style: str


def normalize_card_status(status: str) -> str:
    """Coerce a status to one a stat card can render.

    Unknown values become ``ok``, preserving the long-standing behaviour of
    the backends this replaces.
    """
    return status if status in CARD_STATUSES else STATUS_OK


def trend_presentation(
    trend: float, status: str = STATUS_OK, separator: str = "  "
) -> TrendPresentation:
    """Return the text and semantic style for a card's trend line.

    A non-ok status with no movement takes over the line, because "no change"
    would otherwise hide the fact that something needs attention.
    """
    status = normalize_card_status(status)
    trend = float(trend)

    if status != STATUS_OK and trend == 0:
        return TrendPresentation(_STATUS_TEXT[status], status)
    if trend > 0:
        return TrendPresentation(
            f"↗{separator}{trend:.1f}%{separator}vs last period", TREND_UP
        )
    if trend < 0:
        return TrendPresentation(
            f"↘{separator}{abs(trend):.1f}%{separator}vs last period", TREND_DOWN
        )
    return TrendPresentation(f"—{separator}{_NO_CHANGE}", TREND_FLAT)
