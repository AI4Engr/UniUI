# UniUI `src` Refactor Plan

This document is an implementation brief for Claude. Refactor the source tree
without changing public behavior or the current UI appearance.

## Objective

Replace the current large backend modules with a component-oriented structure:

- shared state and rules live in pure-Python models;
- each backend keeps its native widget, adapter, events, and local CSS/QSS
  together;
- optional backend dependencies remain isolated and lazily imported;
- existing public imports remain compatible.

Do not perform a large one-shot rewrite. Complete one vertical component slice
at a time and run tests after every slice.

## Current problems

- `jupyter_components.py`, `qt_components.py`, and `web_components.py` contain
  every Admin component, styling, theme refresh, and factory registration.
- Status classification, StatCard trends, Chart state, Gauge state, Table data,
  Sidebar state, and Breadcrumb state are repeated across backends.
- Jupyter base styles exist in `jupyter.py`, `jupyter_style.py`, and
  `jupyter_components.py`.
- `core.py`, `display.py`, and `__init__.py` each contain several unrelated
  responsibilities.
- `docs/architecture.md` describes modules that no longer exist.

Existing good shared modules should be preserved and extended:

- `_adapter_mixins.py`
- `theme_runtime.py`
- `visuals.py`
- `icons.py`

## Target structure

```text
src/uniui/
  __init__.py                 # public re-exports only
  factory.py                  # backend detection, use(), create_factory()
  facade.py                   # Label(), Button(), Card(), UniUI, etc.

  contracts/
    primitives.py             # Label, Button, Input interfaces
    layouts.py                # VBox, Grid, Wrap, Overlay interfaces
    components.py             # Card, Table, Sidebar, AppShell, etc.
    factory.py                # IWidgetFactory

  models/
    status.py                 # semantic status normalization
    stat_card.py              # trend/status presentation model
    chart.py                  # x/series/max_points state
    gauge.py                  # range/value/status state
    table.py                  # columns/rows/loading/error state
    navigation.py             # sidebar items/active/collapsed state
    breadcrumb.py             # breadcrumb item/path state

  shared/
    theme.py
    theme_runtime.py
    themed_targets.py
    icons.py
    visuals.py
    browser_css.py            # CSS variables and icon-mask helpers only

  backends/
    qt/
      factory.py
      display.py
      primitives/
      layouts/
      components/
        card.py               # QtCardAdapter + card QSS
        stat_card.py
        metric_list.py
        table.py
        gauge.py
        chart.py
        drawer.py
        sidebar.py
        breadcrumb.py
        app_shell.py
      styles.py               # explicitly combines component style fragments

    jupyter/
      factory.py
      display.py
      primitives/
      layouts/
      components/
        card.py               # JupyterCardAdapter + card CSS
        stat_card.py
        metric_list.py
        table.py
        gauge.py
        chart.py
        drawer.py
        sidebar.py
        breadcrumb.py
        app_shell.py
      styles.py

    web/
      factory.py
      display.py
      primitives/
      layouts/
      components/
      styles.py

    tk/
    wx/
```

The old modules (`qt.py`, `jupyter.py`, `web.py`, `qt_components.py`,
`jupyter_components.py`, and `web_components.py`) must remain as compatibility
modules until the migration is complete. They should re-export the new classes
instead of containing duplicate implementations.

## Dependency rules

Enforce this direction:

```text
public API -> contracts/models -> selected backend factory -> backend component
backend component -> contract + model + shared helpers + native toolkit
```

Rules:

1. `contracts`, `models`, and `shared` must not import a backend toolkit.
2. Importing `uniui` must not import PySide2, NiceGUI, or ipywidgets eagerly.
3. A Qt module must not import Jupyter or Web modules, and vice versa.
4. Shared behavior should use composition through models, not a large
   cross-backend Adapter superclass.
5. Keep explicit factory creation methods. Do not introduce a magical dynamic
   component registry solely to remove a few short methods.

## What to merge

### Status rules

Create one semantic status definition. It must normalize values such as:

- success: `active`, `delivered`, `shipped`, `success`, `ok`
- warning: `processing`, `pending`, `warning`, `warn`
- error: `inactive`, `cancelled`, `failed`, `error`
- everything else: `neutral`

Backends receive only the semantic result and map it to their native style.

### StatCard

Create a `StatCardModel` that owns label, value, unit, trend, and status.
Trend formatting and direction must be shared. The model returns plain text and
semantic style names; HTML escaping remains the responsibility of the backend.

### Chart and Gauge

Move Chart and Gauge state into models. Reuse the existing functions in
`visuals.py`. Backends should only render the model using QPainter, SVG, or
native HTML.

### Table

Create a `TableModel` for columns, rows, loading, error, and row lookup. Move
status classification and numeric-column decisions out of backend renderers.
Keep native table events and HTML generation in backend files.

### Navigation and Breadcrumb

Move keys, labels, icons, active item, collapsed state, and breadcrumb path
normalization into shared models. Native buttons and layout remain backend
specific.

### Theme targets

Replace repeated backend WeakSet/apply-theme loops with a small shared
`ThemeTargetRegistry`. Keep the existing global state machine in
`theme_runtime.py`.

### Browser style helpers

Jupyter and Web may share:

- CSS variable generation;
- icon-mask declarations;
- semantic class names;
- token and metric conversion.

Do not share complete CSS selectors because their DOM structures differ.

## What not to merge

Keep these backend specific:

- Qt QPainter rendering and QSS;
- Jupyter widget-tree compatibility workarounds;
- NiceGUI slots and JavaScript;
- AppShell layout implementation;
- Drawer animation and event plumbing;
- native Table click/selection events;
- toolkit-specific lifecycle and disposal code.

## Component file rule

For a given backend, keep one component's implementation and styling together.
For example, `backends/jupyter/components/table.py` should contain:

- `JupyterTableAdapter`;
- table HTML rendering;
- row-click bridge;
- Jupyter-specific loading/error presentation;
- the Table CSS fragment.

`backends/jupyter/styles.py` should only combine exported style fragments. It
must not become another large file containing every component's CSS.

## Migration phases

### Phase 0: baseline

1. Record `git status --short` and preserve unrelated work.
2. Run the current full test suite and record the result.
3. Add import-isolation tests proving that importing `uniui` does not eagerly
   import optional toolkits.
4. Do not change behavior in this phase.

### Phase 1: shared models

Implement pure-Python models while keeping the existing files in place.
Migrate in this order:

1. status and StatCard;
2. Gauge and Chart;
3. Table;
4. Navigation and Breadcrumb.

For each model:

- add backend-independent unit tests;
- migrate Qt, Jupyter, and Web adapters to use it;
- remove the old duplicate logic;
- run all related backend tests before continuing.

### Phase 2: split Admin components

Create `backends/<backend>/components/` and move one component at a time in
this order:

1. StatCard;
2. Gauge and Chart;
3. Table and MetricList;
4. Card and Drawer;
5. Breadcrumb and Sidebar;
6. AppShell last.

Every moved component must include its backend-specific style fragment. Keep a
compatibility re-export in the old `*_components.py` module immediately after
each move.

### Phase 3: consolidate styles

1. Merge Jupyter base-control CSS generation into one style builder with
   explicit scopes for plain widgets and Admin shells.
2. Extract shared CSS-variable and icon-mask helpers for Jupyter and Web.
3. Keep Qt QSS local to each Qt component.
4. Verify that light/dark output and responsive behavior do not change.

### Phase 4: split primitive backends

After Admin components are stable, split large primitive modules by category:

- text/display controls;
- input controls;
- layouts and containers;
- factory;
- display integration.

Apply this to Qt, Jupyter, Web, Tk, and wx incrementally. Preserve old module
imports through re-exports.

### Phase 5: public API cleanup

1. Move backend detection and factory selection out of `__init__.py`.
2. Move convenience constructors and `UniUI` into `facade.py`.
3. Split contracts out of `core.py`.
4. Keep `uniui.__init__` as the stable public re-export surface.
5. Keep both snake_case and camelCase APIs compatible. Generate compatibility
   aliases in one place instead of duplicating every factory method manually.

### Phase 6: cleanup and documentation

1. Remove compatibility implementations only after all imports have migrated.
2. Delete dead style generators and duplicate theme flags.
3. Update `docs/architecture.md` to match the real dependency graph.
4. Add a short guide explaining where a new component and its styles belong.

## Required checks after every phase

At minimum run:

```text
python -m pytest -q -p no:cacheprovider
python -m py_compile <changed Python files>
git diff --check
```

Also run the contract suite against every installed backend, especially Qt,
Jupyter, and Web. If a backend dependency is unavailable, record that clearly
instead of silently skipping verification.

## Compatibility requirements

The following must continue to work:

- `from uniui import Label, Button, VBox, Card, Table, AppShell`
- `create_factory("qt")`
- `create_factory("jupyter")`
- `create_factory("web")`
- existing snake_case factory methods;
- existing camelCase factory methods;
- existing examples and Notebook usage;
- current light/dark themes and responsive behavior.

Do not rename CSS classes or public adapter classes unless a compatibility
alias is provided.

## Definition of done

- No Admin backend has a single mega-file containing all components and all
  styles.
- Shared status, trend, chart, gauge, table, and navigation rules exist only
  once.
- Component-specific CSS/QSS lives beside that backend's component.
- Backend dependencies remain lazy and isolated.
- Old public imports still work through compatibility re-exports.
- Full tests pass with no new warnings.
- `docs/architecture.md` describes the final structure accurately.

