# Plan: remove Qt-specific page code from `examples/admin_demo.py`

**Status:** ready to execute
**Goal:** `admin_demo.py`'s *pages* contain zero `PySide2` / `QtWidgets` code and are
shared by Qt, Jupyter, and Web — closing the P0 item at TODO.md line 22
("Qt is not actually sharing code with Jupyter yet").

---

## Background: why this is needed

`admin_demo.py` currently has **two parallel implementations of the same four
pages**:

| page | Qt version | browser version |
|---|---|---|
| dashboard | `dashboard_page` (207 lines, raw PySide2) | `_browser_dashboard_page` (126 lines, cross-backend) |
| users | `users_page` (48) | `_browser_users_page` (47) |
| settings | `settings_page` (56) | `_browser_settings_page` (46) |
| components | `components_page` (140) | `_browser_components_page` (95) |
| helpers | `_page_frame` (52), `_qt_labeled_field` (14) | `_browser_page_frame` (36), `_labeled_field` (13) |
| **total** | **~536 lines** | **~369 lines** |

**The duplication is not justified by any Qt-only capability.** The complete set
of raw Qt widgets the Qt pages use is:

```
QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout
```

Every one already has a cross-backend equivalent: `VBox`, `HBox`, `Label`,
`Grid`, `Wrap`.

**Proof this works:** `examples/component_gallery.py` is 490 lines with **zero**
Qt references, runs unmodified on all three backends, and already demonstrates
Card, Table, Chart, Gauge, TabWidget, Grid, Wrap, SplitPane, GroupBox — a
strictly harder set than admin_demo's pages need.

Even the one non-trivial Qt widget, the 36-line `_ResponsiveStats` (a
`QGridLayout` subclass that reflows stat cards at 440px/720px breakpoints), is
reinventing `create_wrap()` — which the browser dashboard already uses for the
*identical* responsive-stat-card problem, and which Qt implements via a real
flow layout (`QtWrapAdapter` / `_QFlowLayout`).

---

## Step 0 — revert the bad in-progress edit (do this first)

The working tree currently has an **uncommitted, unwanted** change to
`components_page` that added *more* raw-Qt code (a `more_card` built from raw
`QtWidgets.QWidget` + `QVBoxLayout` + `QHBoxLayout`, plus `notify_switch` /
`compact_checkbox` wired through `_qt_labeled_field`). It makes this exact
problem worse.

```bash
git checkout -- examples/admin_demo.py
```

Verify `git status` is clean and the suite still passes (**1231 passed**)
before starting Step 1. Do not build on top of that edit.

---

## Step 1 — unify the four pages (the main work)

For each of dashboard / users / settings / components:

1. **Delete** the Qt version (`dashboard_page`, `users_page`, `settings_page`,
   `components_page`, `not_found_page`).
2. **Rename** the browser version to the plain name
   (`_browser_dashboard_page` → `dashboard_page`, etc.).
3. Point **both** routers at the single implementation. After this,
   `_build_qt_router()` and the router inside `create_admin_ui()` should list
   identical page functions — consider collapsing them into one shared
   `_build_router()` used by both.
4. Delete the now-unused Qt helpers: `_page_frame`, `_qt_labeled_field`,
   `_ResponsiveStats`. Rename `_browser_page_frame` → `_page_frame` and
   `_labeled_field` stays as-is.
5. `_NativeWrap` — check whether anything still uses it after the pages are
   gone. The Qt **shell** (Step 3) may still need it; if so keep it, otherwise
   delete it.

### Behavioral differences that MUST be preserved

These are real features in the Qt version that the browser version lacks. Do
**not** silently drop them — port them into the unified page:

- **`TaskRunner` async refresh (Qt dashboard only).** `dashboard_page` runs its
  refresh through `TaskRunner` with `_fetch` / `_on_done` / `on_error`, so the
  UI stays responsive. `_browser_dashboard_page`'s `refresh()` is synchronous.
  Keep the `TaskRunner` version — it's cross-backend (`uniui.state.TaskRunner`)
  and is the better behavior on every backend.
- **The "Live updates" Switch** gating `_live_tick` exists in *both* — keep it.
- **The `/settings` `cache=True`** on both routes — keep it. It fixes a real
  subscription-leak crash; there is a regression test
  (`test_qt_admin_demo_settings_route_survives_repeated_visits_and_theme_toggle`)
  that will fail if it's dropped.
- **Theme picker** (`uniui.list_themes()` + `_apply_named_theme`) exists in both
  and is already identical — keep one copy.

### Watch out for

- `_add_class(...)` / `_set_props(...)` / `_set_icon_class(...)` are browser-only
  helpers that **no-op safely on Qt** (they feature-detect `add_class` /
  `classes` / `props`). They are safe to keep in the unified pages — verify this
  by actually running `--ui qt` rather than assuming.
- `_qt_labeled_field(title, control_native)` takes a **native** widget;
  `_labeled_field(label_text, control)` takes the **adapter**. When merging, use
  the adapter form.

---

## Step 2 — add the new widgets ONCE (the original request)

Only after Step 1 is green. In the now-single `components_page`, using the
cross-backend API only (`f.create_switch()`, `f.create_checkbox()`, etc. — no
`QtWidgets`):

- Replace the two fake `create_button()` toggles in the Settings tab
  ("Notifications: On", "Compact density: Off" — buttons pretending to be
  toggles) with a real `Switch` and `Checkbox`.
- Add a "More controls" card demonstrating `RadioGroup` (table density),
  `NumberInput` (rows per page), and `Slider` (refresh interval, with a live
  "Every Ns" label driven by `on_change`).

Each must do something real and observable, matching the gallery's
"real interaction, not a screenshot" principle.

---

## Step 3 — shell unification (SEPARATE, do NOT bundle into this change)

The **shell** is also duplicated (`create_admin_ui()` ~119 lines browser vs.
`main()`'s Qt shell ~205 lines), but it is a genuinely harder, riskier job and
has real Qt-only pieces that must stay Qt-only:

- `_admin_stylesheet()` (QSS) — legitimately Qt-only.
- `_QT_RESTYLE_HOOK` / `_restyle_shell` — Qt's stylesheet is a one-shot string,
  unlike Web's live CSS variables; this hook is genuinely needed.
- `_ResponsiveTopBar` (`QToolBar` + `QAction` header) — no cross-backend
  equivalent exists today.
- `_header_icon()` — Qt-only icon rendering.

**Do not attempt Step 3 in the same commit as Steps 0–2.** Land the page
unification first, confirm it's green, then evaluate the shell separately.

---

## Verification (required before commit)

1. `python -m pytest -q --no-cov` — must stay at **1231 passed** (or higher if
   tests are added). No new failures.
2. Run all three backends and confirm every page renders and is interactive:
   ```
   python examples/admin_demo.py --ui qt
   python examples/admin_demo.py --ui web
   ```
   For Qt, grab a screenshot of each of the four pages and actually look at it —
   do not assume "it built without raising" means "it renders correctly."
   Several bugs this session (clipped tab labels, oversized badge, black combo
   popup) were invisible to the test suite and only caught by looking.
3. `python -m pytest tests/test_web_backend.py -k smoke -q --no-cov -n0` —
   the admin_demo web smoke test must still pass.
4. **Prove the goal:** `grep -c "PySide2\|QtWidgets" examples/admin_demo.py`
   should drop from 72 to only the shell's usages (Step 3 territory), and
   **zero** of them should be inside a `*_page` function.
5. Sabotage-verify anything you fix, per the standing convention.

## TODO.md

Update line 22 ("The same business code runs in both Qt and Jupyter") once
Step 1 lands — it can finally be checked off for the *pages*, with a note that
the *shell* is still split (Step 3).
