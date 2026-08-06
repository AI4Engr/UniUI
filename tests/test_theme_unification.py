"""One palette, one state machine, shared by every backend.

There used to be two palettes: theme.py (calculator-flavoured: fg/bg_input)
and admin_theme.py (text/input_bg/surface).  They disagreed on shared names —
`accent` was indigo in one and blue in the other — and each backend kept its
own dark/light flag, so switching the theme on Qt left Jupyter untouched.
"""

import pytest


def test_theme_is_mutated_in_place_not_rebound():
    """Backends do `from .theme import THEME` and hold that dict forever.

    Rebinding the name instead of updating it would silently break colours in
    qt/jupyter/web/display with no error anywhere.
    """
    from uniui import theme
    from uniui.theme import THEME, set_theme, toggle_theme

    original_id = id(THEME)
    set_theme(True)
    set_theme(False)
    toggle_theme()

    # The module attribute and the imported reference must still be the same
    # object: a backend that imported THEME earlier has to see the new values.
    assert id(THEME) == original_id
    assert theme.THEME is THEME
    assert THEME["bg"] == theme.THEME["bg"]


@pytest.mark.parametrize("dark", (False, True))
@pytest.mark.parametrize(
    "legacy_name,current_name",
    (
        ("fg", "text"),
        ("fg_muted", "text_muted"),
        ("bg_input", "input_bg"),
        ("border_radius", "radius_medium"),
    ),
)
def test_legacy_token_names_alias_current_ones(dark, legacy_name, current_name):
    from uniui.theme import THEME, set_theme

    set_theme(dark)
    assert THEME[legacy_name] == THEME[current_name]


def test_legacy_backends_still_find_every_key_they_read():
    """qt/jupyter/web/display read these directly; a missing one is a KeyError."""
    from uniui.theme import THEME, set_theme

    set_theme(True)
    required = {
        "bg", "bg_input", "fg", "fg_button", "fg_muted",
        "accent", "accent_hover", "accent_press", "border",
        "font_family", "font_size",
        "padding", "padding_inner", "spacing", "border_radius",
    }
    assert required.issubset(THEME)


def test_public_theme_api_is_unchanged():
    import uniui

    uniui.set_theme(True)
    assert uniui.is_dark() is True

    assert uniui.toggle_theme() is False
    assert uniui.is_dark() is False

    assert uniui.toggle_theme() is True


def test_switching_theme_on_one_backend_switches_them_all():
    """The bug this refactor targets: per-backend flags drifting apart."""
    pytest.importorskip("PySide2")
    pytest.importorskip("ipywidgets")
    from uniui import jupyter_components, qt_components, theme_runtime

    try:
        qt_components.set_admin_theme(True)
        assert qt_components.is_admin_dark() is True
        assert jupyter_components.is_admin_dark() is True
        assert theme_runtime.is_dark() is True

        jupyter_components.set_admin_theme(False)
        assert qt_components.is_admin_dark() is False
        assert jupyter_components.is_admin_dark() is False
    finally:
        theme_runtime.set_theme(False)


def test_backends_agree_on_palette_values():
    pytest.importorskip("PySide2")
    pytest.importorskip("ipywidgets")
    from uniui import jupyter_components, qt_components, theme_runtime

    try:
        theme_runtime.set_theme(True)
        qt_palette = qt_components.get_admin_palette()
        jupyter_palette = jupyter_components.get_admin_palette()

        for token in ("bg", "surface", "text", "accent", "border"):
            assert qt_palette[token] == jupyter_palette[token], token
    finally:
        theme_runtime.set_theme(False)


def test_old_palette_matches_admin_palette_so_they_cannot_fight():
    """refresh_theme_jupyter writes inline styles that no CSS can override.

    It only used to skip admin shells because the two palettes disagreed; the
    values have to stay identical for that skip to remain unnecessary.
    """
    from uniui.theme import get_admin_tokens
    from uniui.theme import THEME, set_theme

    for dark in (False, True):
        set_theme(dark)
        admin = get_admin_tokens(dark)

        assert THEME["bg"] == admin["bg"]
        assert THEME["fg"] == admin["text"]
        assert THEME["accent"] == admin["accent"]
    set_theme(False)


def test_admin_shell_is_no_longer_skipped_by_the_theme_pass():
    pytest.importorskip("ipywidgets")
    import inspect

    from uniui.jupyter import refresh_theme_jupyter

    source = inspect.getsource(refresh_theme_jupyter)
    assert "uniui-admin-shell" not in source, (
        "the admin-shell workaround is back; the two palettes must have "
        "diverged again"
    )
