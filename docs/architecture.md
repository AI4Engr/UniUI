# Architecture

## How a widget gets created

```
create_factory("qt")            # backends/registry.py - picks QtWidgetFactory
  -> factory.createLabel()      # backends/qt/primitives/factory.py
     -> QtLabelAdapter          # backends/qt/primitives/text.py
                                #   implements ILabel from contracts/widgets.py
```

Or via the `UniUI` facade:

```
ui = UniUI("qt")                # facade.py - wraps _create_factory
  -> ui.label()                 #           - calls factory.create_label()
     -> QtLabelAdapter
```

## Module layout

```
uniui/
  __init__.py         public re-export surface; defines almost nothing itself
  facade.py           Label()/Button()/VBox()/... and the legacy UniUI class
  core.py             compat surface: re-exports everything from contracts/
  contracts/
    exceptions.py     UniUIException and friends
    layout.py         SizeSpec, LayoutSpec, LayoutItem, Breakpoints
    widgets.py        IWidget, ILabel, ... and IWidgetFactory
  components.py       Admin component interfaces (ICard, ITable, ...)
  models/             backend-independent view models (status, table, chart, ...)
  theme.py            palettes + the single is_dark() flag
  qt.py web.py jupyter.py tk.py wx.py
                      compat shims; each re-exports its backends/<name>/primitives
  backends/
    registry.py       backend detection and factory selection
    <name>/
      primitives/     the controls every app gets (label, button, layouts, ...)
      components/     the Admin layer (Card, Table, AppShell, ...) - qt/jupyter/web only
      styles.py       that backend's stylesheet generation
      runtime.py      shared per-backend helpers
  browser_css.py      CSS rule builders shared by the jupyter and web sheets
```

## Dependency direction

```
        __init__.py  (public API)
             |
     +-------+--------+----------------+
     |                |                |
 facade.py    backends/registry.py   display.py
     |                |
     +-------+--------+
             |
          core.py  ->  contracts/{exceptions,layout,widgets}.py
             ^
             |  (every backend does `from ...core import *`)
             |
  backends/<name>/primitives/  ->  theme.py, strategies.py
             ^
             |
  backends/<name>/components/  ->  models/, backends/components.py
```

`contracts/` depends on nothing else in the package. `widgets.py` imports
`layout.py` and `exceptions.py`, never the reverse.

**Only one module-level import cycle exists**, and it is the ordinary
package/submodule kind: `backends/web/primitives/__init__.py` imports
`.theming`, which does `from . import state`. Everything else that *looks*
circular in a naive scan (`registry` -> `qt_components` -> ... -> `uniui`) is
broken by a deliberately deferred, function-level import. Two of those are
load-bearing and documented at their call sites:

- `backends/tk/primitives/layouts.py` and `text.py` need each other for
  `isinstance` checks, resolved by a `_group_box()` helper that imports on call.
- `routing.py` calls `_get_factory()` per navigation rather than binding a
  factory at import time.

## Two kinds of mutable state

These are the two things most likely to break when moving code between modules.

**`THEME` is a dict mutated in place.** `set_theme()` calls `THEME.update(...)`,
so every module that did `T = THEME` sees the change with no re-import. Copying
the dict anywhere would silently freeze that module on one palette.
`theme._is_dark` is the single source of truth; the web backend's `_dark_mode`
is *not* a duplicate flag but the NiceGUI `ui.dark_mode()` handle, driven from
`is_dark()`.

**Rebound module variables are not re-exportable.** `backends/registry._factory`
and `backends/web/primitives/state.{_css_installed,_dark_mode,_backend_active}`
are rebound via `global`. A re-export (`from .registry import _factory`) copies
the value at import time and never updates, so `use()` would appear to do
nothing. Import the *module* and assign through it (`state._dark_mode = ...`),
and note that a bare `global` in the consuming module creates a second,
unrelated variable instead.

## Key design decisions

**Adapter pattern**: each backend has two layers — a native widget (`QtLabel`)
and an adapter (`QtLabelAdapter`) implementing the shared interface. App code
only ever sees adapters.

**primitives vs components**: `primitives/` holds the controls every app needs;
`components/` holds the Admin layer. The `_Base<Name>WidgetFactory` class is the
split point, so a plain app never imports the Admin layer. Tk and wx are legacy
and have no Admin layer, hence no `_Base` split.

**Three separate theme spines**, because the backends deliver CSS differently:
Qt mutates a live palette dict, Jupyter re-emits its whole stylesheet, and Web
rewrites CSS custom properties on the shell element. Rule *generation* is shared
(`browser_css.py`, `backends/jupyter/styles.py`); stylesheet *emission* is not.

**Jupyter theming**: ipywidgets has limited inline style support, so dark mode
is hybrid — CSS injection via `widgets.HTML` for backgrounds, inline
`widget.style.*` for text and button colours, plus a recursive tree walk
(`_refresh_widget_tree`).

**Web backend**: maps the same adapters onto NiceGUI elements. The public
selector is `web`, so NiceGUI stays replaceable. Children are created eagerly
and moved into containers when layouts are assembled.

## Two API styles

Both produce the same adapter objects.

```python
factory = create_factory("auto")   # factory style
label = factory.createLabel()

ui = UniUI()                       # facade style
label = ui.label()
```

Every `createFooBar()` has a `create_foo_bar()` alias. These are generated once
from the `_SNAKE_ALIASES` table in `contracts/widgets.py` rather than written
out by hand. The table is explicit because two pairs are irregular:
`createVBox` maps to `create_vbox`, **not** `create_v_box`.

## Event handling

`connect()` for actions, `on_change()` for value changes:

```python
button.connect(handle_calculate)      # button clicked
dropdown.on_change(update_labels)     # selection changed
line_edit.on_change(validate_input)   # every keystroke
line_edit.on_finish_edit(submit)      # Enter / focus lost
```

```
App code:  button.connect(my_callback)
              |
           Adapter:  self._native.connect(my_callback)
              |
           Native widget:
              Qt:      clicked.connect(my_callback)
              Web:     on("click", lambda event: my_callback())
              Jupyter: on_click(lambda btn: my_callback())
```

The callback signature is always `() -> None` — no event object reaches app code.
