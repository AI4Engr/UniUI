"""Qt ISidebar: the primary navigation list."""
from __future__ import annotations

from typing import Callable, Optional

from PySide2 import QtCore, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import ISidebar
from ....icons import ADMIN_ICON_NAMES
from ....models.navigation import (
    SIDEBAR_COLLAPSED, SIDEBAR_MAX, SIDEBAR_MIN, NavigationModel,
)
from ....state import Handle, safe_call
from ..runtime import C, M, nav_icon, track_themed


def _rgba(hex_color: str, alpha: float) -> str:
    """A hex color as an rgba() string at ``alpha`` opacity.

    Used to tint the sidebar's own foreground/accent colors for hover and
    selected states, instead of a second opaque swatch: a low-alpha wash
    reads as a subtle highlight on both a dark rail and a light one (e.g.
    the "sand" theme), where a fixed opaque color would need re-tuning per
    theme to avoid looking either invisible or like a heavy block.
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _sidebar_style() -> str:
    hover_tint = _rgba(C["sidebar_fg"], 0.08)
    selected_tint = _rgba(C["sidebar_edge"], 0.14)
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
        background: {hover_tint};
    }}
    QListWidget::item:selected {{
        background: {selected_tint};
        color: {C['sidebar_act_fg']};
        border-left: {M['sidebar_edge_width']}px solid {C['sidebar_edge']};
    }}
    QListWidget::item:disabled {{
        color: {C['text_muted']};
        background: transparent;
    }}
    QListWidget::item:selected:active {{
        background: {selected_tint};
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


class QtSidebarAdapter(VisibilityMixin, EnableMixin, SizeMixin, ISidebar):
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

    def add_group(self, label: str) -> None:
        nav_item = self._model.add_group(label)
        item = QtWidgets.QListWidgetItem(self._group_text(nav_item))
        item.setFlags(item.flags() & ~(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled))
        item.setSizeHint(QtCore.QSize(0, 28))
        font = item.font()
        font.setPixelSize(11)
        font.setBold(True)
        item.setFont(font)
        self._list.addItem(item)

    def _group_text(self, nav_item) -> str:
        """Blank when collapsed - a section title has nowhere to fit in the
        icon-only rail, so it collapses to just a thin, empty separator row
        rather than trying to show anything."""
        return "" if self._model.collapsed else nav_item.label.upper()

    def set_active(self, key: str) -> None:
        if self._model.set_active(key):
            self._list.blockSignals(True)
            self._list.setCurrentRow(self._model.index_of(key))
            self._list.blockSignals(False)

    def on_select(self, fn: Callable[[str], None]) -> Handle:
        self._select_cb = fn
        def cancel():
            if self._select_cb is fn:
                self._select_cb = None
        return Handle(cancel)

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
            if nav_item.is_group:
                item.setText(self._group_text(nav_item))
                continue
            item.setText(self._item_text(nav_item))
            item.setTextAlignment(
                QtCore.Qt.AlignCenter if collapsed else QtCore.Qt.AlignVCenter
            )

    def _item_text(self, nav_item) -> str:
        """The list-item text, which depends on how the icon is drawn.

        Named icons (from the shared ``ADMIN_ICON_NAMES`` registry - the
        same check ``add_item`` uses to decide whether to call ``setIcon``)
        become a real ``QIcon``, so the item carries the label alone.
        Anything else is treated as an emoji rendered as text, so it has to
        be folded into the string - and it is what stands in for the label
        when the sidebar is collapsed. This used to check a separately
        hand-maintained set of three names that fell out of sync with the
        real icon registry, so any icon added later (e.g. "components")
        rendered as literal icon-name text glued to the label instead of a
        real icon.
        """
        if nav_item.icon in ADMIN_ICON_NAMES:
            return self._model.label_for(nav_item)
        if self._model.collapsed:
            return nav_item.icon or nav_item.initial()
        return f"{nav_item.icon}   {nav_item.label}" if nav_item.icon else nav_item.label

    def apply_theme(self) -> None:
        self._list.setStyleSheet(_sidebar_style())
        for i, nav_item in enumerate(self._model):
            if nav_item.is_group:
                continue
            icon = nav_icon(
                nav_item.icon, C["sidebar_fg"], C["sidebar_edge"]
            )
            if not icon.isNull():
                self._list.item(i).setIcon(icon)

    def _on_row_changed(self, row: int) -> None:
        nav_item = self._model.item_at(row)
        if self._select_cb and nav_item is not None:
            safe_call(self._select_cb, nav_item.key, backend="qt", component="Sidebar", method="on_select")
