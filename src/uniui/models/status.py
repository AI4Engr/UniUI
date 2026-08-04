"""The single semantic-status definition shared by every backend.

Before this module each backend classified status text on its own, and the
copies had drifted apart: Qt recognised ``success``/``ok``/``warn`` and
stripped surrounding whitespace, while the Jupyter and Web tables did not. The
same cell value could therefore render as a green pill in the desktop app and a
grey one in the browser.

Backends must not add their own vocabulary. They take the semantic name
returned by :func:`classify_status` and map it to their native styling.
"""
from typing import Dict, Tuple

STATUS_OK = "ok"
STATUS_WARN = "warn"
STATUS_ERROR = "error"
STATUS_NEUTRAL = "neutral"

#: Every semantic status a backend has to be able to render.
SEMANTIC_STATUSES: Tuple[str, ...] = (
    STATUS_OK,
    STATUS_WARN,
    STATUS_ERROR,
    STATUS_NEUTRAL,
)

#: Raw value -> semantic status. Values are matched case-insensitively after
#: stripping surrounding whitespace. Anything unlisted becomes ``neutral``.
STATUS_ALIASES: Dict[str, str] = {
    # success
    "ok": STATUS_OK,
    "success": STATUS_OK,
    "active": STATUS_OK,
    "delivered": STATUS_OK,
    "shipped": STATUS_OK,
    # warning
    "warn": STATUS_WARN,
    "warning": STATUS_WARN,
    "processing": STATUS_WARN,
    "pending": STATUS_WARN,
    # error
    "error": STATUS_ERROR,
    "failed": STATUS_ERROR,
    "cancelled": STATUS_ERROR,
    "inactive": STATUS_ERROR,
}


def classify_status(value) -> str:
    """Return the semantic status for an arbitrary cell or property value.

    Unknown values - including ``None`` - classify as ``neutral`` rather than
    raising, because this runs against user-supplied table data.
    """
    if value is None:
        return STATUS_NEUTRAL
    return STATUS_ALIASES.get(str(value).strip().lower(), STATUS_NEUTRAL)


def status_values(status: str) -> Tuple[str, ...]:
    """Return the raw values that classify as ``status``, in declaration order.

    ``neutral`` is the fallback and has no explicit vocabulary, so it returns
    an empty tuple.
    """
    return tuple(raw for raw, semantic in STATUS_ALIASES.items() if semantic == status)


def status_class_expression_js(class_prefix: str = "uniui-status-") -> str:
    """Return a JS object literal mapping pill classes to match expressions.

    The Web backend classifies status in the browser inside a Quasar slot, so
    it cannot call :func:`classify_status` at render time. Generating the
    expression from :data:`STATUS_ALIASES` keeps that vocabulary identical to
    the Python backends instead of being a fourth hand-maintained copy.

    The emitted expression normalises with ``trim().toLowerCase()`` to match
    :func:`classify_status`.
    """
    normalized = "String(props.value ?? '').trim().toLowerCase()"
    known = sorted(STATUS_ALIASES)
    lines = []
    for status in SEMANTIC_STATUSES:
        if status == STATUS_NEUTRAL:
            continue
        values = _js_array(sorted(status_values(status)))
        lines.append(f"'{class_prefix}{status}': {values}.includes({normalized})")
    lines.append(
        f"'{class_prefix}{STATUS_NEUTRAL}': !{_js_array(known)}.includes({normalized})"
    )
    return "{\n  " + ",\n  ".join(lines) + "\n}"


def _js_array(values) -> str:
    return "[" + ",".join(f"'{value}'" for value in values) + "]"


def status_token_names(status: str) -> Tuple[str, str]:
    """Return the ``(foreground, background)`` theme token names for a status.

    Accepts a raw value as well as a semantic one, so callers holding
    unnormalised input do not each have to remember to classify first.
    """
    if status not in SEMANTIC_STATUSES:
        status = classify_status(status)
    return f"status_{status}_fg", f"status_{status}_bg"
