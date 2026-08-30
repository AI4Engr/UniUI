# UniUI TODO: Admin / Dashboard Capabilities

> "Admin-like" is defined here as: using the same UniUI Python API to build usable admin backends and data dashboards across Qt, Jupyter, and Web. The wxPython and Tkinter backends have since been removed entirely.
> Audited 2026-08-22 against the actual codebase (5 parallel research passes) — most checkboxes below predate a great deal of shipped work and were stale. Flipped to `[x]` where confirmed done, left `[ ]` with a short note where partially done, left unchanged where confirmed not started.

## Product Positioning

Position UniUI as a "Python engineering data application framework": the same business code can power data dashboards, instrument control, simulation analysis, and parametric 3D tooling in both Qt desktop and Jupyter.

- [ ] Define a clear target user and typical scenarios around engineering data applications
- [ ] Admin, charts, 2D/3D, and CSG share a unified state, data, and task model
- [ ] Keep the core package lightweight; Chart, 3D, and CSG use optional extras or plugins
- [x] Do not market ipywidgets as a standalone web deployment; if a real web app is needed, design a separate Web backend later — `src/uniui/backends/web/` (NiceGUI) is a fully separate backend from `backends/jupyter/` (ipywidgets)
- [ ] Each release should prioritize delivering complete user workflows, not maximizing widget count

## Overall Goals

- [x] Support a standard admin shell: top bar, sidebar, content area, status bar — `IAppShell` on all 3 backends, `backends/{qt,jupyter,web}/components/app_shell.py`
- [x] Display key metrics, data tables, filter forms, and action buttons — StatCard/Table/filter `LineEdit`+`State` binding all live in `examples/admin_demo.py`
- [x] Display and dynamically update charts — `IChart.set_data()`/`.append_data()`, exercised live in `admin_demo.py`
- [ ] Display and edit basic 2D/3D scenes, with a focus on 3D CSG modeling — not started, see "P1: 2D / 3D Visualization" below
- [ ] The same business code runs in both Qt and Jupyter — partially true: Jupyter and Web share one page implementation in `admin_demo.py` (`_browser_dashboard_page` etc.), but Qt has a wholly separate hand-written implementation (`dashboard_page` etc., direct PySide2) — Qt is not actually sharing code with Jupyter yet
- [x] Consistent dark/light theming with runtime toggle support — `theme_runtime.set_active_theme`, toggle wired in `admin_demo.py`, tested in `tests/test_theme_unification.py`
- [ ] Provide a unified interface, backend contract tests, and complete examples for all new components — strong for Admin/Chart (`tests/contracts/test_admin.py`), vacuous for 2D/3D/CSG since those don't exist yet

## P0: Establish the Common Model First

- [ ] Define the scope and non-goals of the first Admin page
- [ ] Design a universal component lifecycle: create, mount, update, destroy
  - Partial (2026-08-19): fixed one concrete instance rather than designing the full lifecycle — `RouterView`/`IOverlay.remove_layer()` on Jupyter now closes a removed page's entire native widget tree (container + every descendant, including each widget's `Layout`/`Style` sub-widgets, which are themselves separately-registered `Widget` instances). Without this, ipywidgets' global `Widget.widgets` registry holds a permanent strong reference to every widget until `.close()` is called — dropping all Python references (what `remove_layer()` already did) is not enough, so every non-cached-route navigation leaked its entire page's widget tree forever. Confirmed via `ipywidgets.Widget.widgets` registry size staying bounded across repeated navigation (`tests/test_jupyter_components.py::test_jupyter_router_view_closes_removed_pages_widgets`), verified the test fails without the fix. Qt (`deleteLater()`) and Web (`element.delete()`) already disposed correctly — this was Jupyter-only. The general problem (no widget/component anywhere has a `dispose()` method; this fix is buried inside `IOverlay.remove_layer()`, not a reusable pattern) remains open.
- [ ] Add an explicit `App` / `Window` lifecycle supporting run, embed, and multi-window modes
- [ ] Gradually replace the global `_factory` and `_root_widget` to avoid cross-contamination between Notebooks, multiple apps, and tests
  - Shelved (2026-08-17): designed an additive `contextvars.ContextVar`-based `using(framework)` scope (fallback-only, `use()`/`_get_factory()` unchanged) but no real usage today runs two backends in one process, so it was dropped as unnecessary complexity. Revisit if that changes.
- [ ] Clearly distinguish `Widget`, `Layout`, `Window`, and `Application` — stop treating all objects as Widgets
  - Investigated (2026-08-20): this line bundles three separate problems with very different sizes. Zero `isinstance(x, IWidget)` checks exist anywhere in `src/uniui` — the type hierarchy is purely structural/documentation today, never enforced at runtime — so splitting it is lower-risk than it sounds, but the three sub-problems still need to be tackled separately:
    - [x] Consolidate the three duplicate hand-rolled "is this native object a layout, wrap it in a widget" implementations into one shared helper.
      - Done (2026-08-20): `backends/qt/primitives/helpers.py` gained `is_qlayout(native)`/`ensure_qwidget(native)`. Replaced the `has_method(native, "addLayout")` duck-typing at all 11 call sites in `primitives/layouts.py` (some kept their addLayout/addWidget branching via `is_qlayout`, since e.g. `QVBoxLayout.addLayout` is the native-preferred path when available; others that always need a widget — ScrollView, Overlay, SplitPane, Grid, Wrap, TabWidget — collapsed to a one-line `ensure_qwidget(...)` call). `backends/qt/runtime.py`'s `as_widget()` now calls `ensure_qwidget()` for the wrap-if-needed step and layers its Admin-specific transparent-background styling on top only when a wrap actually happened (preserved exactly, verified by direct object-identity checks, not just "doesn't crash": wrapped container's `.layout()` is the original QLayout, stylesheet contains `background: transparent`, unwrapped case returns the original object unchanged). `backends/qt/display.py`'s third inline copy (in `show()`) now also calls `ensure_qwidget()`. `has_method()` itself untouched (still exported, still has other potential external uses) — just no longer used for this one pattern. Verified: full suite clean on all three backends (no change expected/observed on Jupyter/Web, Qt-only file), plus manual smoke tests composing a layout-shaped child into every affected container (ScrollView/Overlay/SplitPane/TabWidget/Grid/Wrap/Card).
    - [x] Formally mark `IVBoxLayout`/`IHBoxLayout`/`IGrid` as layout-only in the type system.
      - Done (2026-08-22): added `ILayoutOnly(IWidget)` (`contracts/widgets.py`) — an empty marker interface, purely additive (no behavior change, no new abstract methods). `IVBoxLayout`/`IHBoxLayout`/`IGrid` now inherit `ILayoutOnly` instead of `IWidget` directly; `IWrap`/`IScrollView`/`ISplitPane`/`IOverlay` untouched (confirmed they don't have this problem on any backend). Re-exported alongside every other interface (`uniui`, `uniui.core`, `uniui.contracts`). Verified `isinstance(x, ILayoutOnly)` is `True`/`True`/`True`/`False` for VBox/HBox/Grid/Wrap on all three backends (the marker is Python-side only, so it's backend-independent by construction — confirmed rather than assumed). New contract tests in `tests/contracts/test_layout.py`.
    - [ ] Introduce an `IWindow` concept — `IDrawer` already implicitly depends on one existing (`QApplication.activeWindow()` on Qt) with no way to express that in the type system, and there's no multi-window support at all (`display._root_widget` is a single global). Large, overlaps with the separate "Add an explicit `App`/`Window` lifecycle" P0 item above (partially started: `show_ui()`'s embedding fix, commit `9ff486e`) — do this as part of that item, not this one, to avoid two competing designs.
    - `IApplication` is not separately investigated — no code today gestures at what it would even mean (Qt has no app-level UniUI object beyond the raw `QApplication`; Web's "application" is really `nicegui.ui.run()`; Jupyter has no app concept at all). Revisit once `IWindow` exists and it's clearer whether Application is a real gap or Window absorbs it.
- [x] Fill in common capabilities for all components:
  - [x] `show()` / `hide()` / `is_visible()`
  - [x] `set_enabled()` / `is_enabled()`
  - [x] `set_fixed_width()` / `set_fixed_height()` / `set_minimum_width()` / `set_minimum_height()`
  - [ ] `add_class()` or unified style attributes — deferred, needs its own design (Web has real CSS classes, Qt/Jupyter don't)
  - Done (2026-08-19): all 17 primitive interfaces (`contracts/widgets.py`) and all 10 Admin interfaces (`components.py`) now provide these via non-abstract defaults on `IWidget`, so every existing interface inherits them for free. Real per-backend behavior: Qt via the existing shared `VisibilityMixin`/`EnableMixin`/`SizeMixin` (`_adapter_mixins.py`, generalized to call `get_native()` instead of hardcoding `self._native` — zero behavior change for existing users, but now also works for Qt Admin components, which store their native widget under other attribute names); Jupyter via a new parallel `JupyterVisibilityMixin`/`JupyterEnableMixin`/`JupyterSizeMixin` set operating on `ipywidgets.Widget.layout`/`.disabled` directly (raw ipywidgets containers don't have the camelCase protocol the Qt-style mixins expect); Web via one addition to `_WebAdapter` (`backends/web/primitives/base.py`), which every Web adapter already inherits (also fixed a wrong assumption along the way: NiceGUI's `enable()`/`disable()` are opt-in per element type, not universal — `_set_enabled()` now guards with `hasattr`). Verified per backend via manual smoke scripts for all 27 interfaces and a new shared `CommonCapabilitiesContractTest` mixin (`tests/contract_framework.py`) applied to all 10 Admin component test classes plus a few primitives.
  - Known exception: Qt's `IVBoxLayout`/`IHBoxLayout`/`IGrid` raise `NotSupportedError` for all of these instead — their native object is a raw `QVBoxLayout`/`QHBoxLayout`/`QGridLayout` (a `QLayout`, not a `QWidget`), which has no show/hide/enabled/size surface at all. This is a concrete instance of the separate, larger "distinguish Widget from Layout" item above. Jupyter and Web don't have this problem (their VBox/HBox/Grid wrap real widgets) and implement these normally.
- [x] Event subscriptions return a disposable handle and auto-unsubscribe on `dispose()`
  - Done (2026-08-18), scoped: every `on_*` registration method (`on_change`, `connect`, `on_select`, `on_click`, `on_row_click`, `on_resize`) across all three backends now returns a `uniui.state.Handle` whose `.dispose()` actually unregisters the callback (native Qt signal `.disconnect()`, ipywidgets `.unobserve()`/`Button.on_click(remove=True)`, or list/attribute removal) — verified per backend by subscribing twice, disposing one, and confirming only the surviving callback still fires. "Auto-unsubscribe on `dispose()`" for the *component itself* is deferred — no widget/component has a `dispose()` method today, and adding one to every component belongs to the separate, not-yet-designed "universal component lifecycle" item above; callers hold and dispose the `Handle` themselves for now, same as `State.subscribe()`/`Router.on_navigate()`.
  - Known gap, not fixed here: `LineEdit.on_finish_edit` (Web-only) has no abstract contract declaration and doesn't exist on Qt/Jupyter.
- [x] Unify event signatures; clarify callback parameters and exception handling
- [x] Forbid backends from silently swallowing exceptions; errors must include backend, component type, and the original exception
  - Done (2026-08-18), both items together — same fix. The zero-arg (`on_change`/`connect`) vs. payload-carrying (`on_select`/`on_click`/`on_row_click`/`on_resize`/`Router.on_navigate`/`State.subscribe`) split was already consistent across all three backends; it just wasn't written down, so it's now documented in `docs/architecture.md`'s "Event handling" section rather than changed. The real bug was exception handling: no dispatch site anywhere caught exceptions, so one bad subscriber could abort sibling subscribers in hand-rolled loops (`State.set`, `Router._notify`, `Grid.on_resize`, Web's callback lists) or get silently swallowed by PySide2/ipywidgets with zero UniUI-level context. Every dispatch site now routes through `uniui.state.safe_call()` — logs backend/component/method + full traceback via `logging.getLogger("uniui.events")`, does not propagate, sibling subscribers still run. Verified per backend with a raising-callback-plus-good-callback smoke test, plus new `caplog`-based tests in `tests/test_state.py`/`tests/test_routing.py`/contract tests.
  - Known gap, not fixed here: `IGrid.on_resize` is effectively Qt-only — `JupyterGridAdapter`/`WebGridAdapter` inherit the contract's no-op default and never fire a real breakpoint callback, despite `IGrid` declaring it as shared.
  - Known gap, not fixed here: `on_select`/`on_click`/`on_row_click` are single-slot ("last registration wins") on all three backends, while Web's `on_change`/`connect` are list-based (multi-subscriber) — asymmetry already flagged during the Handle-return pass, deliberately left alone to avoid an unscoped behavior change.
- [ ] Unify data update principle: update existing native controls, avoid rebuilding the entire UI tree on each refresh
  - Investigated (2026-08-22): confirmed real only on Qt and Jupyter; Web already delegates diffing to NiceGUI/Quasar (`self._table.rows = self._model.rows` — the good example already). No stable row identity exists anywhere in `TableModel`/`Column`/`ITable` (rows are plain dicts, click resolution is positional via `TableModel.row_at(index)`), so true identity-based diffing isn't possible without a model change — only positional diffing is. Today's shipped examples use 4-5 rows and call `set_rows` rarely (on search/filter, never polled), so this was a correctness/architecture concern, not a demonstrated performance problem.
  - [x] Qt: done (2026-08-22) — `QtTableAdapter.set_rows()` now diffs positionally: an existing row/cell keeps its `QTableWidgetItem` object, only `.setText()` when the value actually changed (verified via object-identity assertions, not just "doesn't crash" — `tests/test_models_table.py::test_qt_set_rows_reuses_unchanged_cell_items`, confirmed it fails without the fix); only rows beyond the previous count get a freshly-constructed item; `setRowCount` shrinking still relies on Qt's own cleanup for removed trailing rows. Reuses the exact "restyle an existing item" pattern `apply_theme()` already had.
  - [ ] Jupyter: deferred, not attempted — the current architecture renders the *entire* table as one opaque HTML string assigned to a single `ipywidgets.HTML` widget's `.value`; there's no per-cell DOM handle to patch without replacing that architecture (e.g. a grid of individual widgets, or a custom JS-side template), which is a much larger rewrite than the Qt fix and was out of scope for this pass.
- [ ] Use `Protocol`, generics, and dataclasses to improve type-checking of the public API
- [x] Write ADR: decide on the chart implementation approach and optional dependencies
  - Done (2026-08-18): [docs/adr/0001-chart-rendering.md](docs/adr/0001-chart-rendering.md) — documents the shipped decision (hand-rolled QPainter/SVG rendering via `uniui.visuals.render_chart_svg`, no charting dependency), since `Chart` was already fully implemented before this ADR was written.
- [x] Write ADR: decide on reactive state, async tasks, and UI thread scheduling model
  - Done (2026-08-18): [docs/adr/0002-reactive-state-and-scheduling.md](docs/adr/0002-reactive-state-and-scheduling.md) — documents the shipped decision (`State`/`Computed` as plain Python objects, `TaskRunner` as a single daemon thread with results posted back via `schedule_after`, backend-probed UI-thread scheduling with an `asyncio` fallback for Jupyter).

Proposed API draft:

```python
app = App(backend="qt")

with app:
    page = VBox(
        Label("Hello"),
        Button("Refresh"),
    )

app.run(page)
```

### Qt Modernization and Backend Consolidation

- [ ] Migrate the primary Qt backend from PySide2 to PySide6
- [ ] If needed, provide a thin compatibility layer for temporary PySide2 support
- [x] `show_ui()` must not call `sys.exit()` directly; allow embedding in existing Qt applications
  - Done (2026-08-19): the literal `sys.exit()` this line names was already gone (removed in an earlier refactor), but the real bug remained — `backends/qt/display.py`'s `show()` (the path `show_ui()` uses) decided whether to enter the blocking `app.exec_()` loop based on "am I running under pytest," not "did I create this `QApplication`." Embedding a UniUI-built widget into a host app that already owns a `QApplication` would still call `app.exec_()` again, starting a second nested event loop and blocking the host. Fixed by adding the same ownership check (`_app_is_ours = app is None`) that `show_forced()`/`show_qt()` in the same file already used correctly, ANDed with the existing pytest guard. Also `show_ui()`/`UniversalDisplay.show()` now return the native root widget they built (previously `None`), so embedding is actually usable.
  - **Regression found and fixed 2026-08-25**: the `app is None` ownership check above broke every standalone example script. `QtWidgetFactory.__init__` (run by `use("qt")`, which every script calls before building its UI) already creates the `QApplication` as a side effect, so by the time `show_ui()` runs at the end of a script, `QApplication.instance()` is never `None` — `_app_is_ours` was always `False`, `exec_()` never ran, and `python examples/admin_demo.py` (and every other Qt example) built its whole UI, called `show()`, and exited immediately with no error and no visible window. Root cause: "did I create the app *right now*" isn't the right question once *something else in UniUI itself* (the factory) may have already created it earlier in the same run — ownership needs to be tracked at creation time, not re-derived at show()-time. Fixed by stamping `app._uniui_owns_app = True` on the `QApplication` instance wherever UniUI first creates one (the factory or `display.py`, whichever gets there first), and having `show()`/`show_forced()` check that stamp instead of `app is None`. This also required fixing the existing embedding regression test (`tests/test_display.py`), whose "simulate a host app" setup could accidentally reuse a UniUI-stamped `QApplication` left over from an earlier test in the same shared test process — now explicitly forces the stamp off to simulate a genuine host app regardless of process history. Added a new regression test reproducing the exact `admin_demo.py` shape (`create_factory("qt")` first, `show()` after) confirming `exec_()` now fires; verified both the old and new regression tests fail without the fix (reverted each independently, confirmed the specific failure, restored). Manually confirmed `examples/admin_demo.py` and `examples/calculator.py` now block on their event loop instead of exiting after ~1.7s.
- [ ] Support high DPI, system scaling, keyboard navigation, and basic accessibility attributes
  - Partial: high-DPI attrs are set (`AA_EnableHighDpiScaling`/`AA_UseHighDpiPixmaps`, `backends/qt/primitives/factory.py`); `setAccessibleName`/tooltips exist on several Qt Admin components. No dedicated keyboard-navigation logic or system-font-scaling handling found.
- [x] Fix the primary supported backends to Qt, Jupyter, and Web
- [x] Remove wxPython/Tkinter from auto-detection, default tests, and main CI
- [x] Move wxPython/Tkinter to a legacy package, separate branch, or an explicitly frozen compatibility layer *(resolved by deleting both backends outright)*
- [x] Legacy backends must report unsupported uniformly for new components; no further expansion *(no legacy backends remain)*

### Qt Web-Quality Visual Parity Roadmap

> Use the Web Admin implementation as the visual baseline. Qt should reach the
> same level of polish with native rendering, while continuing to share business
> state, routing, data, and task code with Jupyter and Web. The target is visual
> and behavioral parity, not identical backend implementation details.

#### Phase 1: Design System and Shell

- [x] Extract shared Admin design tokens: color, typography, spacing, radius, border, shadow, and semantic status colors
- [x] Add Qt-specific icon and visual-effect modules (now `backends/qt/icons.py` and `backends/qt/effects.py`)
- [x] Use one SVG icon set across Qt, Jupyter, and Web; remove text glyphs and operating-system-dependent icons
- [x] Rebuild the Qt Header, Sidebar, Content, and Footer against the Web visual baseline
- [ ] Match Web navigation states: normal, hover, active, disabled, collapsed, and keyboard focus
  - Partial: hover/active/disabled/collapsed all present in Qt+Web sidebar QSS/CSS; keyboard-focus state missing on both backends.
- [x] Match Web controls: primary/secondary/icon buttons, inputs, status pills, cards, and table chrome
- [x] Keep the Sidebar draggable in wide mode and restore the last user-selected width
- [ ] Support wide Sidebar, medium icon rail, and compact drawer modes without recreating route pages
  - Confirmed still binary, not tri-modal: `app_shell.py`'s responsive sidebar only toggles expanded ↔ icon-rail; no compact drawer/overlay mode exists on any backend.
- [ ] Verify light/dark switching updates existing widgets without losing route, selection, form, chart, or splitter state
  - Architecturally true (every `apply_theme()` only restyles, never touches model/selection state) but unverified by any test that exercises the full combination.

#### Phase 2: Native Dashboard Components

- [x] Add a backend-neutral `Gauge` / `RadialProgress` interface
- [x] Implement Qt Gauge using `QPainter` with antialiasing, semantic colors, units, and animated value transitions
- [x] Add line, area, and bar charts with lightweight `QPainter` / SVG real-time renderers; keep `pyqtgraph` as a future optional high-throughput renderer
- [ ] Keep chart dependencies optional, e.g. `uniui[charts]` — moot per ADR 0001: Chart has zero third-party dependency at all, nothing to gate behind an extra
- [ ] Add chart theme switching, empty/loading/error states, and responsive resize handling
  - Partial: theme switching and an empty-data placeholder both exist (`chart.py`); no `set_loading`/`set_error` on `IChart` at all, unlike `Table`.
- [ ] Replace `QTableWidget` with `QTableView + QAbstractTableModel` for production DataGrid performance
- [ ] Add delegates for status pills, numeric alignment, progress cells, and row action buttons
  - Partial: status-pill delegate (`_StatusPillDelegate`) is real; numeric alignment is done via `setTextAlignment`, not a delegate; progress cells and row action buttons don't exist.
- [ ] Add a themed Calendar component suitable for dashboard and scheduling pages
- [ ] Create an IoT/engineering Dashboard example containing gauges, charts, calendar, table, and live status
  - `admin_demo.py`'s dashboard page already combines Gauge+Chart+StatCards+a metrics list, just without a Calendar and not branded as "IoT."

Proposed API:

```python
Gauge(
    label="Temperature",
    value=88,
    unit="°C",
    status="ok",
)

Chart(
    type="line",
    x=timestamps,
    series=[{"name": "Temperature", "data": values}],
)
```

#### Phase 3: Interaction and Motion

- [ ] Add Sidebar expand/collapse animation without changing route state
- [ ] Add page fade/slide transitions with an option to disable motion
- [ ] Add card hover/focus feedback without expensive full-widget repaints
- [x] Add an animated settings drawer using `QStackedLayout.StackAll` or an equivalent overlay
- [ ] Add smooth Gauge and metric-value transitions
  - Gauge value transitions already ship (`animate_value()`, covered by the already-checked Phase 2 item above); StatCard's `set_value()` still does a plain, un-animated `setText`.
- [ ] Add Toast, Dialog, loading overlay, and Skeleton feedback components
  - Loading overlay exists, but only on `Table` (`_overlay`/`set_loading`/`set_error`); Toast/Dialog/Skeleton don't exist anywhere.
- [ ] Use `QPropertyAnimation`, `QParallelAnimationGroup`, `QGraphicsOpacityEffect`, and `QEasingCurve` through reusable helpers
  - `QPropertyAnimation`+`QEasingCurve` are in real use via `effects.py`'s `animate_value()` and the Drawer's slide animation; `QParallelAnimationGroup`/`QGraphicsOpacityEffect` are unused.
- [ ] Keep ordinary animation and resize interaction at 60 FPS on a typical engineering workstation

#### Phase 4: Responsive, DPI, and Production Quality

- [x] Verify Qt layouts at container widths of 1440, 1180, 900, and 640 logical pixels
- [x] Verify Windows scaling at 100%, 125%, 150%, and 200%
- [x] Ensure responsive reflow does not flicker or recreate gauges, charts, tables, or route pages
- [ ] Debounce chart and viewport resizing by 50–100 ms
- [ ] Ensure real-time charts and data refresh do not block the Qt UI thread
  - `admin_demo.py` routes its one manual "Refresh" button through `TaskRunner` (non-blocking), but no sustained/polling real-time refresh scenario is demonstrated or stress-tested.
- [ ] Support keyboard navigation, visible focus rings, tooltips, and accessible names
  - Partial: accessible names and tooltips are widespread on Qt Admin components; focus rings exist for basic form inputs only; no dedicated keyboard-navigation logic anywhere.
- [x] Add offscreen geometry/state and screenshot render checks for the Qt Admin example
- [ ] Package SVG icons, fonts, and optional chart dependencies correctly for PyInstaller builds

#### Qt Visual Parity Completion Criteria

- [ ] Qt and Web use the same Admin theme tokens and semantic component states
  - Closer to done than it looks: Qt and Web both derive colors from the identical `theme_runtime.get_palette()`/`get_admin_metrics()` source. The one real gap is the missing keyboard-focus state noted above.
- [ ] Qt Dashboard reaches the same hierarchy, spacing, density, and clarity as the Web Dashboard
  - Spacing/metrics are literally shared (`get_admin_metrics()` on both backends); "clarity"/"hierarchy" is a qualitative visual judgment not verifiable from source, left unchecked pending an actual side-by-side look.
- [ ] Theme switching preserves loaded data, route, table selection, chart range, and Sidebar width
  - Same as the Phase 1 item above — architecturally sound, not covered by a test that exercises the full combination.
- [ ] Sidebar drag, responsive collapse, settings drawer, table interaction, and charts work without visible jank
- [ ] The flagship Admin business/page code contains no direct `PySide2` / `PySide6` imports
  - Confirmed false today: `examples/admin_demo.py` imports `PySide2` directly and builds Qt pages with raw `QWidget`/`QGridLayout`/etc.
- [ ] The same flagship app runs with `--ui qt`, `--ui jupyter`, and `--ui web`
  - The CLI flag works for all three today, but per the earlier "same business code" gap, Qt runs a separate hand-written page implementation rather than the one Jupyter/Web already share.

## P0: Adaptive Cross-Backend Layout (Highest Priority)

> Before continuing to develop Admin, chart, and 3D components, the layout common model, Qt adaptive implementation, and Jupyter responsive implementation must be completed first. The goal is behavioral consistency across backends, not pixel-perfect parity.

### Layout Common Model

- [x] Add backend-agnostic `LayoutSpec`, `SizeSpec`, `LayoutItem`, and breakpoint models — `src/uniui/contracts/layout.py`, tested in `tests/test_layout_model.py`
- [x] Add `Row` and `Column`; keep `HBox` / `VBox` as compatibility aliases — `src/uniui/facade.py` (`Row`/`Column` wrap `create_hbox`/`create_vbox`)
- [ ] Add `Grid`, `Wrap`, `ScrollView`, `SplitPane`, `Overlay`, `Center`
  - 5 of 6 exist on all three backends, contract-tested (`tests/contracts/test_layout.py`). `Center` doesn't exist.
- [ ] Add `Container`, `Spacer`, `Divider` — none of the three exist as public widgets
- [ ] Support dynamic `add()`, `insert()`, `remove()`, `replace()`, `clear()`, and reordering
  - Only `add_item()`/`clear()` (and `IOverlay.remove_layer()`) exist; no `insert()`, single-item `remove()`, `replace()`, or reorder anywhere.
- [ ] Child components use stable keys; layout reflows preserve input values, chart state, router pages, and 3D camera state
  - `LayoutItem.key` is modeled but never read by any adapter — dead field. Router-page preservation is real, via a different mechanism (`RouterView._page_cache`). No 3D camera state exists.
- [ ] Layout updates only adjust native layout relationships — do not destroy and recreate business components
  - True only for `AppShell`'s hand-built sidebar-collapse path (resize/re-parent, no rebuild); every container's `clear()` is destructive (`deleteLater()` on every child) and there's no generic non-destructive reflow mechanism.

### Sizing and Flex

- [ ] Unified support for `auto`, `fill`, fixed pixels, and percentage sizes
  - `SizeSpec` models all four (`contracts/layout.py`) but no backend adapter ever reads it — `LayoutItem.grow/shrink/basis` is the actually-wired sizing path instead.
- [ ] Support `min_width`, `max_width`, `min_height`, `max_height`
  - Only the `min_*` pair exists on the base `IWidget` contract; `max_*` exists only on `IScrollView`, not generically.
- [ ] Support `grow`, `shrink`, `basis`, and `aspect_ratio`
  - `grow`/`shrink`/`basis` are fully wired (Qt stretch factor; Jupyter/Web flex CSS). `aspect_ratio` doesn't exist anywhere.
- [ ] Support parent layout `gap`, `padding`, main-axis alignment, cross-axis alignment, and wrapping
  - `gap`/`padding` are applied everywhere `set_spec()` runs. `LayoutSpec.align`/`cross_align`/`wrap` are modeled fields that no `set_spec()` implementation ever reads.
- [ ] Support child `align_self`, Grid row/column/span, and order
  - Grid row/col/span is real and tested. `LayoutItem.align_self` is modeled but unused. There is no `order` field at all.
- [ ] Fixed sizes should only be used for clearly defined cases: icons, toolbars, collapsed Sidebar, etc. — coding guideline, not independently checkable; no counter-evidence found
- [x] Remove the Display layer's recursive enforcement of the same margin/spacing on all nested layouts — confirmed the described problem doesn't exist today: every container (AppShell, Card, ...) already sets its own distinct, purpose-specific margins

Proposed API draft:

```python
page = Column(
    Toolbar(),
    Grid(
        StatCard("Users", 1280, span=3),
        StatCard("Orders", 320, span=3),
        Chart(..., span=8, min_height=320),
        Card(..., span=4),
        columns=12,
        gap=16,
    ),
    grow=1,
    gap=16,
    padding=24,
)
```

### Responsive Rules

- [x] Use container width, not screen width, to determine responsive mode — `_ResizeNotifier`/`_ResponsiveShellWidget` both hook the container's own `resizeEvent()`
- [x] Define default breakpoints: `compact < 720`, `medium < 1200`, `wide >= 1200` — `contracts/layout.py`'s `Breakpoints`/`DEFAULT_BREAKPOINTS`, tested
- [ ] Only reflow structure when crossing a breakpoint; delegate ordinary size changes to the native layout engine
  - Real on Qt (`QtGridAdapter.on_resize` gates on `mode != self._last_mode`), but `on_resize` is Qt-only — Jupyter/Web `Grid` inherit the contract's no-op default and never fire it.
- [ ] Sidebar supports: wide = expanded, medium = icon rail, compact = drawer/Overlay
  - Confirmed binary in practice (expanded ↔ icon-rail only, verified by parametrized width test); no drawer/overlay compact mode exists.
- [ ] Dashboard Grid supports: wide = four columns, medium = two columns, compact = one column — no such breakpoint-driven column count exists; `set_columns()` is a manual, unwired API
- [ ] SplitPane can switch from horizontal to vertical in compact mode — `set_orientation()` exists and is callable, but nothing auto-wires it to a breakpoint
- [x] Responsive rules are overridable by the application; default breakpoints must not be hardcoded into components
  - Fixed 2026-08-22: `AppShell`'s sidebar-collapse threshold on all three backends now reads `DEFAULT_BREAKPOINTS.medium`/`.compact` instead of the literal `1020`/`1019`/`719` it previously hardcoded independently in `backends/{qt,jupyter,web}/components/app_shell.py`. This is a real behavior change, not just a refactor: the collapse point moved from 1020px to 1200px to match the documented default. Updated `tests/test_qt_components_production.py` (1180px now collapses, matching the new threshold) and `tests/test_jupyter_components.py`'s CSS-string assertion; full suite (928 tests) passes. Still not truly "overridable by the application" — `AppShell` reads the module-level `DEFAULT_BREAKPOINTS` singleton directly rather than accepting a `Breakpoints` instance, so an app can't override it per-shell without monkeypatching the shared default.

### Qt Adaptive Renderer

- [ ] Map `fill` / `auto` / fixed sizes to the correct `QSizePolicy`
  - `QSizePolicy` is used, but ad hoc per-component, never systematically driven by `SizeSpec` (which no adapter reads — see Sizing and Flex above).
- [x] Map `grow` to layout stretch factor — `qt/primitives/layouts.py` (`stretch = int(item.grow) ...`)
- [x] Map `Grid` to `QGridLayout`, correctly handling row/column span — tested, `test_add_item_span`
- [ ] Map `SplitPane` to `QSplitter`, supporting drag, minimum size, and ratio persistence
  - Drag works natively; no minimum-size enforcement or ratio persistence implemented for the general-purpose `SplitPane` (AppShell's own internal splitter does set `setChildrenCollapsible(False)`, but `QtSplitPaneAdapter` doesn't).
- [x] Map `ScrollView` to `QScrollArea` with `setWidgetResizable(True)`
- [x] Map `Overlay` to `QStackedLayout.StackAll` or equivalent — `QStackedWidget`
- [x] Implement `Wrap` using a tested FlowLayout — `_QFlowLayout`, explicitly based on Qt's official FlowLayout example, contract-tested
- [x] Responsive containers listen to their own `resizeEvent()`, not screen resolution
- [ ] Debounce chart and 3D Viewport resize events by 50–100 ms
- [ ] Resize only updates the chart renderer, WebGL/OpenGL buffer, and camera aspect ratio — do not re-run data queries or CSG — N/A, no 3D/CSG exists
- [ ] Use logical pixels by default; correctly support Qt high DPI and system font scaling
  - High-DPI attrs are set (`AA_EnableHighDpiScaling`/`AA_UseHighDpiPixmaps`); system font scaling isn't separately confirmed.

### Jupyter Responsive Renderer

- [x] Map `Row` / `Column` to ipywidgets Flex layout
- [x] Map `Grid` to CSS Grid — `widgets.GridBox`/`grid_template_columns`
- [ ] Dashboards should prefer `repeat(auto-fit, minmax(..., 1fr))` for adaptation without Python round-trips
  - Actual implementation is the opposite: a fixed `repeat({columns}, 1fr)` driven by a Python `set_columns()` call — requires a round-trip.
- [x] Map `Wrap` to `flex-flow: row wrap`
- [x] Map `fill` / `grow` / `shrink` / `basis` to corresponding CSS flex properties
- [x] All stretchable content must set `min-width: 0` to prevent charts and 3D canvases from overflowing their containers — applied extensively across Jupyter and Web primitives/components
- [x] Prefer CSS Grid/Flex for responsiveness; do not send every resize back to Python — e.g. `SplitPane`'s drag handle keeps pointer tracking client-side, syncs only on pointer-up
- [ ] For structural changes like Sidebar, prefer container queries; use media queries only as a fallback
  - Jupyter genuinely uses `@container`. Web declares `container-type: inline-size` but its actual Sidebar/AppShell collapse uses a plain `@media` query, not `@container`.
- [ ] Provide a thin `ResizeObserver`-based frontend bridge for Chart/Viewport that requires exact dimensions — N/A, no Viewport exists; Chart has no such bridge
- [ ] Debounce `ResizeObserver` events; only sync to Python when a breakpoint changes or the size has stabilized — moot, no `ResizeObserver` exists
- [ ] Verify core layout behavior in JupyterLab, Classic Notebook, and VS Code Notebook
  - JupyterLab and VS Code Notebook were both debugged and documented (`docs/jupyter-notebook.md`); Classic Notebook isn't confirmed, and there's no automated cross-frontend test matrix.

### Page Layout Spec

- [x] AppShell fills available area; Header, Sidebar, Content, and Footer have clear responsibilities
- [ ] Default page padding 24, card gap 16, form gap 12 — all overridable via theme
  - The override-via-theme mechanism is real (`get_admin_metrics()`), but actual defaults differ: `content_padding=32`, `card_gap=12`, and there's no `form_gap` token at all.
- [ ] Sidebar default width 240, collapsed width 64; Header default height 56
  - Close but not exact: actual values are `sidebar_expanded=236`, `sidebar_collapsed=72`, `header_height=60`.
- [x] Each page has only one primary vertical scroll region — AppShell's content area is a single `QScrollArea`/`overflow:auto` div
- [ ] Sidebar, DataGrid, and Dialog body may have their own independent scroll regions
  - Sidebar/DataGrid are fine; `Drawer` (the closest "Dialog body" analog) has no scroll wrapper around its content at all.
- [ ] 3D Viewport does not participate in page scroll-wheel scrolling; scroll wheel is reserved for camera zoom — N/A, no Viewport exists
- [ ] Parameter panel and Viewport use SplitPane; recommended parameter panel width 280–360 — N/A, no Viewport exists
- [ ] Regular pages may use Container to cap max content width; Dashboard/3D pages may go full width — N/A, no `Container` component exists

### Layout Completion Criteria

- [x] The same code completes Row, Column, Grid, Wrap, ScrollView, and SplitPane examples in both Qt and Jupyter — `tests/contracts/test_layout.py` is backend-agnostic, runs unmodified against `--ui {qt,jupyter,web}`
- [ ] Automatically forms compact, medium, and wide layouts at container widths of 640, 900, and 1440
  - The existing parametrized width test (`tests/test_qt_components_production.py`) proves only a two-state (compact/expanded) system at those widths, not three distinct modes.
- [ ] After a breakpoint switch, form values, routes, chart data, and 3D camera state are preserved
  - Route preservation is real (`RouterView._page_cache`); form-value/chart-data preservation across an actual structural reflow has no test coverage; 3D camera state is N/A.
- [x] No visible flicker, component re-creation, or high-frequency Python communication during continuous window resize — resize-heavy paths (SplitPane drag, breakpoint reflow) are native/CSS-driven, not per-pixel Python round-trips
- [x] Layout API does not require business code to access `QLayout`, `QSizePolicy`, or `widgets.Layout` — `facade.py`'s layout constructors only ever return `IWidget`-family interfaces

## P0: State, Data, and Async Tasks

Admin pages, route parameters, dynamic charts, and parametric CSG need to share a single state mechanism to avoid each component implementing its own refresh logic.

### Reactive State

- [x] Add a lightweight `State[T]` supporting read, write, and subscribe — `src/uniui/state.py`
- [x] Add a read-only `Computed[T]` that recalculates when its dependencies change — explicit dependency list, `Computed(fn, *deps)`, documented in ADR 0002
- [x] Support one-way binding for component properties and two-way binding for form values — `bind_text`/`bind_items`/`bind_enabled`/`bind_visible` (one-way), `bind_value` (two-way, with feedback-loop suppression)
- [x] Support batched updates: one business operation triggers at most one necessary redraw — Done (2026-08-24): `uniui.batch()` context manager (`state.py`) defers `State` notifications until the outermost block exits, coalescing repeated `.set()` calls on the same `State` into its single final value. `.value` still reflects the latest write immediately inside the block — only the subscriber notification is deferred. `Computed` needed no separate code: since it subscribes to its dependencies like any other listener, batching its dependency's notification automatically batches its recompute timing too. Nested batches flatten to one flush; a batch that raises still flushes (values were already written). Known limitation, documented rather than solved: a value set back to what it was before the batch started still fires once at flush time — batching removes redundant *intermediate* notifications, not net-zero ones. 7 new tests; verified by bypassing the batching branch entirely and confirming 4 tests fail before restoring it.
- [ ] Subscriptions return a disposable handle; auto-unsubscribe when the page is destroyed
  - `Handle` is real and used everywhere, but nothing automatically disposes a page's handles when `RouterView` navigates away from it — that wiring doesn't exist.
- [ ] Detect and prevent circular bindings and duplicate subscriptions with clear diagnostics
  - Circular-update half done (2026-08-22): `State`/`Computed` both gained a reentrancy guard (`_updating` flag) — if a subscriber's call chain re-enters `.set()`/`._recompute()` on the same instance before it finished notifying, it now raises a clear `RuntimeError` ("Circular State/Computed update detected...") instead of recursing. Worth noting honestly: Python's own recursion limit already turned a non-converging cycle into a `RecursionError` before this fix, so the real win is failing after ~2 hops with an actionable message instead of after ~1000 hops with a generic one — not preventing an actual infinite hang, which was never possible. A converging ping-pong (both sides settle on the same value) is correctly left alone, since the existing equality-gate already breaks that cycle. 5 new tests in `tests/test_state.py`; verified by disabling each guard and confirming the RecursionError-storm behavior returns before restoring it. "Duplicate subscriptions" detection is still not implemented — deliberately skipped, since deduping identical callables would break the existing contract that each `subscribe()` call gets its own independent `Handle`.
- [x] The state layer is pure Python — no dependency on Qt or ipywidgets — confirmed via ADR 0002 and direct import inspection

Proposed API draft:

```python
status = State("active")
rows = State([])
active_count = Computed(lambda: sum(row["active"] for row in rows.value))

filter_box.bind_value(status)
table.bind_rows(rows)
stat_card.bind_value(active_count)
```

### Data Source

- [ ] Define a unified `DataSource`: `load()`, `refresh()`, `cancel()`
- [ ] Define a pagination request model: page number, page size, sort field, filter conditions
- [ ] Define a pagination result model: data rows, total count, cursor or page info
- [ ] DataGrid, Chart, and StatCard can bind to the same data source or derived state
- [ ] Support in-memory and callback data sources; HTTP/database adapters go in extension packages
- [ ] Support caching, deduplication, retry, and TTL — but keep the default policy simple
- [ ] All errors are normalized to a unified loading state: `idle / loading / success / error`

### Async and Thread Safety

- [x] Add `Task` / `TaskRunner` to wrap long-running functions and coroutines — only `TaskRunner` exists (no separate `Task` class), `state.py`, tested in `tests/test_task_runner.py`
- [ ] Provide unified `run_in_background()` and `run_on_ui_thread()`
  - The capability exists under different names: `TaskRunner.run()` (background) and `schedule_after()` (UI thread) — no functions literally named this.
- [x] Qt uses signal/slot or an event queue to return to the UI thread — a `QObject`-relayed Qt signal, specifically because `QTimer.singleShot` from a non-Qt thread is silently ignored (ADR 0002)
- [x] Jupyter uses the asyncio/IPython event loop to safely update widgets — `asyncio.get_event_loop()`/`loop.call_later` in `schedule_after()`
- [ ] Support progress, cancellation, timeout, error callbacks, and completion callbacks
  - Cancellation, error, completion, and now timeout (2026-08-22) all exist and are tested. `TaskRunner.run(..., timeout=...)` is cooperative — Python can't forcibly kill a thread, so after `timeout` seconds the task is marked cancelled and `on_error` fires with a `TimeoutError`, but `fn` itself only actually stops once it next checks the `cancelled` event it's passed. A lock settles the on_done/on_error race exactly once so a task finishing right as its timeout fires never double-fires. 5 new tests in `tests/test_task_runner.py`; verified by disabling the timeout branch and confirming 2 tests fail before restoring it. Still no `progress` callback support.
- [x] New tasks can cancel old tasks to prevent stale results from overwriting new ones during rapid filtering or CSG parameter changes — `TaskRunner.run()` cancels any in-flight run at the top of every call, tested (`test_new_run_cancels_old`)
- [ ] When a page route is left or a component is destroyed, its tasks are automatically cancelled — no wiring exists between `RouterView` and any `TaskRunner` instance
- [ ] Reserve a process pool execution strategy for CPU-intensive CSG to avoid GIL contention and UI jank — N/A, no CSG exists

## P1: Admin Foundation Components

### Pages and Navigation

- [x] `AppShell`: top bar, sidebar, main content area, status bar
- [x] `Sidebar` / `NavMenu`: icons, grouping, selected state, collapsed state
  - Done (2026-08-25): added `ISidebar.add_group(label)` — a non-clickable section header. `NavItem` gained an `is_group` flag; a group header lives in the same flat `_items` list as regular items (no separate index-mapping layer needed) but is invisible to `index_of`/`set_active`/`is_active`, so it can never become the active item or fire a selection callback even via an accidental blank-key lookup. Qt marks it non-selectable/non-enabled via item flags (verified real, not just visually implied, by checking the flags directly) with a smaller bold muted style; Jupyter renders it as a plain `HTML` header widget; Web as a `ui.label`. All three blank the header text when collapsed (Qt/Jupyter literally blank the text; Web reuses the same `uniui-collapsed` class every button already gets and hides it via CSS) — a section title has nowhere to fit in the icon-only rail. 26 new tests across the model and all three backends; verified by sabotaging both the model-level group exclusion and Qt's non-selectable flag, confirming 3 tests fail, before restoring each.
- [x] `Page` / `Router` / `RouterView`: page registration, matching, navigation, and content area rendering — `src/uniui/routing.py`
- [x] `Breadcrumb`: breadcrumb navigation
- [ ] `Toolbar`: page title, primary actions, secondary actions — doesn't exist as a component
- [ ] `Spacer` / `Divider` / `ScrollArea`
  - `ScrollArea`/`IScrollView` is real. `Spacer`/`Divider` are not public widgets (only exist as `add_stretch()` and a private CSS class inside `MetricList`).
- [x] Respond to window width changes: at minimum support Sidebar expand and collapse — `AppShell`'s live resize callback reshapes the shell/sidebar at a breakpoint

### Router

The first version uses "in-process routing": UniUI maintains the current path and history; business code does not touch native navigation APIs in Qt or Jupyter.

- [x] Add `Router`, `Route`, `RouterView`, and `Link` public interfaces
  - Done (2026-08-24): added `Link(router, label, path=None, name=None, params=None, query=None, factory=None)` in `routing.py`, exported from `uniui`. UniUI has no browser anchor/native-navigation concept to hook a real hyperlink into, so it's a `Button` wired to `push()`/`push_named()` instead — same "compose from existing primitives" shape as `NavMenu.from_router`/`sync_breadcrumb`, not a new low-level widget interface. Requires exactly one of `path=` (a literal path) or `name=` (a registered route name, resolved like `push_named`). 6 new tests parametrized across Qt/Jupyter/Web (clicking actually navigates, on both the literal-path and named-route forms); verified by removing the click handler's navigation call and confirming all 6 backend-parametrized cases fail before restoring it.
- [x] Support static paths: `/dashboard`, `/users`
- [x] Support path parameters: `/users/:id`
- [x] Support query parameters: `/users?page=2&status=active`
- [x] Support named routes to avoid hardcoded paths throughout business code — `Route.name`, `push_named()`
- [x] Support `push()`, `replace()`, `back()`, `forward()` — all four implemented with real history-index bookkeeping
- [x] Support default routes, 404 pages, and redirects
  - Done (2026-08-22): 404 (`not_found`) already existed. Added `Router(default=...)` (resolves `""`/`"/"` to a target path when no route matches root) and `Route(..., redirect=...)` (a route that resolves to another path instead of rendering, interpolating its own matched `:param`s into the target). Both share one `_resolve_path()` hop-bounded resolver (`_MAX_REDIRECT_HOPS = 10`), so a redirect cycle raises `RouteNotFoundError` instead of hanging; query strings carry through unless the target sets its own; the history entry is rewritten to the resolved path so `back()` doesn't land on a dead source route. 13 new tests in `tests/test_routing.py`; verified by temporarily disabling the redirect branch and confirming 10 tests fail before restoring it.
- [x] Sync Sidebar selected state, page title, and Breadcrumb on route changes
  - Sidebar sync (`NavMenu.from_router`) and Breadcrumb sync (`sync_breadcrumb`) already existed. Added `sync_page_title(router, set_title, title_fn=None)` (2026-08-24), same shape as `sync_breadcrumb` — computes the title text and hands it to a caller-supplied setter rather than assuming a specific native "window title" concept, since that's a different thing on each backend (Qt window title, browser tab title, a Jupyter heading). Defaults to the route name, title-cased, or "Not Found" for an unmatched path. 5 new tests (neither `sync_breadcrumb` nor `NavMenu.from_router` had any test coverage before this — `sync_page_title` is now the only one of the three with dedicated tests); verified by sabotaging the default title formatter and confirming 3 tests fail before restoring it.
- [x] Support navigation guards: confirm before leaving unsaved forms, redirect on missing permissions — Done (2026-08-24): `Router.add_guard(fn)` runs every registered guard before a route is entered, in registration order. `fn(ctx)` returns `True`/`None` to allow, `False` to cancel (stays on the current route), or a path string to redirect — matching vue-router's `beforeEach` semantics, including that a redirect restarts the *whole* guard chain against the new target rather than resuming from the next guard, since the new target needs guarding too. Bounded by the same `_MAX_REDIRECT_HOPS` used for `Route.redirect`, so a guard redirect cycle raises `RouteNotFoundError` instead of looping. A guard that raises is logged and treated as an allow — the same fail-open policy every other callback in this codebase already has via `safe_call`, so one broken guard can't make the whole app unnavigable. Required refactoring `_navigate()` to share a `_build_context()` helper with the guard-redirect path (both need to resolve+match a path into a `RouteContext`), and rewriting the history-slot logic once at the end against the final resolved context rather than mid-flight. 10 new tests; verified three separate mechanisms by sabotage (cancel branch, guard-redirect hop cap, and confirming the cap actually terminates a real cycle rather than just running longer) before restoring each.
- [x] Pages are lazily created by default; allow configuring whether page instances are cached — `Route.cache: bool`, `RouterView` only reuses `_page_cache` when set
- [ ] Cancel timers, data subscriptions, and background tasks when a page is left, to avoid resource leaks
  - [x] Widget-tree leak fixed (2026-08-17): `RouterView` no longer accumulates an unbounded `IOverlay` layer per uncached navigation. `IOverlay` gained `remove_layer(index)`/`layer_count()`; `RouterView` tracks the single currently-mounted disposable (non-cached) layer and removes it right before the next layer is added, remapping cached-page indices. Cached pages are never touched. Verified across Qt/Jupyter/Web.
  - [x] Jupyter widget-tree leak fixed (2026-08-19): removed pages' entire native widget tree (container + every descendant, including `Layout`/`Style` sub-widgets) is now explicitly `.close()`'d — see the "universal component lifecycle" note above.
  - Still open: timers/subscriptions/background tasks *inside* a page are not auto-cancelled on navigation away — no wiring exists between `RouterView` and `State`/`TaskRunner` handles a page might hold.
- [x] Route callbacks and page factories receive a unified `RouteContext`

Proposed API draft:

```python
router = Router(
    Route("/dashboard", dashboard_page, name="dashboard"),
    Route("/users", users_page, name="users"),
    Route("/users/:id", user_detail_page, name="user-detail"),
    not_found=not_found_page,
)

app = AppShell(
    sidebar=NavMenu.from_router(router),
    content=RouterView(router),
)

router.push("/users?page=2")
router.push_named("user-detail", params={"id": 42})
```

Backend implementation:

- [x] Qt: `RouterView` uses `QStackedWidget` or equivalent to switch pages — `QtOverlayAdapter` wraps `QStackedWidget`
- [x] Jupyter: update the container's `children`, preserving the same route lifecycle semantics — `JupyterOverlayAdapter`/`ipywidgets.VBox`
- [ ] Jupyter URL/hash sync is an optional enhancement; core routing does not depend on browser capabilities — describes something intentionally not built; the "core doesn't depend on browser capabilities" half is already true (`routing.py` has zero Qt/Jupyter/Web imports)
- [x] Core route matching and history remain pure Python for easy independent testing — `routing.py` imports nothing but `re`/`dataclasses`/`uniui.state`

### Data Display

- [x] `Card`: title, subtitle, content, action area
- [x] `StatCard`: metric value, unit, trend, status color
- [ ] `Badge` / `Tag`: status labels — no standalone widget; the concept only exists baked into `Table`'s status-pill column, not reusable elsewhere
- [ ] `ProgressBar` — doesn't exist
- [ ] `Table` / `DataGrid`:
  - [x] Declare columns and bind row data — `set_columns`/`set_rows`
  - [x] Custom cell formatting — Done (2026-08-24): a column spec can now supply `{"format": callable}`; `Column.text_of()` applies it in place of the plain `str(value)` rendering. Never runs on a missing/blank cell (a formatter written for a real value has no reason to handle `""`), and a raising formatter falls back to the unformatted text rather than breaking the table's render. Qt/Jupyter already called `text_of()` so they picked this up for free; Web needed a fix (`WebTableAdapter._display_rows()`) since Quasar renders straight from row dict field values and never calls `text_of()` at all — formatting would have silently had no effect there otherwise. Known narrow caveat, documented rather than solved: on Web, `on_row_click`'s payload carries the *formatted* string for a formatted column, since the browser's click event reflects whatever's in the rows Quasar was given — Qt/Jupyter always resolve clicks against the raw model instead. Sorting is unaffected either way, since it already reads `value_of()`, not `text_of()`. 8 new tests; verified by disabling the format branch and confirming 4 tests fail across all three backends before restoring it.
  - [x] Sorting — Done (2026-08-22): `TableModel.set_sort()`/`toggle_sort()`/`sorted_rows()` (`models/table.py`) sort display order without touching the underlying row data, so a later `set_rows()` still diffs correctly. Columns opt in via `{"sortable": True}`. Qt clicks the header (`sectionClicked`, native sort-indicator arrow); Jupyter clicks a `<th>` wired through a hidden bridge widget, same pattern as row-click; Web sets `"sortable"` on the Quasar column def for client-side visual sorting plus a Python-observable `set_sort()` API. `ITable.set_sort(key, reverse=False)` is the new backend-agnostic contract method, tested via `tests/contracts/test_admin.py::TestTableContract` on all three backends plus dedicated model/backend tests in `tests/test_models_table.py`. Verified by temporarily breaking `sorted_rows()` and confirming 7 tests fail, then restoring.
  - [ ] Single/multi-select — Partial (2026-08-24): added `ITable.get_selected_row()`, backed by `TableModel.select_row()`/`selected_row` (selection is by value, not index, since rows have no stable identity — a `set_rows()` that no longer contains an equal row clears it automatically). Wired into the same click handler every backend already had for `on_row_click`, so this adds no new click behavior or visual affordance — Qt already visually highlights on click for free via its native `SingleSelection` mode; Jupyter/Web gained no new highlight, only state tracking. Still open: no `on_selection_change` callback (read-only for now), and no multi-select on any backend.
  - [x] Pagination — Done (2026-08-24): `TableModel.set_page_size()`/`set_page()`/`page_count`/`display_rows()` (sorted, then sliced to the current page). Every backend now renders `display_rows()` instead of `sorted_rows()` directly, including `row_at()` for click/selection resolution, so clicks correctly index into the current page rather than the whole dataset. Sorting and pagination compose: sort applies first, then the page slice. Changing the sort or calling `set_rows()` both reset to page 0, since "page 3" from before either change would show an arbitrary, confusing row set. `page_count` is always at least 1 even for zero rows, so a UI can display "Page 1 of 1". This is data-side pagination only — no `Pagination` UI control (buttons/page indicator) was built; that's still the separate, unbuilt "`Pagination` (standalone)" line below. 22 new tests; verified by disabling `display_rows()`'s slicing and confirming 10 tests fail (model, all three backends, and contract tests) before restoring it.
  - [x] Empty, loading, and error states — Done (2026-08-22): `TableModel` tracks whether `set_rows()` has ever run (`_rows_set`), so a table that simply hasn't loaded yet is left alone, but a completed fetch returning zero rows now shows a "No data" placeholder (`is_empty`/`EMPTY_TEXT`) with the existing priority order preserved — error beats loading beats empty, so a refresh that clears rows before repopulating keeps showing "Loading…" instead of flashing "No data". All three backends' `set_rows()` now call the existing overlay/message sync so the placeholder actually renders, not just the model flag. 13 new tests; verified by disabling `is_empty` and confirming 5 tests fail (across all three backends) before restoring it.
  - [ ] Row action buttons — doesn't exist; only whole-row `on_row_click`
- [ ] `Pagination` (standalone) — doesn't exist

### Forms and Feedback

- [x] `Checkbox`, `Switch` — Done (2026-08-29): `ICheckbox`/`ISwitch` (`is_checked()`/`set_checked()`/`on_change()`, matching `IWidget`'s `is_x()`/`set_x()` boolean convention), primitive-layer wiring (`contracts/widgets.py` abstract `createCheckbox`/`createSwitch`, not the optional Admin-component pattern) across Qt (styled `QCheckBox`, Switch is a distinct interface reusing the same native control today), Jupyter (stock `ipywidgets.Checkbox`/`ToggleButton`), and Web (`ui.checkbox`/`ui.switch`). Contract tests via a new shared `CheckedWidgetContractTest` mixin.
- [ ] `RadioGroup`, `NumberInput`, `DateInput`
- [ ] `Form`: field registration, submit, reset
- [ ] Validation rules and field-level error messages
- [ ] `Modal` / `Dialog`: confirmation and edit forms — `IDrawer` is the closest analog (uses `QDialog` on Qt) but is explicitly non-modal, a slide-in side panel, not a blocking confirm/edit dialog
- [x] `Toast` / `Notification` — Done (2026-08-29): `IToast` (`notify()`/`dismiss()`, not `show()`/`hide()` — that pair is already the visibility toggle every widget has), full Qt/Jupyter/Web wiring incl. contract + rendering tests. Renders inline wherever placed in the tree, not as a floating corner overlay — see the floating-overlay upgrade path noted below and in `IToast`'s docstring.
- [ ] `Loading` / `Skeleton`
- [ ] Floating overlay positioning for `Toast` (window-corner popup, stacking multiple messages) — today it's a single inline banner reused per `notify()` call, a real gap not a design choice.

## P1: Components Showcase (Component Gallery)

> Added 2026-08-25, from an external design review (codex) of `examples/admin_demo.py`. Once the Dashboard's last-polish pass (sidebar label bug, Beta badge sizing, live chart, Process card DPI check) is done, Dashboard is frozen as a stable demo page — no more redesign time there. This becomes the next priority: a dedicated `examples/component_gallery.py` (or a "Components" route inside `admin_demo.py`) that demonstrates UniUI's own component library, organized by category, each with a live/interactive demo rather than a static screenshot.

- [x] **Phase 1 — showcase what already exists** — Done (2026-08-28): `examples/component_gallery.py`, organized by category (Overview/Buttons/Inputs/Data Display/Navigation/Layout) with a grouped Sidebar + Router, exactly like `admin_demo.py`'s navigation shape. Written entirely against the cross-backend declarative API (`Card`, `Button`, `Table`, ...) rather than a Qt-specific hand-built path, so the same file runs unmodified on Qt/Jupyter/Web — verified on all three. Covers `Card`, `Badge`, `ProgressBar`, `StatCard`, `MetricList`, `Table` (sortable columns + row selection + click), `Chart`, `Gauge`, `Breadcrumb`, `TabWidget`, `Button` (with a real click counter, not a static screenshot), `LineEdit`/`TextArea`/`ComboBox`/`Dropdown`, `Grid`/`Wrap`/`SplitPane`, `GroupBox`. Deliberately honest about what's NOT a real UniUI feature yet (a note on the Buttons page: visual variants like primary/secondary aren't a separate widget API, just backend-specific styling hooks). Added to the Web smoke-test matrix (`tests/test_web_backend.py`).
  - Not yet covered from the original Phase 1 list: `ScrollView`, `Overlay` (both exist and are tested elsewhere, just not demoed on this page yet) — small follow-up, not blocking.
- [ ] **Phase 2 — fill gaps one component at a time**, adding each to the gallery as it ships rather than waiting for all of them: `RadioGroup`, `NumberInput`, `DateInput`, `Slider` (Inputs); `Avatar`, `List`, `Tree`, `Tag`, `Skeleton`, `Empty state` (Data Display — `Tag` may just be `Badge` restyled, check before building new); `Alert`, `Spinner`, `Confirmation` (Feedback); `Dialog`/`Modal` (blocking, unlike the existing non-modal `Drawer`), `Popover`, `Tooltip`, `Context Menu`, `Dropdown Menu` (Overlays — each needs a real `[Open ...]` trigger button in the gallery, not a screenshot); `Tabs` (may already be covered by `TabWidget`), `Menu`, `Pagination` (standalone), `Segmented Control` (Navigation); `Split View`/`Resizable Panel`/`Stack`/`Master-Detail` (Layout — check overlap with existing `SplitPane`/`Overlay` first).
  - [x] `Toast`/`Notification` — Done (2026-08-29), see Forms and Feedback above. Wired into `examples/component_gallery.py`'s new Feedback category page, with real `[Show success/warning/error/neutral]` trigger buttons calling `toast.notify(...)`, not a screenshot.
  - [x] `Checkbox`/`Switch` — Done (2026-08-29), see Forms and Feedback above. Wired into `examples/component_gallery.py`'s Inputs page with a real on_change-driven echo label, not a screenshot. Qt's Switch reuses a plain `QCheckBox` visually today — a track-and-thumb QSS/custom-paint treatment is a follow-up, not blocking.
  - [x] Also add a real usage demo into `examples/admin_demo.py` itself — Done (2026-08-29): a "Live updates" `Switch` on the Dashboard page (both the Qt hand-written page and the shared Jupyter/Web page) gates whether the existing `_live_tick` random-walk chart update keeps firing, a real on/off effect rather than a decorative control.
  - [x] `Carousel`/image slideshow — Done (2026-08-29): `ICarousel` (`set_images(paths)`, `next_slide()`/`previous_slide()` with wraparound, `get_current_index()`/`set_current_index()`, `set_auto_advance(enabled, interval_ms)`, `on_change()`), Admin-component pattern like Toast (optional, `NotSupportedError` default) since it's a composed display widget, not a core form control. Slides are local file paths only — Jupyter's `ipywidgets.Image` has no URL-loading support, so the interface sticks to the lowest common denominator across backends. Qt: a single `QLabel` + prev/next `QPushButton`s + dot indicators + `QTimer` for auto-advance. Jupyter: single `ipywidgets.Image` with swapped `.value` bytes + `schedule_after`-based auto-advance using the same generation-counter guard as Toast. Web: NiceGUI's native `ui.carousel`/`ui.carousel_slide` — `next_slide()`/`previous_slide()` deliberately drive `set_current_index()` (server-side `set_value()`) rather than the native `.next()`/`.previous()` methods, which are client-side `run_method()` calls that don't synchronously update `.value` without a connected browser. Wired into `examples/component_gallery.py`'s Data Display page with generated placeholder PNGs (pure stdlib `struct`/`zlib`, no Pillow dependency, no bundled assets, no network calls) and a real on_change-driven "Slide N of 4" label.
- [ ] Design tokens: extend the `space_1..6`/`text_xs..lg` scale added 2026-08-25 (`theme.py`) to cover every remaining hardcoded literal across Qt Admin components (progress_bar.py height/radius, primitives/styles.py radius/padding, app_shell.py header margins/viewport margins) — audit found only 9 real `M[...]` call sites before this session's sidebar/card work, everything else was ad hoc per-widget.
- [ ] Responsive/DPI test pass across the gallery specifically (not just Dashboard): 1280×800, 1024×700, maximized; 100%/125%/150% DPI. Check clipping, text elide, minimum size, scrollbar behavior, card wrapping, toolbar overflow, table column behavior, sidebar collapse — via layout/size-policy fixes, not hardcoded pixel positions.
- [ ] Principle carried over from this session's Table/Chart/Sidebar work: fix shared components (e.g. `Card`'s padding), not per-page patches — every page using the shared component picks up the fix automatically.

## P1: Chart Support

### Chart Common API

- [x] Add `IChart` and a `Chart(...)` facade API
- [x] Use backend-agnostic declarative configuration; do not expose Qt/Jupyter native objects to business code
- [ ] First version supports:
  - [x] Line chart `line`
  - [x] Bar chart `bar`
  - [ ] Pie / donut chart `pie` / `donut`
  - [ ] Scatter chart `scatter`
  - [x] Area chart `area`
- [ ] Support title, legend, axes, units, colors, stacking, and tooltip
  - Title, basic axis gridlines, and per-series colors exist. Legend, units, stacking, and tooltip are all absent — ADR 0001 explicitly lists this as a deliberate consequence of the hand-rolled renderer.
- [x] Support empty data, loading, and render error states — Done (2026-08-24): `ChartModel` gained `set_loading`/`set_error` mirroring `Table`'s priority order (error beats loading beats empty). Qt's `_ChartWidget.paintEvent` draws the model's message text instead of a hardcoded "No data" literal; Jupyter/Web share a new `render_chart_message_svg()` (`visuals.py`, factored out of the existing empty-state SVG) so all three status messages sit in the exact spot the chart would occupy. Also fixed a pre-existing cross-backend inconsistency along the way: the SVG empty-state used to show the chart's title text instead of "No data" when a title was set, while Qt always showed literal "No data" — now both agree. 15 new tests; verified by disabling `shows_overlay` and confirming 5 tests fail across all three backends before restoring it.
- [x] Support dark/light theme and redraw on theme switch
- [x] Support responsive sizing and minimum height

Proposed API draft:

```python
chart = Chart(
    type="line",
    title="Last 7 Days — Visits",
    x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    series=[
        {"name": "Visits", "data": [120, 160, 150, 210, 240, 190, 280]},
    ],
)

chart.set_data(
    x=["Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Mon"],
    series=[{"name": "Visits", "data": [160, 150, 210, 240, 190, 280, 310]}],
)
```

### Chart Implementation Tasks

- [x] Compare Plotly, ECharts, and Matplotlib for Qt/Jupyter consistency, package size, offline capability, and packaging complexity — decided against all three; see [docs/adr/0001-chart-rendering.md](docs/adr/0001-chart-rendering.md)
- [ ] Place chart dependencies in an optional extra, e.g. `uniui[charts]` — moot per the ADR: no chart dependency exists at all, nothing to gate
- [x] Implement Qt renderer
- [x] Implement Jupyter renderer
- [x] Provide `set_data()` to refresh data without replacing the component instance
- [x] Provide `append_data()` for real-time monitoring charts
- [x] Cap the number of real-time data points to prevent memory growth over long runs
- [ ] Support PNG/SVG export (can move to P2) — SVG is used internally as the render mechanism (Jupyter/Web) but isn't exposed as an export API; no PNG export exists (Qt renders live via `QPainter`, not to an exportable image)
- [ ] Raise `NotSupportedError` with installation instructions when chart dependencies are missing — moot per the ADR: no dependency exists to be missing

## P1: 2D / 3D Visualization

> Audited 2026-08-22: confirmed zero code artifacts anywhere in `src/uniui` for anything in this entire section — no `Scene2D`/`Scene3D`/`Canvas2D`/`Viewport3D`, no `Solid`/CSG, no 3D primitives, no ADRs comparing 3D/CSG libraries, no `csg`/`3d` optional-dependency extras. Every checkbox below is accurately unchecked; none are annotated individually since there's nothing partial to report.

### Common Scene Model

- [ ] Add backend-agnostic `Scene2D`, `Scene3D`, `Canvas2D`, `Viewport3D` APIs
- [ ] Scene objects use stable IDs; support add, delete, replace, and partial property updates
- [ ] Geometry data, materials, cameras, and lights are decoupled from the rendering backend
- [ ] Support scene tree, parent-child relationships, visibility, locking, and selection state
- [ ] Support translate, rotate, scale, and matrix composition
- [ ] Support dark/light background, grid, and guide line theming
- [ ] Scene updates do not rebuild the entire Viewport

### 2D

- [ ] Basic primitives: point, line, polyline, rect, circle, ellipse, polygon, text, image
- [ ] Paths: `move`, `line`, quadratic/cubic Bézier, closed paths
- [ ] Fill, stroke, opacity, line style, and layer order
- [ ] Coordinate transforms, zoom, pan, fit-to-view, and grid snapping
- [ ] Mouse click, hover, box selection, drag, and scroll-wheel zoom events
- [ ] SVG import/export; PNG export as an enhancement
- [ ] Qt renderer and Jupyter renderer

Proposed API draft:

```python
scene = Scene2D(
    Rect(0, 0, 120, 80, fill="#3b82f6"),
    Circle(60, 40, 20, fill="#f59e0b"),
)

canvas = Canvas2D(scene, grid=True)
canvas.fit_view()
```

### 3D Foundation

- [ ] Basic primitives: `Box`, `Sphere`, `Cylinder`, `Cone`, `Plane`, `Mesh`
- [ ] Transforms: `translate()`, `rotate()`, `scale()`, `transform()`
- [ ] Perspective/orthographic camera, orbit rotate, pan, zoom, and fit-to-view
- [ ] Ambient light, directional light, and basic materials (color, opacity, wireframe)
- [ ] Grid, axes, bounding box, and normal display
- [ ] Object picking, selection highlight, and selection-change callback
- [ ] Partial updates for large scenes; avoid a full renderer rebuild on every modification
- [ ] Qt and Jupyter maintain the same camera and selection semantics

### 3D CSG (Priority)

- [ ] Establish an immutable or copyable `Solid` geometry model
- [ ] Support CSG primitives: box, sphere, cylinder, cone, and custom closed meshes
- [ ] Support boolean operations:
  - [ ] Union `union` / `a | b`
  - [ ] Difference `difference` / `a - b`
  - [ ] Intersection `intersection` / `a & b`
- [ ] Support batch boolean operations on multiple solids
- [ ] Support translate, rotate, and scale before and after boolean operations
- [ ] Validate that meshes are closed, manifold, and have consistent normals; provide understandable error messages
- [ ] Establish tolerance strategies for coplanar faces, tiny faces, floating-point error, and degenerate geometry
- [ ] Run CSG computation in a worker thread; safely update the UI on completion to avoid blocking the interface
- [ ] Support cancellation of long-running CSG tasks and progress reporting
- [ ] Cache intermediate results for identical inputs to reduce redundant computation in parametric models
- [ ] Support STL, OBJ, PLY, glTF/GLB import or export; MVP must at minimum support STL
- [ ] Provide a CSG tree viewer showing operation nodes, input solids, and the final result

Proposed API draft:

```python
body = Box(40, 30, 10)
hole = Cylinder(radius=4, height=20).translate(20, 15, -5)
solid = body - hole

viewport = Viewport3D(
    solid,
    grid=True,
    axes=True,
    camera="perspective",
)

solid.export_stl("part.stl")
```

### 3D Technology Selection

- [ ] Write ADR: compare `manifold3d`, `trimesh`, and OpenCASCADE/CadQuery for CSG stability, license, install size, and Python version support
- [ ] Write ADR: compare PyVista/VTK, Qt3D/OpenGL, and Three.js/Jupyter renderer for dual-backend consistency
- [ ] CSG kernel and renderer are separate optional extras: `uniui[csg]` and `uniui[3d]`
- [ ] First version prioritizes a reliable manifold boolean kernel; do not implement BSP/mesh boolean algorithms from scratch
- [ ] Core UniUI and Admin/Chart features remain fully functional without 3D/CSG dependencies
- [ ] Raise `NotSupportedError` with accurate installation commands when dependencies are missing
- [ ] Define coordinate system, length units, rotation units, winding order, and normal conventions

## P2: Production Backend Capabilities

- [ ] Reusable search/filter bar
- [ ] DataGrid server-side pagination, sorting, and filtering protocol
- [ ] Async task status and cancellation
  - Cancellation infra (`TaskRunner`) exists and works generically, but is unused elsewhere in `src/`, has no explicit "status" property, and no UI component surfaces task state.
- [ ] Permission-driven menu and button visibility
- [ ] Keyboard navigation and basic accessibility support
  - Qt-only, partial: `setAccessibleName` on shell/sidebar regions. No keyboard-navigation logic, no Web/Jupyter ARIA attributes.
- [ ] Layout state persistence (sidebar, filter conditions, table columns)
- [ ] Chart interaction: click legend, data point, or box selection triggers callbacks
- [ ] Dashboard auto-refresh, pause, and refresh interval settings
- [ ] Chart export and Dashboard screenshot/report export
- [ ] Embed 2D/3D Viewport in Dashboard, with filters updating the model
- [ ] Parametric CSG editor: modify dimensions and asynchronously rebuild the model
- [ ] 3D measurement tools: point distance, edge length, angle, and bounding box dimensions
- [ ] Cross-section, clipping plane, and exploded view
- [ ] Undo/redo for scene and CSG operations

### Permissions and Application Services

- [ ] Define `Session` / `UserContext` storing the current user, roles, and permission claims
- [ ] Routes and menus support `requires` permission configuration
- [ ] Unauthorized route access redirects to a unified 403 page
- [ ] Buttons, row actions, and export capabilities support permission-driven visibility or disabling
- [ ] Clarify that UI permissions are for interaction control only; real data permissions must be re-verified server-side
- [ ] Provide an application-level service container for injecting API clients, data repositories, logging, and configuration
- [ ] Provide a global error boundary that displays unhandled exceptions as an error page or notification rather than crashing the entire application

### Configuration and Persistence

- [x] Named, JSON-loadable themes beyond the built-in light/dark pair
      (`register_theme`/`set_active_theme`/`list_themes` in `theme.py`,
      backed by `theme_registry.py`)
- [ ] Add a `Settings` API for unified preferences across Qt desktop and Jupyter environments
- [ ] Persist theme, sidebar state, window size, recent routes, and table column configuration
      — the active theme *name* is not persisted across runs yet; it depends
      on the `Settings` API above
- [ ] Settings file includes a schema version with migration and default-restore support
- [ ] Do not store tokens, passwords, or other sensitive data in regular settings
- [ ] Sensitive data uses the system credential store or is provided by the host application

### Design System and User Experience

- [x] Establish unified design tokens: colors, spacing, border radius, font sizes, shadows, and status colors — `src/uniui/theme.py` is the explicit single source of truth for all three backends
- [x] Establish an icon system to avoid each example mixing Unicode icons ad hoc — `src/uniui/icons.py`, one SVG set consumed by all three backends
- [ ] All data components provide standard Loading, Empty, Error, and Success states
  - `Table` and `Chart` both have real loading/error/empty handling (Table empty added 2026-08-22, Chart loading/error added 2026-08-24); no Success state anywhere, and `Gauge`/`StatCard` still have no loading/error/empty handling at all.
- [ ] Support high DPI, font scaling, keyboard focus, and sensible Tab order
  - Qt sets high-DPI attributes; no font scaling, keyboard focus, or Tab-order management confirmed anywhere.
- [ ] Primary components provide consistent compact/standard density modes — the only "compact" concept found is the layout-width breakpoint mode, not a component density/row-height mode
- [ ] Theme switching does not flicker and does not lose table, route, chart, or 3D scene state — architecturally likely true (`THEME` is mutated in place, `apply_theme()` never touches model state) but not covered by a dedicated test

## Architecture and Code Changes

- [ ] Add new component interfaces in `core.py`; keep interfaces describing only cross-backend capabilities
- [ ] Implement adapters separately in `qt.py` and `jupyter.py`
- [ ] Expose declarative constructor functions in `__init__.py`
- [x] Split complex components into dedicated modules to avoid growing single backend files further — `backends/{qt,jupyter,web}/components/` each already have one dedicated module per component
- [ ] Place 2D/3D scene models, CSG kernel adapters, and renderers in separate sub-packages — N/A, nothing to place yet
- [ ] Establish a component registry to reduce boilerplate in the factory — each factory still hand-writes one `createXxx` line per component; a narrower `_SNAKE_ALIASES` table auto-generates snake_case aliases, but that's not a full registry
- [ ] Legacy backends must uniformly raise `NotSupportedError` for new components; no further expansion — N/A, no legacy backends remain and no new unsupported components exist yet
- [ ] Update optional dependencies and package metadata in `pyproject.toml` — N/A, nothing new to add yet
- [ ] Update the component support matrix in README — the existing matrix (`README.md`) only covers basic primitives, not Admin components or 2D/3D
- [x] Fix references to non-existent modules and outdated architecture diagrams in documentation — checked `docs/architecture.md` against the real module layout; it's accurate, nothing stale found
- [x] Fix package description, keywords, classifiers, and project URLs; remove placeholder addresses — `pyproject.toml`'s description/classifiers/URLs already accurately match the real package
- [ ] Separate installation commands for end users and developers in docs: `.[qt]`, `.[jupyter]`, `.[dev]` — README only documents `pip install -e .` + per-backend extras, no separate dev-install section

Recommended gradual restructure to avoid continuing to pile everything into `core.py` and single backend files:

```text
src/uniui/
    core/              # Common protocols, exceptions, lifecycle
    state/             # State, Computed, binding
    routing/           # Router, Route, history
    data/              # DataSource, pagination, loading state
    tasks/             # Async tasks and UI scheduling
    widgets/           # Base and Admin component facades
    charts/            # Chart model and renderer adapters
    graphics2d/        # 2D scene and primitives
    graphics3d/        # 3D scene, meshes, and renderer adapters
    csg/               # Solid, boolean kernel adapters, import/export
    backends/
        qt/
        jupyter/
```

- [x] Maintain compatibility for existing top-level imports, e.g. `from uniui import Button` — enforced by `tests/test_widget_factory_composition.py`, which breaks every shim and asserts `create_factory("qt")` still works
- [ ] Introduce new modules via compatibility shims first; avoid one-shot large-scale migration — the pattern is already established (`qt.py`/`web.py`/`jupyter.py`/etc. are pure re-export shims) but hasn't been exercised for anything genuinely new yet
- [ ] Define capability probing for optional modules, e.g. `supports("csg")` — doesn't exist
- [ ] Define a stable serialization format for router state, chart configuration, and scene persistence — doesn't exist

## Recommended Implementation Order

### M0: Engineering Foundation

- [ ] Fix and unify duplicate/missing methods in existing component interfaces
  - The common-capabilities gap (show/hide/enabled/sizing missing across most interfaces) was closed 2026-08-19 (see the P0 item above). A broader interface audit beyond that hasn't been done.
- [ ] Migrate to PySide6; remove hardcoded PySide2 references from core flows — not started, `PySide2` is still imported everywhere in `backends/qt/`
- [ ] Main CI and contract tests treat only Qt/Jupyter as official backends — CI still checks wxPython/Tkinter compatibility and doesn't install `nicegui` for the Web contract run
- [ ] Clean up inconsistencies in README, architecture docs, package metadata, and installation instructions — README still says `pip install PySide2` (accurate today, but will need updating once PySide6 migration happens)
- [ ] Establish lifecycle, capability, and backend contract — no `supports()`/capability-probing mechanism exists; only the `NotSupportedError` exception type
- [ ] Extract a progressively migratable new module structure
  - Partial: `src/uniui/contracts/` and `backends/{qt,jupyter,web}/` sub-packages exist with import-isolation enforced by tests. The proposed `state/`/`routing/`/`data/`/`tasks/`/`charts/`/`graphics2d/`/`graphics3d/`/`csg/` split hasn't happened — `core.py`/`state.py`/`routing.py` remain flat files.

### M1: Adaptive Layout

- [x] Complete `LayoutSpec`, `SizeSpec`, and `LayoutItem`
- [x] Complete `Row`, `Column`, `Grid`, `Wrap`, `ScrollView`, `SplitPane`, and `Overlay` — all exist and are contract-tested on Qt/Jupyter/Web
- [x] Complete Qt `QSizePolicy` / stretch / breakpoint renderer
- [ ] Complete Jupyter Flex/Grid/container responsive renderer
  - Containers exist, but there's no breakpoint-switching mechanism analogous to Qt's `_ResizeNotifier` — `on_resize` is Qt-only.
- [ ] Pass the three-width cross-backend layout acceptance criteria before starting new complex business components — only Qt's breakpoint behavior is verified by test; Jupyter parity isn't

### M2: State and Scheduling

- [x] Complete `State`, `Computed`, binding, and `TaskRunner`
- [x] End-to-end validation with existing `Label`, `LineEdit`, and `Dropdown` — `bind_*` helpers + `tests/contracts/test_state_binding.py`
- [ ] Confirm consistent thread and event loop behavior between Qt and Jupyter — no test directly compares Qt vs. Jupyter scheduling semantics side-by-side

### M3: Admin Skeleton

- [x] Complete `AppShell`, `Sidebar`, `Router`, `RouterView`, `Breadcrumb`
- [x] Complete `Card`, `StatCard`, basic `Table`, and loading/error feedback — "basic" Table scope only: no sorting/pagination (see Data Display above)
- [x] Deliver the first navigable Admin example — `examples/admin_demo.py`, not literally named "admin_dashboard.py" but satisfies the intent

### M4: Data Dashboard

- [ ] Complete `DataSource`, pagination/filtering, `Chart`, and dynamic updates
  - `Chart`/dynamic updates (`set_data()`) are done and used in `admin_demo.py`. `DataSource` doesn't exist; filtering is ad-hoc example code, not a framework abstraction; pagination doesn't exist.
- [ ] Complete theme integration and Dashboard auto-refresh
  - Theme integration is extensive and tested. Auto-refresh doesn't exist — `admin_demo.py` only has a manual "Refresh" button.
- [x] Admin example connected to a simulated async data source — `admin_demo.py` uses `TaskRunner` + a simulated delay

### M5: 2D/3D and CSG

- [ ] Freeze the `Solid` / `Mesh` / `Transform` common data model first
- [ ] Integrate a reliable CSG kernel and complete geometry tests without UI
- [ ] Implement Qt/Jupyter `Viewport3D` renderer
- [ ] Complete a parametric drilled-hole model with async rebuild and STL export example

### M6: Integration and Release

- [ ] Embed Chart, Canvas2D, and Viewport3D pages within Admin routes
- [ ] Complete permissions, settings persistence, error boundaries, and resource cleanup
- [ ] Complete documentation, migration guide, performance benchmarks, and packaging verification
- [ ] Before release, clearly designate which APIs are stable and which are still experimental

## Engineering Quality and Release

- [ ] Provide a single command to install the dev environment and run all checks
- [ ] CI runs separate jobs for: core-only tests, Qt contract, Jupyter contract, and optional plugin tests
- [ ] Do not allow a passing CI result when all official backend tests were skipped due to missing dependencies
- [ ] Ruff, format checks, and pytest must block non-conforming commits — CI's `lint` job runs `ruff check`/`ruff format --check`/`black --check`, but branch-protection/required-status-check enforcement isn't visible in-repo to confirm this actually blocks merges
- [ ] Gradually enable strict mypy; stop using `|| true` to suppress type errors — CI still literally runs `mypy src/uniui --ignore-missing-imports || true`
- [x] Test suite default backend must no longer be legacy Tkinter
- [ ] Add public API compatibility tests and a deprecation cycle
- [ ] Add visual snapshot or key-page screenshot regression tests
- [ ] Add performance benchmarks for DataGrid, dynamic charts, and 3D scenes
- [ ] Verify PyInstaller packaging, offline operation, and optional asset bundling
- [ ] Maintain CHANGELOG, migration guide, versioning policy, and API stability documentation
- [ ] Verify that a fresh environment can go from install to running the first example in under 5 minutes

## Testing and Acceptance

- [x] Every new component has public contract tests
- [x] Both Qt and Jupyter have minimal smoke tests
- [x] Layout size, flex, spacing, alignment, Grid span, and child order have pure model tests — `tests/test_layout_model.py`, `tests/contracts/test_layout.py`
- [x] Qt correctly switches layout mode at container widths of 640, 900, and 1440
- [ ] Jupyter Flex/Grid generates key layout attributes that conform to the public `LayoutSpec` — matches the M1 Jupyter breakpoint gap above
- [x] Breakpoint switches do not destroy components with stable keys
- [ ] Continuous resize does not trigger CSG recomputation or duplicate data requests — N/A, no CSG exists
- [ ] Jupyter resize bridging is debounced and does not generate high-frequency comm messages — no debounce mechanism found
- [ ] Key Admin pages have visual snapshot regression tests at compact/medium/wide — no snapshot tests exist at all
- [ ] `State` / `Computed` dependency updates, batching, unsubscribe, and cycle detection have unit tests
  - Dependency updates and unsubscribe/dispose are extensively tested (`tests/test_state.py`). Cycle detection is now implemented and tested (2026-08-22, see the P0 State item above). Batching is still neither implemented nor tested.
- [x] Background task completion, failure, cancellation, timeout, and "new result overwrites old" rule have tests — `tests/test_task_runner.py` (11 tests: completion, failure, cancellation, new-overwrites-old, and timeout added 2026-08-22)
- [ ] State subscriptions, timers, and tasks are all released after a page is destroyed — no combined page-lifecycle-teardown test exists; only `RouterView.dispose()` (narrower) is tested
- [ ] `DataSource` pagination, sorting, filtering, caching, and error states have tests — N/A, `DataSource` doesn't exist
- [x] Route matching, parameter parsing, query parameters, redirects, 404, and history have unit tests — `tests/test_routing.py` (39 tests, including redirect/default-route coverage added 2026-08-22)
- [ ] Navigating to the same path in Qt and Jupyter renders equivalent pages — no direct Qt-vs-Jupyter equivalence test exists; contract tests are parametrized per-backend, not cross-compared
- [ ] Rapid consecutive navigation does not duplicate cached pages or leave behind page tasks
  - Layer/cache-duplication is directly tested (`test_uncached_pages_do_not_accumulate_layers`, `test_cached_pages_are_never_removed_across_navigation`). "No leftover page tasks" isn't separately tested.
- [ ] Chart configuration validation, empty data, and invalid data have unit tests
  - Chart-type validation and fallback-to-line are tested (`tests/test_models_gauge_chart.py`); no dedicated empty-data or invalid-data-rejection test.
- [ ] Dynamic chart updates do not create duplicate event listeners or duplicate native widgets — no such test exists
- [ ] 2D primitive coordinates, transforms, layering, and event hit-testing have unit tests
- [ ] 3D transforms, camera state, and object selection have contract tests
- [ ] CSG boolean results on standard primitives pass volume and mesh topology validation
- [ ] Degenerate CSG inputs, non-manifold meshes, and computation failures do not crash the UI
- [ ] Qt and Jupyter displaying the same CSG model produce consistent vertex/face data
- [ ] Released 3D scene and CSG background tasks leave no lingering threads or large mesh allocations
- [ ] After a theme switch, Admin components, charts, and 2D/3D Viewports update their colors in sync
  - Admin-component sync is well tested (`tests/test_theme_unification.py`); charts aren't explicitly covered by name; Viewports are N/A.
- [ ] Interaction is acceptable with a 1000-row table and typical chart data volumes — no performance/load test exists
- [x] Core package imports and functions correctly when optional dependencies are absent — `tests/test_import_isolation.py` (6 dedicated tests) + `tests/test_optional_backends.py`
- [ ] Permission-based hiding affects only the UI; the example service layer still validates permissions independently — N/A, no permission system exists yet
- [ ] Corrupted or outdated settings files can be safely migrated or reset to defaults — N/A, no `Settings` API exists yet
- [ ] Add a complete `examples/admin_dashboard.py` — `examples/admin_demo.py` exists under a different filename and substantially satisfies the intent
- [ ] Add `examples/csg_demo.py`: parametric input, drilled solid, live preview, and STL export — doesn't exist
- [ ] Add flagship application `examples/engineering_console.py` — doesn't exist; `examples/` only has `admin_demo.py`, `calculator.py`, `credit_card.py`, `sysmon.py`
- [ ] Flagship app includes Dashboard, task table, model browser, CSG Editor, and Settings routes — N/A, flagship app doesn't exist
- [ ] Flagship app uses the same `DataSource` to drive `StatCard`, `DataGrid`, and `Chart` — N/A
- [ ] Flagship app demonstrates async loading, error recovery, permission control, theming, and settings persistence — N/A
- [ ] Examples include at minimum: sidebar, 4 StatCards, filter bar, DataGrid, line chart, pie chart, theme toggle, and auto-refresh
  - `admin_demo.py` has most of this (sidebar, StatCards, filter bar, theme toggle) but no pie chart and no auto-refresh (manual refresh only).
- [x] Examples run with `--ui qt` using the same code and can be displayed in Jupyter — `admin_demo.py`'s docstring documents all three `--ui` flags working from one file

## First Deliverable (MVP)

- [x] `Row` / `Column` / `Grid` / `Wrap`
- [x] `ScrollView` / `SplitPane` / `Overlay`
- [ ] Unified sizing, grow/shrink, gap/padding, and responsive breakpoints — Qt side done; Jupyter breakpoint-switching parity is still missing (see M1)
- [ ] Qt/Jupyter three-tier adaptive layout contract — same Jupyter gap as above; not a clean flip
- [x] `Card` / `StatCard`
- [ ] `Table` (static data, sorting, pagination) — static data and sorting both work and are tested (2026-08-22); no real pagination on any backend
- [x] `Sidebar` + `AppShell`
- [x] `Router` + `RouterView` (static paths, path parameters, 404, forward/back) — all four sub-features directly tested
- [ ] `Chart` (line, bar, pie) — line/bar/area are done; pie doesn't exist
- [x] Chart `set_data()` dynamic updates
- [ ] `Viewport3D` + Box/Sphere/Cylinder/Mesh — doesn't exist
- [ ] CSG union/difference/intersection and STL export — doesn't exist
- [x] Qt/Jupyter dual-backend with theme support
- [ ] Admin Dashboard example and tests — `admin_demo.py` exists and is exercised indirectly via component contract tests; no dedicated end-to-end test file, and it's a different filename than the doc names elsewhere

## Definition of Done

When a user can write Python code with no Qt or ipywidgets branch conditions, create a backend page with navigation, metric cards, a filterable table, a dynamic chart, and a 3D CSG Viewport, perform solid union/difference/intersection and STL export, and run the same code in both Qt and Jupyter — this goal is complete.
