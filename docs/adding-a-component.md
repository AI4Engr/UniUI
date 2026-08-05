# Where a new component and its styles belong

A decision guide for adding UI to UniUI. Read `architecture.md` first for the
dependency graph.

## 1. Is it a primitive or an Admin component?

| | **primitive** | **component** |
|---|---|---|
| Examples | label, button, line edit, VBox, tabs | Card, Table, Sidebar, AppShell, Gauge |
| Lives in | `backends/<name>/primitives/` | `backends/<name>/components/` |
| Interface goes in | `contracts/widgets.py` | `components.py` |
| Factory method on | `IWidgetFactory` (abstract) | `IWidgetFactory` (raises `NotSupportedError` by default) |
| Backends that must implement it | all five | qt, jupyter, web only |

The dividing line is the `_Base<Name>WidgetFactory` class. Everything a plain
app needs is reachable from the base factory; the Admin layer is added by the
subclass. Keep it that way — an app that never touches Admin must not pay to
import it.

**Tk and wx are legacy and unsupported.** They have no Admin layer and no
`_Base` split. Do not add components to them. New *primitives* need a tk/wx
implementation only if they are abstract on `IWidgetFactory`; prefer adding
them as optional methods that raise `NotSupportedError`.

## 2. Add the interface

A primitive, in `contracts/widgets.py`:

```python
class IBadge(IWidget):
    @abstractmethod
    def set_text(self, text: str) -> None: ...
```

An Admin component goes in `components.py` instead. Either way, add the factory
method to `IWidgetFactory` in `contracts/widgets.py`:

```python
def createBadge(self) -> "IBadge":
    """Optional; backends that cannot do this inherit the raise."""
    raise NotSupportedError("Badge not supported on this platform")
```

Then add one line to `_SNAKE_ALIASES` in the same file:

```python
"createBadge": "create_badge",
```

Do **not** hand-write a `create_badge` forwarder — the table generates it.
Check the snake_case spelling you actually want: the rule is not mechanical
(`createVBox` is published as `create_vbox`, not `create_v_box`).

Making a method `@abstractmethod` instead of a raising default forces all five
backends to implement it, including the two legacy ones. That is usually the
wrong trade for anything new.

## 3. Put shared logic in `models/`, not in a backend

If a component classifies, formats, or lays out data, that logic belongs in
`models/` where every backend uses the same copy. `models/status.py` exists
because three backends had each grown their own status vocabulary and drifted:
the same cell rendered as a green pill in Qt and a grey one in the browser.

`models/` must stay free of backend imports — no PySide2, no ipywidgets, no
NiceGUI. A backend converts the model's output into native styling.

## 4. Implement per backend

Add `backends/<name>/components/badge.py` (or `primitives/`), then export it
from that package's `__init__.py` and wire it into `factory.py`.

Match the existing module's imports: components reach shared helpers through
`..runtime` and `..styles`, and the interface through `....components`.

## 5. Where the styles go

Style *generation* is shared where the output is genuinely identical; style
*emission* is not, because the three maintained backends deliver CSS by
different routes and on different schedules.

- **Qt** — a stylesheet string per widget, built in `backends/qt/styles.py`
  and applied with `setStyleSheet`. Colours come from the live palette dict.
- **Jupyter** — one `<style>` node re-emitted wholesale on a theme switch.
  Rules are built by `base_control_rules(scope, nested=...)` in
  `backends/jupyter/styles.py`, which serves both the Admin shell scope and the
  per-widget scope.
- **Web** — CSS custom properties rewritten on the shell element.
  `browser_css.py` builds the variable declarations and icon mask rules shared
  by the Jupyter and Web sheets.

If you are writing a CSS string for both Jupyter and Web, put the rule builder
in `browser_css.py` and call it from both. If you are writing one for Qt only,
keep it in the Qt styles module.

Never read a colour from a copied dict. Every module aliases the live theme
(`T = THEME`), which `set_theme()` mutates in place; a copy freezes on one
palette.

## 6. Test it

Contract tests in `tests/contracts/` run against every backend via `--ui`:

```bash
python -m pytest -q --no-cov --ui qt        # then jupyter, web, tk
```

Two habits worth keeping, both of which caught real bugs during the refactor:

- **Assert on parsed structure, not substrings.** A test asserting
  `".uniui-widget .widget-button {" not in css` passed while the selector was
  broken, because the mutated form was a comma-list.
- **Break your own test before trusting it.** A new invariant that passes on
  first run has not been shown to detect anything. Change the code it guards,
  confirm it fails, then change it back.

Backends whose toolkit is not installed still get static coverage:
`tests/test_primitive_split_bindings.py` checks every name a primitives module
uses is actually bound, and `tests/test_wx_backend_split.py` stubs wxPython to
verify the wx surface without the real library.
