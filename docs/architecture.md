# Architecture

## How a widget gets created

```
create_factory("tk")          # selector.py  - picks TkWidgetFactory
  -> factory.createLabel()    # tk.py        - creates TkLabel + TkLabelAdapter
     -> TkLabelAdapter        # implements ILabel interface from core.py
```

Or via the UniUI facade:

```
ui = UniUI("tk")              # __init__.py  - wraps create_factory
  -> ui.label()               #              - calls create_widget(LABEL, factory)
     -> registry lookup       # registry.py  - maps LABEL -> factory.createLabel
        -> TkLabelAdapter
```

## Module dependency graph

```
                  __init__.py (public API, UniUI facade)
                       |
         +-------------+-------------+
         |             |             |
    selector.py   registry.py   display.py
         |             |             |
         +------+------+      theme.py
                |
            core.py  (interfaces, exceptions)
                |
    +-----------+-----------+-----------+
    |           |           |           |
  qt.py      wx.py       tk.py    jupyter.py
```

Each platform module only depends on `core.py` (for interfaces) and `theme.py` (for colors).

## Key design decisions

**Adapter pattern**: Each platform has two layers:
- Native widget (`TkLabel`, `QtLabel`, ...) - platform-specific API
- Adapter (`TkLabelAdapter`, `QtLabelAdapter`, ...) - unified ILabel interface

App code only sees adapters. This allows camelCase backward compatibility aliases on adapters without polluting the interface.

**Theme as mutable dict**: `THEME` is a single dict object. `toggle_theme()` calls `THEME.update(THEME_DARK)` in place. All modules hold a reference to the same dict (`T = THEME`), so changes propagate instantly without re-import.

**Virtual containers (Tk only)**: Tkinter requires a parent widget at creation time, but UniUI creates layouts before display. So `TkVBoxLayout`/`TkHBoxLayout` are plain Python objects that defer real widget creation to `build(parent)` at show-time.

**Jupyter theming**: ipywidgets has limited inline style support. Dark mode uses a hybrid approach:
- CSS injection (`<style>` via `widgets.HTML`) for backgrounds, dropdown arrows
- Inline `widget.style.*` for text colors, button colors
- Recursive tree walk (`_refresh_widget_tree`) to update all widgets

## Two API styles

**Factory style** (used in `quick_start.py`):
```python
factory = create_factory("auto")
label = factory.createLabel()
label.set_text("Hello")
```

**Facade style** (used in tests):
```python
ui = UniUI()
label = ui.label()
label.set_text("Hello")
```

Both produce the same adapter objects. Factory style is more explicit, facade style is more concise.

## Event handling

Widgets use `connect()` for action events (button click) and `on_change()` for value change events (dropdown selection, text input):

```python
# Button click
button = factory.createButton()
button.connect(handle_calculate)      # called when button is clicked

# Dropdown change
dropdown = factory.createDropdown()
dropdown.on_change(update_labels)     # called when selection changes

# Text input change
line_edit = factory.createLineEdit()
line_edit.on_change(validate_input)   # called on every keystroke
line_edit.on_finish_edit(submit)      # called when user presses Enter / leaves field
```

How it works across platforms:

```
App code:  button.connect(my_callback)
              |
           Adapter:  self._native.connect(my_callback)
              |
           Native widget (platform-specific):
              Qt:      clicked.connect(my_callback)
              Tk:      command=my_callback
              wx:      Bind(wx.EVT_BUTTON, lambda e: my_callback())
              Jupyter: on_click(lambda btn: my_callback())
```

Each platform translates the unified `connect(callback)` / `on_change(callback)` into its native event system. The callback signature is always `() -> None` — no event object is passed to app code.
