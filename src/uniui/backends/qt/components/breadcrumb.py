"""Qt IBreadcrumb: the trail of links above the page content."""
from __future__ import annotations

from PySide2 import QtCore, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import IBreadcrumb
from ....models.navigation import BreadcrumbModel
from ....state import Handle, safe_call
from ..runtime import C, clear_layout, track_themed

def _breadcrumb_button_style() -> str:
    return f"""
    QPushButton {{
        color: {C['accent']};
        background: transparent;
        border: none;
        padding: 0 2px;
        font-size: 13px;
        font-weight: 500;
        min-height: 0;
        min-width: 0;
    }}
    QPushButton:hover {{ color: {C['accent_hover']}; }}
"""


class QtBreadcrumbAdapter(VisibilityMixin, EnableMixin, SizeMixin, IBreadcrumb):
    def __init__(self):
        self._widget = QtWidgets.QWidget()
        self._widget.setStyleSheet("background: transparent;")
        self._layout = QtWidgets.QHBoxLayout(self._widget)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._click_cb = None
        self._model = BreadcrumbModel()
        track_themed(self, self._widget)

    def get_native(self): return self._widget

    def set_items(self, items) -> None:
        self._model.set_items(items)
        self._rebuild()

    def _rebuild(self) -> None:
        clear_layout(self._layout)
        for i, crumb in enumerate(self._model):
            if i > 0:
                sep = QtWidgets.QLabel(BreadcrumbModel.SEPARATOR)
                sep.setStyleSheet(
                    f"color: {C['text_muted']}; font-size: 13px; background: transparent;"
                )
                self._layout.addWidget(sep)

            if not crumb.is_link:
                lbl = QtWidgets.QLabel(crumb.label)
                lbl.setStyleSheet(
                    f"color: {C['text']}; font-size: 13px; font-weight: 600;"
                    " background: transparent;"
                )
                self._layout.addWidget(lbl)
            else:
                btn = QtWidgets.QPushButton(crumb.label)
                btn.setFlat(True)
                btn.setCursor(QtCore.Qt.PointingHandCursor)
                btn.setStyleSheet(_breadcrumb_button_style())
                btn.setSizePolicy(
                    QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
                )
                captured = crumb.path
                btn.clicked.connect(
                    lambda checked=False, p=captured: self._on_click(p)
                )
                self._layout.addWidget(btn)

        self._layout.addStretch()

    def on_click(self, fn) -> Handle:
        self._click_cb = fn
        def cancel():
            if self._click_cb is fn:
                self._click_cb = None
        return Handle(cancel)

    def _on_click(self, path: str) -> None:
        if self._click_cb:
            safe_call(self._click_cb, path, backend="qt", component="Breadcrumb", method="on_click")

    def apply_theme(self) -> None:
        self._widget.setStyleSheet("background: transparent;")
        if len(self._model):
            self._rebuild()
