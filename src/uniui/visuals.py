"""Pure-Python data helpers and SVG renderers for Admin visuals."""
from __future__ import annotations

from html import escape
from typing import Any, Dict, List, Sequence, Tuple


CHART_TYPES = {"line", "area", "bar"}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def normalized_series(series: Sequence[Dict]) -> List[Dict]:
    result = []
    for index, item in enumerate(series):
        result.append({
            "name": str(item.get("name", f"Series {index + 1}")),
            "data": [float(value) for value in item.get("data", [])],
        })
    return result


def append_chart_point(x_values: List[Any], series: List[Dict], x: Any,
                       values: Any, max_points: int) -> None:
    x_values.append(x)
    if isinstance(values, dict):
        lookup = values
        for item in series:
            item["data"].append(float(lookup.get(item["name"], 0.0)))
    else:
        sequence = list(values) if isinstance(values, (list, tuple)) else [values]
        for index, item in enumerate(series):
            value = sequence[index] if index < len(sequence) else 0.0
            item["data"].append(float(value))
    limit = max(2, int(max_points))
    if len(x_values) > limit:
        del x_values[:-limit]
    for item in series:
        if len(item["data"]) > limit:
            del item["data"][:-limit]


def render_gauge_svg(label: str, value: float, unit: str, minimum: float,
                     maximum: float, status: str, palette: Dict[str, str]) -> str:
    span = max(1e-9, maximum - minimum)
    ratio = clamp((value - minimum) / span, 0.0, 1.0)
    circumference = 351.858
    arc = circumference * 0.75
    progress = arc * ratio
    color = palette.get(status, palette["accent"])
    value_text = f"{value:g}{unit}"
    return f"""
<svg class="uniui-gauge-svg" viewBox="0 0 200 180" role="img"
 aria-label="{escape(label)}: {escape(value_text)}">
  <circle cx="100" cy="86" r="56" fill="none" stroke="{palette['border']}"
    stroke-width="14" stroke-linecap="round" stroke-dasharray="{arc:.3f} {circumference:.3f}"
    transform="rotate(135 100 86)"/>
  <circle cx="100" cy="86" r="56" fill="none" stroke="{color}"
    stroke-width="14" stroke-linecap="round" stroke-dasharray="{progress:.3f} {circumference:.3f}"
    transform="rotate(135 100 86)"/>
  <text x="100" y="84" text-anchor="middle" fill="{palette['text']}"
    font-size="26" font-weight="700">{escape(f'{value:g}')}</text>
  <text x="100" y="105" text-anchor="middle" fill="{palette['text_muted']}"
    font-size="12">{escape(unit)}</text>
  <text x="100" y="153" text-anchor="middle" fill="{palette['text_muted']}"
    font-size="13" font-weight="600">{escape(label)}</text>
</svg>""".strip()


def _chart_points(data: Sequence[float], left: float, top: float, width: float,
                  height: float, low: float, high: float) -> List[Tuple[float, float]]:
    if not data:
        return []
    span = max(1e-9, high - low)
    step = width / max(1, len(data) - 1)
    return [
        (left + index * step, top + height - ((value - low) / span) * height)
        for index, value in enumerate(data)
    ]


def render_chart_svg(chart_type: str, title: str, x_values: Sequence[Any],
                     series: Sequence[Dict], palette: Dict[str, str]) -> str:
    chart_type = chart_type if chart_type in CHART_TYPES else "line"
    width, height = 640.0, 250.0
    left, top, plot_width, plot_height = 46.0, 36.0, 574.0, 170.0
    all_values = [value for item in series for value in item.get("data", [])]
    if not all_values:
        return (
            '<svg class="uniui-chart-svg" viewBox="0 0 640 250">'
            f'<text x="320" y="125" text-anchor="middle" fill="{palette["text_muted"]}" '
            f'font-size="14">{escape(title or "No data")}</text></svg>'
        )
    low, high = min(all_values), max(all_values)
    if low == high:
        low -= 1.0
        high += 1.0
    padding = (high - low) * 0.08
    low -= padding
    high += padding
    colors = [palette["accent"], palette["ok"], palette["warn"], palette["error"]]
    parts = [
        '<svg class="uniui-chart-svg" viewBox="0 0 640 250" role="img" '
        f'aria-label="{escape(title or "Chart")}">',
        f'<text x="46" y="22" fill="{palette["text"]}" font-size="14" font-weight="700">'
        f'{escape(title)}</text>',
    ]
    for index in range(5):
        y = top + (plot_height * index / 4)
        value = high - ((high - low) * index / 4)
        parts.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" '
            f'stroke="{palette["border"]}" stroke-width="1"/>'
            f'<text x="{left - 8}" y="{y + 4:.2f}" text-anchor="end" '
            f'fill="{palette["text_muted"]}" font-size="10">{value:.0f}</text>'
        )
    for series_index, item in enumerate(series):
        data = item.get("data", [])
        color = colors[series_index % len(colors)]
        points = _chart_points(data, left, top, plot_width, plot_height, low, high)
        if chart_type == "bar":
            slot = plot_width / max(1, len(data))
            bar_width = max(3.0, slot * 0.62 / max(1, len(series)))
            for index, value in enumerate(data):
                x = left + index * slot + slot * 0.19 + series_index * bar_width
                y = top + plot_height - ((value - low) / (high - low)) * plot_height
                parts.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" '
                    f'height="{top + plot_height - y:.2f}" rx="3" fill="{color}" opacity=".88"/>'
                )
        elif points:
            path = " ".join(
                ("M" if index == 0 else "L") + f"{x:.2f},{y:.2f}"
                for index, (x, y) in enumerate(points)
            )
            if chart_type == "area":
                area = (
                    path + f" L{points[-1][0]:.2f},{top + plot_height:.2f} "
                    f"L{points[0][0]:.2f},{top + plot_height:.2f} Z"
                )
                parts.append(f'<path d="{area}" fill="{color}" opacity=".14"/>')
            parts.append(
                f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5" '
                'stroke-linecap="round" stroke-linejoin="round"/>'
            )
    if x_values:
        parts.append(
            f'<text x="{left}" y="232" fill="{palette["text_muted"]}" font-size="10">'
            f'{escape(str(x_values[0]))}</text>'
            f'<text x="{left + plot_width}" y="232" text-anchor="end" '
            f'fill="{palette["text_muted"]}" font-size="10">{escape(str(x_values[-1]))}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


__all__ = [
    "CHART_TYPES", "append_chart_point", "clamp", "normalized_series",
    "render_chart_svg", "render_gauge_svg",
]
