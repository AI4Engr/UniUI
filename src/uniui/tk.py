"""
Tkinter backend.

Native widgets, adapters, and factory for the Tkinter platform.
Uses virtual layout containers (TkVBoxLayout/TkHBoxLayout) that build
real tk widgets when build(parent) is called.
"""
from __future__ import annotations

# Import capability interfaces from core
from .core import *
from .strategies import normalize_text, parse_float
from .theme import THEME

# Tkinter imports
import tkinter as tk
from tkinter import ttk

T = THEME


# ============================================================================
# Native Widget Classes (imported from widgets/tk_widgets.py)
# ============================================================================

class TkLineEdit(tk.Entry):
    def __init__(self, parent=None):
        super().__init__(
            parent or tk._default_root,
            font=(T["font_family"], T["font_size"]),
            relief=tk.SOLID,
            borderwidth=1,
            bg=T["bg_input"],
            fg=T["fg"],
            insertbackground=T["accent"]
        )
        self.config(highlightthickness=2, highlightcolor=T["accent"], highlightbackground=T["border"])
        self._finish_cb = None
        self._change_cb = None

    def getText(self):
        return self.get()

    def setValue(self, value):
        self.delete(0, tk.END)
        self.insert(0, str(value))

    def setText(self, text):
        self.delete(0, tk.END)
        self.insert(0, text)

    def finishEditing(self, function):
        self._finish_cb = function
        self.bind('<Return>', lambda e: function())
        self.bind('<FocusOut>', lambda e: function())

    def textChanged(self, function):
        self._change_cb = function
        self._text_var = tk.StringVar()
        self.config(textvariable=self._text_var)
        self._text_var.trace_add('write', lambda *args: function())

    def getValue(self):
        text = self.get()
        if text == "":
            return 0.0
        else:
            try:
                return float(text)
            except ValueError:
                return text

    def setFixedWidth(self, width):
        self.config(width=width // 8)

    def hide(self):
        self.grid_remove()

    def show(self):
        self.grid()

    def setEnabled(self, flag):
        self.config(state='normal' if flag else 'disabled')

    def setTextColor(self, color, background):
        self.config(fg=color, bg=background)

    def _rebuild(self, parent):
        text = self.get()
        self.destroy()
        super().__init__(
            parent,
            font=(T["font_family"], T["font_size"]),
            relief=tk.SOLID,
            borderwidth=1,
            bg=T["bg_input"],
            fg=T["fg"],
            insertbackground=T["accent"]
        )
        self.config(highlightthickness=2, highlightcolor=T["accent"], highlightbackground=T["border"])
        if text:
            self.insert(0, text)
        if self._finish_cb:
            self.finishEditing(self._finish_cb)
        if self._change_cb:
            self.textChanged(self._change_cb)
        return self


class TkComboBox(ttk.Combobox):
    def __init__(self, parent=None):
        super().__init__(parent or tk._default_root)
        self['values'] = []
        self._connect_cb = None

    def addItem(self, item):
        current = list(self['values'])
        current.append(item)
        self['values'] = current

    def connect(self, function):
        self._connect_cb = function
        self.bind('<<ComboboxSelected>>', lambda e: function())

    def currentText(self):
        return self.get()

    def clear(self):
        self['values'] = []
        self.set('')

    def deleteItem(self, item):
        current = list(self['values'])
        if item in current:
            current.remove(item)
            self['values'] = current

    def setEditable(self, editable):
        self.config(state='normal' if editable else 'readonly')

    def setEditText(self, text):
        self.set(text)

    def setEnabled(self, flag):
        self.config(state='normal' if flag else 'disabled')

    def setFixedWidth(self, width):
        self.config(width=width // 8)

    def setSelection(self, item):
        if item in self['values']:
            self.set(item)

    def sort(self):
        current = list(self['values'])
        current.sort()
        self['values'] = current

    def _rebuild(self, parent):
        values = list(self['values'])
        selection = self.get()
        state = str(self.cget('state'))
        self.destroy()
        super().__init__(parent)
        self['values'] = values
        if state:
            self.config(state=state)
        if selection:
            self.set(selection)
        if self._connect_cb:
            self.bind('<<ComboboxSelected>>', lambda e: self._connect_cb())
        return self


class TkDropdown(ttk.Combobox):
    def __init__(self, parent=None):
        super().__init__(
            parent or tk._default_root,
            state='readonly',
            font=(T["font_family"], T["font_size"])
        )
        self['values'] = []
        self._connect_cb = None
        # Configure style for better appearance
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox',
                       fieldbackground=T["bg_input"],
                       background=T["bg_input"],
                       borderwidth=1,
                       relief='solid')

    def addItem(self, item):
        current = list(self['values'])
        current.append(item)
        self['values'] = current

    def clear(self):
        self['values'] = []
        self.set('')

    def connect(self, function):
        self._connect_cb = function
        self.bind('<<ComboboxSelected>>', lambda e: function())

    def currentText(self):
        return self.get()

    def deleteItem(self, item):
        current = list(self['values'])
        if item in current:
            current.remove(item)
            self['values'] = current

    def hide(self):
        self.grid_remove()

    def show(self):
        self.grid()

    def setEnabled(self, flag):
        self.config(state='readonly' if flag else 'disabled')

    def setFixedWidth(self, width):
        self.config(width=width // 8)

    def setSelection(self, item):
        if item in self['values']:
            self.set(item)

    def setValue(self, value_list):
        self['values'] = value_list
        if len(value_list) > 0:
            self.current(0)

    def sort(self):
        current = list(self['values'])
        current.sort()
        self['values'] = current

    def _rebuild(self, parent):
        values = list(self['values'])
        selection = self.get()
        self.destroy()
        super().__init__(parent, state='readonly', font=(T["font_family"], T["font_size"]))
        self['values'] = values
        if selection:
            self.set(selection)
        if self._connect_cb:
            self.bind('<<ComboboxSelected>>', lambda e: self._connect_cb())
        return self


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
            elif isinstance(item, (TkVBoxLayout, TkHBoxLayout, TkGroupBox)):
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
            elif isinstance(item, (TkVBoxLayout, TkHBoxLayout, TkGroupBox)):
                child_frame = item.build(self._frame)
                child_frame.grid(row=0, column=col_index, sticky='ew', padx=3)
            elif hasattr(item, '_rebuild'):
                widget = item._rebuild(self._frame)
                widget.grid(row=0, column=col_index, sticky='ew', padx=1)
            elif isinstance(item, tk.Widget):
                item.grid(row=0, column=col_index, sticky='ew', padx=1)
            col_index += 1
        return self._frame


# Map btntype -> theme key prefix
_BTNTYPE_KEY = {
    "action":  "accent_action",
    "op":      "accent_op",
    "sci":     "accent_sci",
    "neutral": "accent_neutral",
}


class TkPushButton(tk.Canvas):
    """Canvas-based rounded button with hover/press colour effects."""
    _DEFAULT_H = 30

    def __init__(self, parent=None):
        self._btntype  = None
        self._callback = None
        self._text_str = ''
        self._enabled  = True
        self._radius   = T.get('border_radius', 8)
        super().__init__(
            parent or tk._default_root,
            bg=T['bg'],
            highlightthickness=0,
            bd=0,
            cursor='hand2',
            height=self._DEFAULT_H,
            width=1,   # grid weight will expand it
        )
        self.bind('<Configure>', self._on_configure)
        self._bind_hover()

    # ---- colour helpers ---- #
    def _colors(self):
        key    = _BTNTYPE_KEY.get(self._btntype, 'accent')
        normal = T[key]
        hover  = T.get(key + '_hover', normal)
        press  = T.get(key + '_press', hover)
        return normal, hover, press

    # ---- drawing ---- #
    def _on_configure(self, event):
        normal, _, _ = self._colors()
        self._draw(normal, event.width, event.height)

    def _draw(self, fill_color, w=None, h=None):
        if w is None: w = self.winfo_width()
        if h is None: h = self.winfo_height()
        if w < 2 or h < 2:
            return
        # Match canvas bg to parent bg (theme may have changed)
        try: super().config(bg=T['bg'])
        except Exception: pass
        self.delete('all')
        r = min(self._radius, w // 2, h // 2)
        # Rounded rectangle via smooth polygon
        pts = [
            r,   0,   w-r, 0,
            w,   0,   w,   r,
            w,   h-r, w,   h,
            w-r, h,   r,   h,
            0,   h,   0,   h-r,
            0,   r,   0,   0,
        ]
        self.create_polygon(pts, smooth=True,
                            fill=fill_color, outline='')
        text_fill = T['fg_button'] if self._enabled else T.get('fg_muted', '#888')
        self.create_text(
            w / 2, h / 2,
            text=self._text_str,
            fill=text_fill,
            font=(T['font_family'], T['font_size'], 'bold'),
        )

    def refresh_colors(self):
        """Re-draw with current theme (called after theme switch)."""
        normal, _, _ = self._colors()
        self._draw(normal)

    # ---- interaction ---- #
    def _bind_hover(self):
        def on_enter(e):
            if not self._enabled: return
            _, hover, _ = self._colors(); self._draw(hover)
        def on_leave(e):
            if not self._enabled: return
            normal, _, _ = self._colors(); self._draw(normal)
        def on_press(e):
            if not self._enabled: return
            _, _, press = self._colors(); self._draw(press)
        def on_release(e):
            if not self._enabled: return
            _, hover, _ = self._colors(); self._draw(hover)
            if self._callback: self._callback()
        self.bind('<Enter>',          on_enter)
        self.bind('<Leave>',          on_leave)
        self.bind('<ButtonPress-1>',  on_press)
        self.bind('<ButtonRelease-1>',on_release)

    def set_btntype(self, btntype):
        self._btntype = btntype
        self.refresh_colors()

    # ---- public API (mirrors original TkPushButton) ---- #
    def setText(self, text):
        self._text_str = text
        self.refresh_colors()

    def connect(self, function):
        self._callback = function

    def cget(self, key):
        if key == 'text':  return self._text_str
        if key == 'state': return 'normal' if self._enabled else 'disabled'
        return super().cget(key)

    def config(self, **kwargs):
        if 'text'    in kwargs: self.setText(kwargs.pop('text'))
        if 'command' in kwargs: self._callback = kwargs.pop('command')
        state = kwargs.pop('state', None)
        if state is not None:
            self._enabled = (state == 'normal')
            super().config(cursor='hand2' if self._enabled else 'arrow')
            self.refresh_colors()
        # Forward only Canvas-legal kwargs
        canvas_keys = {'width', 'height', 'cursor', 'bg', 'background'}
        safe = {k: v for k, v in kwargs.items() if k in canvas_keys}
        if safe:
            try: super().config(**safe)
            except Exception: pass

    def _rebuild(self, parent):
        text     = self._text_str
        btntype  = self._btntype
        callback = self._callback
        self.destroy()
        self.__init__(parent)
        self.setText(text)
        if btntype:  self.set_btntype(btntype)
        if callback: self.connect(callback)
        return self

    def setFixedWidth(self, width):
        super().config(width=width)

    def setFixedHeight(self, height):
        super().config(height=height)

    def setMinimumWidth(self, width):  pass
    def setMinimumHeight(self, height): pass


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


class TkTextarea(tk.Text):
    def __init__(self, parent=None):
        super().__init__(
            parent or tk._default_root,
            state='disabled',
            font=(T["font_family"], T["font_size"]),
            relief=tk.SOLID,
            borderwidth=1,
            bg=T["bg_input"],
            fg=T["fg"],
            wrap=tk.WORD,
            padx=T["padding_inner"],
            pady=T["padding_inner"]
        )
        self.config(highlightthickness=2, highlightcolor=T["accent"], highlightbackground=T["border"])
        self._max_height = None

    def setText(self, text):
        self.config(state='normal')
        self.delete('1.0', tk.END)
        self.insert('1.0', text)
        self.config(state='disabled')

    def clear(self):
        self.config(state='normal')
        self.delete('1.0', tk.END)
        self.config(state='disabled')

    def getText(self):
        return self.get('1.0', tk.END).rstrip('\n')

    def setMaximumHeight(self, value):
        # Convert pixels to approximate lines
        self._max_height = value
        lines = value // 20
        self.config(height=lines)

    def _rebuild(self, parent):
        content = self.get('1.0', tk.END).rstrip('\n')
        max_height = self._max_height
        self.destroy()
        super().__init__(
            parent,
            state='disabled',
            font=(T["font_family"], T["font_size"]),
            relief=tk.SOLID,
            borderwidth=1,
            bg=T["bg_input"],
            fg=T["fg"],
            wrap=tk.WORD,
            padx=T["padding_inner"],
            pady=T["padding_inner"]
        )
        self.config(highlightthickness=2, highlightcolor=T["accent"], highlightbackground=T["border"])
        self._max_height = max_height
        if max_height:
            self.config(height=max_height // 20)
        if content:
            self.config(state='normal')
            self.insert('1.0', content)
            self.config(state='disabled')
        return self


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


class TkImage(tk.Label):
    def __init__(self, parent=None):
        super().__init__(parent or tk._default_root)
        self._photo = None
        self._image_path = None

    def setFixedWidth(self, width):
        self.config(width=width // 8)

    def setImage(self, image_path):
        self._image_path = image_path
        from PIL import Image, ImageTk
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
            if isinstance(self._layout, (TkVBoxLayout, TkHBoxLayout)):
                child = self._layout.build(self._frame)
                child.grid(row=0, column=0, sticky='nsew')
            elif hasattr(self._layout, '_rebuild'):
                widget = self._layout._rebuild(self._frame)
                widget.grid(row=0, column=0, sticky='nsew')
            elif isinstance(self._layout, tk.Widget):
                self._layout.grid(row=0, column=0, sticky='nsew')
        return self._frame


# ============================================================================
# Adapter Classes (snake_case interface methods)
# ============================================================================

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


class TkButtonAdapter(IButton):
    """Tkinter Button adapter - implements new interface convention"""

    def __init__(self, native_widget: TkPushButton):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(text)

    def get_text(self) -> str:
        return self._native.cget('text')

    # IEventCapable
    def connect(self, callback):
        self._native.connect(callback)

    # IEnableCapable
    def set_enabled(self, enabled: bool):
        self._native.config(state='normal' if enabled else 'disabled')

    def is_enabled(self) -> bool:
        return self._native.cget('state') == 'normal'

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        self._native.setFixedHeight(height)

    def set_minimum_width(self, width: int):
        self._native.setMinimumWidth(width)

    def set_minimum_height(self, height: int):
        self._native.setMinimumHeight(height)


class TkLineEditAdapter(ILineEdit):
    """Tkinter LineEdit adapter - implements new interface convention"""

    def __init__(self, native_widget: TkLineEdit):
        self._native = native_widget
        self._visible_state = False

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.getText())

    # IValueCapable
    def set_value(self, value):
        self._native.setValue(value)

    def get_value(self):
        text = self.get_text()
        try:
            return parse_float(text)
        except ValueError:
            raise InvalidValueError(f"Invalid numeric value: {text}")

    # IChangeEventCapable
    def on_change(self, callback):
        self._native.textChanged(callback)

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

    # IEnableCapable
    def set_enabled(self, enabled: bool):
        self._native.setEnabled(enabled)

    def is_enabled(self) -> bool:
        return self._native.cget('state') == 'normal'

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        # Entry widgets have fixed height in tkinter
        pass

    def set_minimum_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_minimum_height(self, height: int):
        # Entry widgets have fixed height in tkinter
        pass


class TkTextAreaAdapter(ITextArea):
    """Tkinter TextArea adapter - implements new interface convention"""

    def __init__(self, native_widget: TkTextarea):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        self._native.setText(text)

    def get_text(self) -> str:
        return self._native.getText()

    # IMultiLineCapable
    def append(self, text: str):
        self._native.config(state='normal')
        self._native.insert(tk.END, text)
        self._native.config(state='disabled')

    def clear(self):
        self._native.clear()

    def set_maximum_height(self, height: int):
        self._native.setMaximumHeight(height)

    # IChangeEventCapable
    def on_change(self, callback):
        # Text widget doesn't have easy change tracking
        pass

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.config(width=width // 8)

    def set_fixed_height(self, height: int):
        self._native.config(height=height // 20)

    def set_minimum_width(self, width: int):
        self._native.config(width=width // 8)

    def set_minimum_height(self, height: int):
        self._native.config(height=height // 20)


class TkComboBoxAdapter(IComboBox):
    """Tkinter ComboBox adapter - implements new interface convention"""

    def __init__(self, native_widget: TkComboBox):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ISelectionCapable
    def add_item(self, item: str):
        self._native.addItem(item)

    def clear(self):
        self._native.clear()

    def set_selection(self, item: str):
        self._native.setSelection(item)

    def get_text(self) -> str:
        return self._native.currentText()

    # IChangeEventCapable
    def on_change(self, callback):
        self._native.connect(callback)

    # IEnableCapable
    def set_enabled(self, enabled: bool):
        self._native.setEnabled(enabled)

    def is_enabled(self) -> bool:
        state = self._native.cget('state')
        return state in ['normal', 'readonly']

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        # Combobox has fixed height in tkinter
        pass

    def set_minimum_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_minimum_height(self, height: int):
        # Combobox has fixed height in tkinter
        pass


class TkDropdownAdapter(IDropdown):
    """Tkinter Dropdown adapter - implements new interface convention"""

    def __init__(self, native_widget: TkDropdown):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ISelectionCapable
    def add_item(self, item: str):
        self._native.addItem(item)

    def clear(self):
        self._native.clear()

    def set_selection(self, item: str):
        self._native.setSelection(item)

    def get_text(self) -> str:
        return self._native.currentText()

    # IValueCapable
    def set_value(self, value_list: list):
        """Set dropdown items from a list."""
        self._native.setValue(value_list)

    # IChangeEventCapable
    def on_change(self, callback):
        self._native.connect(callback)

    # IVisibilityCapable
    def show(self):
        self._native.show()

    def hide(self):
        self._native.hide()

    def is_visible(self) -> bool:
        return self._native.winfo_viewable()

    # IEnableCapable
    def set_enabled(self, enabled: bool):
        self._native.setEnabled(enabled)

    def is_enabled(self) -> bool:
        state = self._native.cget('state')
        return state == 'readonly'

    # ISizeCapable
    def set_fixed_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_fixed_height(self, height: int):
        # Combobox has fixed height in tkinter
        pass

    def set_minimum_width(self, width: int):
        self._native.setFixedWidth(width)

    def set_minimum_height(self, height: int):
        # Combobox has fixed height in tkinter
        pass


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


# ============================================================================
# Tkinter Widget Factory
# ============================================================================

class TkWidgetFactory(IWidgetFactory):
    """Tkinter widget factory - creates properly wrapped widgets"""

    def __init__(self):
        # Ensure Tk root is created
        if tk._default_root is None:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide default window
        else:
            self.root = tk._default_root

    # Basic widgets
    def createLabel(self) -> ILabel:
        native = TkLabel(self.root)
        return TkLabelAdapter(native)

    def createButton(self) -> IButton:
        native = TkPushButton(self.root)
        return TkButtonAdapter(native)

    def createLineEdit(self) -> ILineEdit:
        native = TkLineEdit(self.root)
        return TkLineEditAdapter(native)

    def createTextArea(self) -> ITextArea:
        native = TkTextarea(self.root)
        return TkTextAreaAdapter(native)

    def createComboBox(self) -> IComboBox:
        native = TkComboBox(self.root)
        return TkComboBoxAdapter(native)

    def createDropdown(self) -> IDropdown:
        native = TkDropdown(self.root)
        return TkDropdownAdapter(native)

    # Layouts
    def createVBox(self) -> IVBoxLayout:
        native = TkVBoxLayout(self.root)
        return TkVBoxLayoutAdapter(native)

    def createHBox(self) -> IHBoxLayout:
        native = TkHBoxLayout(self.root)
        return TkHBoxLayoutAdapter(native)

    # Advanced widgets
    def createTabWidget(self) -> ITabWidget:
        native = TkTabWidget(self.root)
        return TkTabWidgetAdapter(native)

    def createImage(self) -> IImage:
        native = TkImage(self.root)
        return TkImageAdapter(native)

    def createGroupBox(self) -> IGroupBox:
        native = TkGroupBox(self.root)
        return TkGroupBoxAdapter(native)
