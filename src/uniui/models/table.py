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

#: Semantic alignments. Backends map these to QSS flags or CSS/Quasar values.
ALIGN_LEFT = "left"
ALIGN_RIGHT = "right"

#: Overlay text shown while rows are being fetched.
LOADING_TEXT = "Loading…"

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
    def cell_kind(self) -> str:
        """The semantic kind of every cell in this column."""
        if self.is_status:
            return CELL_STATUS
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
        """The cell's display text, before any backend-specific escaping."""
        return str(self.value_of(row))

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

    __slots__ = ("_columns", "_rows", "_loading", "_error")

    def __init__(self) -> None:
        self._columns: List[Column] = []
        self._rows: List[Dict] = []
        self._loading = False
        self._error = ""

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

    @property
    def has_status_column(self) -> bool:
        """Whether any column needs the status-pill treatment."""
        return any(col.is_status for col in self._columns)

    def header_labels(self) -> List[str]:
        return [col.label for col in self._columns]

    def cells(self, row: Dict) -> List[Any]:
        """Raw cell values for ``row``, in column order."""
        return [col.value_of(row) for col in self._columns]

    def row_at(self, index: int) -> Optional[Dict]:
        """Return the row at ``index``, or ``None`` if out of range.

        Every backend reports clicks as an integer index and every backend had
        its own bounds check; this is that check, written once. Negative
        indices are rejected rather than wrapping, because a negative index
        from a UI event means "nothing selected", not "count from the end".
        """
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None

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
    def shows_overlay(self) -> bool:
        """Whether the overlay replaces the table right now."""
        return self._loading or bool(self._error)

    def overlay_text(self, separator: str = "  ", escape: Optional[Callable[[str], str]] = None) -> str:
        """Text for the loading/error overlay, or ``""`` when the table shows.

        An error outranks the loading state: if a fetch failed, saying so beats
        claiming the rows are still on their way.

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
        return ""
