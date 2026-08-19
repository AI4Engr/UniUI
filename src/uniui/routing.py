"""
In-process routing for UniUI.

Pure Python — no backend dependencies. Works with Qt, Jupyter, and Web.

Usage:
    router = Router(
        Route("/dashboard", dashboard_page, name="dashboard"),
        Route("/users/:id", user_detail_page, name="user-detail"),
        not_found=not_found_page,
    )
    router.push("/users/42")
    router.push_named("user-detail", params={"id": 42})
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uniui.state import Handle, safe_call


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class RouteNotFoundError(Exception):
    """Raised when no route matches the requested path and no not_found handler exists."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class RouteContext:
    """Immutable snapshot of the current navigation state."""
    path: str
    params: Dict[str, str]
    query: Dict[str, str]
    name: str
    router: "Router"


@dataclass
class Route:
    """Maps a URL pattern to a page factory function."""
    pattern: str
    page_factory: Callable[[RouteContext], Any]
    name: str = ""
    cache: bool = False


# ---------------------------------------------------------------------------
# Path matching helpers
# ---------------------------------------------------------------------------

def _compile_pattern(pattern: str):
    """Return (regex, param_names) for a route pattern like /users/:id."""
    param_names = []
    # Replace :name segments with named capture groups
    def _replacer(m):
        param_names.append(m.group(1))
        return r"([^/]+)"
    regex_str = re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", _replacer, pattern)
    regex_str = "^" + regex_str + r"$"
    return re.compile(regex_str), param_names


def _parse_query(query_string: str) -> Dict[str, str]:
    result = {}
    if not query_string:
        return result
    for part in query_string.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            result[k] = v
        elif part:
            result[part] = ""
    return result


def _split_path_query(full_path: str):
    """Split '/users?page=2' into ('/users', 'page=2')."""
    if "?" in full_path:
        path, qs = full_path.split("?", 1)
    else:
        path, qs = full_path, ""
    return path, qs


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class Router:
    """In-process router. Maintains history; notifies subscribers on navigation."""

    def __init__(self, *routes: Route, not_found: Optional[Callable] = None):
        self._routes: List[Route] = list(routes)
        self._not_found = not_found
        self._compiled: List[tuple] = [
            (_compile_pattern(r.pattern), r) for r in routes
        ]
        self._history: List[str] = []
        self._history_index: int = -1
        self._subscribers: List[Callable[[RouteContext], None]] = []
        self._current_context: Optional[RouteContext] = None

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def push(self, path: str) -> None:
        """Navigate to path, appending to history."""
        # Truncate any forward history
        if self._history_index < len(self._history) - 1:
            self._history = self._history[: self._history_index + 1]
        self._history.append(path)
        self._history_index = len(self._history) - 1
        self._navigate(path)

    def replace(self, path: str) -> None:
        """Navigate to path, replacing current history entry."""
        if self._history_index >= 0:
            self._history[self._history_index] = path
        else:
            self._history.append(path)
            self._history_index = 0
        self._navigate(path)

    def push_named(self, name: str, params: Optional[Dict] = None,
                   query: Optional[Dict] = None) -> None:
        """Navigate to a named route, interpolating params into the pattern."""
        route = self._find_by_name(name)
        if route is None:
            raise RouteNotFoundError(f"No route named {name!r}")
        path = route.pattern
        for k, v in (params or {}).items():
            path = path.replace(f":{k}", str(v))
        if query:
            qs = "&".join(f"{k}={v}" for k, v in query.items())
            path = f"{path}?{qs}"
        self.push(path)

    def back(self) -> None:
        """Navigate backward in history."""
        if self._history_index > 0:
            self._history_index -= 1
            self._navigate(self._history[self._history_index], record=False)

    def forward(self) -> None:
        """Navigate forward in history."""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._navigate(self._history[self._history_index], record=False)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def current_path(self) -> str:
        return self._history[self._history_index] if self._history_index >= 0 else ""

    @property
    def current_context(self) -> Optional[RouteContext]:
        return self._current_context

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def on_navigate(self, fn: Callable[[RouteContext], None]) -> Handle:
        self._subscribers.append(fn)
        def cancel():
            if fn in self._subscribers:
                self._subscribers.remove(fn)
        return Handle(cancel)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _navigate(self, full_path: str, record: bool = True) -> None:
        path, qs = _split_path_query(full_path)
        query = _parse_query(qs)
        matched_route, params = self._match(path)
        if matched_route is None:
            if self._not_found is not None:
                ctx = RouteContext(path=full_path, params={}, query=query,
                                   name="__not_found__", router=self)
                self._current_context = ctx
                self._notify(ctx)
                return
            raise RouteNotFoundError(f"No route matches {full_path!r}")
        ctx = RouteContext(
            path=full_path,
            params=params,
            query=query,
            name=matched_route.name,
            router=self,
        )
        self._current_context = ctx
        self._notify(ctx)

    def _match(self, path: str):
        for (regex, param_names), route in self._compiled:
            m = regex.match(path)
            if m:
                params = dict(zip(param_names, m.groups()))
                return route, params
        return None, {}

    def _find_by_name(self, name: str) -> Optional[Route]:
        for r in self._routes:
            if r.name == name:
                return r
        return None

    def _notify(self, ctx: RouteContext) -> None:
        for fn in list(self._subscribers):
            safe_call(fn, ctx, backend="core", component="Router", method="on_navigate")


# ---------------------------------------------------------------------------
# RouterView
# ---------------------------------------------------------------------------

class RouterView:
    """Renders the current route's page widget inside an IOverlay container.

    Requires the active IWidgetFactory to create an IOverlay.
    Pass `factory` explicitly or call after uniui.use() has been called.
    """

    def __init__(self, router: Router, factory=None):
        if factory is None:
            from uniui import _get_factory
            factory = _get_factory()
        self._router = router
        self._overlay = factory.create_overlay()
        self._page_cache: Dict[str, Any] = {}
        self._layer_index: Dict[str, int] = {}
        self._next_index: int = 0
        # The single currently-mounted, no-longer-reachable non-cached layer.
        # Removed right before the next layer is added, so uncached pages
        # never accumulate — cached pages are never tracked here.
        self._disposable_index: Optional[int] = None
        self._handle = router.on_navigate(self._on_navigate)

    def get_native(self):
        return self._overlay.get_native()

    def dispose(self) -> None:
        self._handle.dispose()

    def _on_navigate(self, ctx: RouteContext) -> None:
        route = self._router._find_by_name(ctx.name) if ctx.name else None
        cache_key = ctx.name if (route and route.cache) else None

        if cache_key and cache_key in self._page_cache:
            idx = self._layer_index[cache_key]
            self._overlay.set_active_index(idx)
            return

        # Find the matching route to get page_factory
        if ctx.name == "__not_found__":
            factory_fn = self._router._not_found
        else:
            matched_route = self._router._find_by_name(ctx.name)
            factory_fn = matched_route.page_factory if matched_route else self._router._not_found

        if factory_fn is None:
            return

        # We're about to mount a new layer — drop the previous disposable
        # (non-cached) one first so uncached pages never accumulate.
        if self._disposable_index is not None:
            old_index = self._disposable_index
            self._overlay.remove_layer(old_index)
            self._disposable_index = None
            for key, idx in self._layer_index.items():
                if idx > old_index:
                    self._layer_index[key] = idx - 1
            self._next_index -= 1

        page_widget = factory_fn(ctx)
        self._overlay.add_layer(page_widget)
        self._overlay.set_active_index(self._next_index)

        if cache_key:
            self._page_cache[cache_key] = page_widget
            self._layer_index[cache_key] = self._next_index
        else:
            self._disposable_index = self._next_index

        self._next_index += 1


# ---------------------------------------------------------------------------
# NavMenu helper
# ---------------------------------------------------------------------------

class NavMenu:
    """Factory helper — creates an ISidebar wired to a Router."""

    @staticmethod
    def from_router(router: Router, factory=None) -> "ISidebar":
        """Create a Sidebar with one item per named route, synced to the router."""
        if factory is None:
            from uniui import _get_factory
            factory = _get_factory()
        sidebar = factory.create_sidebar()

        for route in router._routes:
            if route.name:
                sidebar.add_item(route.name, route.name.replace("-", " ").title())

        def on_select(key: str) -> None:
            router.push_named(key)

        sidebar.on_select(on_select)

        def on_navigate(ctx: RouteContext) -> None:
            if ctx.name and ctx.name != "__not_found__":
                sidebar.set_active(ctx.name)

        router.on_navigate(on_navigate)
        return sidebar


def sync_breadcrumb(breadcrumb, router: Router,
                    trail_fn: Optional[Callable[[RouteContext], List[Dict]]] = None) -> Handle:
    """Wire a Breadcrumb to a Router so it updates on every navigation.

    trail_fn(ctx) -> list of {"label": str, "path": str (optional)} dicts.
    Defaults to a single-item trail showing the current route name.
    """
    def _default_trail(ctx: RouteContext) -> List[Dict]:
        label = ctx.name.replace("-", " ").title() if ctx.name else ctx.path
        return [{"label": label}]

    fn = trail_fn or _default_trail

    def on_navigate(ctx: RouteContext) -> None:
        breadcrumb.set_items(fn(ctx))

    return router.on_navigate(on_navigate)
