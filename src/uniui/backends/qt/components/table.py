"""Qt ITable: a data table with semantic status pills and an overlay."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from PySide2 import QtCore, QtGui, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import ITable
from ....models.status import classify_status, status_token_names
from ....models.table import ALIGN_RIGHT, TableModel
from ....state import Handle, safe_call
from ..runtime import C, M, track_themed
from ..styles import scrollbar_rules

def _table_style() -> str:
    return f"""
    QTableWidget {{
        background: {C['surface']};
        border: 1px solid {C['border']};
        border-radius: 10px;
        gridline-color: {C['border']};
        font-size: 13px;
        color: {C['text']};
        outline: none;
    }}
    QTableWidget::item {{
        padding: 0 14px;
        border: none;
    }}
    QTableWidget::item:hover {{
        background: {C['surface_subtle']};
    }}
    QTableWidget::item:alternate {{
        background: {C['row_alt']};
    }}
    QTableWidget::item:selected {{
        background: {C['row_sel']};
        color: {C['row_sel_fg']};
    }}
    QHeaderView::section {{
        background: {C['surface']};
        color: {C['text_muted']};
        font-weight: 600;
        font-size: {M['stat_label_size']}px;
        padding: 0 14px;
        border: none;
        border-bottom: 1px solid {C['border']};
    }}
    {scrollbar_rules()}
"""


def _status_colors(value) -> Tuple[str, str]:
    """Return the ``(foreground, background)`` pill colours for a cell value."""
    fg_token, bg_token = status_token_names(classify_status(value))
    return C[fg_token], C[bg_token]


class _StatusPillDelegate(QtWidgets.QStyledItemDelegate):
    """Paint status values as compact semantic pills matching the Web table."""

    def paint(self, painter, option, index) -> None:
        base_option = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(base_option, index)
        base_option.text = ""
        super().paint(painter, base_option, index)

        text = str(index.data(QtCore.Qt.DisplayRole) or "")
        foreground, background = _status_colors(text)
        font = QtGui.QFont(option.font)
        font.setPixelSize(11)
        font.setWeight(QtGui.QFont.DemiBold)
        metrics = QtGui.QFontMetrics(font)
        pill_width = min(option.rect.width() - 16, metrics.horizontalAdvance(text) + 20)
        if pill_width <= 8:
            return
        pill = QtCore.QRect(
            option.rect.left() + 8,
            option.rect.center().y() - 12,
            pill_width,
            24,
        )
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(background))
        painter.drawRoundedRect(pill, 12, 12)
        painter.setFont(font)
        painter.setPen(QtGui.QColor(foreground))
        text = metrics.elidedText(
            text, QtCore.Qt.ElideRight, max(1, pill.width() - 12)
        )
        painter.drawText(pill, QtCore.Qt.AlignCenter, text)
        painter.restore()


class QtTableAdapter(VisibilityMixin, EnableMixin, SizeMixin, ITable):
    def __init__(self):
        self._container = QtWidgets.QWidget()
        self._container.setMinimumWidth(0)
        self._container.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding
        )
        self._container.setStyleSheet(f"background: {C['surface']};")
        vbox = QtWidgets.QVBoxLayout(self._container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        self._table = QtWidgets.QTableWidget()
        self._table.setStyleSheet(_table_style())
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive
        )
        self._table.horizontalHeader().setSectionsClickable(True)
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self._table.setShowGrid(False)
        self._table.setFocusPolicy(QtCore.Qt.StrongFocus)
        self._table.setWordWrap(False)
        self._table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._table.setMouseTracking(True)
        self._table.verticalHeader().setDefaultSectionSize(52)
        self._table.horizontalHeader().setFixedHeight(44)
        self._status_delegate = _StatusPillDelegate(self._table)

        self._overlay = QtWidgets.QLabel("")
        self._overlay.setAlignment(QtCore.Qt.AlignCenter)
        self._overlay.setStyleSheet(
            f"color: {C['text_muted']}; font-size: 14px; background: transparent;"
        )
        self._overlay.hide()

        vbox.addWidget(self._table)
        vbox.addWidget(self._overlay)

        self._model = TableModel()
        self._row_click_cb: Optional[Callable] = None
        self._table.cellClicked.connect(self._on_cell_clicked)
        track_themed(self, self._container)
        self.apply_theme()

    def get_native(self): return self._container

    def set_columns(self, columns: List[Dict]) -> None:
        self._model.set_columns(columns)
        self._table.setColumnCount(len(self._model.columns))
        self._table.setHorizontalHeaderLabels(
            [label.upper() for label in self._model.header_labels()]
        )
        for i, col in enumerate(self._model.columns):
            if col.is_status:
                self._table.setItemDelegateForColumn(i, self._status_delegate)
            if col.width is not None:
                self._table.setColumnWidth(i, col.width)
                self._table.horizontalHeader().setSectionResizeMode(
                    i, QtWidgets.QHeaderView.Fixed
                )

    def set_rows(self, rows: List[Dict]) -> None:
        self._model.set_rows(rows)
        self._render_rows()

    def set_sort(self, key: Optional[str], reverse: bool = False) -> None:
        self._model.set_sort(key, reverse)
        self._render_rows()
        self._sync_sort_indicator()

    def _render_rows(self) -> None:
        """Update existing ``QTableWidgetItem``s in place instead of
        rebuilding every cell. Rows have no stable identity in the model
        (see ``TableModel``), so this diffs positionally: a row index that
        existed before and still exists keeps its items, only its text is
        touched (and only when it actually changed); rows beyond the
        previous count are created fresh; ``setRowCount`` shrinking handles
        removed trailing rows (Qt deletes their items automatically).
        """
        old_row_count = self._table.rowCount()
        display_rows = self._model.sorted_rows()
        columns = self._model.columns

        self._table.setRowCount(len(display_rows))
        for r_idx, row in enumerate(display_rows):
            for c_idx, col in enumerate(columns):
                text = col.text_of(row)
                item = self._table.item(r_idx, c_idx) if r_idx < old_row_count else None
                if item is None:
                    item = QtWidgets.QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                    self._table.setItem(r_idx, c_idx, item)
                elif item.text() != text:
                    item.setText(text)
                self._style_item(item, col)

    def _style_item(self, item, col) -> None:
        horizontal = (
            QtCore.Qt.AlignRight if col.align == ALIGN_RIGHT else QtCore.Qt.AlignLeft
        )
        item.setTextAlignment(horizontal | QtCore.Qt.AlignVCenter)

    def apply_theme(self) -> None:
        self._container.setStyleSheet(f"background: {C['surface']};")
        self._table.setStyleSheet(_table_style())
        self._overlay.setStyleSheet(
            f"color: {C['text_muted']}; font-size: 14px; background: transparent;"
        )
        self._table.viewport().update()
        for r_idx in range(len(self._model.rows)):
            for c_idx, col in enumerate(self._model.columns):
                item = self._table.item(r_idx, c_idx)
                if item is not None:
                    self._style_item(item, col)

    def set_loading(self, loading: bool) -> None:
        self._model.set_loading(loading)
        self._sync_overlay()

    def set_error(self, message: str) -> None:
        self._model.set_error(message)
        self._sync_overlay()

    def _sync_overlay(self) -> None:
        if self._model.shows_overlay:
            self._table.hide()
            self._overlay.setText(self._model.overlay_text())
            self._overlay.show()
        else:
            self._overlay.hide()
            self._table.show()

    def on_row_click(self, fn: Callable[[Dict], None]) -> Handle:
        self._row_click_cb = fn
        def cancel():
            if self._row_click_cb is fn:
                self._row_click_cb = None
        return Handle(cancel)

    def _on_cell_clicked(self, row: int, col: int) -> None:
        clicked = self._model.row_at(row)
        if self._row_click_cb and clicked is not None:
            safe_call(self._row_click_cb, clicked, backend="qt", component="Table", method="on_row_click")

    def _on_header_clicked(self, index: int) -> None:
        columns = self._model.columns
        if not (0 <= index < len(columns)) or not columns[index].sortable:
            return
        self._model.toggle_sort(columns[index].key)
        self._render_rows()
        self._sync_sort_indicator()

    def _sync_sort_indicator(self) -> None:
        header = self._table.horizontalHeader()
        columns = self._model.columns
        index = next(
            (i for i, col in enumerate(columns) if col.key == self._model.sort_key), -1
        )
        if index < 0:
            header.setSortIndicatorShown(False)
            return
        order = QtCore.Qt.DescendingOrder if self._model.sort_reverse else QtCore.Qt.AscendingOrder
        header.setSortIndicator(index, order)
        header.setSortIndicatorShown(True)
