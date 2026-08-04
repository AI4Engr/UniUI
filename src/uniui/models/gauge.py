"""Shared state model for gauges.

Every backend held the same six fields with the same coercion rules. The
copies had drifted on one point: Qt widened the range only when
``maximum <= minimum``, while the browser backends always applied
``max(maximum, minimum + 1)``. Those disagree for a range like ``(0, 0.5)`` -
Qt kept it, the others widened it to ``(0, 1)``. This model settles on the Qt
reading, which respects a deliberately narrow range.

Rendering stays with the backend: Qt paints with QPainter, the browser
backends call :func:`uniui.visuals.render_gauge_svg`.
"""
from .stat_card import normalize_card_status

#: Smallest span a gauge can have. A zero or inverted span would divide by
#: zero when computing the fill ratio.
MIN_SPAN = 1.0


class GaugeModel:
    """Label, value, unit, range, and status for a gauge."""

    __slots__ = ("label", "value", "unit", "minimum", "maximum", "status")

    def __init__(self, minimum: float = 0.0, maximum: float = 100.0):
        self.label = ""
        self.value = 0.0
        self.unit = ""
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.status = normalize_card_status("ok")

    def set_label(self, label) -> None:
        self.label = str(label)

    def set_value(self, value) -> None:
        self.value = float(value)

    def set_unit(self, unit) -> None:
        self.unit = str(unit)

    def set_range(self, minimum, maximum) -> None:
        """Store the range, widening it only if it is empty or inverted."""
        minimum, maximum = float(minimum), float(maximum)
        if maximum <= minimum:
            maximum = minimum + MIN_SPAN
        self.minimum, self.maximum = minimum, maximum

    def set_status(self, status) -> None:
        """Unknown statuses fall back to ``ok``, as a stat card's do."""
        self.status = normalize_card_status(status)

    @property
    def span(self) -> float:
        return self.maximum - self.minimum

    @property
    def ratio(self) -> float:
        """Value position within the range, clamped to ``0.0``-``1.0``."""
        return max(0.0, min(1.0, (self.value - self.minimum) / self.span))

    def accessible_description(self) -> str:
        """Screen-reader text, e.g. ``"CPU: 42 %"``."""
        return f"{self.label}: {self.value:g} {self.unit}".strip()

    def render_args(self):
        """Positional arguments for :func:`uniui.visuals.render_gauge_svg`.

        Keeps the argument order in one place instead of three call sites.
        """
        return (
            self.label, self.value, self.unit,
            self.minimum, self.maximum, self.status,
        )
