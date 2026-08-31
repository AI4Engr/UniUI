# Design: promote `add_class()` to a real `IWidget` capability

**Status:** ready for review
**Triggered by:** `examples/admin_demo.py` reinvented a demo-local, partial
version of this (`_add_class()`, `_QT_CLASS_PROPERTY`) instead of it being a
library primitive. TODO.md line 46 already flagged this as deferred:

> `add_class()` or unified style attributes — deferred, needs its own design
> (Web has real CSS classes, Qt/Jupyter don't)

This plan resolves that design and removes the demo-local reinvention.

---

## Why this is simpler than the deferred TODO assumed

The TODO's framing ("Web has real CSS classes, Qt/Jupyter don't") suggested
Qt would need some kind of translation/bridging layer. Verified empirically
(not assumed) that it doesn't:

1. **Qt QSS attribute selectors accept hyphenated property names directly.**
   `widget.setProperty("uniui-demo-subtitle", True)` +
   `QLabel[uniui-demo-subtitle="true"] { ... }` works exactly as written — no
   camelCase translation table needed. (The admin_demo code's camelCase
   property names like `pageSubtitle` were an unnecessary self-imposed
   constraint, not a real QSS limitation.)

2. **Multiple simultaneous classes on one Qt widget work with zero
   collision** — each class is just its own independent boolean dynamic
   property; setting `uniui-class-a` and `uniui-class-b` on the same widget
   and matching each with its own QSS attribute selector both apply
   correctly, same as a real multi-class CSS element.

3. **Late-tagging works**: `setProperty(name, True)` after the widget's
   stylesheet is already applied doesn't take effect until
   `style().unpolish(widget); style().polish(widget)` — this is the standard
   Qt idiom for "a dynamic property changed, please re-evaluate my QSS", and
   it works for both adding (`True`) and removing (`False`) a class.

4. **ipywidgets and NiceGUI already have symmetric native APIs** —
   `widget.add_class(name)`/`.remove_class(name)` (ipywidgets,
   confirmed via `_dom_classes`) and `element.classes(add=name)`/
   `.classes(remove=name)` (NiceGUI, confirmed via `_classes`) — both already
   used ad hoc in `admin_demo.py`'s `_add_class()`.

So the fix is genuinely just: **make the existing per-backend mechanisms into
one `IWidget` method**, following the exact same pattern already established
for `show()`/`hide()`/`set_enabled()` (see `resilient-swimming-lantern.md`,
already executed earlier this session): a default no-op on `IWidget`, backed
by a tiny shared mixin per backend.

## What this primitive does NOT solve

Tagging a widget with a class name is now uniform. **Supplying the actual
style rule for that class name is not** — that still requires a real
stylesheet somewhere (Qt QSS string, Web/Jupyter CSS). This plan only makes
the *tagging* consistent; `admin_demo.py` keeps `_admin_stylesheet()` (it's
legitimate demo-specific chrome) and the browser side keeps its existing CSS.

---

## Interface

`src/uniui/contracts/widgets.py`, on `IWidget` (same section as `show()`/
`set_enabled()`):

```python
def add_class(self, name: str) -> None:
    pass

def remove_class(self, name: str) -> None:
    pass
```

Non-abstract, matching every other "common capability" already on `IWidget` —
a backend that hasn't wired one up yet doesn't fail ABC instantiation.

## Backend implementations

### Web (`src/uniui/backends/web/primitives/base.py`)

Add directly to `_WebAdapter` (every Web adapter already inherits it, same as
`set_enabled`/`show`/sizing):

```python
def add_class(self, name: str) -> None:
    self._native.classes(add=name)

def remove_class(self, name: str) -> None:
    self._native.classes(remove=name)
```

### Jupyter (`src/uniui/_adapter_mixins.py`)

New mixin alongside `JupyterVisibilityMixin`/`JupyterEnableMixin`:

```python
class JupyterClassMixin:
    """add_class / remove_class via ipywidgets' own DOM class list."""

    def add_class(self, name: str) -> None:
        self.get_native().add_class(name)

    def remove_class(self, name: str) -> None:
        self.get_native().remove_class(name)
```

Mix into Jupyter adapters that need it (start with the ones `admin_demo.py`
actually uses: Label, VBox, HBox, Button — extend to others opportunistically,
same rollout style as the show/hide/enabled/sizing plan).

### Qt (`src/uniui/_adapter_mixins.py`)

New mixin alongside `VisibilityMixin`/`EnableMixin`:

```python
class ClassMixin:
    """add_class / remove_class via a Qt dynamic property + QSS attribute
    selector ([name="true"]), repolished so an already-applied stylesheet
    picks up the change immediately. Verified empirically: hyphenated
    property names work fine in PySide2's QSS parser, and multiple
    independent boolean properties on one widget compose without collision
    - no translation table or single combined "classes" property needed.
    """

    def add_class(self, name: str) -> None:
        native = self.get_native()
        native.setProperty(name, True)
        native.style().unpolish(native)
        native.style().polish(native)

    def remove_class(self, name: str) -> None:
        native = self.get_native()
        native.setProperty(name, False)
        native.style().unpolish(native)
        native.style().polish(native)
```

**Correction (post-implementation)**: the original version of this plan
extended the `NotSupportedError` exception used for `show`/`hide`/sizing on
`QtVBoxAdapter`/`QtHBoxAdapter`/`QtGridAdapter` to also cover `add_class`/
`remove_class`. That was wrong and was caught during implementation:
`_page_frame`/`_labeled_field` (shared code used by every unified admin_demo
page, on both Qt and browser backends) call `.add_class()` on VBox/HBox
containers, and those classes carry real, load-bearing CSS on Jupyter/Web
(gap spacing, max-width, flex-wrap — confirmed via `backends/jupyter
/demo_styles.py` and `backends/web/demo_styles.py`). `add_class`/
`remove_class` are not the same kind of capability as `show`/`hide`/
`set_enabled`/sizing: Web's and Jupyter's VBox/HBox/Grid wrap a real,
class-taggable element; only Qt's is a true bare `QLayout` with nothing to
tag. The actual, correct behavior: `QtVBoxAdapter`/`QtHBoxAdapter`/
`QtGridAdapter` do **not** override `add_class`/`remove_class` — they fall
through to `IWidget`'s inherited no-op default, exactly matching the old
pre-migration Qt behavior (the demo-local `_add_class()` helper had no Qt
branch for these, so tagging a VBox/HBox was always a silent no-op). The
`NotSupportedError` override on these three adapters is kept for `show`/
`hide`/`set_enabled`/sizing only.

Mix `ClassMixin` into the Qt adapters that need it (Label, Button, Wrap, and
any other `QWidget`-backed primitive/Admin adapter `admin_demo.py` or future
callers tag) — not into `QtVBoxAdapter`/`QtHBoxAdapter`/`QtGridAdapter`,
which get the no-op for free from `IWidget`.

---

## Migration: `examples/admin_demo.py`

Once the primitive exists:

1. Delete `_add_class()`, `_QT_CLASS_PROPERTY`, and the `_set_icon_class()`
   Qt-branch gap it shares (check whether `_set_icon_class` has the same
   Qt-no-op problem — it iterates `ADMIN_ICON_NAMES` calling
   `remove_class`/`classes(remove=...)` with no Qt branch either, same class
   of bug, not yet caught because no test exercises icon switching on Qt).
2. Every call site (`_add_class(widget, "uniui-demo-subtitle")` etc.) becomes
   `widget.add_class("uniui-demo-subtitle")` directly — no helper function
   needed at all once it's a real `IWidget` method.
3. Rewrite `_admin_stylesheet()`'s three page-level rules to select on the
   actual class names instead of the old bridged property names:
   ```
   QLabel[uniui-demo-subtitle="true"] { ... }      /* was pageSubtitle */
   QLabel[uniui-demo-hint="true"] { ... }           /* was tableHint */
   QLabel[uniui-demo-field-label="true"] { ... }    /* was fieldLabel */
   ```
   Note the value changes from `"1"` to `"true"` (Python `True` stringifies
   to `"true"` via `QVariant`, confirmed empirically above) — every rule in
   `_admin_stylesheet()` needs updating consistently, including the still-
   live shell rules (`topBar`, `logoMark`, etc.) if `main()`'s shell code is
   also switched to call `.setProperty(name, True)` instead of
   `.setProperty(name, "1")` for consistency (optional — the shell isn't
   using the new primitive, it can keep its existing direct
   `setProperty(x, "1")` calls unchanged since that's not demo-local glue,
   it's already Qt-native code).
4. Confirm `QWidget[adminPage="1"], QWidget[pageHeading="1"]` stays deleted
   (already dead, unrelated to this migration — VBox/HBox have no paintable
   `QWidget` to select on regardless of the new primitive).

---

## Verification

1. New contract tests: `add_class`/`remove_class` on a sample primitive
   (Label) across all three backends via the existing `factory` fixture
   parametrization — assert no exception, and for Qt specifically assert
   `native.property(name)` reflects the call.
2. Manual Qt QSS round-trip test (same shape as the empirical checks above,
   formalized): tag a real `QtLabelAdapter`, apply a stylesheet matching the
   class, assert the visual property (e.g. font size) actually changed.
3. Confirm `QtVBoxAdapter().add_class("x")` is a true no-op (returns `None`,
   raises nothing), while `QtVBoxAdapter().show()` still raises
   `NotSupportedError` on the same object — proving the capability split
   is implemented correctly and `add_class` isn't accidentally still
   blocked.
4. Re-run `examples/admin_demo.py --ui qt` after migration, visually confirm
   subtitle/hint/field-label styling still renders exactly as it does today
   (this plan should be visually invisible — same output, less code).
5. Full suite must stay green; sabotage-verify the Qt repolish step (drop
   `unpolish`/`polish`, confirm a test catches the resulting stale style).

## Critical files

- `src/uniui/contracts/widgets.py` — `IWidget.add_class`/`remove_class`
- `src/uniui/_adapter_mixins.py` — `ClassMixin`, `JupyterClassMixin`
- `src/uniui/backends/web/primitives/base.py` — `_WebAdapter.add_class`/
  `remove_class`
- `src/uniui/backends/qt/primitives/*.py`,
  `src/uniui/backends/jupyter/primitives/*.py` — mix in the new mixins
- `examples/admin_demo.py` — delete `_add_class`/`_QT_CLASS_PROPERTY`,
  rewrite call sites and `_admin_stylesheet()`'s selectors
- new contract test file, e.g. `tests/contracts/test_widget_classes.py`
