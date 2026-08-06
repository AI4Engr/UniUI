"""Card: a titled surface with an optional action slot."""
from __future__ import annotations

from html import escape

import ipywidgets as widgets

from ....components import ICard
from ..runtime import M, html, native

class JupyterCardAdapter(ICard):
    def __init__(self):
        self._title = html("", "uniui-card-title")
        self._subtitle = html("", "uniui-card-subtitle")
        self._title.layout.display = "none"
        self._subtitle.layout.display = "none"
        self._copy = widgets.VBox([self._title, self._subtitle])
        self._copy.add_class("uniui-card-copy")
        self._action = widgets.Box()
        self._action.layout.display = "none"
        self._header = widgets.HBox([self._copy, self._action])
        self._header.add_class("uniui-card-header")
        self._content = widgets.Box(layout=widgets.Layout(width="100%", min_width="0"))
        self._native = widgets.VBox([self._header, self._content])
        self._native.add_class("uniui-admin-card")

    def get_native(self): return self._native

    def set_title(self, title: str) -> None:
        self._title.value = f"<p>{escape(str(title))}</p>"
        self._title.layout.display = None if title else "none"

    def set_subtitle(self, subtitle: str) -> None:
        self._subtitle.value = f"<p>{escape(str(subtitle))}</p>"
        self._subtitle.layout.display = None if subtitle else "none"

    def set_content(self, widget) -> None:
        self._content.children = (native(widget),)

    def set_action(self, widget) -> None:
        self._action.children = (native(widget),)
        self._action.layout.display = None


def card_css() -> str:
    """The Card CSS fragment, composed into the shell sheet by ``styles.css``."""
    return f""".uniui-admin-card {{
  width:100%; min-width:0; padding:{M['card_padding']}px {M['card_padding'] + 2}px; gap:{M['card_gap']}px;
  background:var(--uniui-surface); border:1px solid var(--uniui-border);
  border-radius:14px; box-shadow:none;
}}
.uniui-card-header {{display:flex; flex-flow:row; align-items:flex-start; gap:12px}}
.uniui-card-copy {{min-width:0; flex:1 1 auto; gap:2px}}
.uniui-card-title, .uniui-card-title p {{
  margin:0; color:var(--uniui-text); font-size:16px; font-weight:700;
}}
.uniui-card-subtitle, .uniui-card-subtitle p {{
  margin:0; color:var(--uniui-text_muted); font-size:12px;
}}"""
