"""Text and display primitives: labels, images, group boxes."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ....core import *
from ....strategies import normalize_text, parse_float
from ....theme import THEME

#: Alias for the live theme dict, mutated in place on a theme switch.
T = THEME


class TkLabel(tk.Label):
    def __init__(self, parent=None):
        super().__init__(
            parent or tk._default_root,
            font=(T["font_family"], T["font_size"], "normal"),
            bg=T["bg"],
            fg=T["fg"],
            anchor='w',
            justify='left',
        )

    def setText(self, text):
        self.config(text=text)

    def getText(self):
        return self.cget('text')

    def hide(self):
        self.grid_remove()

    def show(self):
        self.grid()

    def setFixedWidth(self, width):
        self.config(width=width // 8)

    def _rebuild(self, parent):
        text = self.cget('text')
        self.destroy()
        super().__init__(
            parent,
            text=text,
            font=(T["font_family"], T["font_size"], "normal"),
            bg=T["bg"],
            fg=T["fg"],
            anchor='w',
            justify='left',
        )
        return self
class TkImage(tk.Label):
    def __init__(self, parent=None):
        super().__init__(parent or tk._default_root)
        self._photo = None
        self._image_path = None

    def setFixedWidth(self, width):
        self.config(width=width // 8)

    def setImage(self, image_path):
        self._image_path = image_path
        try:
            from PIL import Image, ImageTk
        except ImportError:
            self._photo = tk.PhotoImage(file=image_path)
        else:
            img = Image.open(image_path)
            self._photo = ImageTk.PhotoImage(img)
        self.config(image=self._photo)

    def setImageFromUrl(self, url):
        raise NotSupportedError(
            "Image URL loading is not supported in the Tkinter backend. "
            "Use setImage with a local file path."
        )

    def _rebuild(self, parent):
        self.destroy()
        super().__init__(parent)
        if self._image_path:
            self.setImage(self._image_path)
        return self
class TkGroupBox:
    """Tkinter GroupBox - virtual container, builds a LabelFrame on build()."""
    def __init__(self, parent=None):
        self._title = ""
        self._layout = None
        self._frame = None  # built tk.LabelFrame, created in build()

    def setTitle(self, title):
        self._title = title

    def setLayout(self, layout):
        self._layout = layout

    def build(self, parent):
        """Build the actual tk.LabelFrame with correct parent."""
        self._frame = tk.LabelFrame(
            parent,
            text=self._title,
            padx=T["padding_inner"], pady=T["padding_inner"],
            bg=T["bg"],
            fg=T["fg"],
            font=(T["font_family"], T["font_size"], "bold")
        )
        self._frame.grid_rowconfigure(0, weight=1)
        self._frame.grid_columnconfigure(0, weight=1)
        if self._layout is not None:
            from .layouts import TkHBoxLayout, TkVBoxLayout

            if isinstance(self._layout, (TkVBoxLayout, TkHBoxLayout)):
                child = self._layout.build(self._frame)
                child.grid(row=0, column=0, sticky='nsew')
            elif hasattr(self._layout, '_rebuild'):
                widget = self._layout._rebuild(self._frame)
                widget.grid(row=0, column=0, sticky='nsew')
            elif isinstance(self._layout, tk.Widget):
                self._layout.grid(row=0, column=0, sticky='nsew')
        return self._frame
class TkLabelAdapter(ILabel):
    """Tkinter Label adapter - implements new interface convention"""

    def __init__(self, native_widget: TkLabel):
        self._native = native_widget
        self._visible_state = False

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.getText())

    # IVisibilityCapable
    def show(self):
        self._native.show()
        self._visible_state = True

    def hide(self):
        self._native.hide()
        self._visible_state = False

    def is_visible(self) -> bool:
        try:
            return self._native.winfo_viewable() or self._visible_state
        except Exception:
            return self._visible_state

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.config(height=height // 20)  # Approximate conversion to lines

    def set_minimum_width(self, width: int):
        self._native.config(width=width // 8)

    def set_minimum_height(self, height: int):
        self._native.config(height=height // 20)
class TkImageAdapter(IImage):
    """Tkinter Image adapter - implements new interface convention"""

    def __init__(self, native_widget: TkImage):
        self._native = native_widget

    def get_native(self):
        return self._native

    # IImageCapable
    def set_image(self, path: str):
        self._native.setImage(path)

    def set_image_from_url(self, url: str):
        self._native.setImageFromUrl(url)

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.config(height=height // 20)

    def set_minimum_width(self, width: int):
        self._native.config(width=width // 8)

    def set_minimum_height(self, height: int):
        self._native.config(height=height // 20)
class TkGroupBoxAdapter(IGroupBox):
    """Tkinter GroupBox adapter - implements new interface convention"""

    def __init__(self, native_widget: TkGroupBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # IContainerCapable
    def set_layout(self, layout: IWidget):
        self._native.setLayout(layout.get_native())

    # ITitleCapable
    def set_title(self, title: str):
        self._native.setTitle(title)
