"""Qt ISidebar: the primary navigation list."""
from __future__ import annotations

from typing import Callable, Optional

from PySide2 import QtCore, QtWidgets

from ....components import ISidebar
from ....models.navigation import (
    SIDEBAR_COLLAPSED, SIDEBAR_MAX, SIDEBAR_MIN, NavigationModel,
)
from ..runtime import C, M, nav_icon, track_themed

def _sidebar_style() -> str:
    return f"""
    QListWidget {{
        background: {C['sidebar_bg']};
        border: none;
        outline: none;
        padding: 14px 0;
    }}
    QListWidget::item {{
        color: {C['sidebar_fg']};
        padding: 11px 14px;
        font-size: 13px;
        font-weight: 500;
        border-radius: 8px;
        margin: 2px 10px;
    }}
    QListWidget::item:hover {{
        background: {C['sidebar_hover']};
    }}
    QListWidget::item:selected {{
        background: {C['sidebar_act']};
        color: {C['sidebar_act_fg']};
        border-left: {M['sidebar_edge_width']}px solid {C['sidebar_edge']};
    }}
    QListWidget::item:disabled {{
        color: {C['text_muted']};
        background: transparent;
    }}
    QListWidget::item:selected:active {{
        background: {C['sidebar_act']};
        color: {C['sidebar_act_fg']};
        border-left: {M['sidebar_edge_width']}px solid {C['sidebar_edge']};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255,255,255,0.2);
        border-radius: 2px;
    }}
"""


class QtSidebarAdapter(ISidebar):
    def __init__(self):
        self._list = QtWidgets.QListWidget()
        self._list.setAccessibleName("Primary navigation")
        self._list.setFocusPolicy(QtCore.Qt.StrongFocus)
        self._list.setUniformItemSizes(True)
        self._list.setStyleSheet(_sidebar_style())
        self._list.setMinimumWidth(SIDEBAR_MIN)
        self._list.setMaximumWidth(SIDEBAR_MAX)
        self._list.setIconSize(QtCore.QSize(18, 18))
        self._list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._model = NavigationModel()
        self._select_cb: Optional[Callable] = None
        self._list.currentRowChanged.connect(self._on_row_changed)
        track_themed(self, self._list)
        self.apply_theme()

    def get_native(self): return self._list

    def add_item(self, key: str, label: str, icon: str = "") -> None:
        nav_item = self._model.add_item(key, label, icon)
        item = QtWidgets.QListWidgetItem(self._item_text(nav_item))
        named_icon = nav_icon(nav_item.icon)
        if not named_icon.isNull():
            item.setIcon(named_icon)
        item.setData(QtCore.Qt.UserRole, nav_item.key)
        item.setToolTip(nav_item.label)
        item.setSizeHint(QtCore.QSize(0, 44))
        if self._model.collapsed:
            item.setTextAlignment(QtCore.Qt.AlignCenter)
        self._list.addItem(item)

    def set_active(self, key: str) -> None:
        if self._model.set_active(key):
            self._list.blockSignals(True)
            self._list.setCurrentRow(self._model.index_of(key))
            self._list.blockSignals(False)

    def on_select(self, fn: Callable[[str], None]) -> None:
        self._select_cb = fn

    def set_collapsed(self, collapsed: bool) -> None:
        self._model.set_collapsed(collapsed)
        if self._model.collapsed:
            self._list.setMinimumWidth(SIDEBAR_COLLAPSED)
            self._list.setMaximumWidth(SIDEBAR_COLLAPSED)
        else:
            self._list.setMinimumWidth(SIDEBAR_MIN)
            self._list.setMaximumWidth(SIDEBAR_MAX)
        for i, nav_item in enumerate(self._model):
            item = self._list.item(i)
            item.setText(self._item_text(nav_item))
            item.setTextAlignment(
                QtCore.Qt.AlignCenter if collapsed else QtCore.Qt.AlignVCenter
            )

    def _item_text(self, nav_item) -> str:
        """The list-item text, which depends on how the icon is drawn.

        Named icons become a real ``QIcon``, so the item carries the label
        alone. Anything else is an emoji rendered as text, so it has to be
        folded into the string - and it is what stands in for the label when
        the sidebar is collapsed.
        """
        if nav_item.icon in {"dashboard", "users", "settings"}:
            return self._model.label_for(nav_item)
        if self._model.collapsed:
            return nav_item.icon or nav_item.initial()
        return f"{nav_item.icon}   {nav_item.label}" if nav_item.icon else nav_item.label

    def apply_theme(self) -> None:
        self._list.setStyleSheet(_sidebar_style())
        for i, nav_item in enumerate(self._model):
            icon = nav_icon(
                nav_item.icon, C["sidebar_fg"], C["sidebar_edge"]
            )
            if not icon.isNull():
                self._list.item(i).setIcon(icon)

    def _on_row_changed(self, row: int) -> None:
        nav_item = self._model.item_at(row)
        if self._select_cb and nav_item is not None:
            self._select_cb(nav_item.key)
