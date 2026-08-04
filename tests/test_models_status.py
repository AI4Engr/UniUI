"""Unit tests for the shared semantic-status model.

Backend-independent by design: this module must not import a GUI toolkit.
"""
import pytest

from uniui.models.status import (
    STATUS_ERROR,
    STATUS_NEUTRAL,
    STATUS_OK,
    STATUS_WARN,
    SEMANTIC_STATUSES,
    classify_status,
    status_token_names,
)


@pytest.mark.parametrize("value", ["ok", "success", "active", "delivered", "shipped"])
def test_success_vocabulary(value):
    assert classify_status(value) == STATUS_OK


@pytest.mark.parametrize("value", ["warn", "warning", "processing", "pending"])
def test_warning_vocabulary(value):
    assert classify_status(value) == STATUS_WARN


@pytest.mark.parametrize("value", ["error", "failed", "cancelled", "inactive"])
def test_error_vocabulary(value):
    assert classify_status(value) == STATUS_ERROR


@pytest.mark.parametrize("value", ["", "unknown", "n/a", "42", "draft"])
def test_unknown_values_are_neutral(value):
    assert classify_status(value) == STATUS_NEUTRAL


def test_none_is_neutral_rather_than_raising():
    """Table data is user supplied, so this must not blow up."""
    assert classify_status(None) == STATUS_NEUTRAL


@pytest.mark.parametrize("value", ["ACTIVE", "Active", "  active  ", "\tActive\n"])
def test_matching_ignores_case_and_surrounding_whitespace(value):
    """Qt stripped and lowercased; Jupyter and Web did not. Now all do."""
    assert classify_status(value) == STATUS_OK


def test_non_string_values_do_not_raise():
    assert classify_status(0) == STATUS_NEUTRAL
    assert classify_status(object()) == STATUS_NEUTRAL


def test_token_names_follow_the_theme_key_convention():
    assert status_token_names(STATUS_OK) == ("status_ok_fg", "status_ok_bg")
    assert status_token_names(STATUS_NEUTRAL) == (
        "status_neutral_fg",
        "status_neutral_bg",
    )


def test_token_names_accept_raw_values_too():
    assert status_token_names("delivered") == ("status_ok_fg", "status_ok_bg")
    assert status_token_names("nonsense") == (
        "status_neutral_fg",
        "status_neutral_bg",
    )


def test_every_semantic_status_has_theme_tokens():
    """Guards against adding a status with no palette entry behind it."""
    from uniui.theme import ADMIN_LIGHT, ADMIN_DARK

    for status in SEMANTIC_STATUSES:
        fg, bg = status_token_names(status)
        for palette_name, palette in (("light", ADMIN_LIGHT), ("dark", ADMIN_DARK)):
            assert fg in palette, f"{fg} missing from {palette_name} palette"
            assert bg in palette, f"{bg} missing from {palette_name} palette"


class TestBackendsAgree:
    """Every backend must classify a value the same way.

    Before the shared model these had drifted: Qt recognised ``ok``/``success``
    /``warn`` and stripped whitespace, Jupyter and Web did not - so ``"ok"``
    rendered green on the desktop and grey in the browser.
    """

    CASES = [
        ("active", STATUS_OK),
        ("ok", STATUS_OK),
        ("success", STATUS_OK),
        ("  Delivered ", STATUS_OK),
        ("pending", STATUS_WARN),
        ("warn", STATUS_WARN),
        ("WARNING", STATUS_WARN),
        ("failed", STATUS_ERROR),
        ("cancelled", STATUS_ERROR),
        ("mystery", STATUS_NEUTRAL),
    ]

    @pytest.mark.parametrize("value,expected", CASES)
    def test_jupyter_pill_class(self, value, expected):
        """Assert on the rendered pill rather than a helper.

        This covers the classification *and* the renderer that consumes it, so
        it keeps working however the backend gets the class internally.
        """
        pytest.importorskip("ipywidgets")
        from uniui.jupyter_components import JupyterTableAdapter

        table = JupyterTableAdapter()
        table.set_columns([{"key": "status", "label": "Status"}])
        table.set_rows([{"status": value}])
        assert f"uniui-status-{expected}" in table._table.value

    @pytest.mark.parametrize("value,expected", CASES)
    def test_qt_pill_colors(self, value, expected):
        pytest.importorskip("PySide2")
        from uniui import qt_components

        fg, bg = qt_components._status_colors(value)
        palette = qt_components.get_palette()
        assert fg == palette[f"status_{expected}_fg"]
        assert bg == palette[f"status_{expected}_bg"]

    @pytest.mark.parametrize("value,expected", CASES)
    def test_web_js_expression_covers_value(self, value, expected):
        """The browser-side expression must list the value under its class."""
        from uniui.models.status import status_class_expression_js

        js = status_class_expression_js()
        normalized = value.strip().lower()
        for status in SEMANTIC_STATUSES:
            line = next(l for l in js.splitlines() if f"uniui-status-{status}'" in l)
            listed = f"'{normalized}'" in line
            if status == STATUS_NEUTRAL:
                # neutral is the negated set of all known values
                assert listed is (expected != STATUS_NEUTRAL)
            else:
                assert listed is (status == expected), (
                    f"{value!r} wrongly {'listed' if listed else 'absent'} "
                    f"for {status}"
                )
