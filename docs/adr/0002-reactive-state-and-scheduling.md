# ADR 0002: Reactive state, background tasks, and UI-thread scheduling

## Status

Accepted (already implemented — this ADR documents a shipped decision).

## Context

TODO.md's P0 backlog asked for an ADR deciding the reactive-state, async-task,
and UI-thread-scheduling model before those pieces shipped. `State`/`Computed`
(`src/uniui/state.py`), `TaskRunner` (same file), and `schedule_after()`
(`src/uniui/display.py` + a per-backend leg in `backends/{qt,web}/display.py`)
have since been implemented and are in active use (e.g. `bind_text`/
`bind_value`/`bind_items`/`bind_enabled`/`bind_visible`), so this ADR records
the decision as built.

The core constraint: UniUI runs under three fundamentally different
concurrency models — Qt's own event loop and thread affinity rules, a Jupyter
kernel's `asyncio` event loop, and NiceGUI's `asyncio`-based server — and
needs one reactive-state API and one "run this in the background, then touch
the UI" API that behaves correctly under all three without app code branching
on which backend is active.

## Decision

**Reactive state: plain Python objects, not a dependency, not a metaclass.**

- `State[T]` (`state.py`) is a mutable value with `.value`, `.set(value)`,
  and `.subscribe(fn) -> Handle`. Equality-gated (`set()` is a no-op if the
  new value equals the old one) so subscribers aren't asked to react to
  no-op writes.
- `Computed[T]` is a read-only value derived from one or more `State`
  dependencies via `dep.subscribe(lambda _: self._recompute())` — pull-based
  recomputation triggered by push-based dependency notification, not a
  reactive-graph/signals library. No dependency auto-tracking: `Computed`'s
  dependencies are passed explicitly (`Computed(fn, *deps)`), not inferred by
  intercepting attribute reads.
- `bind_text`/`bind_value`/`bind_items`/`bind_enabled`/`bind_visible`
  (`state.py`) are the one-way (and, for `bind_value`, two-way) glue between
  a `State` and a widget — thin wrappers around `.subscribe()`, not a
  separate binding engine.
- Every subscription returns a `Handle` (`Handle(cancel_fn)`, idempotent
  `.dispose()`) — the same disposable-subscription shape used for every
  `on_*` widget callback (see `docs/architecture.md`'s "Event handling"
  section) and `Router.on_navigate()`. One shape for every kind of
  subscription in the codebase, not a separate pattern for state vs. events
  vs. routing.
- Every dispatch (`State.set`, `Computed._recompute`) routes through
  `uniui.state.safe_call()` — a raising subscriber is logged, not
  propagated, and does not stop sibling subscribers.

**Background tasks: `TaskRunner`, one daemon thread, results posted back via
`schedule_after`.**

- `TaskRunner.run(fn, on_done, on_error)` starts `fn` on a `daemon=True`
  `threading.Thread`, regardless of backend — no backend-specific thread
  pool or `asyncio.Task`, because Qt widgets cannot be touched off the Qt
  main thread and a single `threading.Thread` is the one primitive that
  behaves the same under Qt, a Jupyter kernel, and a NiceGUI server.
- `fn`'s signature is `fn(cancelled: threading.Event) -> result` — the
  runner hands `fn` a cancellation flag rather than killing the thread, since
  Python threads cannot be forcibly cancelled.
- `on_done`/`on_error` are **not** called directly from the background
  thread — they're posted back via `schedule_after(0, ...)`, which is what
  actually crosses back onto whichever thread/loop each backend requires
  (see below). This is the one rule that makes `TaskRunner` safe to use
  identically from all three backends: never touch a widget from the
  worker thread, always post the callback.
- Calling `.run()` again implicitly cancels the previous run
  (`self.cancel()` at the top of `run()`) — `TaskRunner` models "at most one
  in-flight task per instance," not a queue.

**UI-thread scheduling: `schedule_after(ms, callback)`, backend-probed, with
an `asyncio` fallback for Jupyter and a `threading.Timer` fallback for
everything else.**

- Order of attempts, each cheap and side-effect-free to probe:
  1. **Web** — only checked if `sys.modules` already shows NiceGUI's theming
     module imported (probing `sys.modules` rather than importing keeps this
     branch a no-op when Web was never selected, so a Qt-only process never
     pulls NiceGUI in just to ask "is this Web?").
  2. **Qt** — relayed through a `QObject` cached on the `QApplication`
     instance (`_uniui_dispatcher`) using a Qt signal, because
     `QTimer.singleShot` called from a non-Qt thread is silently ignored;
     the signal relay is what makes `schedule_after` safely callable from
     `TaskRunner`'s background thread.
  3. **Jupyter/asyncio** — deliberately inlined in `display.py` itself
     rather than delegated to `backends/jupyter/display.py`, specifically so
     this check stays toolkit-free (no ipywidgets import) and doesn't drag
     ipywidgets into every Qt or fallback schedule. The check is just "is
     there a running `asyncio` loop" — a notebook kernel always provides
     one, so this needs no Jupyter-specific import at all.
  4. **Fallback** — a daemon `threading.Timer`, for any context with none of
     the above (headless scripts, tests).
- Each backend leg returns `True`/`False` for "did I accept this," so
  `display.py`'s `schedule_after` owns only the *order* and the final
  fallback, not any backend-specific scheduling logic itself.

## Consequences

- **No reactive/state-management dependency** (no MobX-style proxies, no
  signals library) — `State`/`Computed` are ~80 lines of plain Python,
  auditable and debuggable without stepping through a third-party reactivity
  engine.
- **`Computed` requires explicit dependencies.** Missing one in
  `Computed(fn, *deps)` means a stale value that silently doesn't update —
  there is no dependency-tracking safety net. This is a known sharp edge,
  not an oversight: automatic tracking would mean instrumenting `State`
  reads, which conflicts with "plain Python objects."
- **`TaskRunner` is single-flight per instance.** Code that needs concurrent
  background work uses multiple `TaskRunner` instances, not one runner with
  a queue — callers own that decision, `TaskRunner` doesn't hide it.
- **`schedule_after`'s Jupyter leg trusts "any running loop."** In an
  environment that runs an unrelated `asyncio` loop without also being a
  real Jupyter kernel, this would schedule via that loop rather than falling
  through to the `threading.Timer` fallback — considered acceptable since
  the only realistic case of "a running loop that isn't Jupyter and isn't
  Web" during a Qt/desktop run is nested event-loop testing, not production
  usage.
