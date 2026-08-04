"""Backend-independent presentation models.

These modules hold the rules that every backend used to reimplement: status
classification, trend formatting, chart/gauge/table state, and navigation
state. They are pure Python and must never import a GUI toolkit - see the
dependency rules in ``docs/src-refactor-plan.md``.

Backends consume a model's *semantic* result (``"ok"``, ``"warn"``, ...) and
map it to their own colours, CSS classes, or QSS.
"""
from .chart import ChartModel
from .gauge import GaugeModel
from .stat_card import (
    CARD_STATUSES,
    TREND_DOWN,
    TREND_FLAT,
    TREND_UP,
    TrendPresentation,
    normalize_card_status,
    trend_presentation,
)
from .navigation import (
    SIDEBAR_COLLAPSED,
    SIDEBAR_EXPANDED,
    SIDEBAR_MAX,
    SIDEBAR_MIN,
    BreadcrumbModel,
    Crumb,
    NavItem,
    NavigationModel,
    clamp_width,
)
from .table import (
    ALIGN_LEFT,
    ALIGN_RIGHT,
    CELL_NUMBER,
    CELL_STATUS,
    CELL_TEXT,
    LOADING_TEXT,
    NUMERIC_COLUMN_KEYS,
    STATUS_COLUMN_KEY,
    Column,
    TableModel,
)
from .status import (
    STATUS_OK,
    STATUS_WARN,
    STATUS_ERROR,
    STATUS_NEUTRAL,
    SEMANTIC_STATUSES,
    STATUS_ALIASES,
    classify_status,
    status_class_expression_js,
    status_token_names,
    status_values,
)

__all__ = [
    # visual state
    "ChartModel",
    "GaugeModel",
    # status
    "STATUS_OK",
    "STATUS_WARN",
    "STATUS_ERROR",
    "STATUS_NEUTRAL",
    "SEMANTIC_STATUSES",
    "STATUS_ALIASES",
    "classify_status",
    "status_class_expression_js",
    "status_token_names",
    "status_values",
    # stat card
    "CARD_STATUSES",
    "TREND_UP",
    "TREND_DOWN",
    "TREND_FLAT",
    "TrendPresentation",
    "normalize_card_status",
    "trend_presentation",
    # table
    "TableModel",
    "Column",
    "NUMERIC_COLUMN_KEYS",
    "STATUS_COLUMN_KEY",
    "CELL_TEXT",
    "CELL_NUMBER",
    "CELL_STATUS",
    "ALIGN_LEFT",
    "ALIGN_RIGHT",
    "LOADING_TEXT",
    # navigation
    "NavigationModel",
    "NavItem",
    "BreadcrumbModel",
    "Crumb",
    "clamp_width",
    "SIDEBAR_EXPANDED",
    "SIDEBAR_COLLAPSED",
    "SIDEBAR_MIN",
    "SIDEBAR_MAX",
]
