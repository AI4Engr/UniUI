"""Layout data models: sizing, specs, and responsive breakpoints.

Plain data, no behaviour and no backend imports, so the widget contracts can
depend on this module without creating a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SizeSpec:
    """Describes how a widget sizes itself along one axis.

    value meanings:
      - None / "auto"  : size to content
      - "fill"         : expand to fill available space (grow=1, shrink=1)
      - int / float    : fixed pixel size
      - str "50%"      : percentage of parent (renderer may interpret)
    min / max are pixel bounds applied after the main value is resolved.
    """
    value: Any = None          # None = "auto"
    min: Optional[int] = None
    max: Optional[int] = None

    # Flexbox-style coefficients
    grow: float = 0.0
    shrink: float = 1.0
    basis: Any = None          # None = auto

    @classmethod
    def auto(cls) -> "SizeSpec":
        return cls(value=None)

    @classmethod
    def fill(cls) -> "SizeSpec":
        return cls(value="fill", grow=1.0, shrink=1.0)

    @classmethod
    def fixed(cls, px: int) -> "SizeSpec":
        return cls(value=px, grow=0.0, shrink=0.0)

    @classmethod
    def pct(cls, percent: float) -> "SizeSpec":
        return cls(value=f"{percent}%")
@dataclass
class LayoutSpec:
    """Layout parameters for a container (Row, Column, etc.).

    gap     : spacing between children in pixels
    padding : inner padding of the container in pixels
    wrap    : allow children to wrap to next row/column
    align   : main-axis alignment ("start", "center", "end", "space-between", "space-around")
    cross_align : cross-axis alignment ("start", "center", "end", "stretch")
    """
    gap: int = 0
    padding: int = 0
    wrap: bool = False
    align: str = "start"
    cross_align: str = "start"
@dataclass
class LayoutItem:
    """Wraps a widget with per-child layout overrides.

    grow / shrink override the parent SizeSpec for this child only.
    align_self overrides cross-axis alignment for this child.
    span is used by Grid layouts (column span).
    """
    widget: Any                # IWidget — forward reference avoids circular import
    grow: float = 0.0
    shrink: float = 1.0
    basis: Any = None
    align_self: Optional[str] = None
    span: int = 1
    key: Optional[str] = None  # stable identity across reflows
@dataclass
class Breakpoints:
    """Container-width breakpoints for responsive layout mode switching.

    mode_for(width) returns "compact", "medium", or "wide".
    Default thresholds match TODO.md: compact < 720, medium < 1200, wide >= 1200.
    """
    compact: int = 720
    medium: int = 1200

    def mode_for(self, width: int) -> str:
        if width < self.compact:
            return "compact"
        if width < self.medium:
            return "medium"
        return "wide"


DEFAULT_BREAKPOINTS = Breakpoints()
