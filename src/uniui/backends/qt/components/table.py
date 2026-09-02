"""Qt ITable: a data table with semantic status pills and an overlay."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from PySide2 import QtCore, QtGui, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import ITable
from ....models.status import classify_status, status_token_names
from ....models.table import ALIGN_RIGHT, SELECTION_COLUMN_KEY, TableModel
from ....state import Handle, safe_call
from ..icons import admin_icon
from ..runtime import C, M, track_themed
from ..styles import scrollbar_rules

def _table_style() -> str:
    return f"""
    QTableView {{
        background: {C['surface']};
        border: 1px solid {C['border']};
        border-radius: 10px;
        gridline-color: {C['border']};
        font-size: 13px;
        color: {C['text']};
        outline: none;
    }}
    QTableView::item {{
        padding: 0 14px;
        border: none;
    }}
    QTableView::item:hover {{
        background: {C['surface_subtle']};
    }}
    QTableView::item:alternate {{
        background: {C['row_alt']};
    }}
    QTableView::item:selected {{
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


def _paint_cell_chrome(delegate, painter, option, index) -> None:
    """Paint an item's background/selection/hover chrome without its text.

    Custom cell delegates (progress bars, action buttons) still need the
    normal selection highlight and alternating-row background under their
    own painting, but must not let the base style draw the raw cell text
    underneath. Blanking ``QStyleOptionViewItem.text`` (and even its
    ``HasDisplay`` feature bit) is not enough - ``QStyledItemDelegate.paint()``
    still leaves a faint ghost of the model's real DisplayRole value peeking
    out on at least this Qt/style combination. Drawing only the
    ``PE_PanelItemViewItem`` primitive (background/selection/hover, no text)
    sidesteps the whole text-painting path instead of fighting it.
    """
    base_option = QtWidgets.QStyleOptionViewItem(option)
    delegate.initStyleOption(base_option, index)
    base_option.text = ""
    style = base_option.widget.style() if base_option.widget else QtWidgets.QApplication.style()
    style.drawPrimitive(QtWidgets.QStyle.PE_PanelItemViewItem, base_option, painter, base_option.widget)


class _ProgressCellDelegate(QtWidgets.QStyledItemDelegate):
    """Paint a progress-column cell as a rounded track + filled chunk.

    Paint-only - a progress cell isn't interactive, so no editorEvent().
    """

    def paint(self, painter, option, index) -> None:
        _paint_cell_chrome(self, painter, option, index)

        raw = index.data(QtCore.Qt.DisplayRole)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = 0.0
        value = max(0.0, min(100.0, value))

        track_height = 8
        track = QtCore.QRect(
            option.rect.left() + 8,
            option.rect.center().y() - track_height // 2,
            option.rect.width() - 16,
            track_height,
        )
        if track.width() <= 0:
            return
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(C["border"]))
        radius = track_height / 2
        painter.drawRoundedRect(track, radius, radius)

        chunk_width = round(track.width() * (value / 100.0))
        if chunk_width > 0:
            chunk = QtCore.QRect(track.left(), track.top(), chunk_width, track.height())
            painter.setBrush(QtGui.QColor(C["accent"]))
            painter.drawRoundedRect(chunk, radius, radius)
        painter.restore()


class _ActionButtonDelegate(QtWidgets.QStyledItemDelegate):
    """Paint row action buttons and dispatch clicks back to the adapter.

    Needs the shared TableModel (to resolve a column's actions and a
    clicked row) and a dispatch callback (to fire the adapter's
    on_row_action callback) - both passed in rather than holding a
    reference to the whole adapter, so this delegate doesn't need to know
    anything about QtTableAdapter beyond what it uses.
    """

    GAP = 4

    def __init__(self, model: TableModel, dispatch: Callable[[Dict, str], None], parent=None):
        super().__init__(parent)
        self._model = model
        self._dispatch = dispatch

    def _action_rects(self, option, actions: List[Dict]) -> List[QtCore.QRect]:
        """One equal-width rect per action, inset from the cell edges with
        a small gap between them. Used by both paint() and editorEvent() so
        hit-testing and visuals never disagree."""
        if not actions:
            return []
        inset = 6
        available = QtCore.QRect(
            option.rect.left() + inset,
            option.rect.top() + inset,
            option.rect.width() - 2 * inset,
            option.rect.height() - 2 * inset,
        )
        count = len(actions)
        total_gap = self.GAP * (count - 1)
        width = max(1, (available.width() - total_gap) // count)
        rects = []
        x = available.left()
        for _ in actions:
            rects.append(QtCore.QRect(x, available.top(), width, available.height()))
            x += width + self.GAP
        return rects

    def paint(self, painter, option, index) -> None:
        _paint_cell_chrome(self, painter, option, index)

        col = self._model.columns[index.column()]
        actions = col.actions
        rects = self._action_rects(option, actions)
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        for action, rect in zip(actions, rects):
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor(C["surface_subtle"]))
            painter.drawRoundedRect(rect, 6, 6)

            icon_name = action.get("icon")
            if icon_name:
                icon = admin_icon(icon_name, C["text"])
                icon_size = min(16, rect.height() - 4)
                pixmap = icon.pixmap(icon_size, icon_size)
                x = rect.center().x() - pixmap.width() // 2
                y = rect.center().y() - pixmap.height() // 2
                painter.drawPixmap(x, y, pixmap)
            else:
                painter.setPen(QtGui.QColor(C["text"]))
                font = QtGui.QFont(option.font)
                font.setPixelSize(11)
                painter.setFont(font)
                metrics = QtGui.QFontMetrics(font)
                label = metrics.elidedText(
                    str(action.get("label", "")), QtCore.Qt.ElideRight, max(1, rect.width() - 8)
                )
                painter.drawText(rect, QtCore.Qt.AlignCenter, label)
        painter.restore()

    def editorEvent(self, event, model, option, index) -> bool:
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            col = self._model.columns[index.column()]
            actions = col.actions
            rects = self._action_rects(option, actions)
            for action, rect in zip(actions, rects):
                if rect.contains(event.pos()):
                    row = self._model.row_at(index.row())
                    if row is not None:
                        self._dispatch(row, action["id"])
                    return True
        return super().editorEvent(event, model, option, index)


class _CheckboxDelegate(QtWidgets.QStyledItemDelegate):
    """Paint the multi-select checkbox column and dispatch toggle clicks.

    Same shape as _ActionButtonDelegate: needs the shared TableModel (to
    resolve the clicked row and its current selection state) and a dispatch
    callback (to fire the adapter's on_selection_change callback).
    """

    SIZE = 16

    def __init__(self, model: TableModel, dispatch: Callable[[], None], parent=None):
        super().__init__(parent)
        self._model = model
        self._dispatch = dispatch

    def _box_rect(self, option) -> QtCore.QRect:
        """The checkbox's square hit/paint rect, centered in the cell. Used
        by both paint() and editorEvent() so hit-testing and visuals never
        disagree."""
        return QtCore.QRect(
            option.rect.center().x() - self.SIZE // 2,
            option.rect.center().y() - self.SIZE // 2,
            self.SIZE, self.SIZE,
        )

    def paint(self, painter, option, index) -> None:
        _paint_cell_chrome(self, painter, option, index)

        row = self._model.row_at(index.row())
        checked = row is not None and row in self._model.selected_rows
        box = self._box_rect(option)
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if checked:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor(C["accent"]))
            painter.drawRoundedRect(box, 4, 4)
            painter.setPen(QtGui.QPen(QtGui.QColor(C["surface"]), 2))
            painter.drawLine(
                box.left() + 3, box.center().y(),
                box.center().x() - 1, box.bottom() - 3,
            )
            painter.drawLine(
                box.center().x() - 1, box.bottom() - 3,
                box.right() - 2, box.top() + 3,
            )
        else:
            painter.setPen(QtGui.QPen(QtGui.QColor(C["border"]), 1.5))
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRoundedRect(box, 4, 4)
        painter.restore()

    def editorEvent(self, event, model, option, index) -> bool:
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if self._box_rect(option).contains(event.pos()):
                row = self._model.row_at(index.row())
                if row is not None and self._model.toggle_row_selection(row):
                    self._dispatch()
                return True
        return super().editorEvent(event, model, option, index)


class _TableGridModel(QtCore.QAbstractTableModel):
    def __init__(self, model: TableModel):
        super().__init__()
        self._model = model

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._model.display_rows())

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._model.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        col = self._model.columns[index.column()]
        row = self._model.display_rows()[index.row()]
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return col.text_of(row)
        if role == QtCore.Qt.TextAlignmentRole:
            horizontal = QtCore.Qt.AlignRight if col.align == ALIGN_RIGHT else QtCore.Qt.AlignLeft
            return int(horizontal | QtCore.Qt.AlignVCenter)
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._model.header_labels()[section].upper()
        return None

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def refresh(self) -> None:
        """Call after any TableModel mutation (set_rows/set_sort/set_page/
        set_columns) - full reset. Rows have no stable identity in the
        shared TableModel (see its own docstring), so incremental
        row-level dataChanged would require inventing a row-id mechanism
        across the shared model layer used by all three backends - out of
        scope. QTableView repaints efficiently on reset without the
        per-cell Python object allocation QTableWidget required, so this
        is still a real improvement, just not row-diffed."""
        self.beginResetModel()
        self.endResetModel()


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

        self._table = QtWidgets.QTableView()
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
        self._progress_delegate = _ProgressCellDelegate(self._table)

        self._overlay = QtWidgets.QLabel("")
        self._overlay.setAlignment(QtCore.Qt.AlignCenter)
        self._overlay.setStyleSheet(
            f"color: {C['text_muted']}; font-size: 14px; background: transparent;"
        )
        self._overlay.hide()

        vbox.addWidget(self._table)
        vbox.addWidget(self._overlay)

        self._model = TableModel()
        self._grid_model = _TableGridModel(self._model)
        self._table.setModel(self._grid_model)
        self._row_click_cb: Optional[Callable] = None
        self._row_action_cb: Optional[Callable] = None
        self._selection_change_cb: Optional[Callable] = None
        #: The columns last passed to set_columns(), without the synthetic
        #: checkbox column - so a later set_columns() call after enabling
        #: multi-select can still re-prepend it.
        self._column_specs: List[Dict] = []
        self._action_delegate = _ActionButtonDelegate(
            self._model, self._dispatch_row_action, self._table
        )
        self._checkbox_delegate = _CheckboxDelegate(
            self._model, self._dispatch_selection_change, self._table
        )
        self._table.clicked.connect(self._on_clicked)
        track_themed(self, self._container)
        self.apply_theme()

    def get_native(self): return self._container

    def set_selection_mode(self, mode: str) -> None:
        self._model.set_selection_mode(mode)
        self.set_columns(self._column_specs)

    def set_columns(self, columns: List[Dict]) -> None:
        self._column_specs = list(columns)
        effective = columns
        if self._model.selection_mode == "multiple":
            effective = [{"key": SELECTION_COLUMN_KEY, "label": "", "width": 40}] + list(columns)
        self._model.set_columns(effective)
        self._grid_model.refresh()
        for i, col in enumerate(self._model.columns):
            if col.is_checkbox:
                self._table.setItemDelegateForColumn(i, self._checkbox_delegate)
            elif col.is_status:
                self._table.setItemDelegateForColumn(i, self._status_delegate)
            elif col.is_progress:
                self._table.setItemDelegateForColumn(i, self._progress_delegate)
            elif col.is_actions:
                self._table.setItemDelegateForColumn(i, self._action_delegate)
            if col.width is not None:
                self._table.setColumnWidth(i, col.width)
                self._table.horizontalHeader().setSectionResizeMode(
                    i, QtWidgets.QHeaderView.Fixed
                )

    def set_rows(self, rows: List[Dict]) -> None:
        changed = self._model.set_rows(rows)
        self._grid_model.refresh()
        self._sync_overlay()
        if changed:
            self._dispatch_selection_change()

    def set_sort(self, key: Optional[str], reverse: bool = False) -> None:
        self._model.set_sort(key, reverse)
        self._grid_model.refresh()
        self._sync_sort_indicator()

    def set_page_size(self, size: Optional[int]) -> None:
        self._model.set_page_size(size)
        self._grid_model.refresh()

    def set_page(self, page: int) -> None:
        self._model.set_page(page)
        self._grid_model.refresh()

    def apply_theme(self) -> None:
        self._container.setStyleSheet(f"background: {C['surface']};")
        self._table.setStyleSheet(_table_style())
        self._overlay.setStyleSheet(
            f"color: {C['text_muted']}; font-size: 14px; background: transparent;"
        )
        self._table.viewport().update()

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

    def on_row_action(self, fn: Callable[[Dict, str], None]) -> Handle:
        self._row_action_cb = fn
        def cancel():
            if self._row_action_cb is fn:
                self._row_action_cb = None
        return Handle(cancel)

    def _dispatch_row_action(self, row: Dict, action_id: str) -> None:
        if self._row_action_cb:
            safe_call(
                self._row_action_cb, row, action_id,
                backend="qt", component="Table", method="on_row_action",
            )

    def on_selection_change(self, fn: Callable[[List[Dict]], None]) -> Handle:
        self._selection_change_cb = fn
        def cancel():
            if self._selection_change_cb is fn:
                self._selection_change_cb = None
        return Handle(cancel)

    def _dispatch_selection_change(self) -> None:
        if self._selection_change_cb:
            safe_call(
                self._selection_change_cb, self._model.selected_rows,
                backend="qt", component="Table", method="on_selection_change",
            )

    def get_selected_row(self):
        rows = self.get_selected_rows()
        return rows[0] if rows else None

    def get_selected_rows(self) -> List[Dict]:
        return self._model.selected_rows

    def _on_clicked(self, index) -> None:
        self._on_cell_clicked(index.row(), index.column())

    def _on_cell_clicked(self, row: int, col: int) -> None:
        clicked = self._model.row_at(row)
        if self._model.select_row(clicked):
            self._dispatch_selection_change()
        if self._row_click_cb and clicked is not None:
            safe_call(self._row_click_cb, clicked, backend="qt", component="Table", method="on_row_click")

    def _on_header_clicked(self, index: int) -> None:
        columns = self._model.columns
        if not (0 <= index < len(columns)) or not columns[index].sortable:
            return
        self._model.toggle_sort(columns[index].key)
        self._grid_model.refresh()
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
