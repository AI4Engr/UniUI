"""Unit tests for the shared gauge and chart state models."""
import pytest

from uniui.models.chart import (
    DEFAULT_CHART_TYPE,
    DEFAULT_MAX_POINTS,
    MIN_MAX_POINTS,
    ChartModel,
)
from uniui.models.gauge import MIN_SPAN, GaugeModel
from uniui.models.status import STATUS_ERROR, STATUS_OK, STATUS_WARN


class TestGaugeRange:
    def test_defaults(self):
        gauge = GaugeModel()
        assert (gauge.minimum, gauge.maximum) == (0.0, 100.0)

    def test_ordinary_range_is_kept(self):
        gauge = GaugeModel()
        gauge.set_range(10, 50)
        assert (gauge.minimum, gauge.maximum) == (10.0, 50.0)

    def test_inverted_range_is_widened(self):
        gauge = GaugeModel()
        gauge.set_range(10, 5)
        assert (gauge.minimum, gauge.maximum) == (10.0, 10.0 + MIN_SPAN)

    def test_empty_range_is_widened(self):
        """A zero span would divide by zero when computing the ratio."""
        gauge = GaugeModel()
        gauge.set_range(7, 7)
        assert gauge.span == MIN_SPAN

    def test_narrow_range_is_preserved(self):
        """Qt kept ``(0, 0.5)``; the browser backends widened it to ``(0, 1)``.

        The Qt reading wins: a deliberately narrow range is respected.
        """
        gauge = GaugeModel()
        gauge.set_range(0, 0.5)
        assert (gauge.minimum, gauge.maximum) == (0.0, 0.5)

    def test_string_inputs_are_coerced(self):
        gauge = GaugeModel()
        gauge.set_range("2", "8")
        assert (gauge.minimum, gauge.maximum) == (2.0, 8.0)


class TestGaugeRatio:
    @pytest.mark.parametrize("value,expected", [(0, 0.0), (50, 0.5), (100, 1.0)])
    def test_ratio_across_default_range(self, value, expected):
        gauge = GaugeModel()
        gauge.set_value(value)
        assert gauge.ratio == pytest.approx(expected)

    @pytest.mark.parametrize("value", [-10, 200])
    def test_out_of_range_values_are_clamped(self, value):
        gauge = GaugeModel()
        gauge.set_value(value)
        assert 0.0 <= gauge.ratio <= 1.0

    def test_ratio_honours_a_non_zero_minimum(self):
        gauge = GaugeModel()
        gauge.set_range(100, 200)
        gauge.set_value(150)
        assert gauge.ratio == pytest.approx(0.5)


class TestGaugeStatus:
    @pytest.mark.parametrize("status", [STATUS_OK, STATUS_WARN, STATUS_ERROR])
    def test_known_statuses_pass_through(self, status):
        gauge = GaugeModel()
        gauge.set_status(status)
        assert gauge.status == status

    @pytest.mark.parametrize("status", ["neutral", "bogus", None])
    def test_unknown_statuses_fall_back_to_ok(self, status):
        gauge = GaugeModel()
        gauge.set_status(status)
        assert gauge.status == STATUS_OK


class TestGaugeAccessibility:
    def test_description_includes_label_value_and_unit(self):
        gauge = GaugeModel()
        gauge.set_label("CPU")
        gauge.set_unit("%")
        gauge.set_value(42)
        assert gauge.accessible_description() == "CPU: 42 %"

    def test_description_is_stripped_when_unit_is_missing(self):
        gauge = GaugeModel()
        gauge.set_label("CPU")
        gauge.set_value(42)
        assert gauge.accessible_description() == "CPU: 42"

    def test_value_uses_general_format_not_trailing_zeros(self):
        gauge = GaugeModel()
        gauge.set_label("X")
        gauge.set_value(3.0)
        assert "3 " in gauge.accessible_description() + " "


class TestChartType:
    def test_default(self):
        assert ChartModel().chart_type == DEFAULT_CHART_TYPE

    @pytest.mark.parametrize("chart_type", ["line", "area", "bar"])
    def test_known_types_pass_through(self, chart_type):
        chart = ChartModel()
        chart.set_type(chart_type)
        assert chart.chart_type == chart_type

    @pytest.mark.parametrize("chart_type", ["pie", "", None])
    def test_unknown_types_fall_back_to_line(self, chart_type):
        chart = ChartModel()
        chart.set_type(chart_type)
        assert chart.chart_type == DEFAULT_CHART_TYPE


class TestChartWindow:
    def test_default_max_points(self):
        assert ChartModel().max_points == DEFAULT_MAX_POINTS

    def test_set_data_trims_to_the_window(self):
        chart = ChartModel(max_points=3)
        chart.set_data([1, 2, 3, 4, 5], [{"name": "a", "data": [1, 2, 3, 4, 5]}])
        assert chart.x_values == [3, 4, 5]
        assert chart.series[0]["data"] == [3.0, 4.0, 5.0]

    def test_append_respects_the_window(self):
        chart = ChartModel(max_points=3)
        chart.set_data([1], [{"name": "a", "data": [1]}])
        for x in (2, 3, 4):
            chart.append_data(x, [x])
        assert chart.x_values == [2, 3, 4]
        assert chart.series[0]["data"] == [2.0, 3.0, 4.0]

    def test_shrinking_the_window_trims_existing_data(self):
        chart = ChartModel()
        chart.set_data(list(range(10)), [{"name": "a", "data": list(range(10))}])
        chart.set_max_points(4)
        assert chart.x_values == [6, 7, 8, 9]
        assert chart.series[0]["data"] == [6.0, 7.0, 8.0, 9.0]

    def test_window_has_a_floor(self):
        """One point cannot describe a line."""
        chart = ChartModel()
        chart.set_max_points(0)
        assert chart.max_points == MIN_MAX_POINTS

    def test_series_values_are_coerced_to_float(self):
        chart = ChartModel()
        chart.set_data([1], [{"name": "a", "data": ["3"]}])
        assert chart.series[0]["data"] == [3.0]

    def test_unnamed_series_get_positional_names(self):
        chart = ChartModel()
        chart.set_data([1], [{"data": [1]}, {"data": [2]}])
        assert [s["name"] for s in chart.series] == ["Series 1", "Series 2"]


class TestChartAppendByName:
    def test_dict_values_are_matched_by_series_name(self):
        chart = ChartModel()
        chart.set_data([1], [{"name": "a", "data": [1]}, {"name": "b", "data": [2]}])
        chart.append_data(2, {"b": 20, "a": 10})
        assert chart.series[0]["data"] == [1.0, 10.0]
        assert chart.series[1]["data"] == [2.0, 20.0]

    def test_missing_series_in_dict_appends_zero(self):
        chart = ChartModel()
        chart.set_data([1], [{"name": "a", "data": [1]}, {"name": "b", "data": [2]}])
        chart.append_data(2, {"a": 10})
        assert chart.series[1]["data"] == [2.0, 0.0]


class TestChartOverlay:
    def test_empty_by_default(self):
        chart = ChartModel()
        assert chart.shows_overlay
        assert chart.overlay_text() == "No data"

    def test_not_empty_once_data_is_set(self):
        chart = ChartModel()
        chart.set_data([1], [{"name": "a", "data": [1]}])
        assert not chart.shows_overlay
        assert chart.overlay_text() == ""

    def test_series_with_no_points_still_counts_as_empty(self):
        chart = ChartModel()
        chart.set_data([], [{"name": "a", "data": []}])
        assert chart.shows_overlay

    def test_loading_overrides_existing_data(self):
        chart = ChartModel()
        chart.set_data([1], [{"name": "a", "data": [1]}])
        chart.set_loading(True)
        assert chart.shows_overlay
        assert chart.overlay_text() == "Loading…"

    def test_error_outranks_loading(self):
        chart = ChartModel()
        chart.set_loading(True)
        chart.set_error("boom")
        assert chart.overlay_text() == "⚠  boom"

    def test_loading_outranks_empty(self):
        chart = ChartModel()
        chart.set_loading(True)
        assert chart.overlay_text() == "Loading…"

    def test_clearing_loading_and_error_reveals_data(self):
        chart = ChartModel()
        chart.set_data([1], [{"name": "a", "data": [1]}])
        chart.set_loading(True)
        chart.set_error("boom")
        chart.set_error("")
        chart.set_loading(False)
        assert not chart.shows_overlay

    @pytest.mark.parametrize("blank", ["", None])
    def test_blank_error_clears(self, blank):
        chart = ChartModel()
        chart.set_error("boom")
        chart.set_error(blank)
        assert chart.error == ""


class TestBackendsShareTheModel:
    """Each backend's adapter must delegate to the model, not keep a copy."""

    @pytest.mark.parametrize("framework", ["qt", "jupyter", "web"])
    def test_chart_window_is_enforced(self, framework):
        _skip_unless_available(framework)
        from uniui import create_factory

        chart = create_factory(framework).create_chart()
        chart.set_max_points(3)
        chart.set_data([1, 2], [{"name": "Load", "data": [20, 30]}])
        chart.append_data(3, [40])
        chart.append_data(4, [50])
        model = _chart_model(chart)
        assert model.x_values == [2, 3, 4]
        assert model.series[0]["data"] == [30.0, 40.0, 50.0]

    @pytest.mark.parametrize("framework", ["qt", "jupyter", "web"])
    def test_chart_set_error_reaches_the_shared_model(self, framework):
        _skip_unless_available(framework)
        from uniui import create_factory

        chart = create_factory(framework).create_chart()
        chart.set_error("network down")
        model = _chart_model(chart)
        assert model.error == "network down"
        assert model.overlay_text() == "⚠  network down"

    @pytest.mark.parametrize("framework", ["qt", "jupyter", "web"])
    def test_chart_set_loading_reaches_the_shared_model(self, framework):
        _skip_unless_available(framework)
        from uniui import create_factory

        chart = create_factory(framework).create_chart()
        chart.set_data([1], [{"name": "a", "data": [1]}])
        chart.set_loading(True)
        model = _chart_model(chart)
        assert model.loading
        assert model.overlay_text() == "Loading…"

    @pytest.mark.parametrize("framework", ["jupyter", "web"])
    def test_chart_error_replaces_the_rendered_svg(self, framework):
        """Jupyter/Web render to an HTML/SVG string - verify the error
        message actually reaches it, not just the model."""
        _skip_unless_available(framework)
        from uniui import create_factory

        chart = create_factory(framework).create_chart()
        chart.set_data([1], [{"name": "a", "data": [1]}])
        chart.set_error("network down")
        native = chart.get_native()
        content = getattr(native, "value", None)
        if content is None:
            content = native._props.get("innerHTML", "")
        assert "network down" in content

    @pytest.mark.parametrize("framework", ["qt", "jupyter", "web"])
    def test_gauge_range_rules_are_shared(self, framework):
        _skip_unless_available(framework)
        from uniui import create_factory

        gauge = create_factory(framework).create_gauge()
        gauge.set_range(10, 5)
        model = _gauge_model(gauge)
        assert (model.minimum, model.maximum) == (10.0, 11.0)

    @pytest.mark.parametrize("framework", ["qt", "jupyter", "web"])
    def test_gauge_status_falls_back_to_ok(self, framework):
        _skip_unless_available(framework)
        from uniui import create_factory

        gauge = create_factory(framework).create_gauge()
        gauge.set_status("bogus")
        assert _gauge_model(gauge).status == STATUS_OK


def _skip_unless_available(framework):
    module = {"qt": "PySide2", "jupyter": "ipywidgets", "web": "nicegui"}[framework]
    pytest.importorskip(module)
    if framework == "web":
        from uniui import use

        use("web")


def _chart_model(adapter):
    """Qt keeps the model on the painted widget; the others hold it directly."""
    return getattr(adapter, "_model", None) or adapter._widget.model


def _gauge_model(adapter):
    return getattr(adapter, "_model", None) or adapter._widget.model
