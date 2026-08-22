"""Tests for the shared table model and the three backends that consume it."""
import pytest

from uniui.models.table import (
    ALIGN_LEFT,
    ALIGN_RIGHT,
    CELL_NUMBER,
    CELL_STATUS,
    CELL_TEXT,
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
