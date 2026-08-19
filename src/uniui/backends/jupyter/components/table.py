"""Table: HTML table with a hidden int widget bridging row clicks back to Python."""
from __future__ import annotations

from html import escape
from typing import Callable, Dict, List, Optional

import ipywidgets as widgets

from ....components import ITable
from ....models.table import CELL_NUMBER, CELL_STATUS, TableModel
from ....state import Handle, safe_call
from ..runtime import M, html

class JupyterTableAdapter(ITable):
    def __init__(self):
        self._model = TableModel()
        self._row_click_cb: Optional[Callable[[Dict], None]] = None
        self._table = html("", "uniui-table-html")
        self._message = html("", "uniui-table-message")
        self._message.layout.display = "none"
        self._bridge = widgets.BoundedIntText(value=-1, min=-1, max=1_000_000)
        self._bridge.layout.display = "none"
        self._bridge.add_class("uniui-table-bridge")
        self._bridge.observe(self._on_bridge, names="value")
        self._native = widgets.VBox([self._table, self._message, self._bridge])
        self._native.add_class("uniui-admin-table")

    def get_native(self): return self._native

    def set_columns(self, columns: List[Dict]) -> None:
        self._model.set_columns(columns)
        self._render()

    def set_rows(self, rows: List[Dict]) -> None:
        self._model.set_rows(rows)
        self._render()

    def _render(self) -> None:
        headers = "".join(
            f"<th>{escape(col.label)}</th>" for col in self._model.columns
        )
        rendered_rows = []
        for index, row in enumerate(self._model.rows):
            cells = []
            for col in self._model.columns:
                kind = col.cell_kind
                classes = []
                rendered_value = escape(col.text_of(row))
                if kind == CELL_NUMBER:
                    classes.append("uniui-number")
                elif kind == CELL_STATUS:
                    rendered_value = (
                        f'<span class="uniui-status-pill '
                        f'uniui-status-{col.status_of(row)}">'
                        f"{rendered_value}</span>"
                    )
                class_attr = f' class="{" ".join(classes)}"' if classes else ""
                cells.append(f"<td{class_attr}>{rendered_value}</td>")
            click = (
                "const root=this.closest('.uniui-admin-table'),input=root.querySelector(" 
                "'.uniui-table-bridge input');if(input){input.value='" + str(index) +
                "';input.dispatchEvent(new Event('change',{bubbles:true}));}"
            )
            rendered_rows.append(f'<tr onclick="{click}">{"".join(cells)}</tr>')
        self._table.value = (
            f'<div class="uniui-admin-table-wrap"><table><thead><tr>{headers}</tr></thead>'
            f'<tbody>{"".join(rendered_rows)}</tbody></table></div>'
        )

    def set_loading(self, loading: bool) -> None:
        self._model.set_loading(loading)
        self._sync_message()

    def set_error(self, message: str) -> None:
        self._model.set_error(message)
        self._sync_message()

    def _sync_message(self) -> None:
        if self._model.shows_overlay:
            self._table.layout.display = "none"
            text = self._model.overlay_text(" &nbsp;", escape)
            self._message.value = f"<p>{text}</p>"
            self._message.layout.display = None
        else:
            self._message.layout.display = "none"
            self._table.layout.display = None

    def on_row_click(self, fn: Callable[[Dict], None]) -> Handle:
        self._row_click_cb = fn
        def cancel():
            if self._row_click_cb is fn:
                self._row_click_cb = None
        return Handle(cancel)

    def _on_bridge(self, change) -> None:
        index = int(change["new"])
        clicked = self._model.row_at(index)
        if clicked is not None and self._row_click_cb:
            safe_call(self._row_click_cb, clicked, backend="jupyter", component="Table", method="on_row_click")
        if index != -1:
            self._bridge.value = -1


def table_css() -> str:
    """The Table CSS fragment, composed into the shell sheet by ``styles.css``.

    Includes the status-pill rules: the pill is a table-cell rendering concern
    and its markup is emitted by this module.
    """
    return f""".uniui-admin-table {{width:100%; min-width:0}}
.uniui-admin-table table {{width:100%; border-collapse:separate; border-spacing:0; color:var(--uniui-text); font-size:13px}}
.uniui-admin-table th {{
  padding:10px 12px; text-align:left; color:var(--uniui-text_muted);
  background:var(--uniui-surface); border-bottom:1px solid var(--uniui-border);
  font-size:{M['stat_label_size']}px; font-weight:600;
}}
.uniui-admin-table td {{padding:11px 12px;border-bottom:1px solid var(--uniui-border)}}
.uniui-admin-table tbody tr {{cursor:pointer}}
.uniui-admin-table tbody tr:hover {{background:var(--uniui-surface_subtle)}}
.uniui-admin-table .uniui-number {{text-align:right}}
.uniui-status-pill {{display:inline-flex;align-items:center;min-height:24px;padding:3px 9px;
  border-radius:999px;font-size:11px;font-weight:700}}
.uniui-status-pill.uniui-status-ok {{color:var(--uniui-status_ok_fg);background:var(--uniui-status_ok_bg)}}
.uniui-status-pill.uniui-status-warn {{color:var(--uniui-status_warn_fg);background:var(--uniui-status_warn_bg)}}
.uniui-status-pill.uniui-status-error {{color:var(--uniui-status_error_fg);background:var(--uniui-status_error_bg)}}
.uniui-status-pill.uniui-status-neutral {{color:var(--uniui-status_neutral_fg);background:var(--uniui-status_neutral_bg)}}
.uniui-table-message, .uniui-table-message p {{margin:20px 0;text-align:center;color:var(--uniui-text_muted)}}"""
