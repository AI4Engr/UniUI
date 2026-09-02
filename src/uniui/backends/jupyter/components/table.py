"""Table: HTML table with a hidden int widget bridging row clicks back to Python."""
from __future__ import annotations

from html import escape
from typing import Callable, Dict, List, Optional

import ipywidgets as widgets

from ...._adapter_mixins import JupyterEnableMixin, JupyterSizeMixin, JupyterVisibilityMixin
from ....components import ITable
from ....models.table import (
    CELL_ACTIONS, CELL_CHECKBOX, CELL_NUMBER, CELL_PROGRESS, CELL_STATUS,
    SELECTION_COLUMN_KEY, TableModel,
)
from ....state import Handle, safe_call
from ..runtime import M, html

class JupyterTableAdapter(JupyterVisibilityMixin, JupyterEnableMixin, JupyterSizeMixin, ITable):
    def __init__(self):
        self._model = TableModel()
        self._row_click_cb: Optional[Callable[[Dict], None]] = None
        self._row_action_cb: Optional[Callable[[Dict, str], None]] = None
        self._selection_change_cb: Optional[Callable[[List[Dict]], None]] = None
        #: The columns last passed to set_columns(), without the synthetic
        #: checkbox column - so a later set_columns() call after enabling
        #: multi-select can still re-prepend it.
        self._column_specs: List[Dict] = []
        self._table = html("", "uniui-table-html")
        self._message = html("", "uniui-table-message")
        self._message.layout.display = "none"
        self._bridge = widgets.BoundedIntText(value=-1, min=-1, max=1_000_000)
        self._bridge.layout.display = "none"
        self._bridge.add_class("uniui-table-bridge")
        self._bridge.observe(self._on_bridge, names="value")
        self._sort_bridge = widgets.Text(value="")
        self._sort_bridge.layout.display = "none"
        self._sort_bridge.add_class("uniui-table-sortbridge")
        self._sort_bridge.observe(self._on_sort_bridge, names="value")
        self._action_bridge = widgets.Text(value="")
        self._action_bridge.layout.display = "none"
        self._action_bridge.add_class("uniui-table-actionbridge")
        self._action_bridge.observe(self._on_action_bridge, names="value")
        self._selection_bridge = widgets.BoundedIntText(value=-1, min=-1, max=1_000_000)
        self._selection_bridge.layout.display = "none"
        self._selection_bridge.add_class("uniui-table-selectionbridge")
        self._selection_bridge.observe(self._on_selection_bridge, names="value")
        self._native = widgets.VBox([
            self._table, self._message, self._bridge, self._sort_bridge,
            self._action_bridge, self._selection_bridge,
        ])
        self._native.add_class("uniui-admin-table")

    def get_native(self): return self._native

    def set_selection_mode(self, mode: str) -> None:
        self._model.set_selection_mode(mode)
        self.set_columns(self._column_specs)

    def set_columns(self, columns: List[Dict]) -> None:
        self._column_specs = list(columns)
        effective = columns
        if self._model.selection_mode == "multiple":
            effective = [{"key": SELECTION_COLUMN_KEY, "label": "", "width": 40}] + list(columns)
        self._model.set_columns(effective)
        self._render()

    def set_rows(self, rows: List[Dict]) -> None:
        changed = self._model.set_rows(rows)
        self._render()
        self._sync_message()
        if changed:
            self._dispatch_selection_change()

    def set_sort(self, key: Optional[str], reverse: bool = False) -> None:
        self._model.set_sort(key, reverse)
        self._render()

    def set_page_size(self, size: Optional[int]) -> None:
        self._model.set_page_size(size)
        self._render()

    def set_page(self, page: int) -> None:
        self._model.set_page(page)
        self._render()

    def _header_cell(self, col) -> str:
        label = escape(col.label)
        if not col.sortable:
            return f"<th>{label}</th>"
        arrow = ""
        if self._model.sort_key == col.key:
            arrow = " ▼" if self._model.sort_reverse else " ▲"
        click = (
            "const root=this.closest('.uniui-admin-table'),input=root.querySelector("
            "'.uniui-table-sortbridge input');if(input){input.value='" + col.key +
            "';input.dispatchEvent(new Event('change',{bubbles:true}));}"
        )
        return f'<th class="uniui-sortable" onclick="{click}">{label}{arrow}</th>'

    def _action_click_js(self, index: int, action_id: str) -> str:
        """JS for a row-action button's onclick: writes "row:action" to the
        action bridge and stops the click from also bubbling up to the row
        (which would otherwise also fire the row-click bridge)."""
        payload = escape(f"{index}:{action_id}", quote=True)
        return (
            "event.stopPropagation();"
            "const root=this.closest('.uniui-admin-table'),input=root.querySelector("
            "'.uniui-table-actionbridge input');if(input){input.value='" + payload +
            "';input.dispatchEvent(new Event('change',{bubbles:true}));}"
        )

    def _selection_click_js(self, index: int) -> str:
        """JS for a checkbox cell's onclick: writes the row index to the
        selection bridge and stops the click from also bubbling up to the
        row (which would otherwise also fire the row-click bridge) - same
        idiom as _action_click_js."""
        return (
            "event.stopPropagation();"
            "const root=this.closest('.uniui-admin-table'),input=root.querySelector("
            "'.uniui-table-selectionbridge input');if(input){input.value='" + str(index) +
            "';input.dispatchEvent(new Event('change',{bubbles:true}));}"
        )

    def _render(self) -> None:
        headers = "".join(self._header_cell(col) for col in self._model.columns)
        rendered_rows = []
        for index, row in enumerate(self._model.display_rows()):
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
                elif kind == CELL_PROGRESS:
                    value = col.value_of(row)
                    try:
                        pct = max(0.0, min(100.0, float(value)))
                    except (TypeError, ValueError):
                        pct = 0.0
                    rendered_value = (
                        f'<progress class="uniui-table-progress" value="{pct}" '
                        f'max="100"></progress>'
                    )
                elif kind == CELL_ACTIONS:
                    buttons = []
                    for action in col.actions:
                        action_id = str(action.get("id", ""))
                        label = escape(str(action.get("label", "")))
                        click = self._action_click_js(index, action_id)
                        buttons.append(
                            f'<button type="button" class="uniui-table-action-btn" '
                            f'onclick="{click}">{label}</button>'
                        )
                    rendered_value = "".join(buttons)
                elif kind == CELL_CHECKBOX:
                    checked = "checked" if row in self._model.selected_rows else ""
                    click = self._selection_click_js(index)
                    rendered_value = (
                        f'<input type="checkbox" class="uniui-table-checkbox" '
                        f'{checked} onclick="{click}">'
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

    def on_row_action(self, fn: Callable[[Dict, str], None]) -> Handle:
        self._row_action_cb = fn
        def cancel():
            if self._row_action_cb is fn:
                self._row_action_cb = None
        return Handle(cancel)

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
                backend="jupyter", component="Table", method="on_selection_change",
            )

    def get_selected_row(self):
        rows = self.get_selected_rows()
        return rows[0] if rows else None

    def get_selected_rows(self) -> List[Dict]:
        return self._model.selected_rows

    def _on_action_bridge(self, change) -> None:
        value = change["new"]
        if not value:
            return
        index_str, _, action_id = value.partition(":")
        try:
            index = int(index_str)
        except ValueError:
            self._action_bridge.value = ""
            return
        row = self._model.row_at(index)
        if row is not None and self._row_action_cb:
            safe_call(
                self._row_action_cb, row, action_id,
                backend="jupyter", component="Table", method="on_row_action",
            )
        self._action_bridge.value = ""

    def _on_bridge(self, change) -> None:
        index = int(change["new"])
        clicked = self._model.row_at(index)
        if clicked is not None and self._model.select_row(clicked):
            self._dispatch_selection_change()
        if clicked is not None and self._row_click_cb:
            safe_call(self._row_click_cb, clicked, backend="jupyter", component="Table", method="on_row_click")
        if index != -1:
            self._bridge.value = -1

    def _on_selection_bridge(self, change) -> None:
        index = int(change["new"])
        row = self._model.row_at(index)
        if row is not None and self._model.toggle_row_selection(row):
            self._render()
            self._dispatch_selection_change()
        if index != -1:
            self._selection_bridge.value = -1

    def _on_sort_bridge(self, change) -> None:
        key = change["new"]
        if key:
            self._model.toggle_sort(key)
            self._render()
            self._sort_bridge.value = ""


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
.uniui-admin-table th.uniui-sortable {{cursor:pointer; user-select:none}}
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
.uniui-table-progress {{width:100%; height:8px; -webkit-appearance:none; -moz-appearance:none; appearance:none;
  border:none; border-radius:4px; overflow:hidden; vertical-align:middle}}
.uniui-table-progress::-webkit-progress-bar {{background:var(--uniui-border); border-radius:4px}}
.uniui-table-progress::-webkit-progress-value {{background:var(--uniui-accent); border-radius:4px}}
.uniui-table-progress::-moz-progress-bar {{background:var(--uniui-accent); border-radius:4px}}
.uniui-table-action-btn {{
  cursor:pointer; border:none; border-radius:6px; padding:4px 10px; margin-right:6px;
  font-size:12px; font-weight:600; color:var(--uniui-text); background:var(--uniui-surface_subtle);
}}
.uniui-table-checkbox {{cursor:pointer; width:16px; height:16px; accent-color:var(--uniui-accent)}}
.uniui-table-action-btn:hover {{background:var(--uniui-border)}}
.uniui-table-message, .uniui-table-message p {{margin:20px 0;text-align:center;color:var(--uniui-text_muted)}}"""
