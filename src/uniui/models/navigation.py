"""Shared presentation model for the sidebar navigation.

Every backend kept parallel ``_keys`` / ``_labels`` / ``_icons`` lists plus an
active key and a collapsed flag, and every backend re-derived the same two
rules: whether an item is the active one, and how to clamp a requested sidebar
width. The width clamp in particular was written four times - once in the Qt
adapter, twice in the Jupyter adapter, and once in its splitter bridge - which
is how the ``fixed`` case came to disagree with the others.

The model owns item bookkeeping and width arithmetic. Backends own their
native list/button widgets and decide what "active" looks like.
"""
from typing import Dict, Iterator, List, NamedTuple, Optional

from ..theme import get_admin_metrics

_M = get_admin_metrics()

#: Sidebar geometry, in pixels. Sourced from the design tokens so the model
#: and the emitted CSS/QSS cannot drift apart.
SIDEBAR_EXPANDED = _M["sidebar_expanded"]
SIDEBAR_COLLAPSED = _M["sidebar_collapsed"]
SIDEBAR_MIN = _M["sidebar_min"]
SIDEBAR_MAX = _M["sidebar_max"]


class NavItem(NamedTuple):
    """One sidebar entry."""

    key: str
    label: str
    icon: str

    def initial(self) -> str:
        """A one-character stand-in for the label when collapsed with no icon."""
        return self.label[:1].upper() if self.label else "?"


def clamp_width(width: int, fixed: bool = False) -> int:
    """Clamp a requested sidebar width to the allowed range.

    ``fixed`` is the collapsed case, where the sidebar is pinned to its
    collapsed width and so may go below the normal minimum.
    """
    minimum = SIDEBAR_COLLAPSED if fixed else SIDEBAR_MIN
    return max(minimum, min(SIDEBAR_MAX, int(width)))


class NavigationModel:
    """Sidebar items, the active key, and the collapsed state."""

    __slots__ = ("_items", "_active", "_collapsed")

    def __init__(self) -> None:
        self._items: List[NavItem] = []
        self._active = ""
        self._collapsed = False

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[NavItem]:
        return iter(self._items)

    @property
    def items(self) -> List[NavItem]:
        return self._items

    @property
    def keys(self) -> List[str]:
        return [item.key for item in self._items]

    def add_item(self, key: str, label: str, icon: str = "") -> NavItem:
        """Append an item and return it, so the backend can build its widget."""
        item = NavItem(str(key), str(label), str(icon))
        self._items.append(item)
        return item

    def item_at(self, index: int) -> Optional[NavItem]:
        """The item at ``index``, or ``None``.

        Negative indices are rejected rather than wrapping: a list widget
        reports ``-1`` when the selection is cleared, and that must not be
        read as "the last item".
        """
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def index_of(self, key: str) -> int:
        """The row of ``key``, or ``-1`` when it is not present."""
        for index, item in enumerate(self._items):
            if item.key == key:
                return index
        return -1

    # -- active ----------------------------------------------------------
    @property
    def active(self) -> str:
        return self._active

    def set_active(self, key: str) -> bool:
        """Mark ``key`` active. Returns whether it was a known key.

        An unknown key leaves the previous selection alone, which is what the
        Qt adapter always did; the browser backends used to clear every
        highlight instead, leaving the sidebar with nothing selected.
        """
        if self.index_of(key) < 0:
            return False
        self._active = key
        return True

    def is_active(self, key: str) -> bool:
        return bool(self._active) and key == self._active

    # -- collapsed -------------------------------------------------------
    @property
    def collapsed(self) -> bool:
        return self._collapsed

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = bool(collapsed)

    @property
    def width(self) -> int:
        """The width the sidebar should occupy in its current state."""
        return SIDEBAR_COLLAPSED if self._collapsed else SIDEBAR_EXPANDED

    def label_for(self, item: NavItem) -> str:
        """The text to show next to the icon, blank when collapsed."""
        return "" if self._collapsed else item.label


class BreadcrumbModel:
    """The breadcrumb trail and the decision of which crumbs are links."""

    __slots__ = ("_items",)

    #: Drawn between crumbs by every backend.
    SEPARATOR = "›"

    def __init__(self) -> None:
        self._items: List["Crumb"] = []

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator["Crumb"]:
        return iter(self._items)

    @property
    def items(self) -> List["Crumb"]:
        return self._items

    def set_items(self, items) -> None:
        specs = list(items)
        last = len(specs) - 1
        self._items = [
            Crumb(spec, is_last=(index == last)) for index, spec in enumerate(specs)
        ]


class Crumb:
    """One breadcrumb entry.

    A crumb is a link only when it has a path *and* is not the last one: the
    last crumb is where you already are, so linking to it would be a no-op
    that still looks clickable.
    """

    __slots__ = ("label", "path", "is_last")

    def __init__(self, spec: Dict, is_last: bool = False) -> None:
        self.label = str(spec.get("label", ""))
        self.path = spec.get("path", "") or ""
        self.is_last = is_last

    @property
    def is_link(self) -> bool:
        return bool(self.path) and not self.is_last

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Crumb(label={self.label!r}, is_link={self.is_link})"
