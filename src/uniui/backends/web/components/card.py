"""Card: a titled surface with an optional action slot."""
from __future__ import annotations


from nicegui import ui

from ....components import ICard
from ..primitives import _WebAdapter
from ..runtime import clear, native
from ..styles import install_admin_css

class WebCardAdapter(_WebAdapter, ICard):
    def __init__(self):
        install_admin_css()
        card = ui.card().classes("uniui-web-card")
        with card:
            with ui.row().classes("w-full items-start no-wrap"):
                with ui.column().classes("gap-0 grow"):
                    self._title = ui.label("").classes("uniui-web-card-title")
                    self._subtitle = ui.label("").classes("uniui-web-card-subtitle")
                self._action = ui.row().classes("items-start")
            self._content = ui.column().classes("w-full items-stretch")
        super().__init__(card)

    def set_title(self, title: str) -> None: self._title.set_text(str(title))
    def set_subtitle(self, subtitle: str) -> None: self._subtitle.set_text(str(subtitle))
    def set_content(self, widget) -> None:
        clear(self._content); native(widget).move(self._content)
    def set_action(self, widget) -> None:
        clear(self._action); native(widget).move(self._action)


def card_css() -> str:
    """The Card CSS fragment, composed into the sheet by ``styles.install_admin_css``.

    Indentation is part of the emitted text: the fragments are concatenated
    into one block that was originally written inline at this indent level.
    """
    return """        .uniui-web-card {width:100%;min-width:0;padding:var(--uniui-card-padding);border:1px solid var(--uniui-border)!important;
          border-radius:14px!important;background:var(--uniui-surface)!important;color:var(--uniui-text);box-shadow:none!important}
        .uniui-web-card-title {color:var(--uniui-text);font-size:16px;font-weight:700;line-height:1.3}
        .uniui-web-card-subtitle {margin-top:2px;color:var(--uniui-text_muted);font-size:12px}
        .uniui-web-card .uniui-vbox {gap:var(--uniui-card-gap)!important}
"""
