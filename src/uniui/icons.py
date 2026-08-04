"""Backend-neutral SVG icons used by the Admin interface."""
from __future__ import annotations

from html import escape
from typing import Dict, Tuple
from urllib.parse import quote


_ICON_ELEMENTS: Dict[str, Tuple[str, ...]] = {
    "dashboard": (
        '<rect x="3" y="3" width="7" height="7" rx="1.5"/>',
        '<rect x="14" y="3" width="7" height="7" rx="1.5"/>',
        '<rect x="3" y="14" width="7" height="7" rx="1.5"/>',
        '<rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    ),
    "users": (
        '<circle cx="12" cy="8" r="3.5"/>',
        '<path d="M5.5 20c.7-4 3-6 6.5-6s5.8 2 6.5 6"/>',
        '<path d="M4 9.5a2.7 2.7 0 0 1 3-2.6M3 17c.4-2.7 1.7-4.2 4-4.7"/>',
        '<path d="M20 9.5a2.7 2.7 0 0 0-3-2.6M21 17c-.4-2.7-1.7-4.2-4-4.7"/>',
    ),
    "settings": (
        '<path d="M4 6h16M4 12h16M4 18h16"/>',
        '<circle cx="9" cy="6" r="2" fill="currentColor"/>',
        '<circle cx="15" cy="12" r="2" fill="currentColor"/>',
        '<circle cx="8" cy="18" r="2" fill="currentColor"/>',
    ),
    "components": (
        '<rect x="3" y="3" width="8" height="8" rx="2"/>',
        '<circle cx="17.5" cy="7" r="4"/>',
        '<path d="M4 21l7-7 7 7"/>',
    ),
    "arrow_back": ('<path d="M15 5l-7 7 7 7M8 12h12"/>',),
    "arrow_forward": ('<path d="M9 5l7 7-7 7M4 12h12"/>',),
    "notifications": (
        '<path d="M6.5 10a5.5 5.5 0 0 1 11 0c0 5 2 5.5 2 5.5h-15s2-.5 2-5.5"/>',
        '<path d="M10 19a2.2 2.2 0 0 0 4 0"/>',
    ),
    "dark_mode": ('<path d="M20 15.2A8.5 8.5 0 0 1 8.8 4 8.5 8.5 0 1 0 20 15.2z"/>',),
    "light_mode": (
        '<circle cx="12" cy="12" r="4"/>',
        '<path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    ),
    "search": (
        '<circle cx="11" cy="11" r="6.5"/>',
        '<path d="M16 16l4.5 4.5"/>',
    ),
    "close": ('<path d="M6 6l12 12M18 6L6 18"/>',),
}

ADMIN_ICON_NAMES = tuple(_ICON_ELEMENTS)


def svg_icon(name: str, color: str = "currentColor", size: int = 24) -> str:
    """Return a standalone SVG string from the shared Admin icon set."""
    if name not in _ICON_ELEMENTS:
        raise KeyError(f"Unknown Admin icon: {name}")
    safe_color = escape(str(color), quote=True)
    body = "".join(_ICON_ELEMENTS[name])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(size)}" '
        f'height="{int(size)}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{safe_color}" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round" color="{safe_color}" aria-hidden="true">'
        f"{body}</svg>"
    )


def svg_data_uri(name: str) -> str:
    """Return a monochrome SVG data URI suitable for a CSS mask."""
    return "data:image/svg+xml," + quote(svg_icon(name, color="#000000"), safe="")


def css_mask(name: str) -> str:
    """Return CSS declarations which color the icon through ``currentColor``."""
    uri = svg_data_uri(name)
    return (
        f'-webkit-mask-image:url("{uri}");mask-image:url("{uri}");'
        "-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;"
        "-webkit-mask-position:center;mask-position:center;"
        "-webkit-mask-size:contain;mask-size:contain;background:currentColor;"
    )


__all__ = ["ADMIN_ICON_NAMES", "css_mask", "svg_icon", "svg_data_uri"]
