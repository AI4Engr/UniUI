"""
Contract Tests for Image Widget

These tests ensure that Image behaves consistently across all platforms.
"""
from pathlib import Path

import pytest

from tests.contract_framework import WidgetContractTest
from uniui import IMAGE

TINY_GIF_BYTES = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!"
    b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)


class TestImageContract(WidgetContractTest):
    """Contract tests for Image widget."""

    widget_kind = IMAGE

    def create_widget(self, factory):
        """Create image widget."""
        return factory.create_image()

    def create_tiny_gif(self, tmp_path: Path) -> str:
        """Create a tiny valid GIF image for backend loading tests."""
        image_path = tmp_path / "tiny.gif"
        image_path.write_bytes(TINY_GIF_BYTES)
        return str(image_path)

    @pytest.mark.contract
    def test_set_fixed_width(self, factory):
        """Test set_fixed_width."""
        image = self.create_widget(factory)

        image.set_fixed_width(200)
        image.set_fixed_width(64)

    @pytest.mark.contract
    def test_set_image_from_local_file(self, factory, tmp_path):
        """Test loading an image from a local file path."""
        image = self.create_widget(factory)

        image.set_image(self.create_tiny_gif(tmp_path))
