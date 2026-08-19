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
  display.py          framework-detecting dispatcher; owns no backend code
  qt.py web.py jupyter.py
  qt_components.py web_components.py jupyter_components.py
  qt_style.py qt_icons.py qt_effects.py jupyter_style.py
                      compat shims; pure re-exports, nothing is defined in them
  backends/
    registry.py       backend detection and factory selection
    <name>/
      primitives/     the controls every app gets (label, button, layouts, ...)
        styles.py     the themed sheet for those plain controls
      components/     the Admin layer (Card, Table, AppShell, ...)
      factory.py      the canonical factory: primitives + components
      display.py      that backend's show / theme-refresh / scheduling
      styles.py       shared base rules + composition of component fragments
      demo_styles.py  .uniui-demo-* rules for examples/ (jupyter, web)
      icons.py        SVG icon rendering (qt)
      effects.py      optional motion helpers (qt)
      runtime.py      shared per-backend helpers
  browser_css.py      CSS rule builders shared by the jupyter and web sheets
```

There are three backends: `qt`, `jupyter` and `web`. The legacy `tk` and `wx`
backends were removed; `create_factory("tk")` now raises `ValueError` like any
other unknown framework name.

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
broken by a deliberately deferred, function-level import. Three of those are
load-bearing and documented at their call sites:

- `routing.py` calls `_get_factory()` per navigation rather than binding a
  factory at import time.
- `backends/<name>/styles.py` imports each component's `*_css()` fragment
  *inside* the composing function, because the component modules import back
  from `styles.py`.
- `display.py` imports `backends/<name>/display.py` inside each dispatch
  branch, so `import uniui` never pulls in PySide2, ipywidgets or NiceGUI.

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
split point, so a plain app never imports the Admin layer.
`backends/<name>/factory.py` combines the two into the public factory the
registry actually returns.

**The canonical import chain never touches a compat shim.** It runs
`registry -> backends/<name>/factory.py -> primitives + components`. The root
`qt.py` / `web.py` / `jupyter.py` / `*_components.py` modules exist only for
external callers that still import the old names; nothing inside the package
imports them, so the package never depends on its own back-compat surface.
`tests/test_widget_factory_composition.py` enforces this by breaking every
shim and asserting `create_factory("qt")` still works. The same holds for the
implementation modules that used to sit at the root: `qt_style.py`,
`qt_icons.py`, `qt_effects.py` and `jupyter_style.py` are re-export files now,
and the code lives under `backends/`.

**Component CSS lives beside its component.** Each Jupyter/Web component module
exports a `*_css()` fragment; `styles.py` keeps only what no single component
owns (CSS variables, base control rules, shared icon helpers) and concatenates
the fragments. Rules that style `examples/` markup rather than a widget live in
`demo_styles.py`. Fragment order is the original rule order and must stay that
way — CSS resolves ties by source order. Qt keeps its component QSS local
already and is deliberately not centralised.

**`display.py` is a dispatcher, not an implementation.** It detects the
framework and delegates to `backends/<name>/display.py`. The per-backend
`refresh_theme_*` forwarders are looked up as module globals so they stay
monkeypatchable. `schedule_after()` keeps its Jupyter leg inlined on purpose —
it is a toolkit-free `asyncio` check, and delegating it would drag ipywidgets
into every Qt and fallback schedule.

**Three separate theme spines**, because the backends deliver CSS differently:
Qt mutates a live palette dict, Jupyter re-emits its whole stylesheet, and Web
rewrites CSS custom properties on the shell element. Rule *generation* is shared
(`browser_css.py`, `backends/jupyter/styles.py`); stylesheet *emission* is not.

**Themes are named, not just light/dark.** `theme_registry.py` holds any
number of registered palettes (`register_theme(name, palette_or_json_path,
dark=...)`); `theme.py` seeds it with the two built-in `"light"`/`"dark"`
entries and adds `set_active_theme(name)` alongside the unchanged
`set_theme(bool)`. This generalizes palette *count* only — it does not
change how any backend delivers CSS. Each theme still flows through the
same one `THEME` dict, mutated in place, that the three spines above
already read from; a fourth registered theme needs no backend code changes,
only a per-theme `dark` flag (Web's `ui.dark_mode()` is inherently
boolean, so any theme still has to say which side of that split it's on).

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
Re-read the new value yourself via `get_text()` / `get_value()` inside the
callback; the native event's payload (Qt's `textChanged(str)`, ipywidgets'
`change` dict, NiceGUI's `ValueChangeEventArguments`) is deliberately
discarded at the adapter boundary rather than forwarded.

A second family of callbacks is deliberately **payload-carrying** instead —
they tell you *what* happened, not just *that* something changed, because
there's no single native widget to re-query for the answer:

```python
sidebar.on_select(lambda key: router.push_named(key))     # selected item's key
breadcrumb.on_click(lambda path: router.push(path))        # clicked crumb's path
table.on_row_click(lambda row: open_detail(row))            # the clicked row dict
grid.on_resize(lambda mode: layout.set_mode(mode))           # "compact"|"medium"|"wide"
router.on_navigate(lambda ctx: breadcrumb.set_items(...))    # the RouteContext
state.subscribe(lambda value: label.set_text(str(value)))    # the new value
```

Both conventions are consistent across Qt, Jupyter, and Web — pick the shape
based on which family the method belongs to, not the backend.

**Exception safety**: every dispatch site (native-signal wrappers and
hand-rolled multi-subscriber loops alike) routes through
`uniui.state.safe_call()`, which invokes the callback, and on an exception
logs it (via the standard `logging` module, logger name `"uniui.events"`,
message includes the backend, component type, and method name, full
traceback) instead of letting it propagate. A callback that raises does not
stop sibling subscribers in the same dispatch from running, and does not
propagate into unrelated caller code such as `state.set()` or
`router.push()`.
