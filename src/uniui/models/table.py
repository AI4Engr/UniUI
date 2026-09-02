"""Shared presentation model for data tables.

Each backend used to keep its own copy of the column list, the row list, and
the rules for deciding how a cell should be presented - which columns are
numeric, which column holds a status, and what the loading/error overlay says.
The copies had already drifted apart in the numeric-column set's ordering and
in how a missing key was handled, so this model owns those rules.

The model deliberately stops short of rendering. It answers *what* a cell
means (``ALIGN_RIGHT``, ``CELL_STATUS``) and leaves *how* to show it to the
backend, because a QSS text alignment, a CSS class, and a Quasar column
descriptor have nothing in common but the decision behind them.
"""
from typing import Any, Callable, Dict, List, Optional, Sequence

from .status import classify_status

#: Column keys rendered right-aligned. These are amounts, so aligning the
#: digits matters more than matching the header.
NUMERIC_COLUMN_KEYS = frozenset({"amount", "price", "total"})

#: The column key that carries a semantic status and renders as a pill.
STATUS_COLUMN_KEY = "status"

#: Semantic cell kinds a backend must be able to render.
CELL_TEXT = "text"
CELL_NUMBER = "number"
CELL_STATUS = "status"
CELL_PROGRESS = "progress"
CELL_ACTIONS = "actions"

#: Semantic alignments. Backends map these to QSS flags or CSS/Quasar values.
ALIGN_LEFT = "left"
ALIGN_RIGHT = "right"

#: Overlay text shown while rows are being fetched.
LOADING_TEXT = "Loading…"

#: Overlay text shown when a fetch completed but returned zero rows.
EMPTY_TEXT = "No data"

_ERROR_PREFIX = "⚠"


class Column:
    """A normalised table column.

    Backends receive these instead of raw dicts so that the fallback rules for
    a missing ``label`` or ``key`` are applied in exactly one place.
    """

    __slots__ = ("key", "label", "width", "source")

    def __init__(self, spec: Dict) -> None:
        self.key = str(spec.get("key", ""))
        self.label = str(spec.get("label", self.key))
        width = spec.get("width")
        self.width = int(width) if width is not None else None
        #: The original dict, so a backend can read keys this model does not
        #: model yet without having to be updated in lockstep.
        self.source = spec

    @property
    def is_numeric(self) -> bool:
        return self.key in NUMERIC_COLUMN_KEYS

    @property
    def is_status(self) -> bool:
        return self.key == STATUS_COLUMN_KEY

    @property
    def is_progress(self) -> bool:
        return self.source.get("cell") == "progress"

    @property
    def is_actions(self) -> bool:
        return self.source.get("cell") == "actions"

    @property
    def actions(self) -> List[Dict]:
        """Row action-button specs for an actions column.

        Each item: {"id": str, "label": str, "icon": Optional[str]}.
        """
        return self.source.get("actions", [])

    @property
    def sortable(self) -> bool:
        return bool(self.source.get("sortable", False))

    @property
    def cell_kind(self) -> str:
        """The semantic kind of every cell in this column.

        Status, progress, and actions are all explicit opt-ins - status via
        the fixed "status" key name, progress/actions via the "cell" key -
        so they're checked before the numeric key-name inference, which is
        the only kind that's ever inferred rather than declared.
        """
        if self.is_status:
            return CELL_STATUS
        if self.is_progress:
            return CELL_PROGRESS
        if self.is_actions:
            return CELL_ACTIONS
        if self.is_numeric:
            return CELL_NUMBER
        return CELL_TEXT

    @property
    def align(self) -> str:
        return ALIGN_RIGHT if self.is_numeric else ALIGN_LEFT

    def value_of(self, row: Dict) -> Any:
        """Read this column's cell out of ``row``.

        Missing keys become ``""`` rather than ``None`` so that every backend
        renders a blank cell instead of the string ``"None"``.
        """
        value = row.get(self.key, "")
        return "" if value is None else value

    def text_of(self, row: Dict) -> str:
        """The cell's display text, before any backend-specific escaping.

        A column may supply a ``{"format": callable}`` in its spec to
        override the plain ``str(value)`` rendering (e.g. currency, date
        formatting). It never runs on a missing/blank cell - a formatter
        written for a real value has no reason to also handle "", and a
        formatter that raises falls back to the unformatted text rather than
        breaking the whole table's render.

        An actions column has no meaningful text value - it only hosts
        buttons - so it short-circuits to "". A progress column is *not*
        short-circuited: its numeric value still has a legitimate text
        rendering (a backend may want it as a fallback or tooltip even
        though the primary rendering is a progress bar), so it falls
        through to the normal formatting below.
        """
        if self.is_actions:
            return ""
        value = self.value_of(row)
        formatter = self.source.get("format")
        if formatter is not None and value != "":
            try:
                return str(formatter(value))
            except Exception:
                pass
        return str(value)

    def status_of(self, row: Dict) -> str:
        """The semantic status of this row's cell, for status columns."""
        return classify_status(self.value_of(row))

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Column(key={self.key!r}, label={self.label!r})"


class TableModel:
    """Column/row state plus the loading and error overlay decisions.

    Backends own their native table widget and their event wiring; they ask
    this model what to display and whether the table or the overlay is
    currently visible.
    """

    __slots__ = (
        "_columns", "_rows", "_rows_set", "_loading", "_error",
        "_sort_key", "_sort_reverse", "_selected_row",
        "_page_size", "_page",
    )

    def __init__(self) -> None:
        self._columns: List[Column] = []
        self._rows: List[Dict] = []
        #: Whether set_rows() has ever been called. A model that was simply
        #: never populated yet must not show the empty-state placeholder -
        #: only a fetch that genuinely returned nothing should.
        self._rows_set = False
        self._loading = False
        self._error = ""
        self._selected_row: Optional[Dict] = None
        self._sort_key: Optional[str] = None
        self._sort_reverse = False
        #: None = pagination disabled (every row displays).
        self._page_size: Optional[int] = None
        self._page = 0

    # -- columns and rows ------------------------------------------------
    @property
    def columns(self) -> List[Column]:
        return self._columns

    @property
    def rows(self) -> List[Dict]:
        return self._rows

    def set_columns(self, columns: Sequence[Dict]) -> None:
        self._columns = [Column(spec) for spec in columns]

    def set_rows(self, rows: Sequence[Dict]) -> None:
        self._rows = list(rows)
        self._rows_set = True
        self._page = 0
        if self._selected_row is not None and self._selected_row not in self._rows:
            self._selected_row = None

    # -- selection ---------------------------------------------------------
    def select_row(self, row: Optional[Dict]) -> None:
        """Mark ``row`` as selected, or clear the selection with ``None``.

        Rows have no stable identity in this model (see the module
        docstring), so selection is by value: a later ``set_rows()`` that no
        longer contains an equal row clears it automatically rather than
        leaving a stale selection pointing at data that's gone.
        """
        self._selected_row = row

    @property
    def selected_row(self) -> Optional[Dict]:
        return self._selected_row

    @property
    def has_status_column(self) -> bool:
        """Whether any column needs the status-pill treatment."""
        return any(col.is_status for col in self._columns)

    @property
    def has_progress_column(self) -> bool:
        """Whether any column needs the progress-bar treatment."""
        return any(col.is_progress for col in self._columns)

    @property
    def has_action_column(self) -> bool:
        """Whether any column needs the row-action-buttons treatment."""
        return any(col.is_actions for col in self._columns)

    def header_labels(self) -> List[str]:
        return [col.label for col in self._columns]

    def cells(self, row: Dict) -> List[Any]:
        """Raw cell values for ``row``, in column order."""
        return [col.value_of(row) for col in self._columns]

    def row_at(self, index: int) -> Optional[Dict]:
        """Return the displayed row at ``index``, or ``None`` if out of range.

        Every backend reports clicks as an integer index into whatever is
        currently on screen, which is ``display_rows()`` — not necessarily
        the order ``set_rows()`` was called with, and not necessarily every
        row if pagination is active. Negative indices are rejected rather
        than wrapping, because a negative index from a UI event means
        "nothing selected", not "count from the end".
        """
        rows = self.display_rows()
        if 0 <= index < len(rows):
            return rows[index]
        return None

    # -- sorting -----------------------------------------------------------
    @property
    def sort_key(self) -> Optional[str]:
        return self._sort_key

    @property
    def sort_reverse(self) -> bool:
        return self._sort_reverse

    def set_sort(self, key: Optional[str], reverse: bool = False) -> None:
        """Sort displayed rows by column ``key``; ``None`` clears sorting.

        Display order only — the row data itself (``self._rows``, what a
        future ``set_rows()`` diffs against) is never reordered.
        """
        if key is not None and not any(col.key == key for col in self._columns):
            return
        self._sort_key = key
        self._sort_reverse = bool(reverse)
        self._page = 0

    def toggle_sort(self, key: str) -> None:
        """Cycle a column through ascending, descending, then unsorted."""
        if self._sort_key != key:
            self.set_sort(key, reverse=False)
        elif not self._sort_reverse:
            self.set_sort(key, reverse=True)
        else:
            self.set_sort(None)

    def sorted_rows(self) -> List[Dict]:
        """Rows in display order: unsorted rows if no sort is active."""
        if self._sort_key is None:
            return self._rows
        column = next((col for col in self._columns if col.key == self._sort_key), None)
        if column is None:
            return self._rows

        def sort_value(row: Dict):
            value = column.value_of(row)
            if column.is_numeric:
                try:
                    return (0, float(value))
                except (TypeError, ValueError):
                    return (1, 0.0)
            return (0, str(value).lower())

        return sorted(self._rows, key=sort_value, reverse=self._sort_reverse)

    # -- pagination ----------------------------------------------------
    @property
    def page_size(self) -> Optional[int]:
        return self._page_size

    @property
    def page(self) -> int:
        return self._page

    @property
    def page_count(self) -> int:
        """Always at least 1, even for zero rows, so a UI can show "Page 1 of 1"."""
        if not self._page_size:
            return 1
        return max(1, -(-len(self.sorted_rows()) // self._page_size))  # ceil div

    def set_page_size(self, size: Optional[int]) -> None:
        """Rows per page; ``None`` or ``0`` disables pagination (every row displays)."""
        self._page_size = int(size) if size else None
        self._page = 0

    def set_page(self, page: int) -> None:
        """Jump to ``page`` (0-indexed), clamped to ``[0, page_count - 1]``."""
        self._page = max(0, min(int(page), self.page_count - 1))

    def display_rows(self) -> List[Dict]:
        """Rows actually on screen: sorted, then sliced to the current page
        if pagination is active. Every backend renders this, not
        sorted_rows() directly, once pagination is in play.
        """
        rows = self.sorted_rows()
        if not self._page_size:
            return rows
        start = self._page * self._page_size
        return rows[start:start + self._page_size]

    # -- overlay state ---------------------------------------------------
    def set_loading(self, loading: bool) -> None:
        self._loading = bool(loading)

    def set_error(self, message: str) -> None:
        self._error = str(message) if message else ""

    @property
    def loading(self) -> bool:
        return self._loading

    @property
    def error(self) -> str:
        return self._error

    @property
    def is_empty(self) -> bool:
        """Whether set_rows() ran and genuinely returned nothing.

        A model that was simply never populated yet is not "empty" in this
        sense - only a completed fetch that returned zero rows is.
        """
        return self._rows_set and not self._rows

    @property
    def shows_overlay(self) -> bool:
        """Whether the overlay replaces the table right now."""
        return self._loading or bool(self._error) or self.is_empty

    def overlay_text(self, separator: str = "  ", escape: Optional[Callable[[str], str]] = None) -> str:
        """Text for the loading/error/empty overlay, or ``""`` when the table shows.

        Priority: an error outranks loading (if a fetch failed, saying so beats
        claiming the rows are still on their way), which outranks the empty
        state (a refresh that clears rows before repopulating them should
        keep showing "Loading…", not flash "No data" first).

        ``separator`` sits between the warning sign and the message because the
        HTML backends need ``&nbsp;`` to keep the gap from collapsing, while Qt
        uses ordinary spaces. ``escape`` is applied to the message only - never
        to the separator - so an HTML backend can pass its escaper without the
        entity being escaped back into text.
        """
        if self._error:
            message = escape(self._error) if escape is not None else self._error
            return f"{_ERROR_PREFIX}{separator}{message}"
        if self._loading:
            return LOADING_TEXT
        if self.is_empty:
            return EMPTY_TEXT
        return ""
