"""
Pure-Python unit tests for Router, Route, RouteContext.

No backend dependency — these run without Qt, Jupyter, or NiceGUI.
"""
import pytest
from uniui.routing import (
    Router, Route, RouteContext, RouteNotFoundError,
    _compile_pattern, _parse_query, _split_path_query, sync_page_title,
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
# Default route and redirects
# ---------------------------------------------------------------------------

def test_default_route_used_for_empty_path():
    router = Router(Route("/dashboard", _dummy_page, name="dashboard"), default="/dashboard")
    router.push("")
    assert router.current_context.name == "dashboard"
    assert router.current_path == "/dashboard"


def test_default_route_used_for_root_path():
    router = Router(Route("/dashboard", _dummy_page, name="dashboard"), default="/dashboard")
    router.push("/")
    assert router.current_context.name == "dashboard"


def test_default_route_does_not_override_an_explicit_root_route():
    router = Router(Route("/", _dummy_page, name="home"), default="/elsewhere")
    router.push("/")
    assert router.current_context.name == "home"


def test_default_route_preserves_query_string():
    router = Router(Route("/dashboard", _dummy_page, name="dashboard"), default="/dashboard")
    router.push("/?tab=charts")
    assert router.current_context.query == {"tab": "charts"}


def test_no_default_route_falls_through_to_not_found_handling():
    router = Router(Route("/dashboard", _dummy_page, name="dashboard"))
    with pytest.raises(RouteNotFoundError):
        router.push("/")


def test_redirect_route_resolves_to_target():
    router = Router(
        Route("/old", _dummy_page, name="old", redirect="/new"),
        Route("/new", _dummy_page, name="new"),
    )
    router.push("/old")
    assert router.current_context.name == "new"
    assert router.current_path == "/new"


def test_redirect_interpolates_matched_params():
    router = Router(
        Route("/u/:id", _dummy_page, name="short", redirect="/users/:id"),
        Route("/users/:id", _dummy_page, name="user-detail"),
    )
    router.push("/u/42")
    ctx = router.current_context
    assert ctx.name == "user-detail"
    assert ctx.params == {"id": "42"}
    assert router.current_path == "/users/42"


def test_redirect_preserves_query_string():
    router = Router(
        Route("/old", _dummy_page, name="old", redirect="/new"),
        Route("/new", _dummy_page, name="new"),
    )
    router.push("/old?page=2")
    assert router.current_context.query == {"page": "2"}


def test_redirect_chain_resolves_to_final_target():
    router = Router(
        Route("/a", _dummy_page, name="a", redirect="/b"),
        Route("/b", _dummy_page, name="b", redirect="/c"),
        Route("/c", _dummy_page, name="c"),
    )
    router.push("/a")
    assert router.current_context.name == "c"


def test_redirect_cycle_raises_instead_of_hanging():
    router = Router(
        Route("/a", _dummy_page, name="a", redirect="/b"),
        Route("/b", _dummy_page, name="b", redirect="/a"),
    )
    with pytest.raises(RouteNotFoundError):
        router.push("/a")


def test_redirect_notifies_subscribers_with_the_final_context_only():
    """A redirect must not fire on_navigate for the intermediate route."""
    events = []
    router = Router(
        Route("/old", _dummy_page, name="old", redirect="/new"),
        Route("/new", _dummy_page, name="new"),
    )
    router.on_navigate(events.append)
    router.push("/old")
    assert len(events) == 1
    assert events[0].name == "new"


def test_redirect_target_does_not_leave_stale_history_entry():
    """back() after a redirected push() must not land on the dead source path."""
    router = Router(
        Route("/x", _dummy_page, name="x"),
        Route("/old", _dummy_page, name="old", redirect="/new"),
        Route("/new", _dummy_page, name="new"),
    )
    router.push("/x")
    router.push("/old")
    assert router.current_path == "/new"
    router.back()
    assert router.current_path == "/x"


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


# ---------------------------------------------------------------------------
# sync_page_title
# ---------------------------------------------------------------------------

def test_sync_page_title_uses_the_default_title_case_formatter():
    router = Router(Route("/user-list", _dummy_page, name="user-list"))
    titles = []
    sync_page_title(router, titles.append)
    router.push("/user-list")
    assert titles == ["User List"]


def test_sync_page_title_fires_on_every_navigation():
    router = Router(
        Route("/a", _dummy_page, name="a"),
        Route("/b", _dummy_page, name="b"),
    )
    titles = []
    sync_page_title(router, titles.append)
    router.push("/a")
    router.push("/b")
    assert titles == ["A", "B"]


def test_sync_page_title_not_found_gets_a_readable_default():
    router = Router(Route("/home", _dummy_page, name="home"), not_found=_dummy_page)
    titles = []
    sync_page_title(router, titles.append)
    router.push("/missing")
    assert titles == ["Not Found"]


def test_sync_page_title_accepts_a_custom_title_fn():
    router = Router(Route("/users/:id", _dummy_page, name="user-detail"))
    titles = []
    sync_page_title(router, titles.append, title_fn=lambda ctx: f"User {ctx.params.get('id')}")
    router.push("/users/42")
    assert titles == ["User 42"]


def test_sync_page_title_returns_a_disposable_handle():
    router = Router(Route("/home", _dummy_page, name="home"))
    titles = []
    handle = sync_page_title(router, titles.append)
    handle.dispose()
    router.push("/home")
    assert titles == []


# ---------------------------------------------------------------------------
# Navigation guards
# ---------------------------------------------------------------------------

def test_guard_allowing_true_lets_navigation_through():
    router = Router(Route("/home", _dummy_page, name="home"))
    router.add_guard(lambda ctx: True)
    router.push("/home")
    assert router.current_context.name == "home"


def test_guard_allowing_none_lets_navigation_through():
    router = Router(Route("/home", _dummy_page, name="home"))
    router.add_guard(lambda ctx: None)
    router.push("/home")
    assert router.current_context.name == "home"


def test_guard_returning_false_cancels_navigation():
    router = Router(
        Route("/home", _dummy_page, name="home"),
        Route("/admin", _dummy_page, name="admin"),
    )
    router.push("/home")
    router.add_guard(lambda ctx: ctx.name != "admin")
    router.push("/admin")
    assert router.current_context.name == "home", "must stay on the current route"


def test_guard_returning_a_path_redirects():
    router = Router(
        Route("/admin", _dummy_page, name="admin"),
        Route("/login", _dummy_page, name="login"),
    )
    router.add_guard(lambda ctx: "/login" if ctx.name == "admin" else True)
    router.push("/admin")
    assert router.current_context.name == "login"


def test_guard_redirect_restarts_the_whole_chain_on_the_new_target():
    """A guard's redirect must itself be guarded: the whole chain restarts
    against the new target rather than resuming from the next guard - the
    same pattern vue-router's beforeEach redirect uses."""
    calls = []
    router = Router(
        Route("/admin", _dummy_page, name="admin"),
        Route("/login", _dummy_page, name="login"),
    )
    router.add_guard(lambda ctx: "/login" if ctx.name == "admin" else True)
    router.add_guard(lambda ctx: (calls.append(ctx.name), True)[-1])
    router.push("/admin")
    assert calls == ["login"], "guard 2 must only ever see the resolved target"
    assert router.current_context.name == "login"


def test_guard_redirect_loop_raises_instead_of_hanging():
    router = Router(
        Route("/a", _dummy_page, name="a"),
        Route("/b", _dummy_page, name="b"),
    )
    router.add_guard(lambda ctx: "/b" if ctx.name == "a" else "/a")
    with pytest.raises(RouteNotFoundError):
        router.push("/a")


def test_guard_exception_fails_open(caplog):
    """A broken guard must not make the app unnavigable."""
    router = Router(Route("/home", _dummy_page, name="home"))

    def bad_guard(ctx):
        raise ValueError("boom")

    router.add_guard(bad_guard)
    with caplog.at_level("ERROR", logger="uniui.events"):
        router.push("/home")  # must not raise

    assert router.current_context.name == "home"
    assert "Router.add_guard" in caplog.text


def test_guard_dispose_stops_it_from_running():
    router = Router(
        Route("/home", _dummy_page, name="home"),
        Route("/admin", _dummy_page, name="admin"),
    )
    handle = router.add_guard(lambda ctx: ctx.name != "admin")
    handle.dispose()
    router.push("/admin")
    assert router.current_context.name == "admin"


def test_cancelled_navigation_does_not_notify_subscribers():
    router = Router(
        Route("/home", _dummy_page, name="home"),
        Route("/admin", _dummy_page, name="admin"),
    )
    router.push("/home")
    events = []
    router.on_navigate(events.append)
    router.add_guard(lambda ctx: ctx.name != "admin")
    router.push("/admin")
    assert events == []


def test_redirected_history_entry_replaces_the_blocked_path():
    """back() after a guard-redirected push() must not land on the blocked path."""
    router = Router(
        Route("/x", _dummy_page, name="x"),
        Route("/admin", _dummy_page, name="admin"),
        Route("/login", _dummy_page, name="login"),
    )
    router.add_guard(lambda ctx: "/login" if ctx.name == "admin" else True)
    router.push("/x")
    router.push("/admin")
    assert router.current_path == "/login"
    router.back()
    assert router.current_path == "/x"
