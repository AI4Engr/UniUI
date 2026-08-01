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
