# UniUI TODO: Admin / Dashboard Capabilities

> "Admin-like" is defined here as: using the same UniUI Python API to build usable admin backends and data dashboards in both Qt and Jupyter. The wxPython and Tkinter backends have since been removed entirely.

## Product Positioning

Position UniUI as a "Python engineering data application framework": the same business code can power data dashboards, instrument control, simulation analysis, and parametric 3D tooling in both Qt desktop and Jupyter.

- [ ] Define a clear target user and typical scenarios around engineering data applications
- [ ] Admin, charts, 2D/3D, and CSG share a unified state, data, and task model
- [ ] Keep the core package lightweight; Chart, 3D, and CSG use optional extras or plugins
- [ ] Do not market ipywidgets as a standalone web deployment; if a real web app is needed, design a separate Web backend later
- [ ] Each release should prioritize delivering complete user workflows, not maximizing widget count

## Overall Goals

- [ ] Support a standard admin shell: top bar, sidebar, content area, status bar
- [ ] Display key metrics, data tables, filter forms, and action buttons
- [ ] Display and dynamically update charts
- [ ] Display and edit basic 2D/3D scenes, with a focus on 3D CSG modeling
- [ ] The same business code runs in both Qt and Jupyter
- [ ] Consistent dark/light theming with runtime toggle support
- [ ] Provide a unified interface, backend contract tests, and complete examples for all new components

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
  - Done (2026-08-19): the literal `sys.exit()` this line names was already gone (removed in an earlier refactor), but the real bug remained — `backends/qt/display.py`'s `show()` (the path `show_ui()` uses) decided whether to enter the blocking `app.exec_()` loop based on "am I running under pytest," not "did I create this `QApplication`." Embedding a UniUI-built widget into a host app that already owns a `QApplication` would still call `app.exec_()` again, starting a second nested event loop and blocking the host. Fixed by adding the same ownership check (`_app_is_ours = app is None`) that `show_forced()`/`show_qt()` in the same file already used correctly, ANDed with the existing pytest guard (both still needed — pytest guard alone doesn't distinguish embedding from "first QApplication in this test process"; ownership check alone doesn't stop tests from entering a real event loop the first time they create one). Also `show_ui()`/`UniversalDisplay.show()` now return the native root widget they built (previously `None` — the widget was only reachable via the private `display._root_widget` global), so embedding is actually usable. Verified with a monkeypatch-based regression test (`tests/test_display.py`) and manual smoke scripts for both the embedding and standalone cases; confirmed the regression test fails without the fix by temporarily reverting it.
- [ ] Support high DPI, system scaling, keyboard navigation, and basic accessibility attributes
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
- [x] Match Web controls: primary/secondary/icon buttons, inputs, status pills, cards, and table chrome
- [x] Keep the Sidebar draggable in wide mode and restore the last user-selected width
- [ ] Support wide Sidebar, medium icon rail, and compact drawer modes without recreating route pages
- [ ] Verify light/dark switching updates existing widgets without losing route, selection, form, chart, or splitter state

#### Phase 2: Native Dashboard Components

- [x] Add a backend-neutral `Gauge` / `RadialProgress` interface
- [x] Implement Qt Gauge using `QPainter` with antialiasing, semantic colors, units, and animated value transitions
- [x] Add line, area, and bar charts with lightweight `QPainter` / SVG real-time renderers; keep `pyqtgraph` as a future optional high-throughput renderer
- [ ] Keep chart dependencies optional, e.g. `uniui[charts]`
- [ ] Add chart theme switching, empty/loading/error states, and responsive resize handling
- [ ] Replace `QTableWidget` with `QTableView + QAbstractTableModel` for production DataGrid performance
- [ ] Add delegates for status pills, numeric alignment, progress cells, and row action buttons
- [ ] Add a themed Calendar component suitable for dashboard and scheduling pages
- [ ] Create an IoT/engineering Dashboard example containing gauges, charts, calendar, table, and live status

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
- [ ] Add Toast, Dialog, loading overlay, and Skeleton feedback components
- [ ] Use `QPropertyAnimation`, `QParallelAnimationGroup`, `QGraphicsOpacityEffect`, and `QEasingCurve` through reusable helpers
- [ ] Keep ordinary animation and resize interaction at 60 FPS on a typical engineering workstation

#### Phase 4: Responsive, DPI, and Production Quality

- [x] Verify Qt layouts at container widths of 1440, 1180, 900, and 640 logical pixels
- [x] Verify Windows scaling at 100%, 125%, 150%, and 200%
- [x] Ensure responsive reflow does not flicker or recreate gauges, charts, tables, or route pages
- [ ] Debounce chart and viewport resizing by 50–100 ms
- [ ] Ensure real-time charts and data refresh do not block the Qt UI thread
- [ ] Support keyboard navigation, visible focus rings, tooltips, and accessible names
- [x] Add offscreen geometry/state and screenshot render checks for the Qt Admin example
- [ ] Package SVG icons, fonts, and optional chart dependencies correctly for PyInstaller builds

#### Qt Visual Parity Completion Criteria

- [ ] Qt and Web use the same Admin theme tokens and semantic component states
- [ ] Qt Dashboard reaches the same hierarchy, spacing, density, and clarity as the Web Dashboard
- [ ] Theme switching preserves loaded data, route, table selection, chart range, and Sidebar width
- [ ] Sidebar drag, responsive collapse, settings drawer, table interaction, and charts work without visible jank
- [ ] The flagship Admin business/page code contains no direct `PySide2` / `PySide6` imports
- [ ] The same flagship app runs with `--ui qt`, `--ui jupyter`, and `--ui web`

## P0: Adaptive Cross-Backend Layout (Highest Priority)

> Before continuing to develop Admin, chart, and 3D components, the layout common model, Qt adaptive implementation, and Jupyter responsive implementation must be completed first. The goal is behavioral consistency across backends, not pixel-perfect parity.

### Layout Common Model

- [ ] Add backend-agnostic `LayoutSpec`, `SizeSpec`, `LayoutItem`, and breakpoint models
- [ ] Add `Row` and `Column`; keep `HBox` / `VBox` as compatibility aliases
- [ ] Add `Grid`, `Wrap`, `ScrollView`, `SplitPane`, `Overlay`, `Center`
- [ ] Add `Container`, `Spacer`, `Divider`
- [ ] Support dynamic `add()`, `insert()`, `remove()`, `replace()`, `clear()`, and reordering
- [ ] Child components use stable keys; layout reflows preserve input values, chart state, router pages, and 3D camera state
- [ ] Layout updates only adjust native layout relationships — do not destroy and recreate business components

### Sizing and Flex

- [ ] Unified support for `auto`, `fill`, fixed pixels, and percentage sizes
- [ ] Support `min_width`, `max_width`, `min_height`, `max_height`
- [ ] Support `grow`, `shrink`, `basis`, and `aspect_ratio`
- [ ] Support parent layout `gap`, `padding`, main-axis alignment, cross-axis alignment, and wrapping
- [ ] Support child `align_self`, Grid row/column/span, and order
- [ ] Fixed sizes should only be used for clearly defined cases: icons, toolbars, collapsed Sidebar, etc.
- [ ] Remove the Display layer's recursive enforcement of the same margin/spacing on all nested layouts

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

- [ ] Use container width, not screen width, to determine responsive mode
- [ ] Define default breakpoints: `compact < 720`, `medium < 1200`, `wide >= 1200`
- [ ] Only reflow structure when crossing a breakpoint; delegate ordinary size changes to the native layout engine
- [ ] Sidebar supports: wide = expanded, medium = icon rail, compact = drawer/Overlay
- [ ] Dashboard Grid supports: wide = four columns, medium = two columns, compact = one column
- [ ] SplitPane can switch from horizontal to vertical in compact mode
- [ ] Responsive rules are overridable by the application; default breakpoints must not be hardcoded into components

### Qt Adaptive Renderer

- [ ] Map `fill` / `auto` / fixed sizes to the correct `QSizePolicy`
- [ ] Map `grow` to layout stretch factor
- [ ] Map `Grid` to `QGridLayout`, correctly handling row/column span
- [ ] Map `SplitPane` to `QSplitter`, supporting drag, minimum size, and ratio persistence
- [ ] Map `ScrollView` to `QScrollArea` with `setWidgetResizable(True)`
- [ ] Map `Overlay` to `QStackedLayout.StackAll` or equivalent
- [ ] Implement `Wrap` using a tested FlowLayout
- [ ] Responsive containers listen to their own `resizeEvent()`, not screen resolution
- [ ] Debounce chart and 3D Viewport resize events by 50–100 ms
- [ ] Resize only updates the chart renderer, WebGL/OpenGL buffer, and camera aspect ratio — do not re-run data queries or CSG
- [ ] Use logical pixels by default; correctly support Qt high DPI and system font scaling

### Jupyter Responsive Renderer

- [ ] Map `Row` / `Column` to ipywidgets Flex layout
- [ ] Map `Grid` to CSS Grid
- [ ] Dashboards should prefer `repeat(auto-fit, minmax(..., 1fr))` for adaptation without Python round-trips
- [ ] Map `Wrap` to `flex-flow: row wrap`
- [ ] Map `fill` / `grow` / `shrink` / `basis` to corresponding CSS flex properties
- [ ] All stretchable content must set `min-width: 0` to prevent charts and 3D canvases from overflowing their containers
- [ ] Prefer CSS Grid/Flex for responsiveness; do not send every resize back to Python
- [ ] For structural changes like Sidebar, prefer container queries; use media queries only as a fallback
- [ ] Provide a thin `ResizeObserver`-based frontend bridge for Chart/Viewport that requires exact dimensions
- [ ] Debounce `ResizeObserver` events; only sync to Python when a breakpoint changes or the size has stabilized
- [ ] Verify core layout behavior in JupyterLab, Classic Notebook, and VS Code Notebook

### Page Layout Spec

- [ ] AppShell fills available area; Header, Sidebar, Content, and Footer have clear responsibilities
- [ ] Default page padding 24, card gap 16, form gap 12 — all overridable via theme
- [ ] Sidebar default width 240, collapsed width 64; Header default height 56
- [ ] Each page has only one primary vertical scroll region
- [ ] Sidebar, DataGrid, and Dialog body may have their own independent scroll regions
- [ ] 3D Viewport does not participate in page scroll-wheel scrolling; scroll wheel is reserved for camera zoom
- [ ] Parameter panel and Viewport use SplitPane; recommended parameter panel width 280–360
- [ ] Regular pages may use Container to cap max content width; Dashboard/3D pages may go full width

### Layout Completion Criteria

- [ ] The same code completes Row, Column, Grid, Wrap, ScrollView, and SplitPane examples in both Qt and Jupyter
- [ ] Automatically forms compact, medium, and wide layouts at container widths of 640, 900, and 1440
- [ ] After a breakpoint switch, form values, routes, chart data, and 3D camera state are preserved
- [ ] No visible flicker, component re-creation, or high-frequency Python communication during continuous window resize
- [ ] Layout API does not require business code to access `QLayout`, `QSizePolicy`, or `widgets.Layout`

## P0: State, Data, and Async Tasks

Admin pages, route parameters, dynamic charts, and parametric CSG need to share a single state mechanism to avoid each component implementing its own refresh logic.

### Reactive State

- [ ] Add a lightweight `State[T]` supporting read, write, and subscribe
- [ ] Add a read-only `Computed[T]` that recalculates when its dependencies change
- [ ] Support one-way binding for component properties and two-way binding for form values
- [ ] Support batched updates: one business operation triggers at most one necessary redraw
- [ ] Subscriptions return a disposable handle; auto-unsubscribe when the page is destroyed
- [ ] Detect and prevent circular bindings and duplicate subscriptions with clear diagnostics
- [ ] The state layer is pure Python — no dependency on Qt or ipywidgets

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

- [ ] Add `Task` / `TaskRunner` to wrap long-running functions and coroutines
- [ ] Provide unified `run_in_background()` and `run_on_ui_thread()`
- [ ] Qt uses signal/slot or an event queue to return to the UI thread
- [ ] Jupyter uses the asyncio/IPython event loop to safely update widgets
- [ ] Support progress, cancellation, timeout, error callbacks, and completion callbacks
- [ ] New tasks can cancel old tasks to prevent stale results from overwriting new ones during rapid filtering or CSG parameter changes
- [ ] When a page route is left or a component is destroyed, its tasks are automatically cancelled
- [ ] Reserve a process pool execution strategy for CPU-intensive CSG to avoid GIL contention and UI jank

## P1: Admin Foundation Components

### Pages and Navigation

- [ ] `AppShell`: top bar, sidebar, main content area, status bar
- [ ] `Sidebar` / `NavMenu`: icons, grouping, selected state, collapsed state
- [ ] `Page` / `Router` / `RouterView`: page registration, matching, navigation, and content area rendering
- [ ] `Breadcrumb`: breadcrumb navigation
- [ ] `Toolbar`: page title, primary actions, secondary actions
- [ ] `Spacer` / `Divider` / `ScrollArea`
- [ ] Respond to window width changes: at minimum support Sidebar expand and collapse

### Router

The first version uses "in-process routing": UniUI maintains the current path and history; business code does not touch native navigation APIs in Qt or Jupyter.

- [ ] Add `Router`, `Route`, `RouterView`, and `Link` public interfaces
- [ ] Support static paths: `/dashboard`, `/users`
- [ ] Support path parameters: `/users/:id`
- [ ] Support query parameters: `/users?page=2&status=active`
- [ ] Support named routes to avoid hardcoded paths throughout business code
- [ ] Support `push()`, `replace()`, `back()`, `forward()`
- [ ] Support default routes, 404 pages, and redirects
- [ ] Sync Sidebar selected state, page title, and Breadcrumb on route changes
- [ ] Support navigation guards: confirm before leaving unsaved forms, redirect on missing permissions
- [ ] Pages are lazily created by default; allow configuring whether page instances are cached
- [ ] Cancel timers, data subscriptions, and background tasks when a page is left, to avoid resource leaks
  - [x] Widget-tree leak fixed (2026-08-17): `RouterView` no longer accumulates an unbounded `IOverlay` layer per uncached navigation. `IOverlay` gained `remove_layer(index)`/`layer_count()`; `RouterView` tracks the single currently-mounted disposable (non-cached) layer and removes it right before the next layer is added, remapping cached-page indices. Cached pages are never touched. Verified across Qt/Jupyter/Web. Still open: timers/subscriptions/background tasks *inside* a page are not auto-cancelled on navigation away — that's a separate mechanism from this fix.
- [ ] Route callbacks and page factories receive a unified `RouteContext`

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

- [ ] Qt: `RouterView` uses `QStackedWidget` or equivalent to switch pages
- [ ] Jupyter: update the container's `children`, preserving the same route lifecycle semantics
- [ ] Jupyter URL/hash sync is an optional enhancement; core routing does not depend on browser capabilities
- [ ] Core route matching and history remain pure Python for easy independent testing

### Data Display

- [ ] `Card`: title, subtitle, content, action area
- [ ] `StatCard`: metric value, unit, trend, status color
- [ ] `Badge` / `Tag`: status labels
- [ ] `ProgressBar`
- [ ] `Table` / `DataGrid`:
  - [ ] Declare columns and bind row data
  - [ ] Custom cell formatting
  - [ ] Sorting
  - [ ] Single/multi-select
  - [ ] Pagination
  - [ ] Empty, loading, and error states
  - [ ] Row action buttons
- [ ] `Pagination`

### Forms and Feedback

- [ ] `Checkbox`, `RadioGroup`, `NumberInput`, `DateInput`
- [ ] `Form`: field registration, submit, reset
- [ ] Validation rules and field-level error messages
- [ ] `Modal` / `Dialog`: confirmation and edit forms
- [ ] `Toast` / `Notification`
- [ ] `Loading` / `Skeleton`

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
- [ ] Support empty data, loading, and render error states
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

- [ ] Compare Plotly, ECharts, and Matplotlib for Qt/Jupyter consistency, package size, offline capability, and packaging complexity
- [ ] Place chart dependencies in an optional extra, e.g. `uniui[charts]`
- [x] Implement Qt renderer
- [x] Implement Jupyter renderer
- [x] Provide `set_data()` to refresh data without replacing the component instance
- [x] Provide `append_data()` for real-time monitoring charts
- [x] Cap the number of real-time data points to prevent memory growth over long runs
- [ ] Support PNG/SVG export (can move to P2)
- [ ] Raise `NotSupportedError` with installation instructions when chart dependencies are missing

## P1: 2D / 3D Visualization

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
- [ ] Permission-driven menu and button visibility
- [ ] Keyboard navigation and basic accessibility support
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

- [ ] Establish unified design tokens: colors, spacing, border radius, font sizes, shadows, and status colors
- [ ] Establish an icon system to avoid each example mixing Unicode icons ad hoc
- [ ] All data components provide standard Loading, Empty, Error, and Success states
- [ ] Support high DPI, font scaling, keyboard focus, and sensible Tab order
- [ ] Primary components provide consistent compact/standard density modes
- [ ] Theme switching does not flicker and does not lose table, route, chart, or 3D scene state

## Architecture and Code Changes

- [ ] Add new component interfaces in `core.py`; keep interfaces describing only cross-backend capabilities
- [ ] Implement adapters separately in `qt.py` and `jupyter.py`
- [ ] Expose declarative constructor functions in `__init__.py`
- [ ] Split complex components into dedicated modules to avoid growing single backend files further
- [ ] Place 2D/3D scene models, CSG kernel adapters, and renderers in separate sub-packages
- [ ] Establish a component registry to reduce boilerplate in the factory
- [ ] Legacy backends must uniformly raise `NotSupportedError` for new components; no further expansion
- [ ] Update optional dependencies and package metadata in `pyproject.toml`
- [ ] Update the component support matrix in README
- [ ] Fix references to non-existent modules and outdated architecture diagrams in documentation
- [ ] Fix package description, keywords, classifiers, and project URLs; remove placeholder addresses
- [ ] Separate installation commands for end users and developers in docs: `.[qt]`, `.[jupyter]`, `.[dev]`

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

- [ ] Maintain compatibility for existing top-level imports, e.g. `from uniui import Button`
- [ ] Introduce new modules via compatibility shims first; avoid one-shot large-scale migration
- [ ] Define capability probing for optional modules, e.g. `supports("csg")`
- [ ] Define a stable serialization format for router state, chart configuration, and scene persistence

## Recommended Implementation Order

### M0: Engineering Foundation

- [ ] Fix and unify duplicate/missing methods in existing component interfaces
- [ ] Migrate to PySide6; remove hardcoded PySide2 references from core flows
- [ ] Main CI and contract tests treat only Qt/Jupyter as official backends
- [ ] Clean up inconsistencies in README, architecture docs, package metadata, and installation instructions
- [ ] Establish lifecycle, capability, and backend contract
- [ ] Extract a progressively migratable new module structure

### M1: Adaptive Layout

- [ ] Complete `LayoutSpec`, `SizeSpec`, and `LayoutItem`
- [ ] Complete `Row`, `Column`, `Grid`, `Wrap`, `ScrollView`, `SplitPane`, and `Overlay`
- [ ] Complete Qt `QSizePolicy` / stretch / breakpoint renderer
- [ ] Complete Jupyter Flex/Grid/container responsive renderer
- [ ] Pass the three-width cross-backend layout acceptance criteria before starting new complex business components

### M2: State and Scheduling

- [ ] Complete `State`, `Computed`, binding, and `TaskRunner`
- [ ] End-to-end validation with existing `Label`, `LineEdit`, and `Dropdown`
- [ ] Confirm consistent thread and event loop behavior between Qt and Jupyter

### M3: Admin Skeleton

- [ ] Complete `AppShell`, `Sidebar`, `Router`, `RouterView`, `Breadcrumb`
- [ ] Complete `Card`, `StatCard`, basic `Table`, and loading/error feedback
- [ ] Deliver the first navigable Admin example

### M4: Data Dashboard

- [ ] Complete `DataSource`, pagination/filtering, `Chart`, and dynamic updates
- [ ] Complete theme integration and Dashboard auto-refresh
- [ ] Admin example connected to a simulated async data source

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
- [ ] Ruff, format checks, and pytest must block non-conforming commits
- [ ] Gradually enable strict mypy; stop using `|| true` to suppress type errors
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
- [ ] Layout size, flex, spacing, alignment, Grid span, and child order have pure model tests
- [x] Qt correctly switches layout mode at container widths of 640, 900, and 1440
- [ ] Jupyter Flex/Grid generates key layout attributes that conform to the public `LayoutSpec`
- [x] Breakpoint switches do not destroy components with stable keys
- [ ] Continuous resize does not trigger CSG recomputation or duplicate data requests
- [ ] Jupyter resize bridging is debounced and does not generate high-frequency comm messages
- [ ] Key Admin pages have visual snapshot regression tests at compact/medium/wide
- [ ] `State` / `Computed` dependency updates, batching, unsubscribe, and cycle detection have unit tests
- [ ] Background task completion, failure, cancellation, timeout, and "new result overwrites old" rule have tests
- [ ] State subscriptions, timers, and tasks are all released after a page is destroyed
- [ ] `DataSource` pagination, sorting, filtering, caching, and error states have tests
- [ ] Route matching, parameter parsing, query parameters, redirects, 404, and history have unit tests
- [ ] Navigating to the same path in Qt and Jupyter renders equivalent pages
- [ ] Rapid consecutive navigation does not duplicate cached pages or leave behind page tasks
- [ ] Chart configuration validation, empty data, and invalid data have unit tests
- [ ] Dynamic chart updates do not create duplicate event listeners or duplicate native widgets
- [ ] 2D primitive coordinates, transforms, layering, and event hit-testing have unit tests
- [ ] 3D transforms, camera state, and object selection have contract tests
- [ ] CSG boolean results on standard primitives pass volume and mesh topology validation
- [ ] Degenerate CSG inputs, non-manifold meshes, and computation failures do not crash the UI
- [ ] Qt and Jupyter displaying the same CSG model produce consistent vertex/face data
- [ ] Released 3D scene and CSG background tasks leave no lingering threads or large mesh allocations
- [ ] After a theme switch, Admin components, charts, and 2D/3D Viewports update their colors in sync
- [ ] Interaction is acceptable with a 1000-row table and typical chart data volumes
- [ ] Core package imports and functions correctly when optional dependencies are absent
- [ ] Permission-based hiding affects only the UI; the example service layer still validates permissions independently
- [ ] Corrupted or outdated settings files can be safely migrated or reset to defaults
- [ ] Add a complete `examples/admin_dashboard.py`
- [ ] Add `examples/csg_demo.py`: parametric input, drilled solid, live preview, and STL export
- [ ] Add flagship application `examples/engineering_console.py`
- [ ] Flagship app includes Dashboard, task table, model browser, CSG Editor, and Settings routes
- [ ] Flagship app uses the same `DataSource` to drive `StatCard`, `DataGrid`, and `Chart`
- [ ] Flagship app demonstrates async loading, error recovery, permission control, theming, and settings persistence
- [ ] Examples include at minimum: sidebar, 4 StatCards, filter bar, DataGrid, line chart, pie chart, theme toggle, and auto-refresh
- [ ] Examples run with `--ui qt` using the same code and can be displayed in Jupyter

## First Deliverable (MVP)

- [ ] `Row` / `Column` / `Grid` / `Wrap`
- [ ] `ScrollView` / `SplitPane` / `Overlay`
- [ ] Unified sizing, grow/shrink, gap/padding, and responsive breakpoints
- [ ] Qt/Jupyter three-tier adaptive layout contract
- [ ] `Card` / `StatCard`
- [ ] `Table` (static data, sorting, pagination)
- [ ] `Sidebar` + `AppShell`
- [ ] `Router` + `RouterView` (static paths, path parameters, 404, forward/back)
- [ ] `Chart` (line, bar, pie)
- [ ] Chart `set_data()` dynamic updates
- [ ] `Viewport3D` + Box/Sphere/Cylinder/Mesh
- [ ] CSG union/difference/intersection and STL export
- [ ] Qt/Jupyter dual-backend with theme support
- [ ] Admin Dashboard example and tests

## Definition of Done

When a user can write Python code with no Qt or ipywidgets branch conditions, create a backend page with navigation, metric cards, a filterable table, a dynamic chart, and a 3D CSG Viewport, perform solid union/difference/intersection and STL export, and run the same code in both Qt and Jupyter — this goal is complete.
