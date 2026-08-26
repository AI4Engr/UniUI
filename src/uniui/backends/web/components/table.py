"""Table: a Quasar table whose status column is rendered by a Vue slot."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from nicegui import ui

from ....components import ITable
from ....models.status import status_class_expression_js
from ....models.table import TableModel
from ....state import Handle, safe_call
from ..primitives import _WebAdapter
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
            {
                "name": c.key, "label": c.label, "field": c.key, "align": c.align,
                "sortable": c.sortable,
            }
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
        self._model.set_rows(rows); self._table.rows = self._display_rows(); self._table.update()
        self._sync_message()
    def set_sort(self, key: Optional[str], reverse: bool = False) -> None:
        self._model.set_sort(key, reverse)
        self._table.rows = self._display_rows()
        self._table.update()
    def _display_rows(self) -> List[Dict]:
        """sorted_rows(), with any column.format() applied.

        Quasar renders straight from these dicts' field values - unlike Qt
        and Jupyter, it never calls Column.text_of() - so a column's format
        callable has to be applied here or it would silently have no effect
        on this backend.

        Known caveat: the browser's rowClick event reports back whatever
        dict is in ``self._table.rows``, so on_row_click's payload carries
        the *formatted* string for a formatted column, not its original
        value - unlike Qt/Jupyter, which always resolve clicks against the
        raw model. Narrow enough (only affects code reading a formatted
        column's value out of a click payload) that it's documented here
        rather than solved with position-based click resolution.
        """
        rows = self._model.sorted_rows()
        formatted = [c for c in self._model.columns if c.source.get("format")]
        if not formatted:
            return rows
        result = []
        for row in rows:
            display = dict(row)
            for col in formatted:
                display[col.key] = col.text_of(row)
            result.append(display)
        return result
    def set_loading(self, loading: bool) -> None:
        self._model.set_loading(loading); self._sync_message()
    def set_error(self, message: str) -> None:
        self._model.set_error(message); self._sync_message()
    def _sync_message(self) -> None:
        overlay = self._model.shows_overlay
        self._table.set_visibility(not overlay)
        self._message.set_text(self._model.overlay_text())
        self._message.set_visibility(overlay)
    def on_row_click(self, fn: Callable[[Dict], None]) -> Handle:
        self._row_click_cb = fn
        def cancel():
            if self._row_click_cb is fn:
                self._row_click_cb = None
        return Handle(cancel)
    def _on_row_event(self, event) -> None:
        args = getattr(event, "args", None)
        row = args.get("row") if isinstance(args, dict) else None
        if row is None and isinstance(args, (list, tuple)) and args:
            row = args[-1]
        if self._row_click_cb and isinstance(row, dict):
            safe_call(self._row_click_cb, row, backend="web", component="Table", method="on_row_click")


def table_css() -> str:
    """The Table CSS fragment, composed into the sheet by ``styles.install_admin_css``.

    Includes the status-pill rules: the pill is a table-cell rendering concern
    and its markup is emitted by this module.
    """
    return """        .uniui-web-table {width:100%;color:var(--uniui-text);background:var(--uniui-surface);border:1px solid var(--uniui-border);
          border-radius:10px;box-shadow:none!important;overflow:hidden;font-family:inherit}
        .uniui-web-table .q-table__container,.uniui-web-table .q-table__card {box-shadow:none!important;background:transparent}
        .uniui-web-table thead tr {height:44px;background:var(--uniui-surface);color:var(--uniui-text_muted);
          border-bottom:1px solid var(--uniui-border)}
        .uniui-web-table thead th {font-size:var(--uniui-stat-label-size);font-weight:600}
        .uniui-web-table tbody td {height:52px;font-size:13px;border-color:var(--uniui-border)}
        .uniui-web-table tbody tr:hover {background:var(--uniui-surface_subtle)}
        .uniui-web-table .q-table__bottom {min-height:42px;border-top:1px solid var(--uniui-border);color:var(--uniui-text_muted);font-size:12px}
"""


def status_pill_css() -> str:
    """The status-pill rules, emitted after the drawer block.

    Separate from :func:`table_css` only to preserve the original rule order in
    the emitted sheet - CSS is order-sensitive, and these sat further down.
    """
    return """        .uniui-status-pill {display:inline-flex;align-items:center;min-height:24px;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:700}
        .uniui-status-pill.uniui-status-ok {color:var(--uniui-status_ok_fg);background:var(--uniui-status_ok_bg)}
        .uniui-status-pill.uniui-status-warn {color:var(--uniui-status_warn_fg);background:var(--uniui-status_warn_bg)}
        .uniui-status-pill.uniui-status-error {color:var(--uniui-status_error_fg);background:var(--uniui-status_error_bg)}
        .uniui-status-pill.uniui-status-neutral {color:var(--uniui-status_neutral_fg);background:var(--uniui-status_neutral_bg)}
"""
