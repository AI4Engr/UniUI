"""
Pure-Python unit tests for State[T] and Computed[T].

No backend dependency — these run without Qt, Jupyter, or NiceGUI.
"""
from uniui.state import State, Computed, Handle


# ---------------------------------------------------------------------------
# State[T]
# ---------------------------------------------------------------------------

def test_state_initial_value():
    s = State(42)
    assert s.value == 42


def test_state_set_changes_value():
    s = State(0)
    s.set(10)
    assert s.value == 10


def test_state_set_fires_subscribers():
    s = State("hello")
    received = []
    s.subscribe(received.append)
    s.set("world")
    assert received == ["world"]


def test_state_multiple_subscribers():
    s = State(1)
    a, b = [], []
    s.subscribe(a.append)
    s.subscribe(b.append)
    s.set(2)
    assert a == [2]
    assert b == [2]


def test_state_no_fire_on_equal_value():
    s = State(5)
    called = []
    s.subscribe(called.append)
    s.set(5)
    assert called == []


def test_handle_dispose_stops_callback():
    s = State(0)
    called = []
    h = s.subscribe(called.append)
    h.dispose()
    s.set(1)
    assert called == []


def test_handle_dispose_idempotent():
    s = State(0)
    called = []
    h = s.subscribe(called.append)
    h.dispose()
    h.dispose()   # must not raise
    s.set(1)
    assert called == []


def test_state_retains_remaining_subscribers_after_dispose():
    s = State(0)
    a, b = [], []
    h = s.subscribe(a.append)
    s.subscribe(b.append)
    h.dispose()
    s.set(7)
    assert a == []
    assert b == [7]


def test_state_subscriber_exception_does_not_stop_siblings(caplog):
    s = State(0)
    good = []

    def bad(_value):
        raise ValueError("boom")

    s.subscribe(bad)
    s.subscribe(good.append)

    with caplog.at_level("ERROR", logger="uniui.events"):
        s.set(1)  # must not raise

    assert good == [1]
    assert "State.subscribe" in caplog.text
    assert "boom" in caplog.text


def test_state_reentrant_set_is_detected_and_logged(caplog):
    """A subscriber that calls set() on the same State it's reacting to must
    fail fast with a clear message, not silently recurse."""
    s = State(0)
    calls = []

    def naive_mirror(v):
        calls.append(v)
        s.set(v + 1)  # always different - would recurse forever unguarded

    s.subscribe(naive_mirror)

    with caplog.at_level("ERROR", logger="uniui.events"):
        s.set(1)  # must not raise, and must not recurse hundreds of times

    assert len(calls) == 1, "the guard must stop the second, reentrant set() call"
    assert "Circular State update detected" in caplog.text


def test_state_mutual_cycle_across_two_states_is_detected(caplog):
    """The cycle doesn't have to be direct - A -> B -> A must be caught too."""
    a, b = State(0), State(0)
    calls = []
    a.subscribe(lambda v: (calls.append(("a", v)), b.set(v + 1)))
    b.subscribe(lambda v: (calls.append(("b", v)), a.set(v + 1)))

    with caplog.at_level("ERROR", logger="uniui.events"):
        a.set(1)  # must not raise

    assert len(calls) == 2, "must fail on the first re-entry into A, not recurse"
    assert "Circular State update detected" in caplog.text


def test_state_converging_ping_pong_is_not_flagged_as_circular():
    """Two States that settle on the same value must not trip the guard -
    only non-converging (truly infinite) cycles are a problem."""
    a, b = State(0), State(0)
    a.subscribe(lambda v: b.set(v))
    b.subscribe(lambda v: a.set(v))

    a.set(5)  # must not raise

    assert a.value == 5
    assert b.value == 5


# ---------------------------------------------------------------------------
# Computed[T]
# ---------------------------------------------------------------------------

def test_computed_initial_value():
    s = State(3)
    c = Computed(lambda: s.value * 2, s)
    assert c.value == 6


def test_computed_updates_on_dep_change():
    s = State(5)
    c = Computed(lambda: s.value + 1, s)
    s.set(10)
    assert c.value == 11


def test_computed_notifies_subscribers():
    s = State(1)
    c = Computed(lambda: s.value * 10, s)
    received = []
    c.subscribe(received.append)
    s.set(3)
    assert received == [30]


def test_computed_no_fire_on_equal_result():
    s = State(5)
    c = Computed(lambda: abs(s.value), s)
    called = []
    c.subscribe(called.append)
    s.set(-5)  # abs(-5) == abs(5) == 5 — same result
    assert called == []


def test_computed_multiple_deps():
    a = State(2)
    b = State(3)
    c = Computed(lambda: a.value + b.value, a, b)
    assert c.value == 5
    a.set(10)
    assert c.value == 13
    b.set(7)
    assert c.value == 17


def test_computed_subscribe_handle_dispose():
    s = State(1)
    c = Computed(lambda: s.value, s)
    received = []
    h = c.subscribe(received.append)
    h.dispose()
    s.set(99)
    assert received == []


def test_computed_dispose_stops_dep_tracking():
    s = State(1)
    c = Computed(lambda: s.value, s)
    received = []
    c.subscribe(received.append)
    c.dispose()
    s.set(42)
    assert received == []
    assert c.value == 1  # frozen at disposal time


def test_computed_reentrant_recompute_is_detected_and_logged(caplog):
    """A subscriber that, via a *different* dependency, causes this same
    Computed to recompute again before it finished notifying must fail fast
    with a clear message rather than recursing."""
    s1, s2 = State(0), State(0)
    c = Computed(lambda: s1.value + s2.value, s1, s2)
    calls = []

    def naive_mirror(v):
        calls.append(v)
        s2.set(s2.value + 1)

    c.subscribe(naive_mirror)

    with caplog.at_level("ERROR", logger="uniui.events"):
        s1.set(1)  # must not raise

    assert len(calls) == 1, "the guard must stop the nested recompute"
    assert "Circular Computed update detected" in caplog.text


def test_computed_subscriber_exception_does_not_stop_siblings(caplog):
    s = State(1)
    c = Computed(lambda: s.value * 10, s)
    good = []

    def bad(_value):
        raise ValueError("boom")

    c.subscribe(bad)
    c.subscribe(good.append)

    with caplog.at_level("ERROR", logger="uniui.events"):
        s.set(3)  # must not raise

    assert good == [30]
    assert "Computed.subscribe" in caplog.text
