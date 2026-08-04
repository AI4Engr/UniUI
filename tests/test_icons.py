"""Tests for the shared Admin SVG icon source."""

import pytest

from uniui.icons import ADMIN_ICON_NAMES, css_mask, svg_data_uri, svg_icon


def test_shared_admin_icons_are_valid_svg_and_css_masks():
    assert {"dashboard", "users", "settings", "arrow_back"} <= set(
        ADMIN_ICON_NAMES
    )
    for name in ADMIN_ICON_NAMES:
        svg = svg_icon(name, color="#2563eb")
        assert svg.startswith("<svg ")
        assert 'viewBox="0 0 24 24"' in svg
        assert svg.endswith("</svg>")
        assert svg_data_uri(name).startswith("data:image/svg+xml,")
        assert "mask-image:url" in css_mask(name)


def test_unknown_admin_icon_is_rejected():
    with pytest.raises(KeyError, match="Unknown Admin icon"):
        svg_icon("not-real")
