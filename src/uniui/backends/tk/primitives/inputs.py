"""Input primitives: buttons, text entry, and selection controls."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ....core import *
from ....strategies import normalize_text, parse_float
from ....theme import THEME

#: Alias for the live theme dict, mutated in place on a theme switch.
T = THEME

#: Maps a button's semantic type onto its palette key. Used only by
#: TkPushButton, so it lives here rather than in a shared module.
_BTNTYPE_KEY = {
    "action":  "accent_action",
    "op":      "accent_op",
    "sci":     "accent_sci",
    "neutral": "accent_neutral",
}

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
class TkButtonAdapter(IButton):
    """Tkinter Button adapter - implements new interface convention"""

    def __init__(self, native_widget: TkPushButton):
        self._native = native_widget

    def get_native(self):
        return self._native

    # ITextCapable
    def set_text(self, text: str):
        value = "" if text is None else str(text).strip()
        self._native.setText(value)

    def get_text(self) -> str:
        value = self._native.cget('text')
        return "" if value is None else str(value).strip()

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
        def _handle_modified(_event=None):
            if self._native.edit_modified():
                self._native.edit_modified(False)
                callback()

        self._native.bind("<<Modified>>", _handle_modified, add="+")
        self._native.edit_modified(False)

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
        self._enabled = True

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
        self._enabled = bool(enabled)

    def is_enabled(self) -> bool:
        return self._enabled

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
        self._enabled = True

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
        self._enabled = bool(enabled)

    def is_enabled(self) -> bool:
        return self._enabled

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
