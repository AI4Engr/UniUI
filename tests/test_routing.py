"""
Pure-Python unit tests for Router, Route, RouteContext.

No backend dependency — these run without Qt, Jupyter, or NiceGUI.
"""
import pytest
from uniui.routing import (
    Router, Route, RouteContext, RouteNotFoundError,
    _compile_pattern, _parse_query, _split_path_query,
)
from uniui.state import Handle


# ---------------------------------------------------------------------------
# Pattern matching helpers
# ---------------------------------------------------------------------------

def test_compile_static_pattern():
    regex, params = _compile_pattern("/dashboard")
    assert regex.match("/dashboard")
    assert not regex.match("/dashboard/extra")
    assert params == []


def test_compile_param_pattern():
    regex, params = _compile_pattern("/users/:id")
    m = regex.match("/users/42")
    assert m
    assert params == ["id"]
    assert m.group(1) == "42"


def test_compile_multi_param():
    regex, params = _compile_pattern("/org/:org/repo/:repo")
    m = regex.match("/org/acme/repo/myapp")
    assert m
    assert params == ["org", "repo"]
    assert m.groups() == ("acme", "myapp")


def test_parse_query_empty():
    assert _parse_query("") == {}


def test_parse_query_basic():
    result = _parse_query("page=2&status=active")
    assert result == {"page": "2", "status": "active"}


def test_parse_query_no_value():
    result = _parse_query("flag")
    assert result == {"flag": ""}


def test_split_path_query_no_qs():
    path, qs = _split_path_query("/users")
    assert path == "/users"
    assert qs == ""


def test_split_path_query_with_qs():
    path, qs = _split_path_query("/users?page=2&status=active")
    assert path == "/users"
    assert qs == "page=2&status=active"


# ---------------------------------------------------------------------------
# Route matching
# ---------------------------------------------------------------------------

def _dummy_page(ctx): return object()

def test_router_static_path():
    router = Router(Route("/dashboard", _dummy_page, name="dashboard"))
    router.push("/dashboard")
    assert router.current_path == "/dashboard"
    assert router.current_context.name == "dashboard"
    assert router.current_context.params == {}
    assert router.current_context.query == {}


def test_router_path_params():
    router = Router(Route("/users/:id", _dummy_page, name="user-detail"))
    router.push("/users/42")
    ctx = router.current_context
    assert ctx.params == {"id": "42"}
    assert ctx.name == "user-detail"


def test_router_query_params():
    router = Router(Route("/users", _dummy_page, name="users"))
    router.push("/users?page=2&status=active")
    ctx = router.current_context
    assert ctx.query == {"page": "2", "status": "active"}


def test_router_not_found_raises():
    router = Router(Route("/home", _dummy_page, name="home"))
    with pytest.raises(RouteNotFoundError):
        router.push("/nonexistent")


def test_router_not_found_handler():
    """When a path doesn't match, the router builds a __not_found__ context
    and notifies subscribers. The not_found page factory is called by RouterView."""
    events = []
    def not_found_page(ctx): events.append(ctx)
    router = Router(Route("/home", _dummy_page), not_found=not_found_page)
    router.on_navigate(events.append)
    router.push("/missing")
    assert len(events) == 1
    assert events[0].name == "__not_found__"
    assert events[0].path == "/missing"


# ---------------------------------------------------------------------------
# Named routes
# ---------------------------------------------------------------------------

def test_router_named_route():
    router = Router(Route("/users/:id", _dummy_page, name="user-detail"))
    router.push_named("user-detail", params={"id": 99})
    ctx = router.current_context
    assert ctx.params == {"id": "99"}
    assert ctx.path == "/users/99"


def test_router_named_route_with_query():
    router = Router(Route("/users", _dummy_page, name="users"))
    router.push_named("users", query={"page": "3"})
    ctx = router.current_context
    assert ctx.query == {"page": "3"}


def test_router_push_named_unknown_raises():
    router = Router(Route("/home", _dummy_page, name="home"))
    with pytest.raises(RouteNotFoundError):
        router.push_named("unknown")


# ---------------------------------------------------------------------------
# History — back / forward / replace
# ---------------------------------------------------------------------------

def test_router_back_forward():
    router = Router(
        Route("/a", _dummy_page, name="a"),
        Route("/b", _dummy_page, name="b"),
        Route("/c", _dummy_page, name="c"),
    )
    router.push("/a")
    router.push("/b")
    router.push("/c")
    assert router.current_path == "/c"
    router.back()
    assert router.current_path == "/b"
    router.back()
    assert router.current_path == "/a"
    router.forward()
    assert router.current_path == "/b"


def test_router_back_at_start_is_noop():
    router = Router(Route("/a", _dummy_page))
    router.push("/a")
    router.back()  # must not raise
    assert router.current_path == "/a"


def test_router_forward_at_end_is_noop():
    router = Router(Route("/a", _dummy_page))
    router.push("/a")
    router.forward()  # must not raise
    assert router.current_path == "/a"


def test_router_push_truncates_forward_history():
    router = Router(
        Route("/a", _dummy_page),
        Route("/b", _dummy_page),
        Route("/c", _dummy_page),
    )
    router.push("/a")
    router.push("/b")
    router.back()
    router.push("/c")
    router.forward()  # should be noop — forward history was truncated
    assert router.current_path == "/c"


def test_router_replace():
    router = Router(
        Route("/a", _dummy_page),
        Route("/b", _dummy_page),
    )
    router.push("/a")
    router.replace("/b")
    assert router.current_path == "/b"
    router.back()  # should be noop — replace did not grow history
    assert router.current_path == "/b"


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

def test_router_on_navigate_fires():
    router = Router(Route("/home", _dummy_page, name="home"))
    events = []
    router.on_navigate(events.append)
    router.push("/home")
    assert len(events) == 1
    assert events[0].name == "home"


def test_router_on_navigate_multiple_subscribers():
    router = Router(Route("/home", _dummy_page))
    a, b = [], []
    router.on_navigate(a.append)
    router.on_navigate(b.append)
    router.push("/home")
    assert len(a) == 1
    assert len(b) == 1


def test_router_on_navigate_handle_dispose():
    router = Router(Route("/home", _dummy_page))
    called = []
    h = router.on_navigate(called.append)
    h.dispose()
    router.push("/home")
    assert called == []


def test_router_on_navigate_handle_dispose_idempotent():
    router = Router(Route("/home", _dummy_page))
    h = router.on_navigate(lambda ctx: None)
    h.dispose()
    h.dispose()  # must not raise


def test_router_on_navigate_subscriber_exception_does_not_stop_siblings(caplog):
    router = Router(Route("/home", _dummy_page, name="home"))
    good = []

    def bad(ctx):
        raise ValueError("boom")

    router.on_navigate(bad)
    router.on_navigate(good.append)

    with caplog.at_level("ERROR", logger="uniui.events"):
        router.push("/home")  # must not raise

    assert len(good) == 1
    assert "Router.on_navigate" in caplog.text


# ---------------------------------------------------------------------------
# current_path before any navigation
# ---------------------------------------------------------------------------

def test_router_initial_path_is_empty():
    router = Router(Route("/home", _dummy_page))
    assert router.current_path == ""
    assert router.current_context is None
