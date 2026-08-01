"""
Contract tests for RouterView — verifies page rendering and navigation
using the active Qt backend factory.
"""
import pytest

from uniui.routing import Router, Route, RouterView, RouteNotFoundError


def _make_page(text):
    """Factory helper that creates a simple page factory returning a label."""
    def page_factory(ctx, _text=text):
        from uniui import _get_factory
        lbl = _get_factory().create_label()
        lbl.set_text(_text)
        return lbl
    return page_factory


class TestRouterViewContract:
    """RouterView renders pages and switches on navigation."""

    @pytest.mark.contract
    def test_router_view_creates_native(self, factory):
        """RouterView.get_native() returns a non-None object before any navigation."""
        router = Router(Route("/home", _make_page("Home"), name="home"))
        rv = RouterView(router, factory)
        assert rv.get_native() is not None

    @pytest.mark.contract
    def test_router_view_renders_on_push(self, factory):
        """Pushing a route causes RouterView to render the page without error."""
        router = Router(Route("/home", _make_page("Home"), name="home"))
        rv = RouterView(router, factory)
        router.push("/home")   # must not raise

    @pytest.mark.contract
    def test_router_view_switches_page(self, factory):
        """Navigating to a second route switches the active page."""
        router = Router(
            Route("/a", _make_page("Page A"), name="a"),
            Route("/b", _make_page("Page B"), name="b"),
        )
        rv = RouterView(router, factory)
        router.push("/a")
        router.push("/b")   # must not raise; overlay index should advance

    @pytest.mark.contract
    def test_router_view_back_navigation(self, factory):
        """back() causes the RouterView to re-render the previous page."""
        router = Router(
            Route("/a", _make_page("A"), name="a"),
            Route("/b", _make_page("B"), name="b"),
        )
        rv = RouterView(router, factory)
        router.push("/a")
        router.push("/b")
        router.back()   # must not raise

    @pytest.mark.contract
    def test_router_view_not_found_with_handler(self, factory):
        """RouterView handles 404 via not_found without raising."""
        not_found_page = _make_page("404 Not Found")
        router = Router(
            Route("/home", _make_page("Home"), name="home"),
            not_found=not_found_page,
        )
        rv = RouterView(router, factory)
        router.push("/missing")   # must not raise

    @pytest.mark.contract
    def test_router_view_dispose(self, factory):
        """dispose() unsubscribes from router without error."""
        router = Router(Route("/home", _make_page("Home"), name="home"))
        rv = RouterView(router, factory)
        router.push("/home")
        rv.dispose()
        router.push("/home")   # subsequent navigation must not re-trigger the view
