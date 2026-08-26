"""Tests for the shared table model and the three backends that consume it."""
import pytest

from uniui.models.table import (
    ALIGN_LEFT,
    ALIGN_RIGHT,
    CELL_NUMBER,
    CELL_STATUS,
    CELL_TEXT,
    EMPTY_TEXT,
    LOADING_TEXT,
    NUMERIC_COLUMN_KEYS,
    Column,
    TableModel,
)

COLUMNS = [
    {"key": "id", "label": "ID"},
    {"key": "amount", "label": "Amount"},
    {"key": "status", "label": "Status"},
]


class TestColumn:
    def test_label_falls_back_to_key(self):
        assert Column({"key": "id"}).label == "id"

    def test_missing_key_yields_empty_strings(self):
        col = Column({})
        assert col.key == ""
        assert col.label == ""

    def test_label_and_key_are_coerced_to_str(self):
        col = Column({"key": 7, "label": 9})
        assert col.key == "7"
        assert col.label == "9"

    def test_width_is_optional_and_coerced(self):
        assert Column({"key": "id"}).width is None
        assert Column({"key": "id", "width": "80"}).width == 80

    @pytest.mark.parametrize("key", sorted(NUMERIC_COLUMN_KEYS))
    def test_numeric_columns_are_right_aligned(self, key):
        col = Column({"key": key})
        assert col.is_numeric
        assert col.align == ALIGN_RIGHT
        assert col.cell_kind == CELL_NUMBER

    def test_other_columns_are_left_aligned_text(self):
        col = Column({"key": "name"})
        assert not col.is_numeric
        assert col.align == ALIGN_LEFT
        assert col.cell_kind == CELL_TEXT

    def test_status_column_is_left_aligned_but_a_pill(self):
        col = Column({"key": "status"})
        assert col.is_status
        assert col.align == ALIGN_LEFT
        assert col.cell_kind == CELL_STATUS

    def test_missing_cell_renders_blank_not_none(self):
        """A missing key must not print the string "None" in the cell."""
        col = Column({"key": "absent"})
        assert col.value_of({}) == ""
        assert col.text_of({}) == ""

    def test_explicit_none_also_renders_blank(self):
        col = Column({"key": "x"})
        assert col.text_of({"x": None}) == ""

    def test_falsy_values_are_preserved(self):
        """0 and "" are real values, not missing ones."""
        col = Column({"key": "x"})
        assert col.text_of({"x": 0}) == "0"
        assert col.text_of({"x": False}) == "False"

    def test_status_of_classifies(self):
        col = Column({"key": "status"})
        assert col.status_of({"status": "  Delivered "}) == "ok"
        assert col.status_of({"status": "mystery"}) == "neutral"

    def test_source_dict_is_kept_for_backend_specific_keys(self):
        spec = {"key": "id", "sortable": True}
        assert Column(spec).source is spec

    def test_format_overrides_plain_str_rendering(self):
        col = Column({"key": "amount", "format": lambda v: f"${v:,.2f}"})
        assert col.text_of({"amount": 1234.5}) == "$1,234.50"

    def test_format_does_not_change_the_sort_value(self):
        """Sorting must use the raw value, not the formatted string."""
        col = Column({"key": "amount", "format": lambda v: f"${v:,.2f}"})
        assert col.value_of({"amount": 1234.5}) == 1234.5

    def test_format_does_not_run_on_a_missing_cell(self):
        """A formatter written for a real value has no reason to handle ''."""
        calls = []

        def fmt(v):
            calls.append(v)
            return f"${v}"

        col = Column({"key": "amount", "format": fmt})
        assert col.text_of({}) == ""
        assert calls == []

    def test_a_raising_formatter_falls_back_to_the_unformatted_text(self):
        def bad_format(v):
            raise ValueError("boom")

        col = Column({"key": "amount", "format": bad_format})
        assert col.text_of({"amount": 5}) == "5"

    def test_no_format_key_behaves_as_before(self):
        col = Column({"key": "name"})
        assert col.text_of({"name": "Alice"}) == "Alice"


class TestTableModel:
    def test_starts_empty_and_visible(self):
        model = TableModel()
        assert model.columns == []
        assert model.rows == []
        assert not model.loading
        assert model.error == ""
        assert not model.shows_overlay
        assert model.overlay_text() == ""

    def test_set_columns_normalises(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        assert model.header_labels() == ["ID", "Amount", "Status"]
        assert [c.align for c in model.columns] == [
            ALIGN_LEFT, ALIGN_RIGHT, ALIGN_LEFT
        ]

    def test_has_status_column(self):
        model = TableModel()
        model.set_columns([{"key": "id"}])
        assert not model.has_status_column
        model.set_columns(COLUMNS)
        assert model.has_status_column

    def test_set_rows_copies_the_sequence(self):
        """Mutating the caller's list must not change the table."""
        model = TableModel()
        rows = [{"id": 1}]
        model.set_rows(rows)
        rows.append({"id": 2})
        assert len(model.rows) == 1

    def test_cells_follow_column_order(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        assert model.cells({"status": "ok", "id": 3, "amount": 9}) == [3, 9, "ok"]

    def test_row_at_in_range(self):
        model = TableModel()
        model.set_rows([{"id": 1}, {"id": 2}])
        assert model.row_at(0) == {"id": 1}
        assert model.row_at(1) == {"id": 2}

    @pytest.mark.parametrize("index", [-1, -5, 2, 99])
    def test_row_at_out_of_range_returns_none(self, index):
        """Negative indices must not wrap - they mean "nothing selected"."""
        model = TableModel()
        model.set_rows([{"id": 1}, {"id": 2}])
        assert model.row_at(index) is None

    def test_row_at_on_empty_table(self):
        assert TableModel().row_at(0) is None


class TestSelection:
    def test_nothing_selected_by_default(self):
        model = TableModel()
        model.set_rows([{"id": 1}])
        assert model.selected_row is None

    def test_select_row(self):
        model = TableModel()
        model.set_rows([{"id": 1}, {"id": 2}])
        model.select_row({"id": 2})
        assert model.selected_row == {"id": 2}

    def test_select_row_none_clears_it(self):
        model = TableModel()
        model.set_rows([{"id": 1}])
        model.select_row({"id": 1})
        model.select_row(None)
        assert model.selected_row is None

    def test_selecting_a_different_row_replaces_the_previous_one(self):
        model = TableModel()
        model.set_rows([{"id": 1}, {"id": 2}])
        model.select_row({"id": 1})
        model.select_row({"id": 2})
        assert model.selected_row == {"id": 2}

    def test_set_rows_clears_a_selection_that_no_longer_exists(self):
        model = TableModel()
        model.set_rows([{"id": 1}])
        model.select_row({"id": 1})
        model.set_rows([{"id": 2}])
        assert model.selected_row is None

    def test_set_rows_keeps_a_selection_still_present_in_the_new_data(self):
        model = TableModel()
        model.set_rows([{"id": 1}, {"id": 2}])
        model.select_row({"id": 1})
        model.set_rows([{"id": 1}, {"id": 3}])
        assert model.selected_row == {"id": 1}


class TestPagination:
    def test_disabled_by_default(self):
        model = TableModel()
        model.set_rows([{"id": i} for i in range(5)])
        assert model.page_size is None
        assert model.page_count == 1
        assert model.display_rows() == model.sorted_rows()

    def test_page_size_slices_rows(self):
        model = TableModel()
        model.set_rows([{"id": i} for i in range(5)])
        model.set_page_size(2)
        assert model.display_rows() == [{"id": 0}, {"id": 1}]

    def test_set_page_navigates(self):
        model = TableModel()
        model.set_rows([{"id": i} for i in range(5)])
        model.set_page_size(2)
        model.set_page(1)
        assert model.display_rows() == [{"id": 2}, {"id": 3}]
        model.set_page(2)
        assert model.display_rows() == [{"id": 4}]

    def test_page_count_rounds_up(self):
        model = TableModel()
        model.set_rows([{"id": i} for i in range(5)])
        model.set_page_size(2)
        assert model.page_count == 3

    def test_page_count_is_at_least_one_for_zero_rows(self):
        model = TableModel()
        model.set_rows([])
        model.set_page_size(10)
        assert model.page_count == 1
        assert model.display_rows() == []

    def test_set_page_clamps_to_the_last_page(self):
        model = TableModel()
        model.set_rows([{"id": i} for i in range(5)])
        model.set_page_size(2)
        model.set_page(99)
        assert model.page == 2
        assert model.display_rows() == [{"id": 4}]

    def test_set_page_clamps_negative_to_zero(self):
        model = TableModel()
        model.set_rows([{"id": i} for i in range(5)])
        model.set_page_size(2)
        model.set_page(-1)
        assert model.page == 0

    def test_set_page_size_resets_to_the_first_page(self):
        model = TableModel()
        model.set_rows([{"id": i} for i in range(5)])
        model.set_page_size(2)
        model.set_page(2)
        model.set_page_size(3)
        assert model.page == 0

    def test_new_rows_reset_to_the_first_page(self):
        model = TableModel()
        model.set_rows([{"id": i} for i in range(5)])
        model.set_page_size(2)
        model.set_page(2)
        model.set_rows([{"id": i} for i in range(5)])
        assert model.page == 0

    def test_zero_page_size_disables_pagination(self):
        model = TableModel()
        model.set_rows([{"id": i} for i in range(5)])
        model.set_page_size(2)
        model.set_page_size(0)
        assert model.page_size is None
        assert len(model.display_rows()) == 5

    def test_pagination_applies_after_sorting(self):
        model = TableModel()
        model.set_columns([{"key": "id"}])
        model.set_rows([{"id": "c"}, {"id": "a"}, {"id": "b"}])
        model.set_sort("id")
        model.set_page_size(2)
        assert model.display_rows() == [{"id": "a"}, {"id": "b"}]

    def test_changing_sort_resets_to_the_first_page(self):
        model = TableModel()
        model.set_columns([{"key": "id"}])
        model.set_rows([{"id": i} for i in range(5)])
        model.set_page_size(2)
        model.set_page(2)
        model.set_sort("id")
        assert model.page == 0

    def test_row_at_indexes_into_the_current_page(self):
        model = TableModel()
        model.set_rows([{"id": i} for i in range(5)])
        model.set_page_size(2)
        model.set_page(1)
        assert model.row_at(0) == {"id": 2}
        assert model.row_at(2) is None, "index 2 is out of range for a 2-row page"


class TestSorting:
    def test_unsorted_by_default(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        model.set_rows([{"id": 2}, {"id": 1}])
        assert model.sort_key is None
        assert model.sorted_rows() == [{"id": 2}, {"id": 1}]

    def test_sort_ascending_by_string_key(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        model.set_rows([{"id": "banana"}, {"id": "apple"}])
        model.set_sort("id")
        assert model.sorted_rows() == [{"id": "apple"}, {"id": "banana"}]

    def test_sort_descending(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        model.set_rows([{"id": "apple"}, {"id": "banana"}])
        model.set_sort("id", reverse=True)
        assert model.sorted_rows() == [{"id": "banana"}, {"id": "apple"}]

    def test_sort_numeric_column_compares_numerically_not_lexically(self):
        """Lexical sort would put "10" before "2" - numeric columns must not."""
        model = TableModel()
        model.set_columns(COLUMNS)
        model.set_rows([{"amount": 10}, {"amount": 2}])
        model.set_sort("amount")
        assert model.sorted_rows() == [{"amount": 2}, {"amount": 10}]

    def test_sort_numeric_column_tolerates_non_numeric_values(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        model.set_rows([{"amount": 5}, {"amount": "n/a"}])
        model.set_sort("amount")
        assert model.sorted_rows() == [{"amount": 5}, {"amount": "n/a"}]

    def test_set_sort_ignores_unknown_column(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        model.set_rows([{"id": 2}, {"id": 1}])
        model.set_sort("nope")
        assert model.sort_key is None
        assert model.sorted_rows() == [{"id": 2}, {"id": 1}]

    def test_set_sort_none_clears(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        model.set_rows([{"id": 2}, {"id": 1}])
        model.set_sort("id")
        model.set_sort(None)
        assert model.sort_key is None
        assert model.sorted_rows() == [{"id": 2}, {"id": 1}]

    def test_toggle_sort_cycles_asc_desc_none(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        model.toggle_sort("id")
        assert (model.sort_key, model.sort_reverse) == ("id", False)
        model.toggle_sort("id")
        assert (model.sort_key, model.sort_reverse) == ("id", True)
        model.toggle_sort("id")
        assert model.sort_key is None

    def test_toggle_sort_switching_columns_resets_to_ascending(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        model.toggle_sort("id")
        model.toggle_sort("id")  # now descending
        model.toggle_sort("amount")
        assert (model.sort_key, model.sort_reverse) == ("amount", False)

    def test_sort_does_not_mutate_underlying_rows(self):
        """Display order changes; the rows a future set_rows() diffs against don't."""
        model = TableModel()
        model.set_columns(COLUMNS)
        rows = [{"id": 2}, {"id": 1}]
        model.set_rows(rows)
        model.set_sort("id")
        assert model.rows == [{"id": 2}, {"id": 1}]

    def test_row_at_reflects_sorted_order(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        model.set_rows([{"id": 2}, {"id": 1}])
        model.set_sort("id")
        assert model.row_at(0) == {"id": 1}
        assert model.row_at(1) == {"id": 2}

    def test_column_sortable_defaults_false(self):
        assert not Column({"key": "id"}).sortable

    def test_column_sortable_reads_source_dict(self):
        assert Column({"key": "id", "sortable": True}).sortable


class TestOverlay:
    def test_loading_text(self):
        model = TableModel()
        model.set_loading(True)
        assert model.shows_overlay
        assert model.overlay_text() == LOADING_TEXT

    def test_error_text(self):
        model = TableModel()
        model.set_error("boom")
        assert model.shows_overlay
        assert model.overlay_text() == "⚠  boom"

    def test_error_separator_is_configurable(self):
        model = TableModel()
        model.set_error("boom")
        assert model.overlay_text(" &nbsp;") == "⚠ &nbsp;boom"

    def test_escape_applies_to_the_message_only(self):
        """The separator must survive an HTML escaper unchanged."""
        model = TableModel()
        model.set_error("<b>x</b>")
        from html import escape

        assert model.overlay_text(" &nbsp;", escape) == "⚠ &nbsp;&lt;b&gt;x&lt;/b&gt;"

    def test_error_outranks_loading(self):
        """A failed fetch beats claiming rows are still on their way."""
        model = TableModel()
        model.set_loading(True)
        model.set_error("boom")
        assert model.overlay_text() == "⚠  boom"

    def test_clearing_error_while_loading_falls_back_to_loading(self):
        model = TableModel()
        model.set_loading(True)
        model.set_error("boom")
        model.set_error("")
        assert model.overlay_text() == LOADING_TEXT

    @pytest.mark.parametrize("blank", ["", None])
    def test_blank_error_clears(self, blank):
        model = TableModel()
        model.set_error("boom")
        model.set_error(blank)
        assert model.error == ""
        assert not model.shows_overlay

    def test_clearing_loading_keeps_the_error_visible(self):
        """The Web backend used to reveal the table here, hiding the error."""
        model = TableModel()
        model.set_error("boom")
        model.set_loading(True)
        model.set_loading(False)
        assert model.shows_overlay
        assert model.overlay_text() == "⚠  boom"


class TestEmptyState:
    def test_never_populated_is_not_empty(self):
        """A table that hasn't had set_rows() called yet is not "empty" -
        it just hasn't loaded, so it must not show a "No data" placeholder."""
        model = TableModel()
        assert not model.is_empty
        assert not model.shows_overlay
        assert model.overlay_text() == ""

    def test_set_rows_with_zero_rows_is_empty(self):
        model = TableModel()
        model.set_rows([])
        assert model.is_empty
        assert model.shows_overlay
        assert model.overlay_text() == EMPTY_TEXT

    def test_set_rows_with_data_is_not_empty(self):
        model = TableModel()
        model.set_rows([{"id": 1}])
        assert not model.is_empty
        assert not model.shows_overlay

    def test_clearing_rows_after_data_becomes_empty(self):
        model = TableModel()
        model.set_rows([{"id": 1}])
        model.set_rows([])
        assert model.is_empty
        assert model.overlay_text() == EMPTY_TEXT

    def test_repopulating_after_empty_clears_the_placeholder(self):
        model = TableModel()
        model.set_rows([])
        model.set_rows([{"id": 1}])
        assert not model.is_empty
        assert not model.shows_overlay

    def test_loading_outranks_empty(self):
        """A refresh that clears rows before repopulating must keep showing
        "Loading…", not flash "No data" in between."""
        model = TableModel()
        model.set_rows([])
        model.set_loading(True)
        assert model.overlay_text() == LOADING_TEXT

    def test_error_outranks_empty(self):
        model = TableModel()
        model.set_rows([])
        model.set_error("boom")
        assert model.overlay_text() == "⚠  boom"


class TestBackendsAgree:
    """Every backend must make the same column and row-lookup decisions."""

    ROWS = [
        {"id": 1, "amount": 10, "status": "Delivered"},
        {"id": 2, "amount": 20, "status": "mystery"},
    ]

    def _qt(self):
        pytest.importorskip("PySide2")
        pytest.importorskip("PySide2.QtWidgets")
        from uniui import qt_components
        from PySide2 import QtWidgets

        if QtWidgets.QApplication.instance() is None:
            QtWidgets.QApplication([])
        table = qt_components.QtTableAdapter()
        table.set_columns(COLUMNS)
        table.set_rows(self.ROWS)
        return table

    def _jupyter(self):
        pytest.importorskip("ipywidgets")
        from uniui.jupyter_components import JupyterTableAdapter

        table = JupyterTableAdapter()
        table.set_columns(COLUMNS)
        table.set_rows(self.ROWS)
        return table

    def test_qt_right_aligns_only_the_amount_column(self):
        from PySide2 import QtCore

        table = self._qt()
        aligns = [
            table._table.item(0, c).textAlignment() & QtCore.Qt.AlignHorizontal_Mask
            for c in range(3)
        ]
        assert aligns == [
            QtCore.Qt.AlignLeft, QtCore.Qt.AlignRight, QtCore.Qt.AlignLeft
        ]

    def test_qt_set_rows_reuses_unchanged_cell_items(self):
        """set_rows() must update existing QTableWidgetItems in place rather
        than rebuilding every cell — this is what makes it "update existing
        native controls" instead of "rebuild the whole tree" on every call.
        """
        table = self._qt()
        unchanged_item = table._table.item(0, 0)
        changed_item = table._table.item(1, 1)

        new_rows = [
            dict(self.ROWS[0]),                          # row 0: identical
            {**self.ROWS[1], "amount": 999},              # row 1: amount changed
            {"id": 3, "amount": 30, "status": "Pending"},  # row 2: new
        ]
        table.set_rows(new_rows)

        assert table._table.item(0, 0) is unchanged_item, (
            "a cell whose text didn't change must keep the same item object"
        )
        assert table._table.item(1, 1) is changed_item, (
            "a changed cell must still reuse the same item object, just with new text"
        )
        assert table._table.item(1, 1).text() == "999"
        assert table._table.item(2, 0).text() == "3"
        assert table._table.rowCount() == 3

        table.set_rows(new_rows[:1])
        assert table._table.rowCount() == 1

    def test_jupyter_marks_only_the_amount_column_numeric(self):
        html = self._jupyter()._table.value
        assert html.count("uniui-number") == len(self.ROWS)

    def test_jupyter_renders_a_pill_per_row(self):
        html = self._jupyter()._table.value
        assert "uniui-status-ok" in html
        assert "uniui-status-neutral" in html

    def test_qt_row_click_uses_the_shared_bounds_check(self):
        table = self._qt()
        seen = []
        table.on_row_click(seen.append)
        table._on_cell_clicked(1, 0)
        table._on_cell_clicked(99, 0)
        table._on_cell_clicked(-1, 0)
        assert seen == [self.ROWS[1]]

    def test_jupyter_row_click_uses_the_shared_bounds_check(self):
        table = self._jupyter()
        seen = []
        table.on_row_click(seen.append)
        table._on_bridge({"new": 1})
        table._on_bridge({"new": 99})
        assert seen == [self.ROWS[1]]

    def test_qt_clicking_a_row_selects_it(self):
        table = self._qt()
        assert table.get_selected_row() is None
        table._on_cell_clicked(1, 0)
        assert table.get_selected_row() == self.ROWS[1]

    def test_qt_clicking_out_of_range_does_not_select_anything(self):
        table = self._qt()
        table._on_cell_clicked(99, 0)
        assert table.get_selected_row() is None

    def test_jupyter_clicking_a_row_selects_it(self):
        table = self._jupyter()
        assert table.get_selected_row() is None
        table._on_bridge({"new": 1})
        assert table.get_selected_row() == self.ROWS[1]

    def test_web_clicking_a_row_selects_it(self):
        pytest.importorskip("nicegui")
        from uniui.web_components import WebTableAdapter

        table = WebTableAdapter()
        table.set_columns(COLUMNS)
        table.set_rows(self.ROWS)
        assert table.get_selected_row() is None

        class Event:
            args = {"row": self.ROWS[1]}

        table._on_row_event(Event())
        assert table.get_selected_row() == self.ROWS[1]

    def test_qt_header_click_sorts_and_updates_indicator(self):
        from PySide2 import QtCore

        table = self._qt()
        table.set_columns([{"key": "id", "label": "ID", "sortable": True}])
        table.set_rows([{"id": "banana"}, {"id": "apple"}])

        table._on_header_clicked(0)
        assert table._table.item(0, 0).text() == "apple"
        assert table._table.horizontalHeader().sortIndicatorSection() == 0
        assert table._table.horizontalHeader().sortIndicatorOrder() == QtCore.Qt.AscendingOrder

        table._on_header_clicked(0)
        assert table._table.item(0, 0).text() == "banana"
        assert table._table.horizontalHeader().sortIndicatorOrder() == QtCore.Qt.DescendingOrder

    def test_qt_empty_rows_shows_the_overlay_and_hides_the_table(self):
        table = self._qt()  # already populated with self.ROWS
        assert table._table.isHidden() is False
        table.set_rows([])
        assert table._table.isHidden() is True
        assert table._overlay.isHidden() is False
        assert table._overlay.text() == "No data"

    def test_qt_repopulating_hides_the_overlay_again(self):
        table = self._qt()
        table.set_rows([])
        table.set_rows(self.ROWS)
        assert table._table.isHidden() is False
        assert table._overlay.isHidden() is True

    def test_jupyter_empty_rows_shows_the_overlay_and_hides_the_table(self):
        table = self._jupyter()
        table.set_rows([])
        assert table._table.layout.display == "none"
        assert table._message.layout.display is None
        assert "No data" in table._message.value

    def test_web_empty_rows_shows_the_overlay_and_hides_the_table(self):
        pytest.importorskip("nicegui")
        from uniui.web_components import WebTableAdapter

        table = WebTableAdapter()
        table.set_columns(COLUMNS)
        table.set_rows([])
        assert table._message.text == "No data"

    def test_qt_header_click_ignores_non_sortable_column(self):
        table = self._qt()
        table.set_columns(COLUMNS)  # none declared sortable
        table.set_rows(self.ROWS)
        table._on_header_clicked(0)
        assert table._model.sort_key is None

    def test_jupyter_header_click_sorts_via_bridge(self):
        table = self._jupyter()
        table.set_columns([{"key": "id", "label": "ID", "sortable": True}])
        table.set_rows([{"id": "banana"}, {"id": "apple"}])

        table._on_sort_bridge({"new": "id"})
        assert table._model.sort_key == "id"
        assert table._model.sorted_rows() == [{"id": "apple"}, {"id": "banana"}]
        assert table._table.value.index("apple") < table._table.value.index("banana")

    def test_qt_format_reaches_the_rendered_cell(self):
        table = self._qt()
        table.set_columns([{"key": "amount", "label": "Amount", "format": lambda v: f"${v:,.2f}"}])
        table.set_rows([{"amount": 1234.5}])
        assert table._table.item(0, 0).text() == "$1,234.50"

    def test_jupyter_format_reaches_the_rendered_cell(self):
        table = self._jupyter()
        table.set_columns([{"key": "amount", "label": "Amount", "format": lambda v: f"${v:,.2f}"}])
        table.set_rows([{"amount": 1234.5}])
        assert "$1,234.50" in table._table.value

    def test_web_format_reaches_the_rendered_row(self):
        pytest.importorskip("nicegui")
        from uniui.web_components import WebTableAdapter

        table = WebTableAdapter()
        table.set_columns([{"key": "amount", "label": "Amount", "format": lambda v: f"${v:,.2f}"}])
        table.set_rows([{"amount": 1234.5}])
        assert table._table.rows == [{"amount": "$1,234.50"}]

    def test_qt_set_page_size_reaches_the_rendered_table(self):
        table = self._qt()  # 2 rows from self.ROWS
        table.set_page_size(1)
        assert table._table.rowCount() == 1
        table.set_page(1)
        assert table._table.rowCount() == 1
        assert table._table.item(0, 0).text() == str(self.ROWS[1]["id"])

    def test_jupyter_set_page_size_reaches_the_rendered_table(self):
        table = self._jupyter()  # 2 rows from self.ROWS
        table.set_page_size(1)
        table.set_page(1)
        html = table._table.value
        assert html.count("<tr") == 2, "only the header row and one data row must render"
        assert "Delivered" not in html, "page 0's row must not still be there"
        assert "mystery" in html, "page 1's row must be the one that renders"

    def test_web_set_page_size_reaches_the_rendered_rows(self):
        pytest.importorskip("nicegui")
        from uniui.web_components import WebTableAdapter

        table = WebTableAdapter()
        table.set_columns(COLUMNS)
        table.set_rows(self.ROWS)
        table.set_page_size(1)
        table.set_page(1)
        assert table._table.rows == [self.ROWS[1]]

    def test_web_set_sort_reorders_the_native_rows(self):
        pytest.importorskip("nicegui")
        from uniui.web_components import WebTableAdapter

        table = WebTableAdapter()
        table.set_columns([{"key": "id", "label": "ID", "sortable": True}])
        table.set_rows([{"id": "banana"}, {"id": "apple"}])
        table.set_sort("id")
        assert table._table.rows == [{"id": "apple"}, {"id": "banana"}]

    def test_all_backends_agree_on_header_labels(self):
        model = TableModel()
        model.set_columns(COLUMNS)
        expected = model.header_labels()

        jupyter_html = self._jupyter()._table.value
        for label in expected:
            assert f"<th>{label}</th>" in jupyter_html

        qt_table = self._qt()._table
        # Qt upper-cases its headers; that is a Qt styling choice, not a
        # different label.
        assert [
            qt_table.horizontalHeaderItem(i).text() for i in range(3)
        ] == [label.upper() for label in expected]
