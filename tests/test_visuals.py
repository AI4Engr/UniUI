"""Backend-neutral tests for Gauge and streaming Chart data."""

from uniui.theme import get_admin_tokens
from uniui.visuals import (
    append_chart_point, normalized_series, render_chart_svg, render_gauge_svg,
)


def test_streaming_chart_keeps_a_bounded_history():
    x = [0, 1]
    series = normalized_series([{"name": "Load", "data": [10, 20]}])
    for value in range(2, 20):
        append_chart_point(x, series, value, [value * 10], max_points=5)

    assert x == [15, 16, 17, 18, 19]
    assert series[0]["data"] == [150.0, 160.0, 170.0, 180.0, 190.0]


def test_visual_svg_renderers_are_responsive_and_escape_labels():
    palette = get_admin_tokens(False)
    gauge = render_gauge_svg("Load <unsafe>", 72, "%", 0, 100, "ok", palette)
    chart = render_chart_svg(
        "area", "Live <activity>", ["a", "b"],
        [{"name": "Load", "data": [10, 20]}], palette,
    )

    assert 'viewBox="0 0 200 180"' in gauge
    assert "Load &lt;unsafe&gt;" in gauge
    assert 'viewBox="0 0 640 250"' in chart
    assert "Live &lt;activity&gt;" in chart
    assert "<path" in chart
