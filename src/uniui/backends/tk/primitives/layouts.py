"""Layout and container primitives."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ....core import *
from ....strategies import normalize_text, parse_float
from ....theme import THEME

#: Alias for the live theme dict, mutated in place on a theme switch.
T = THEME


def _group_box():
    """Return ``TkGroupBox``, imported on demand.

    ``text`` imports this module back for its own isinstance check, so a
    module-level import here would be circular.
    """
    from .text import TkGroupBox

    return TkGroupBox


class TkVBoxLayout:
    """Tkinter VBox - virtual container that tracks items.

    Items are recorded and only laid out when build() is called with the
    actual parent widget, ensuring correct parent-child relationships.
    """
    def __init__(self, parent=None):
        self._items = []
        self._frame = None

    def addItem(self, item):
        self._items.append(item)

    def addStretch(self):
        self._items.append('__stretch__')

    def setAlignmentTop(self):
        pass

    def build(self, parent, is_root=False):
        """Build the actual tk.Frame with correct parent and grid children into it."""
        pad = T["padding"] if is_root else 0
        self._frame = tk.Frame(parent, bg=T["bg"], padx=pad, pady=pad)
        self._frame.grid_columnconfigure(0, weight=1)
        for row, item in enumerate(self._items):
            if item == '__stretch__':
                spacer = tk.Frame(self._frame, bg=T["bg"])
                spacer.grid(row=row, column=0, sticky='nsew')
                self._frame.grid_rowconfigure(row, weight=1)
            elif isinstance(item, (TkVBoxLayout, TkHBoxLayout, _group_box())):
                child_frame = item.build(self._frame)
                child_frame.grid(row=row, column=0, sticky='ew', pady=2)
            elif hasattr(item, '_rebuild'):
                # Rebuild widget with correct parent
                widget = item._rebuild(self._frame)
                widget.grid(row=row, column=0, sticky='ew', pady=2)
            elif isinstance(item, tk.Widget):
                item.grid(row=row, column=0, sticky='ew', pady=2)
        return self._frame
class TkHBoxLayout:
    """Tkinter HBox - virtual container that tracks items."""
    def __init__(self, parent=None):
        self._items = []
        self._frame = None

    def addItem(self, item):
        self._items.append(item)

    def addStretch(self):
        self._items.append('__stretch__')

    def setAlignmentTop(self):
        pass

    def build(self, parent, is_root=False):
        """Build the actual tk.Frame with correct parent and grid children into it."""
        self._frame = tk.Frame(parent, bg=T["bg"])

        # First pass: assign column indices and configure weights
        # stretch cols get higher weight (act as spacers); widget cols uniform equal
        col_index = 0
        for item in self._items:
            if item == '__stretch__':
                self._frame.grid_columnconfigure(col_index, weight=3)
            else:
                self._frame.grid_columnconfigure(col_index, weight=1, uniform="equal")
            col_index += 1

        # Second pass: build and place widgets
        col_index = 0
        for item in self._items:
            if item == '__stretch__':
                spacer = tk.Frame(self._frame, bg=T["bg"])
                spacer.grid(row=0, column=col_index, sticky='nsew')
            elif isinstance(item, (TkVBoxLayout, TkHBoxLayout, _group_box())):
                child_frame = item.build(self._frame)
                child_frame.grid(row=0, column=col_index, sticky='ew', padx=3)
            elif hasattr(item, '_rebuild'):
                widget = item._rebuild(self._frame)
                widget.grid(row=0, column=col_index, sticky='ew', padx=1)
            elif isinstance(item, tk.Widget):
                item.grid(row=0, column=col_index, sticky='ew', padx=1)
            col_index += 1
        return self._frame
class TkTabWidget(ttk.Notebook):
    def __init__(self, parent=None):
        super().__init__(parent or tk._default_root)

    def addTab(self, item, tab_name):
        if not isinstance(item, tk.Frame):
            # Create frame if item is not already a frame
            frame = tk.Frame(self)
            if isinstance(item, tk.Widget):
                item.pack(fill='both', expand=True)
            item = frame
        self.add(item, text=tab_name)

    def currentIndex(self):
        return self.index(self.select())

    def hide(self):
        self.grid_remove()

    def show(self):
        self.grid()

    def removeTabs(self):
        for tab in self.tabs():
            self.forget(tab)

    def _rebuild(self, parent):
        self.destroy()
        super().__init__(parent)
        return self
class TkVBoxLayoutAdapter(IVBoxLayout):
    """Tkinter VBox adapter - implements new interface convention"""

    def __init__(self, native_layout: TkVBoxLayout):
        self._native = native_layout

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        self._native.addItem(widget.get_native())

    def add_stretch(self):
        self._native.addStretch()

    def set_alignment_top(self):
        self._native.setAlignmentTop()
class TkHBoxLayoutAdapter(IHBoxLayout):
    """Tkinter HBox adapter - implements new interface convention"""

    def __init__(self, native_layout: TkHBoxLayout):
        self._native = native_layout

    def get_native(self):
        return self._native

    # ILayoutCapable
    def add_item(self, widget: IWidget):
        self._native.addItem(widget.get_native())

    def add_stretch(self):
        self._native.addStretch()

    def set_alignment_top(self):
        self._native.setAlignmentTop()
class TkTabWidgetAdapter(ITabWidget):
    """Tkinter TabWidget adapter - implements new interface convention"""

    def __init__(self, native_widget: TkTabWidget):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITabCapable
    def add_tab(self, widget: IWidget, name: str):
        self._native.addTab(widget.get_native(), name)

    def remove_tabs(self):
        self._native.removeTabs()

    def get_current_index(self) -> int:
        return self._native.currentIndex()

    # IVisibilityCapable
    def show(self):
        self._native.show()

    def hide(self):
        self._native.hide()

    def is_visible(self) -> bool:
        return self._native.winfo_viewable()
