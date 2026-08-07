# Evaluating Flet and magicgui against UniUI

**Date:** 2026-08-06
**Question:** Should UniUI adopt Flet as a backend, rebuild on magicgui, or stay
on its current architecture?

**Answer: stay on the current architecture.** Add a Flet backend — no. Rebuild
Qt/Jupyter on magicgui — no. Take magicgui's form widgets as a *reference
implementation* and write them ourselves — yes.

The reason is the same in both cases and worth stating once: **UniUI's premise is
that one piece of business code runs on Qt, Jupyter and Web.** Flet cannot render
in a notebook. magicgui has no Web backend. Adopting either as a foundation
breaks the premise, and the premise is the product.

---

## Part 1 — Flet

### What it is

A Python framework from Appveyor Systems, Apache-2.0, **0.86.5 (1 Aug 2026)**,
Python **>= 3.10**.

Architecturally it is a **dual-runtime system**: a Python process holds state and
business logic, a **Flutter** client renders the UI, and the two talk over a
messaging protocol (JSON over WebSockets). As one 2026 analysis puts it, you are
"effectively building a distributed app, even when it runs on your laptop."

The model is imperative and property-based:

```python
import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("Hello, World!"))

ft.app(target=main)
```

Mutate a property, call `page.update()`. Handlers are constructor kwargs
(`on_click=...`). Styling is **control properties, not stylesheets** — `size=18`,
`padding=20`. Targets: desktop, native iOS/Android, web (server or WASM), with
built-in packaging to executables and app stores.

### Comparison

| | **UniUI** | **Flet** |
|---|---|---|
| Targets | Qt desktop, Jupyter, Web | Desktop, iOS, Android, Web |
| Rendering | native per backend | Flutter everywhere |
| **Native mobile** | ✗ | ✓ |
| **Jupyter inline** | ✓ first-class | ✗ |
| **Native desktop widgets** | ✓ real QWidgets | Flutter-drawn, not native |
| Controls | 26 factory + 10 Admin | 150+ |
| Reactive state / routing | ✓ own `State`/`Computed`/`TaskRunner`/`Router` | ✗ none built in (3rd-party FletX) |
| Packaging | ✗ | ✓ incl. app stores |
| License | MIT | Apache-2.0 |

### Why not a backend

**1. It cannot render in Jupyter.** No `_repr_html_`, no ipywidgets bridge. The
community workaround is a background-thread web server embedded via
`IPython.display.IFrame` at `localhost:8550`. That breaks on hosted Jupyter
(Colab, JupyterHub) without port forwarding, orphans servers on cell re-run, and
leaves the notebook unable to inspect or drive the widgets. It is an iframe to a
foreign process, not a Jupyter backend.

**2. Mobile — the one thing it adds — is unreachable through UniUI.** It requires
`flet build` bundling a CPython interpreter into a Flutter app. UniUI would be a
library inside that bundle with its other backends dead weight. Users wanting
Flet-on-mobile are better served using Flet directly.

**3. The cost duplicates the Web backend.** Our contract surface is **83 abstract
methods across 26 factory methods** plus **10 Admin interfaces**; existing
backends run **1,820 lines (Web) to 3,244 lines (Qt)**. A conforming Flet backend
is comparable — and lands in the slot NiceGUI already occupies.

There is also a **process-model conflict**: `ft.app(target=main)` owns the entry
point and event loop, and controls exist only inside the `main(page)` callback.
UniUI's model is the inverse — `create_factory()` returns a factory usable
anytime, `show_ui()` displays the result.

**4. Pre-1.0 with active breaking changes.** The 0.28.3 → 0.80.0 jump was
explicitly not a drop-in upgrade; 0.86.0 changed the bundled CPython default to
3.14.

---

## Part 2 — magicgui

This is the **closest competitor**, and its architecture is nearly identical to
UniUI's.

### What it is

From the napari team (pyapp-kit), **MIT**, **0.10.2 (10 Apr 2026)**, Python
**>= 3.9**, "Development Status: 4 - Beta".

It declares a set of `WidgetProtocol`s that each backend implements; every
magicgui `Widget` wraps a backend-specific widget. Backends: **Qt (PySide2/6,
PyQt5/6) and Jupyter Widgets (ipywidgets)** — exactly the pairing UniUI claims as
its differentiator. The backend layer is public and documented for backend
authors, and `create_widget()` accepts a `backend` argument.

### Where it is ahead of us

- Battle-tested inside napari, a large real scientific application
- Already on **PySide6/PyQt6** (we are still on PySide2)
- Far richer form widgets: SpinBox, FloatSpinBox, Slider, FloatSlider, LogSlider,
  RangeSlider, CheckBox, RadioButtons, DateEdit, DateTimeEdit, TimeEdit,
  FileEdit, ListEdit, TupleEdit, Password, QuantityEdit — **most of which are on
  our TODO and unbuilt**
- Auto-generates GUIs from Python type annotations (a genuinely distinct feature)

### Where it stops — by design

The docs state the emphasis is on *"rapid development of relatively simple GUIs,
with minimal boilerplate"* and explicitly redirect: *"for highly customized GUIs
with complex layouts, it may be more appropriate to use a lower-level GUI
framework."*

Concretely, the **`ContainerProtocol` is `margins` + `insert(position, widget)` +
`remove`.** That is the whole layout abstraction. There is no flex, no
grow/shrink/basis, no grid span, no breakpoints, no wrap, no splitter, no
overlay.

Also missing: any Web backend, any Admin layer, routing, design tokens/theming,
reactive state.

### Overlap analysis — how much would we actually save?

Mapping our 26 factory methods onto magicgui:

| UniUI | In magicgui? |
|---|---|
| Label, Button, LineEdit, TextArea, ComboBox, Dropdown, Image, Table | ✓ (8) |
| VBox, HBox | △ `Container` only |
| GroupBox, TabWidget | ✗ |
| Grid, Wrap, ScrollView, SplitPane, Overlay | ✗ — protocol can't express them |
| Card, StatCard, MetricList, Sidebar, AppShell, Breadcrumb, Gauge, Chart, Drawer, Table(Admin) | ✗ — explicitly out of scope |

**8 of 26.** The rest is layout (its protocol can't carry) or Admin (it doesn't do).

By line count:

| Layer | Lines | Replaceable? |
|---|---|---|
| Qt primitives | 1,352 | partly — layouts still ours |
| Jupyter primitives | 1,616 | partly — same |
| **Qt components (Admin)** | **1,263** | **no** |
| **Jupyter components (Admin)** | **942** | **no** |
| **Web backend (all)** | **1,820** | **no — magicgui has no Web** |

Optimistically **1,000–1,500 lines saved**, in exchange for:

1. **Asymmetric backends.** Qt/Jupyter on magicgui, Web on its own — breaking the
   `primitives/` + `components/` symmetry that makes cross-backend contract
   testing meaningful. Three-backend consistency is the selling point.
2. **`get_native()` semantics to re-derive.** magicgui has both `.native` and
   `root_native_widget`, which differ when a widget is wrapped (e.g. scroll
   bars). Our Admin components lean on `get_native()` throughout.
3. **Layout saves nothing.** Grid/Wrap/SplitPane/Overlay/breakpoints have no
   counterpart in the protocol, so that work remains — now built *on top of*
   someone else's Container rather than our own.

The saved code is the simplest, least error-prone, already-written, already-tested
part. **The direction is backwards: it replaces what we finished and keeps what we
haven't started.**

### Would upstream reject a PR?

No evidence of that, and it is not the argument. pyapp-kit is open, active, MIT,
and the docs invite backend contributions. The real objections are independent of
upstream's attitude:

- Extending `ContainerProtocol` with flex/grid-span/breakpoints pushes magicgui
  from "form abstraction" toward "application layout" — a direction their docs
  explicitly decline. A friendly "not our scope" is a plausible and legitimate
  answer.
- Even if fully merged, review/release/stabilise cadence is upstream's, and our
  Admin work would block on their schedule.
- Even if merged and fast, the result — "magicgui with flex layout" — largely
  duplicates what `contracts/layout.py` already does today.

---

## Other frameworks in this space

| Project | Qt + Jupyter? | Assessment |
|---|---|---|
| **magicgui** | ✓ | closest competitor — see above |
| **VisPy** | ✓ | visualization canvas only, not general UI |
| **Flexx** | partial | web-engine rendering, not native Qt; maintenance unclear |
| **Panel / Solara / Streamlit** | ✗ | web frameworks; "Qt desktop" only via `QWebEngineView` |
| **PySimpleGUI** | ✗ | multi-backend, but no Jupyter |
| `%gui qt` | ✗ | pop-out windows, not inline |

---

## Where UniUI actually stands

**Honest positioning**, after this review:

> **magicgui = the form layer for Qt + Jupyter.**
> **UniUI = the application layer for Qt + Jupyter + Web.**

Only UniUI combines all three of: three backends (Web included), an
Admin/Dashboard component layer, and application infrastructure (routing, state,
tasks, theming, responsive breakpoints). That slot is genuinely open — but it is
narrower than "nobody else does Qt + Jupyter", which is false. magicgui does, and
does it more maturely.

**Real strengths** (verified):
1. **Jupyter is the moat** — Flet cannot do it at all.
2. **Genuinely native desktop widgets** — real QWidgets, inheriting system theme,
   accessibility, IME, native context menus. Flet draws with Flutter.
3. **Application infrastructure** — the standard critique of Flet is "no built-in
   reactivity, business logic mixes with UI." We have `State`/`Computed`/
   `TaskRunner`/`Router`. magicgui has none of these either.
4. **Responsive is implemented, not just modelled** — all three backends: Web via
   `@media`, Jupyter via `@container`, Qt via `resizeEvent` + `_compact_mode`,
   breakpoints 1020/720.

**Real weaknesses** (not softened):
1. **Maturity gap of an order of magnitude** — 0.6.0, 45 commits, one author,
   versus company-backed 0.86.5 and napari-proven 0.10.2.
2. **26 controls vs 150+** — missing Checkbox, RadioGroup, NumberInput,
   DateInput, Modal, Toast, Pagination.
3. **Three renderers = triple maintenance and consistency risk.**
4. **No packaging, no mobile.**
5. **Contract coverage is weaker than the numbers suggest** — see below.

---

## Decision

**Stay on the current architecture.** Not from sunk cost — because we are already
past the dividing line. Responsive breakpoints are implemented on all three
backends; six layout interfaces exist; `SizeSpec`'s flex model is built. These are
precisely what magicgui declines to do. Retreating onto its abstraction discards
our only real advantage over it, in exchange for form widgets we can write
ourselves.

**On the missing form widgets — write them ourselves, using magicgui as a
reference.** Interop (embedding `magicgui_widget.native` into a UniUI layout) is
viable as an *escape hatch* for users wanting to embed existing napari/magicgui
forms, but it cannot fill our own control set: **magicgui has no Web backend, so
any control sourced that way breaks `--ui web`** — and with it the premise. Widgets
entering `IWidgetFactory` must work on all three backends and consume our design
tokens, so the code must be ours. Reading their Qt and ipywidgets implementations
as reference is fine (MIT).

**Worth borrowing from Flet:** its packaging story (our PyInstaller verification
is unresolved in TODO.md), and its property-based styling as a possible long-term
replacement for three theme spines — our contracts are already styling-agnostic.

### Blocking prerequisite

**`tests/conftest.py` calls `use(framework)` only when `framework == "web"`.** For
`--ui jupyter`, facade constructors (`Label()`, `VBox()`) still return **Qt**
objects because the global factory is never set. The 21 "baseline failures" are
Qt and Jupyter objects mixed in one tree:

```
TraitError: 'children' trait of JupyterTabWidget expected a Widget,
not the QTVBoxLayout
```

This must be fixed before adding controls. Until it is, Jupyter and Web contract
tests are not exercising those backends, and any new widget × 3 backends would be
written blind.

Recommended order: **fix conftest → re-measure real failures → then build
controls.**

---

## Sources

**Flet**
- [Flet homepage](https://flet.dev/) · [flet on PyPI](https://pypi.org/project/flet/)
- [DeepWiki: flet-dev/flet architecture](https://deepwiki.com/flet-dev/flet)
- [Flet in 2026: trade-offs you need to admit upfront](https://startdebugging.net/2026/01/flet-in-2026-flutter-ui-python-logic-and-the-trade-offs-you-need-to-admit-upfront/)
- [PythonGUIs: Getting started with Flet](https://www.pythonguis.com/tutorials/getting-started-flet/)
- [Flet 1.0 Beta](https://flet.dev/blog/flet-1-0-beta/) · [Breaking changes: bundled Python 3.14](https://flet.dev/docs/updates/breaking-changes/v0-86-0/default-bundled-python-3-14/)
- [Publishing a Flet app](https://flet.dev/docs/publish/) · [FletApp control](https://flet.dev/docs/controls/fletapp/)

**magicgui**
- [magicgui docs](https://pyapp-kit.github.io/magicgui/) · [magicgui on PyPI](https://pypi.org/project/magicgui/)
- [widgets.bases — `.native` / `root_native_widget`](https://pyapp-kit.github.io/magicgui/api/widgets/bases/)
- [widgets.protocols — backend author spec](https://pyapp-kit.github.io/magicgui/api/protocols/)
- [napari: creating widgets with magicgui](https://napari.org/dev/howtos/extending/magicgui.html)

**Others**
- [VisPy installation / backends](https://vispy.org/installation.html) · [Flexx docs](https://flexx.readthedocs.io/en/stable/)
- [Panel vs Streamlit comparison](https://panel.holoviz.org/explanation/comparisons/compare_streamlit.html) · [Solara](https://solara.dev/)
