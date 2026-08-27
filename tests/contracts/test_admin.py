"""
Contract tests for Admin components: Card, StatCard, Table, Sidebar, AppShell, Breadcrumb.
"""
import pytest

from tests.contract_framework import CommonCapabilitiesContractTest as _Common
from uniui import (
    APP_SHELL, BREADCRUMB, CARD, CHART, DRAWER, GAUGE,
    METRIC_LIST, SIDEBAR, STAT_CARD, TABLE,
)


class TestCardContract(_Common):
    widget_kind = CARD

    def create_widget(self, factory):
        return factory.create_card()

    @pytest.mark.contract
    def test_set_title(self, factory):
        card = self.create_widget(factory)
        card.set_title("My Card")

    @pytest.mark.contract
    def test_set_subtitle(self, factory):
        card = self.create_widget(factory)
        card.set_subtitle("A subtitle")

    @pytest.mark.contract
    def test_set_title_and_subtitle(self, factory):
        card = self.create_widget(factory)
        card.set_title("Title")
        card.set_subtitle("Subtitle")

    @pytest.mark.contract
    def test_set_content_label(self, factory):
        card = self.create_widget(factory)
        label = factory.create_label()
        label.set_text("Card body")
        card.set_content(label)

    @pytest.mark.contract
    def test_set_action_button(self, factory):
        card = self.create_widget(factory)
        btn = factory.create_button()
        btn.set_text("Action")
        card.set_action(btn)

    @pytest.mark.contract
    def test_set_content_and_action(self, factory):
        card = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("Content")
        card.set_content(lbl)
        btn = factory.create_button()
        btn.set_text("OK")
        card.set_action(btn)


class TestStatCardContract(_Common):
    widget_kind = STAT_CARD

    def create_widget(self, factory):
        return factory.create_stat_card()

    @pytest.mark.contract
    def test_set_label(self, factory):
        sc = self.create_widget(factory)
        sc.set_label("Active Users")

    @pytest.mark.contract
    def test_set_value(self, factory):
        sc = self.create_widget(factory)
        sc.set_value("1,280")

    @pytest.mark.contract
    def test_set_unit(self, factory):
        sc = self.create_widget(factory)
        sc.set_unit("users")

    @pytest.mark.contract
    @pytest.mark.parametrize("trend", [5.2, -3.1, 0.0])
    def test_set_trend(self, factory, trend):
        sc = self.create_widget(factory)
        sc.set_trend(trend)

    @pytest.mark.contract
    @pytest.mark.parametrize("status", ["ok", "warn", "error"])
    def test_set_status(self, factory, status):
        sc = self.create_widget(factory)
        sc.set_status(status)


class TestMetricListContract(_Common):
    widget_kind = METRIC_LIST

    def create_widget(self, factory):
        return factory.create_metric_list()

    @pytest.mark.contract
    def test_set_items(self, factory):
        ml = self.create_widget(factory)
        ml.set_items([
            {"label": "Active handles", "value": "4"},
            {"label": "Heap size", "value": "13.5 MiB"},
        ])

    @pytest.mark.contract
    def test_set_items_empty(self, factory):
        ml = self.create_widget(factory)
        ml.set_items([])

    @pytest.mark.contract
    def test_set_items_replaces_previous(self, factory):
        ml = self.create_widget(factory)
        ml.set_items([{"label": "A", "value": "1"}])
        ml.set_items([{"label": "B", "value": "2"}])


class TestTableContract(_Common):
    widget_kind = TABLE

    def create_widget(self, factory):
        return factory.create_table()

    @pytest.mark.contract
    def test_set_columns(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([
            {"key": "name", "label": "Name"},
            {"key": "age", "label": "Age", "width": 80},
        ])

    @pytest.mark.contract
    def test_set_rows(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "name", "label": "Name"}, {"key": "age", "label": "Age"}])
        tbl.set_rows([
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ])

    @pytest.mark.contract
    def test_set_rows_empty(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "id", "label": "ID"}])
        tbl.set_rows([])

    @pytest.mark.contract
    def test_set_loading_true(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_loading(True)

    @pytest.mark.contract
    def test_set_loading_false(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_loading(True)
        tbl.set_loading(False)

    @pytest.mark.contract
    def test_set_error_message(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_error("Failed to load data")

    @pytest.mark.contract
    def test_set_error_clear(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_error("Failed")
        tbl.set_error("")

    @pytest.mark.contract
    def test_on_row_click_registers(self, factory):
        tbl = self.create_widget(factory)
        tbl.on_row_click(lambda row: None)

    @pytest.mark.contract
    def test_on_row_click_dispose_clears_callback(self, factory):
        tbl = self.create_widget(factory)
        handle = tbl.on_row_click(lambda row: None)
        handle.dispose()
        assert tbl._row_click_cb is None

    @pytest.mark.contract
    def test_get_selected_row_starts_as_none(self, factory):
        tbl = self.create_widget(factory)
        assert tbl.get_selected_row() is None

    @pytest.mark.contract
    def test_set_page_size_slices_the_displayed_rows(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "id"}])
        tbl.set_rows([{"id": i} for i in range(5)])
        tbl.set_page_size(2)
        assert tbl._model.display_rows() == [{"id": 0}, {"id": 1}]

    @pytest.mark.contract
    def test_set_page_navigates(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "id"}])
        tbl.set_rows([{"id": i} for i in range(5)])
        tbl.set_page_size(2)
        tbl.set_page(2)
        assert tbl._model.display_rows() == [{"id": 4}]

    @pytest.mark.contract
    def test_set_page_size_none_disables_pagination(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "id"}])
        tbl.set_rows([{"id": i} for i in range(5)])
        tbl.set_page_size(2)
        tbl.set_page_size(None)
        assert len(tbl._model.display_rows()) == 5

    @pytest.mark.contract
    def test_set_sort_ascending(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "name", "label": "Name", "sortable": True}])
        tbl.set_rows([{"name": "Bob"}, {"name": "Alice"}])
        tbl.set_sort("name")
        assert tbl._model.sorted_rows() == [{"name": "Alice"}, {"name": "Bob"}]

    @pytest.mark.contract
    def test_set_sort_descending(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "name", "label": "Name", "sortable": True}])
        tbl.set_rows([{"name": "Alice"}, {"name": "Bob"}])
        tbl.set_sort("name", reverse=True)
        assert tbl._model.sorted_rows() == [{"name": "Bob"}, {"name": "Alice"}]

    @pytest.mark.contract
    def test_set_sort_none_clears(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "name", "label": "Name", "sortable": True}])
        tbl.set_rows([{"name": "Bob"}, {"name": "Alice"}])
        tbl.set_sort("name")
        tbl.set_sort(None)
        assert tbl._model.sorted_rows() == [{"name": "Bob"}, {"name": "Alice"}]

    @pytest.mark.contract
    def test_set_sort_persists_across_new_rows(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "amount", "label": "Amount", "sortable": True}])
        tbl.set_rows([{"amount": 3}, {"amount": 1}])
        tbl.set_sort("amount")
        tbl.set_rows([{"amount": 5}, {"amount": 2}])
        assert tbl._model.sorted_rows() == [{"amount": 2}, {"amount": 5}]


class TestSidebarContract(_Common):
    widget_kind = SIDEBAR

    def create_widget(self, factory):
        return factory.create_sidebar()

    @pytest.mark.contract
    def test_add_item(self, factory):
        sb = self.create_widget(factory)
        sb.add_item("dashboard", "Dashboard")

    @pytest.mark.contract
    def test_add_multiple_items(self, factory):
        sb = self.create_widget(factory)
        sb.add_item("dashboard", "Dashboard")
        sb.add_item("users", "Users")
        sb.add_item("settings", "Settings")

    @pytest.mark.contract
    def test_set_active(self, factory):
        sb = self.create_widget(factory)
        sb.add_item("dashboard", "Dashboard")
        sb.add_item("users", "Users")
        sb.set_active("users")

    @pytest.mark.contract
    def test_on_select_registers(self, factory):
        sb = self.create_widget(factory)
        sb.add_item("dashboard", "Dashboard")
        sb.on_select(lambda key: None)

    @pytest.mark.contract
    def test_on_select_dispose_clears_callback(self, factory):
        sb = self.create_widget(factory)
        sb.add_item("dashboard", "Dashboard")
        handle = sb.on_select(lambda key: None)
        handle.dispose()
        assert sb._select_cb is None

    @pytest.mark.contract
    def test_set_collapsed_true(self, factory):
        sb = self.create_widget(factory)
        sb.set_collapsed(True)

    @pytest.mark.contract
    def test_set_collapsed_false(self, factory):
        sb = self.create_widget(factory)
        sb.set_collapsed(True)
        sb.set_collapsed(False)


class TestAppShellContract(_Common):
    widget_kind = APP_SHELL

    def create_widget(self, factory):
        return factory.create_app_shell()

    @pytest.mark.contract
    def test_set_header(self, factory):
        shell = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("Header")
        shell.set_header(lbl)

    @pytest.mark.contract
    def test_set_sidebar(self, factory):
        shell = self.create_widget(factory)
        sb = factory.create_sidebar()
        sb.add_item("home", "Home")
        shell.set_sidebar(sb)

    @pytest.mark.contract
    def test_set_content(self, factory):
        shell = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("Main content")
        shell.set_content(lbl)

    @pytest.mark.contract
    def test_set_footer(self, factory):
        shell = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("Footer")
        shell.set_footer(lbl)

    @pytest.mark.contract
    def test_full_shell(self, factory):
        """AppShell can have all four regions set without error."""
        shell = self.create_widget(factory)
        header = factory.create_label()
        header.set_text("Admin Demo")
        shell.set_header(header)

        sb = factory.create_sidebar()
        sb.add_item("dashboard", "Dashboard")
        sb.add_item("users", "Users")
        shell.set_sidebar(sb)

        content = factory.create_label()
        content.set_text("Welcome")
        shell.set_content(content)

        footer = factory.create_label()
        footer.set_text("v1.0.0")
        shell.set_footer(footer)


class TestBreadcrumbContract(_Common):
    widget_kind = BREADCRUMB

    def create_widget(self, factory):
        return factory.create_breadcrumb()

    @pytest.mark.contract
    @pytest.mark.parametrize("items", [
        [],
        [{"label": "Home"}],
        [
            {"label": "Home", "path": "/"},
            {"label": "Users", "path": "/users"},
            {"label": "Alice"},
        ],
    ], ids=["empty", "single", "trail"])
    def test_set_items(self, factory, items):
        bc = self.create_widget(factory)
        bc.set_items(items)

    @pytest.mark.contract
    def test_set_items_replaces(self, factory):
        """Calling set_items twice replaces the previous trail."""
        bc = self.create_widget(factory)
        bc.set_items([{"label": "Home", "path": "/"}, {"label": "Old"}])
        bc.set_items([{"label": "Home", "path": "/"}, {"label": "New"}])

    @pytest.mark.contract
    def test_on_click_registers(self, factory):
        bc = self.create_widget(factory)
        bc.on_click(lambda path: None)

    @pytest.mark.contract
    def test_on_click_dispose_clears_callback(self, factory):
        bc = self.create_widget(factory)
        handle = bc.on_click(lambda path: None)
        handle.dispose()
        assert bc._click_cb is None


class TestGaugeContract(_Common):
    widget_kind = GAUGE

    def create_widget(self, factory):
        return factory.create_gauge()

    @pytest.mark.contract
    def test_configure_gauge(self, factory):
        gauge = self.create_widget(factory)
        gauge.set_range(0, 120)
        gauge.set_label("Temperature")
        gauge.set_unit("°C")
        gauge.set_status("warn")
        gauge.set_value(88)


class TestChartContract(_Common):
    widget_kind = CHART

    def create_widget(self, factory):
        return factory.create_chart()

    @pytest.mark.contract
    def test_set_and_append_chart_data(self, factory):
        chart = self.create_widget(factory)
        chart.set_type("area")
        chart.set_title("Temperature")
        chart.set_max_points(3)
        chart.set_data([1, 2], [{"name": "T", "data": [20, 22]}])
        chart.append_data(3, [24])
        chart.append_data(4, [23])


class TestDrawerContract(_Common):
    widget_kind = DRAWER

    def create_widget(self, factory):
        return factory.create_drawer()

    @pytest.mark.contract
    def test_drawer_content_and_visibility(self, factory):
        drawer = self.create_widget(factory)
        label = factory.create_label()
        label.set_text("Settings")
        drawer.set_title("Details")
        drawer.set_content(label)
        drawer.open()
        assert drawer.is_open()
        drawer.toggle()
        assert not drawer.is_open()
