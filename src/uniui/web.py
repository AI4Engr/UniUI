"""NiceGUI-powered Web backend for UniUI.

The public backend name is ``web``. NiceGUI remains an implementation detail.
Widgets are created eagerly and moved into containers when UniUI layouts are
assembled, which preserves the existing declarative API.
"""

from __future__ import annotations

import html as html_lib
import re
from pathlib import Path
from typing import Any, Callable, List

from nicegui import ui

from .core import (
    IButton,
    IComboBox,
    IDropdown,
    IGroupBox,
    IHBoxLayout,
    IImage,
    ILabel,
    ILineEdit,
    ITabWidget,
    ITextArea,
    IVBoxLayout,
    IWidget,
    IWidgetFactory,
    InvalidValueError,
)
from .strategies import normalize_text, parse_float
from .theme import THEME, is_dark

T = THEME
_adapters: List[Any] = []
_css_installed = False
_dark_mode = None
_backend_active = False


def set_backend_active(active: bool) -> None:
    global _backend_active
    _backend_active = bool(active)


def _install_css() -> None:
    global _css_installed
    if _css_installed:
        return
    ui.add_css(
        """
        body { margin: 0; }
        .uniui-root { min-height: 100vh; box-sizing: border-box; }
        .uniui-vbox, .uniui-hbox { gap: var(--uniui-spacing, 8px); }
        .uniui-hbox { flex-wrap: wrap; }
        .uniui-label { font-weight: 600; }
        .uniui-button { min-height: 32px; font-weight: 600; }
        .uniui-input .q-field__control,
        .uniui-select .q-field__control { border-radius: var(--uniui-radius, 8px); }
        .uniui-textarea { overflow: auto; white-space: pre-wrap; width: 100%; box-sizing: border-box; }
        .uniui-group { width: 100%; box-sizing: border-box; }
        .uniui-group-title { font-weight: 700; }
        @media (max-width: 640px) {
            .uniui-root { width: 100% !important; padding: 10px !important; }
            .uniui-hbox { flex-direction: column; align-items: stretch; }
            .uniui-hbox > * { width: 100%; }
        }
        """,
        shared=True,
    )
    _css_installed = True


def _style_size(native, name: str, value: int) -> None:
    native.style(f"{name}: {int(value)}px")


def _set_enabled(native, enabled: bool) -> None:
    if enabled:
        native.enable()
    else:
        native.disable()


def _plain_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    return html_lib.unescape(value).strip()


class _WebAdapter:
    def __init__(self, native):
        _install_css()
        self._native = native
        _adapters.append(self)

    def get_native(self):
        return self._native

    def _apply_theme(self) -> None:
        pass

    def set_fixed_width(self, width: int) -> None:
        _style_size(self._native, "width", width)

    def set_fixed_height(self, height: int) -> None:
        _style_size(self._native, "height", height)

    def set_minimum_width(self, width: int) -> None:
        _style_size(self._native, "min-width", width)

    def set_minimum_height(self, height: int) -> None:
        _style_size(self._native, "min-height", height)

    def show(self) -> None:
        self._native.set_visibility(True)

    def hide(self) -> None:
        self._native.set_visibility(False)

    def is_visible(self) -> bool:
        return bool(self._native.visible)


class WebLabelAdapter(_WebAdapter, ILabel):
    def __init__(self):
        super().__init__(ui.label("").classes("uniui-label"))
        self._apply_theme()

    def set_text(self, text: str) -> None:
        self._native.set_text(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.text)

    def _apply_theme(self) -> None:
        self._native.style(f"color: {T.get('fg_muted', T['fg'])}")


class WebButtonAdapter(_WebAdapter, IButton):
    _BUTTON_KEYS = {
        "action": "accent_action",
        "op": "accent_op",
        "sci": "accent_sci",
        "neutral": "accent_neutral",
    }

    def __init__(self):
        self._callbacks: List[Callable[[], None]] = []
        self._enabled = True
        self._button_type = None
        native = ui.button("").classes("uniui-button")
        super().__init__(native)
        native._callback = self._emit_click
        native.set_btntype = self.set_btntype
        native.on("click", lambda _event: self._emit_click())
        self._apply_theme()

    def _emit_click(self) -> None:
        if self._enabled:
            for callback in list(self._callbacks):
                callback()

    def set_btntype(self, button_type) -> None:
        self._button_type = button_type
        self._apply_theme()

    def set_text(self, text: str) -> None:
        self._native.set_text(normalize_text(text))

    def get_text(self) -> str:
        return normalize_text(self._native.text)

    def connect(self, callback: Callable[[], None]) -> None:
        self._callbacks.append(callback)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        _set_enabled(self._native, self._enabled)

    def is_enabled(self) -> bool:
        return self._enabled

    def _apply_theme(self) -> None:
        key = self._BUTTON_KEYS.get(self._button_type, "accent")
        self._native.style(
            f"background-color: {T.get(key, T['accent'])}; "
            f"color: {T['fg_button']}; border-radius: {T['border_radius']}px"
        )


class WebLineEditAdapter(_WebAdapter, ILineEdit):
    def __init__(self):
        self._callbacks: List[Callable[[], None]] = []
        self._enabled = True
        self._suppress_change = False
        native = ui.input(value="").classes("uniui-input w-full")
        super().__init__(native)
        native.on_value_change(lambda _event: self._emit_change())
        native.event_generate = lambda _name: self._emit_change()
        self._apply_theme()

    def _emit_change(self) -> None:
        if self._suppress_change:
            return
        for callback in list(self._callbacks):
            callback()

    def set_text(self, text: str) -> None:
        self._suppress_change = True
        try:
            self._native.set_value(normalize_text(text))
        finally:
            self._suppress_change = False
        self._emit_change()

    def get_text(self) -> str:
        return normalize_text(self._native.value)

    def set_value(self, value: Any) -> None:
        self.set_text(value)

    def get_value(self):
        text = self.get_text()
        try:
            return parse_float(text)
        except ValueError as exc:
            raise InvalidValueError(f"Invalid numeric value: {text}") from exc

    def on_change(self, callback: Callable[[], None]) -> None:
        self._callbacks.append(callback)

    def on_finish_edit(self, callback: Callable[[], None]) -> None:
        self._native.on("blur", lambda _event: callback())
        self._native.on("keydown.enter", lambda _event: callback())

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        _set_enabled(self._native, self._enabled)

    def is_enabled(self) -> bool:
        return self._enabled

    def _apply_theme(self) -> None:
        self._native.style(
            f"color: {T['fg']}; background: {T['bg_input']}; "
            f"border-radius: {T['border_radius']}px"
        )


class WebTextAreaAdapter(_WebAdapter, ITextArea):
    def __init__(self):
        self._text = ""
        self._callbacks: List[Callable[[], None]] = []
        native = ui.html("", sanitize=False).classes("uniui-textarea")
        super().__init__(native)
        native.edit_modified = lambda _value=None: None
        native.event_generate = lambda _name: self._emit_change()
        self._apply_theme()

    def _emit_change(self) -> None:
        for callback in list(self._callbacks):
            callback()

    def _plain_content(self) -> str:
        escaped = html_lib.escape(self._text)
        return f'<pre style="margin:0;white-space:pre-wrap">{escaped}</pre>'

    def set_text(self, text: str) -> None:
        self._text = "" if text is None else str(text)
        self._native.set_content(self._plain_content())

    def set_html(self, html: str) -> None:
        self._text = _plain_html(html)
        self._native.set_content(html or "")

    def get_text(self) -> str:
        return self._text

    def append(self, text: str) -> None:
        self.set_text(f"{self._text}{'' if text is None else str(text)}")

    def clear(self) -> None:
        self.set_text("")

    def on_change(self, callback: Callable[[], None]) -> None:
        self._callbacks.append(callback)

    def set_maximum_height(self, height: int) -> None:
        _style_size(self._native, "max-height", height)

    def _apply_theme(self) -> None:
        self._native.style(
            f"color: {T['fg']}; background: {T['bg_input']}; "
            f"border: 1px solid {T['border']}; border-radius: {T['border_radius']}px; "
            f"padding: {T['padding_inner']}px"
        )


class _WebSelectAdapter(_WebAdapter):
    def __init__(self, *, editable: bool):
        self._callbacks: List[Callable[[], None]] = []
        self._enabled = True
        self._suppress_change = False
        native = ui.select([], with_input=editable).classes("uniui-select w-full")
        super().__init__(native)
        native.on_value_change(lambda _event: self._emit_change())
        native.event_generate = lambda _name: self._emit_change()
        self._apply_theme()

    def _emit_change(self) -> None:
        if self._suppress_change:
            return
        for callback in list(self._callbacks):
            callback()

    def add_item(self, item: str) -> None:
        item = normalize_text(item)
        options = list(self._native.options)
        options.append(item)
        self._native.options = options
        if self._native.value is None:
            self._native.value = item
        self._native.update()

    def clear(self) -> None:
        self._native.options = []
        self._native.value = None
        self._native.update()

    def set_selection(self, item: str) -> None:
        item = normalize_text(item)
        if item in self._native.options:
            self._suppress_change = True
            try:
                self._native.set_value(item)
            finally:
                self._suppress_change = False

    def get_text(self) -> str:
        return normalize_text(self._native.value)

    def on_change(self, callback: Callable[[], None]) -> None:
        self._callbacks.append(callback)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        _set_enabled(self._native, self._enabled)

    def is_enabled(self) -> bool:
        return self._enabled

    def _apply_theme(self) -> None:
        self._native.style(
            f"color: {T['fg']}; background: {T['bg_input']}; "
            f"border-radius: {T['border_radius']}px"
        )


class WebComboBoxAdapter(_WebSelectAdapter, IComboBox):
    def __init__(self):
        super().__init__(editable=True)


class WebDropdownAdapter(_WebSelectAdapter, IDropdown):
    def __init__(self):
        super().__init__(editable=False)

    def set_value(self, values: list) -> None:
        self.clear()
        for value in values:
            self.add_item(value)


class WebVBoxAdapter(_WebAdapter, IVBoxLayout):
    def __init__(self):
        super().__init__(ui.column().classes("uniui-vbox w-full items-stretch"))
        self._apply_theme()

    def add_item(self, widget: IWidget) -> None:
        widget.get_native().move(self._native)

    def add_stretch(self) -> None:
        ui.element("div").classes("grow").move(self._native)

    def set_alignment_top(self) -> None:
        self._native.classes(add="justify-start")

    def _apply_theme(self) -> None:
        self._native.style(f"color: {T['fg']}")


class WebHBoxAdapter(_WebAdapter, IHBoxLayout):
    def __init__(self):
        super().__init__(ui.row().classes("uniui-hbox w-full items-center"))
        self._apply_theme()

    def add_item(self, widget: IWidget) -> None:
        widget.get_native().move(self._native)

    def add_stretch(self) -> None:
        ui.element("div").classes("grow").move(self._native)

    def set_alignment_top(self) -> None:
        self._native.classes(add="items-start")

    def _apply_theme(self) -> None:
        self._native.style(f"color: {T['fg']}")


class WebGroupBoxAdapter(_WebAdapter, IGroupBox):
    def __init__(self):
        card = ui.card().classes("uniui-group")
        with card:
            self._title = ui.label("").classes("uniui-group-title")
            self._content = ui.column().classes("w-full items-stretch")
        super().__init__(card)
        self._apply_theme()

    def set_title(self, title: str) -> None:
        self._title.set_text(normalize_text(title))

    def set_layout(self, layout) -> None:
        native = layout.get_native() if hasattr(layout, "get_native") else layout
        for child in list(self._content.default_slot.children):
            child.delete()
        native.move(self._content)

    def _apply_theme(self) -> None:
        self._native.style(
            f"color: {T['fg']}; background: {T['bg_input']}; "
            f"border: 1px solid {T['border']}; border-radius: {T['border_radius']}px"
        )
        self._title.style(f"color: {T.get('fg_muted', T['fg'])}")


class WebTabWidgetAdapter(_WebAdapter, ITabWidget):
    def __init__(self):
        root = ui.column().classes("w-full items-stretch")
        with root:
            self._tabs = ui.tabs().classes("w-full")
            self._panels = ui.tab_panels(self._tabs).classes("w-full")
        self._tab_items = []
        self._panel_items = []
        super().__init__(root)
        self._apply_theme()

    def add_tab(self, widget: IWidget, name: str) -> None:
        with self._tabs:
            tab = ui.tab(normalize_text(name))
        with self._panels:
            panel = ui.tab_panel(tab)
        widget.get_native().move(panel)
        self._tab_items.append(tab)
        self._panel_items.append(panel)
        if len(self._tab_items) == 1:
            self._tabs.set_value(tab)
            self._panels.set_value(tab)

    def remove_tabs(self) -> None:
        for panel in self._panel_items:
            panel.delete()
        for tab in self._tab_items:
            tab.delete()
        self._tab_items.clear()
        self._panel_items.clear()

    def get_current_index(self) -> int:
        if not self._tab_items:
            return 0
        current = self._tabs.value
        try:
            return self._tab_items.index(current)
        except ValueError:
            return 0

    def _apply_theme(self) -> None:
        self._native.style(f"color: {T['fg']}; background: {T['bg']}")


class WebImageAdapter(_WebAdapter, IImage):
    def __init__(self):
        super().__init__(ui.image(""))

    def set_image(self, path: str) -> None:
        self._native.set_source(Path(path))

    def set_image_from_url(self, url: str) -> None:
        self._native.set_source(url)


class NiceGUIWidgetFactory(IWidgetFactory):
    """Create UniUI adapters backed by NiceGUI elements."""

    def __init__(self):
        set_backend_active(True)

    def createLabel(self) -> ILabel:
        return WebLabelAdapter()

    def createButton(self) -> IButton:
        return WebButtonAdapter()

    def createLineEdit(self) -> ILineEdit:
        return WebLineEditAdapter()

    def createTextArea(self) -> ITextArea:
        return WebTextAreaAdapter()

    def createComboBox(self) -> IComboBox:
        return WebComboBoxAdapter()

    def createDropdown(self) -> IDropdown:
        return WebDropdownAdapter()

    def createVBox(self) -> IVBoxLayout:
        return WebVBoxAdapter()

    def createHBox(self) -> IHBoxLayout:
        return WebHBoxAdapter()

    def createTabWidget(self) -> ITabWidget:
        return WebTabWidgetAdapter()

    def createGroupBox(self) -> IGroupBox:
        return WebGroupBoxAdapter()

    def createImage(self) -> IImage:
        return WebImageAdapter()


def refresh_theme_web(root_widget=None) -> None:
    """Refresh all live NiceGUI-backed UniUI elements."""
    global _dark_mode
    ui.colors(primary=T["accent"])
    if _dark_mode is None:
        _dark_mode = ui.dark_mode(is_dark())
    elif is_dark():
        _dark_mode.enable()
    else:
        _dark_mode.disable()

    for adapter in list(_adapters):
        try:
            adapter._apply_theme()
        except Exception:
            continue

    if root_widget is not None:
        root_widget.classes(add="uniui-root")
        root_widget.style(
            f"background: {T['bg']}; color: {T['fg']}; "
            f"padding: {T['padding']}px; gap: {T['spacing']}px; "
            f"--uniui-spacing: {T['spacing']}px; --uniui-radius: {T['border_radius']}px"
        )


def schedule_after_web(ms: int, callback: Callable[[], None]) -> bool:
    """Schedule a callback on the NiceGUI event loop when Web is active."""
    if not _backend_active:
        return False

    from nicegui import app, core

    delay = max(0, ms) / 1000

    def schedule() -> None:
        if core.loop is not None:
            core.loop.call_later(delay, callback)

    if app.is_started and core.loop is not None:
        core.loop.call_soon_threadsafe(schedule)
    else:
        app.on_startup(schedule)
    return True
