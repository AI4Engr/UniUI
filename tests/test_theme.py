"""Backend-neutral Admin design token tests."""

from uniui.theme import (
    ADMIN_DARK,
    ADMIN_LIGHT,
    ADMIN_METRICS,
    get_admin_metrics,
    get_admin_tokens,
)


def test_admin_palettes_have_the_same_contract():
    assert set(ADMIN_LIGHT) == set(ADMIN_DARK)
    assert {
        "bg", "surface", "text", "text_muted", "border", "accent",
        "ok", "warn", "error", "sidebar_bg", "sidebar_active",
        "header_bg", "input_bg", "shadow",
    }.issubset(ADMIN_LIGHT)


def test_admin_token_accessors_return_copies():
    palette = get_admin_tokens(dark=True)
    metrics = get_admin_metrics()
    palette["bg"] = "changed"
    metrics["header_height"] = 999

    assert ADMIN_DARK["bg"] == "#0b0f19"
    assert ADMIN_METRICS["header_height"] == 60


def test_admin_metrics_define_cross_backend_shell_sizes():
    assert ADMIN_METRICS["header_height"] == 60
    assert ADMIN_METRICS["footer_height"] == 36
    assert ADMIN_METRICS["sidebar_expanded"] == 212
    assert ADMIN_METRICS["sidebar_collapsed"] == 72
    assert ADMIN_METRICS["sidebar_min"] < ADMIN_METRICS["sidebar_expanded"]
    assert ADMIN_METRICS["sidebar_expanded"] < ADMIN_METRICS["sidebar_max"]
