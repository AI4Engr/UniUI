"""
Reactive state layer for UniUI.

Pure Python — no backend dependencies. Works with Qt, Jupyter, and Web.
"""
from typing import TypeVar, Generic, Callable, Dict, List, Optional, Tuple
import logging
import threading

T = TypeVar("T")

_logger = logging.getLogger("uniui.events")


def safe_call(callback: Callable, *args, backend: str, component: str, method: str, **kwargs):
    """Invoke a user callback, logging (not propagating) any exception it raises.

    Keeps one failing subscriber from aborting sibling subscribers in a
    multi-subscriber dispatch loop, and from propagating into unrelated
    caller code (state.set(), router.push(), a Qt signal emission). Logged
    at ERROR with the full traceback, so it surfaces on stderr by default
    (Python's "handler of last resort") without forcing a project-wide
    logging setup.
    """
    try:
        return callback(*args, **kwargs)
    except Exception:
        _logger.exception(
            "Unhandled exception in %s.%s callback (%s)", component, method, backend
        )
        return None


class Handle:
    """Disposable subscription handle returned by subscribe() and bind_*()."""

    def __init__(self, cancel: Callable[[], None]):
        self._cancel = cancel
        self._disposed = False

    def dispose(self) -> None:
        if not self._disposed:
            self._disposed = True
            self._cancel()


#: > 0 while inside a batch() block. Module-level, not per-State: batching is
#: a UI-thread-only concept, same assumption schedule_after() already makes.
_batch_depth = 0
#: id(state) -> (state, value) for State.set() calls made during a batch,
#: keyed by identity so N sets on the same State during one batch collapse
#: to its single final value instead of firing N notifications.
_pending: Dict[int, Tuple["State", object]] = {}


class batch:
    """Context manager: defer State notifications until the outermost
    ``batch()`` block exits, coalescing repeated ``set()`` calls on the same
    State into a single notification - "one business operation triggers at
    most one necessary redraw."

    ``.value`` always reflects the latest write immediately; only the
    subscriber notification is deferred. A ``Computed`` that depends on a
    batched State is a subscriber like any other, so it also only recomputes
    once, at flush time - not once per intermediate ``set()`` call.

    Nested batches are flattened: only the outermost block flushes. If a
    State is set back to a value that nets out unchanged from before the
    batch started, subscribers still fire once with that value - batching
    only removes *redundant intermediate* notifications, not net-zero ones.
    """

    def __enter__(self) -> "batch":
        global _batch_depth
        _batch_depth += 1
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        global _batch_depth
        _batch_depth -= 1
        if _batch_depth == 0 and _pending:
            pending = list(_pending.values())
            _pending.clear()
            for instance, value in pending:
                instance._notify(value)


class State(Generic[T]):
    """Mutable reactive value. Subscribers are notified when value changes."""

    def __init__(self, value: T):
        self._value: T = value
        self._subscribers: List[Callable[[T], None]] = []
        self._updating = False

    @property
    def value(self) -> T:
        return self._value

    def set(self, value: T) -> None:
        if value == self._value:
            return
        self._value = value
        if _batch_depth > 0:
            _pending[id(self)] = (self, value)
            return
        self._notify(value)

    def _notify(self, value: T) -> None:
        if self._updating:
            raise RuntimeError(
                "Circular State update detected: a subscriber triggered "
                "set() on this same State before its previous set() finished "
                "notifying subscribers. Break the cycle in your subscriber "
                "(e.g. only forward a value when it actually changes)."
            )
        self._updating = True
        try:
            for fn in list(self._subscribers):
                safe_call(fn, value, backend="core", component="State", method="subscribe")
        finally:
            self._updating = False

    def subscribe(self, fn: Callable[[T], None]) -> Handle:
        self._subscribers.append(fn)
        def cancel():
            if fn in self._subscribers:
                self._subscribers.remove(fn)
        return Handle(cancel)


class Computed(Generic[T]):
    """Read-only reactive value derived from one or more State dependencies."""

    def __init__(self, fn: Callable[[], T], *deps: State):
        self._fn = fn
        self._value: T = fn()
        self._subscribers: List[Callable[[T], None]] = []
        self._dep_handles: List[Handle] = []
        self._updating = False
        for dep in deps:
            h = dep.subscribe(lambda _: self._recompute())
            self._dep_handles.append(h)

    @property
    def value(self) -> T:
        return self._value

    def subscribe(self, fn: Callable[[T], None]) -> Handle:
        self._subscribers.append(fn)
        def cancel():
            if fn in self._subscribers:
                self._subscribers.remove(fn)
        return Handle(cancel)

    def dispose(self) -> None:
        for h in self._dep_handles:
            h.dispose()
        self._dep_handles.clear()
        self._subscribers.clear()

    def _recompute(self) -> None:
        new_val = self._fn()
        if new_val == self._value:
            return
        if self._updating:
            raise RuntimeError(
                "Circular Computed update detected: recomputing this "
                "Computed's value triggered another recompute of the same "
                "Computed before the previous one finished notifying "
                "subscribers. Check for a dependency cycle."
            )
        self._value = new_val
        self._updating = True
        try:
            for fn in list(self._subscribers):
                safe_call(fn, new_val, backend="core", component="Computed", method="subscribe")
        finally:
            self._updating = False


# ---------------------------------------------------------------------------
# Binding helpers
# ---------------------------------------------------------------------------

def bind_text(label, state: State) -> Handle:
    """One-way binding: State[str] → label.set_text()."""
    label.set_text(str(state.value))
    return state.subscribe(lambda v: label.set_text(str(v)))


def bind_value(widget, state: State) -> Handle:
    """Two-way binding: State ↔ LineEdit.

    suppress flag prevents feedback loops (State.set → widget → State.set).
    Note: the widget→state direction cannot be unsubscribed (on_change API
    limitation). Only the state→widget direction is covered by the returned Handle.
    """
    suppress = [False]

    def on_state(v):
        if suppress[0]:
            return
        suppress[0] = True
        try:
            widget.set_text(str(v))
        finally:
            suppress[0] = False

    def on_widget():
        if suppress[0]:
            return
        suppress[0] = True
        try:
            state.set(widget.get_text())
        finally:
            suppress[0] = False

    widget.set_text(str(state.value))
    h = state.subscribe(on_state)
    widget.on_change(on_widget)
    return h


def bind_items(dropdown, state: State) -> Handle:
    """One-way binding: State[list] → dropdown items."""
    def update(items):
        dropdown.clear()
        for item in items:
            dropdown.add_item(str(item))
    update(state.value)
    return state.subscribe(update)


def bind_enabled(widget, state: State) -> Handle:
    """One-way binding: State[bool] → widget.set_enabled()."""
    widget.set_enabled(bool(state.value))
    return state.subscribe(lambda v: widget.set_enabled(bool(v)))


def bind_visible(widget, state: State) -> Handle:
    """One-way binding: State[bool] → widget.show()/hide()."""
    def _apply(v):
        if v:
            widget.show()
        else:
            widget.hide()
    _apply(state.value)
    return state.subscribe(_apply)


# ---------------------------------------------------------------------------
# TaskRunner
# ---------------------------------------------------------------------------

class TaskRunner:
    """Run a callable in a daemon thread; post result back to the UI thread.

    fn signature: fn(cancelled: threading.Event) -> result
    """

    def __init__(self):
        self._cancelled: threading.Event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def run(self,
            fn: Callable,
            on_done: Optional[Callable] = None,
            on_error: Optional[Callable[[Exception], None]] = None,
            timeout: Optional[float] = None) -> None:
        """Run ``fn(cancelled)`` in a daemon thread.

        ``timeout``, if given, is cooperative: after ``timeout`` seconds the
        task is marked cancelled and ``on_error`` is called with a
        ``TimeoutError`` — but ``fn`` itself keeps running until it next
        checks ``cancelled``. Python cannot forcibly kill a thread. A ``lock``
        settles the on_done/on_error race once, so a task that finishes right
        as its timeout fires calls back exactly one of them, never both.
        """
        from uniui.display import schedule_after

        self.cancel()
        cancelled = threading.Event()
        self._cancelled = cancelled
        lock = threading.Lock()
        settled = False

        def settle_once() -> bool:
            nonlocal settled
            with lock:
                if settled:
                    return False
                settled = True
                return True

        def worker():
            try:
                result = fn(cancelled)
            except Exception as exc:
                if not cancelled.is_set() and settle_once() and on_error is not None:
                    captured = exc
                    schedule_after(0, lambda: on_error(captured))
                return
            if not cancelled.is_set() and settle_once() and on_done is not None:
                schedule_after(0, lambda: on_done(result))

        t = threading.Thread(target=worker, daemon=True)
        self._thread = t
        t.start()

        if timeout is not None:
            def on_timeout():
                if settle_once():
                    cancelled.set()
                    if on_error is not None:
                        schedule_after(0, lambda: on_error(TimeoutError(
                            f"Task timed out after {timeout}s"
                        )))

            timer = threading.Timer(timeout, on_timeout)
            timer.daemon = True
            timer.start()

    def cancel(self) -> None:
        self._cancelled.set()
