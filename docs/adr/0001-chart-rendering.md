# ADR 0001: Chart rendering — hand-rolled SVG/QPainter, no charting dependency

## Status

Accepted (already implemented — this ADR documents a shipped decision).

## Context

TODO.md's P0 backlog asked for an ADR deciding the chart implementation
approach and optional dependencies before `Chart` shipped. `Chart` has since
been implemented across all three backends
(`src/uniui/models/chart.py`, `src/uniui/backends/{qt,jupyter,web}/components/chart.py`,
`src/uniui/visuals.py`), so this ADR records the decision as built rather
than proposing a new one.

The options considered were:
1. **Bind an existing charting library** per backend (e.g. QtCharts for Qt,
   bqplot/plotly for Jupyter, a JS charting library via NiceGUI).
2. **Hand-roll rendering**: Qt draws with `QPainter` directly; the two
   browser-facing backends (Jupyter, Web) render an SVG string.
3. **Skip Chart entirely** for the first Admin milestone.

## Decision

**Hand-roll rendering, no chart dependency.**

- `ChartModel` (`src/uniui/models/chart.py`) owns everything
  backend-agnostic: type validation (falls back to `"line"` for an unknown
  `chart_type`), title, the rolling `max_points` window (trimmed via
  `_trim()`), and series normalization — implemented once instead of three
  times, mirroring the same "shared model, backend-only rendering" split
  used elsewhere (`TableModel`, `NavigationModel`, `BreadcrumbModel`).
- Qt renders with `QPainter` directly against the widget's paint event.
- Jupyter and Web both render through the same
  `uniui.visuals.render_chart_svg(chart_type, title, x_values, series, palette)`
  helper, producing an SVG string assigned to an `ipywidgets.HTML`/NiceGUI
  element respectively — one rendering implementation shared by both
  browser-facing backends, not three renderers total.
- Supported chart types today: `{"line", "area", "bar"}`
  (`uniui.visuals.CHART_TYPES`).

## Consequences

- **No optional dependency** for charting — `Chart` works out of the box in
  every install, with no `pip install uniui[charts]` extra to remember, and
  no version-compat surface against a third-party charting library (the kind
  of drift this session already hit once with NiceGUI itself).
- **Feature ceiling is deliberately low.** No zoom/pan, no tooltips, no
  legend interaction, no animation — anything beyond what `render_chart_svg`
  and the Qt `QPainter` path already draw requires either extending that
  hand-rolled renderer or revisiting this decision.
- **This is not necessarily final.** If a future milestone needs
  interactive charts (zoom, hover tooltips, large-dataset performance), that
  will most likely mean introducing a real charting dependency for at least
  the Web backend (browsers have mature JS charting libraries NiceGUI can
  wrap) and possibly QtCharts for Qt — at which point this ADR should be
  superseded, not silently reinterpreted. `ChartModel`'s shared
  type/data-normalization layer should still be reusable underneath a new
  renderer either way.
