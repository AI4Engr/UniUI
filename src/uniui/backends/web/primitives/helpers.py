"""Small DOM helpers shared by the Web primitive adapters."""
from __future__ import annotations

import html as html_lib
import re

def _style_size(native, name: str, value: int) -> None:
    native.style(f"{name}: {int(value)}px")
def _set_enabled(native, enabled: bool) -> None:
    if enabled:
        native.enable()
    else:
        native.disable()
def _plain_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    return html_lib.unescape(value).strip()
