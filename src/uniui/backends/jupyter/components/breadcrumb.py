"""Breadcrumb: the shared BreadcrumbModel rendered as buttons plus separators."""
from __future__ import annotations

from html import escape
from typing import Callable, Dict, List, Optional

import ipywidgets as widgets

from ....components import IBreadcrumb
from ....models.navigation import BreadcrumbModel
from ....state import Handle, safe_call
from ..runtime import html

class JupyterBreadcrumbAdapter(IBreadcrumb):
    def __init__(self):
        self._native = widgets.HBox()
        self._native.add_class("uniui-breadcrumb")
        self._click_cb: Optional[Callable[[str], None]] = None
        self._model = BreadcrumbModel()

    def get_native(self): return self._native

    def set_items(self, items: List[Dict]) -> None:
        self._model.set_items(items)
        children = []
        for index, crumb in enumerate(self._model):
            if index:
                children.append(html(
                    f"<p>{BreadcrumbModel.SEPARATOR}</p>",
                    "uniui-breadcrumb-separator",
                ))
            if crumb.is_link:
                button = widgets.Button(
                    description=crumb.label, layout=widgets.Layout(width="auto")
                )
                button.on_click(lambda _button, p=crumb.path: self._on_click(p))
                children.append(button)
            else:
                children.append(html(
                    f"<p>{escape(crumb.label)}</p>", "uniui-breadcrumb-current"
                ))
        self._native.children = tuple(children)

    def on_click(self, fn: Callable[[str], None]) -> Handle:
        self._click_cb = fn
        def cancel():
            if self._click_cb is fn:
                self._click_cb = None
        return Handle(cancel)

    def _on_click(self, path: str) -> None:
        if self._click_cb:
            safe_call(self._click_cb, path, backend="jupyter", component="Breadcrumb", method="on_click")


def breadcrumb_css() -> str:
    """The Breadcrumb CSS fragment, composed into the shell sheet by ``styles.css``."""
    return """.uniui-breadcrumb {align-items:center;gap:4px;min-width:0}
.uniui-breadcrumb .widget-button,
.uniui-breadcrumb .widget-button button {
  min-height:28px;padding:2px 5px;background:transparent!important;
  color:var(--uniui-text_muted)!important;border-color:transparent!important;
}
.uniui-breadcrumb-current, .uniui-breadcrumb-current p {margin:0;color:var(--uniui-text);font-weight:650}
.uniui-breadcrumb-separator, .uniui-breadcrumb-separator p {margin:0;color:var(--uniui-text_muted)}"""
