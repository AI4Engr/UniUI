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


# ---------------------------------------------------------------------------
# Named themes: registering and switching beyond the built-in light/dark pair.
# ---------------------------------------------------------------------------


def test_builtin_themes_are_present_with_no_explicit_registration():
    """light/dark/ocean/midnight/sand/sunset ship inside uniui.themes and are
    registered at uniui.theme import time -- any program that imports uniui
    can reach them, not just examples/admin_demo.py (which used to register
    ocean/midnight/sand/sunset itself from files next to the demo script)."""
    from uniui import list_themes

    for name in ("light", "dark", "ocean", "midnight", "sand", "sunset"):
        assert name in list_themes()


def test_builtin_theme_json_loads_from_the_installed_package():
    """The bundled loader goes through importlib.resources, not a relative
    filesystem path -- confirm it actually reads a packaged resource."""
    from uniui.theme import _load_bundled_colors

    colors = _load_bundled_colors("light.json")
    assert colors["bg"] == "#f6f8fc"


def test_registry_round_trip_with_a_dict_palette():
    from uniui.theme import LIGHT, list_themes, register_theme, get_active_theme_name
    from uniui import theme_registry

    palette = dict(LIGHT, accent="#00cc88")
    register_theme("mint-test", palette, dark=False)
    try:
        assert "mint-test" in list_themes()

        built = theme_registry.get_theme("mint-test")
        assert built["accent"] == "#00cc88"
        # METRICS, aliases and legacy extras are present too, same as any
        # built-in theme -- a registered theme gets the identical treatment.
        assert built["font_family"] == LIGHT.get("font_family", built["font_family"])
        assert built["fg"] == built["text"]  # alias applied
        assert "fg_button" in built  # legacy extra applied
    finally:
        theme_registry._REGISTRY.pop("mint-test", None)
        theme_registry._DARK_FLAGS.pop("mint-test", None)


def test_registry_round_trip_with_a_json_file(tmp_path):
    import json

    from uniui.theme import LIGHT, register_theme, list_themes
    from uniui import theme_registry

    theme_path = tmp_path / "ocean.json"
    theme_path.write_text(json.dumps(dict(LIGHT, accent="#0077be")), encoding="utf-8")

    register_theme("ocean-test", str(theme_path), dark=False)
    try:
        assert "ocean-test" in list_themes()
        assert theme_registry.get_theme("ocean-test")["accent"] == "#0077be"
    finally:
        theme_registry._REGISTRY.pop("ocean-test", None)
        theme_registry._DARK_FLAGS.pop("ocean-test", None)


def test_registering_a_theme_missing_required_keys_fails_fast():
    from uniui.theme import register_theme, list_themes
    from uniui import theme_registry

    incomplete = {"accent": "#000000"}  # missing every other required token
    before = set(list_themes())

    with pytest.raises(ValueError, match="missing required tokens"):
        register_theme("broken-test", incomplete, dark=False)

    # A failed registration must not leave a partial entry behind.
    assert set(list_themes()) == before
    assert "broken-test" not in theme_registry._REGISTRY


def test_theme_mutated_in_place_holds_for_a_third_theme():
    """The same invariant test_theme_is_mutated_in_place_not_rebound checks
    for light/dark must also hold once a theme beyond the built-in two is
    made active -- THEME must never be rebound, only updated."""
    from uniui.theme import THEME, LIGHT, register_theme, set_active_theme
    from uniui import theme_registry

    register_theme("third-test", dict(LIGHT, accent="#ff00ff"), dark=False)
    try:
        original_id = id(THEME)
        set_active_theme("third-test")
        assert id(THEME) == original_id
        assert THEME["accent"] == "#ff00ff"
    finally:
        set_active_theme("dark")
        theme_registry._REGISTRY.pop("third-test", None)
        theme_registry._DARK_FLAGS.pop("third-test", None)


def test_is_dark_is_derived_from_the_active_themes_own_flag():
    """is_dark() must be correct for any registered theme, not just the two
    built-in ones -- this is also what keeps the Web backend's
    ui.dark_mode() call correct without any Web-specific code."""
    from uniui.theme import LIGHT, register_theme, set_active_theme, is_dark
    from uniui import theme_registry

    register_theme("dusk-test", dict(LIGHT, accent="#111111"), dark=True)
    try:
        set_active_theme("dusk-test")
        assert is_dark() is True
    finally:
        set_active_theme("dark")
        theme_registry._REGISTRY.pop("dusk-test", None)
        theme_registry._DARK_FLAGS.pop("dusk-test", None)


def test_set_theme_and_set_active_theme_agree_on_what_ended_up_in_theme():
    """set_theme(dark) is a special case of set_active_theme, not a parallel
    path -- they must never disagree about the resulting palette."""
    from uniui.theme import THEME, set_theme, set_active_theme

    set_theme(True)
    via_bool = dict(THEME)
    set_active_theme("dark")
    via_name = dict(THEME)
    assert via_bool == via_name
    set_theme(False)


def test_theme_runtime_set_active_theme_fires_registered_refreshers():
    from uniui import theme_runtime

    calls = []
    callback = lambda: calls.append(1)
    theme_runtime.register_refresh(callback)
    try:
        theme_runtime.set_active_theme("light")
        assert calls
        assert theme_runtime.get_active_theme_name() == "light"
    finally:
        theme_runtime._refreshers.remove(callback)
        theme_runtime.set_theme(False)
