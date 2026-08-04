"""Table: a Quasar table whose status column is rendered by a Vue slot."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from nicegui import ui

from ....components import ITable
from ....models.status import status_class_expression_js
from ....models.table import TableModel
from ....web import _WebAdapter
from ..styles import install_admin_css

class WebTableAdapter(_WebAdapter, ITable):
    def __init__(self):
        install_admin_css()
        self._model = TableModel()
        self._row_click_cb: Optional[Callable[[Dict], None]] = None
        root = ui.column().classes("w-full items-stretch gap-0")
        with root:
            self._table = ui.table(columns=[], rows=[], pagination={"rowsPerPage": 0}).classes("uniui-web-table")
            self._message = ui.label("").classes("self-center q-pa-lg")
        self._message.set_visibility(False)
        self._table.on("rowClick", self._on_row_event)
        super().__init__(root)

    def set_columns(self, columns: List[Dict]) -> None:
        self._model.set_columns(columns)
        self._table.columns = [
            {"name": c.key, "label": c.label, "field": c.key, "align": c.align}
            for c in self._model.columns
        ]
        if self._model.has_status_column:
            # Classification happens in the browser, so the vocabulary is
            # generated from the shared status model rather than restated here.
            self._table.add_slot(
                "body-cell-status",
                f"""
                <q-td :props="props">
                  <span class="uniui-status-pill"
                    :class="{status_class_expression_js()}">{{{{ props.value }}}}</span>
                </q-td>
                """,
            )
        self._table.update()
    def set_rows(self, rows: List[Dict]) -> None:
        self._model.set_rows(rows); self._table.rows = self._model.rows; self._table.update()
    def set_loading(self, loading: bool) -> None:
        self._model.set_loading(loading); self._sync_message()
    def set_error(self, message: str) -> None:
        self._model.set_error(message); self._sync_message()
    def _sync_message(self) -> None:
        overlay = self._model.shows_overlay
        self._table.set_visibility(not overlay)
        self._message.set_text(self._model.overlay_text())
        self._message.set_visibility(overlay)
    def on_row_click(self, fn: Callable[[Dict], None]) -> None: self._row_click_cb = fn
    def _on_row_event(self, event) -> None:
        args = getattr(event, "args", None)
        row = args.get("row") if isinstance(args, dict) else None
        if row is None and isinstance(args, (list, tuple)) and args:
            row = args[-1]
        if self._row_click_cb and isinstance(row, dict): self._row_click_cb(row)
