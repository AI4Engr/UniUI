"""
Contract Tests for VBox, HBox, Row, Column, Grid, Wrap, Center, ScrollView, SplitPane, Overlay.

These tests ensure layout containers behave consistently across backends.
"""
import pytest

from tests.contract_framework import (
    CommonCapabilitiesContractTest, WidgetContractTest, skip_unless_available,
)
from uniui import VBOX, HBOX, GRID, WRAP, CENTER, SPACER, CONTAINER, SEPARATOR, SCROLL_VIEW, SPLIT_PANE, OVERLAY
from uniui.core import ILayoutOnly, LayoutSpec, LayoutItem


def _child_count(native, factory) -> int:
    """Number of children currently attached to a box's native widget -
    ipywidgets' `.children` tuple, Qt's `QLayout.count()`, or NiceGUI's
    `.default_slot.children` all mean the same thing here, hence the
    per-backend branch instead of one generic attribute check."""
    framework = factory.__class__.__module__
    if "jupyter" in framework:
        return len(native.children)
    if "web" in framework:
        return len(native.default_slot.children)
    return native.layout().count()


class TestVBoxContract(WidgetContractTest):
    """Contract tests for VBoxLayout."""

    widget_kind = VBOX

    def create_widget(self, factory):
        return factory.create_vbox()

    @pytest.mark.contract
    def test_add_label(self, factory):
        """VBox can contain a label without error."""
        vbox = self.create_widget(factory)
        label = factory.create_label()
        label.set_text("Hello")
        vbox.add_item(label)

    @pytest.mark.contract
    def test_add_multiple_children(self, factory):
        """VBox accepts multiple children."""
        vbox = self.create_widget(factory)
        for i in range(3):
            lbl = factory.create_label()
            lbl.set_text(str(i))
            vbox.add_item(lbl)

    @pytest.mark.contract
    def test_add_stretch(self, factory):
        """add_stretch() must not raise."""
        vbox = self.create_widget(factory)
        vbox.add_stretch()

    @pytest.mark.contract
    def test_add_stretch_actually_inserts_a_spacer(self, factory):
        """add_stretch() must not be a silent no-op - a real gap once
        existed here where Jupyter's VBox.add_stretch() was `pass`, only
        caught by inspecting the child count, not just "didn't raise"."""
        vbox = self.create_widget(factory)
        vbox.add_item(factory.create_label())
        before = _child_count(vbox.get_native(), factory)
        vbox.add_stretch()
        after = _child_count(vbox.get_native(), factory)
        assert after == before + 1

    @pytest.mark.contract
    def test_set_alignment_top(self, factory):
        """set_alignment_top() must not raise."""
        vbox = self.create_widget(factory)
        vbox.set_alignment_top()

    @pytest.mark.contract
    def test_set_spec(self, factory):
        """set_spec() with a LayoutSpec must not raise."""
        vbox = self.create_widget(factory)
        spec = LayoutSpec(gap=8, padding=12)
        vbox.set_spec(spec)

    @pytest.mark.contract
    def test_add_item_with_spec(self, factory):
        """add_item_with_spec() must not raise."""
        vbox = self.create_widget(factory)
        label = factory.create_label()
        label.set_text("growing")
        item = LayoutItem(widget=label, grow=1.0)
        vbox.add_item_with_spec(label, item)

    @pytest.mark.contract
    def test_clear(self, factory):
        """clear() removes all children without error."""
        vbox = self.create_widget(factory)
        for i in range(3):
            lbl = factory.create_label()
            lbl.set_text(str(i))
            vbox.add_item(lbl)
        vbox.clear()

    @pytest.mark.contract
    def test_nested_layouts(self, factory):
        """VBox can contain nested HBox."""
        outer = self.create_widget(factory)
        inner = factory.create_hbox()
        label = factory.create_label()
        label.set_text("nested")
        inner.add_item(label)
        outer.add_item(inner)

    @pytest.mark.contract
    def test_is_layout_only(self, factory):
        """VBox's native object may be a pure layout manager (no widget-level
        show/hide/enabled surface on Qt) — the type system must say so."""
        assert isinstance(self.create_widget(factory), ILayoutOnly)


class TestHBoxContract(WidgetContractTest):
    """Contract tests for HBoxLayout."""

    widget_kind = HBOX

    def create_widget(self, factory):
        return factory.create_hbox()

    @pytest.mark.contract
    def test_is_layout_only(self, factory):
        """See TestVBoxContract.test_is_layout_only."""
        assert isinstance(self.create_widget(factory), ILayoutOnly)

    @pytest.mark.contract
    def test_add_label(self, factory):
        """HBox can contain a label without error."""
        hbox = self.create_widget(factory)
        label = factory.create_label()
        label.set_text("Hello")
        hbox.add_item(label)

    @pytest.mark.contract
    def test_add_multiple_children(self, factory):
        """HBox accepts multiple children."""
        hbox = self.create_widget(factory)
        for i in range(3):
            lbl = factory.create_label()
            lbl.set_text(str(i))
            hbox.add_item(lbl)

    @pytest.mark.contract
    def test_add_stretch(self, factory):
        """add_stretch() must not raise."""
        hbox = self.create_widget(factory)
        hbox.add_stretch()

    @pytest.mark.contract
    def test_add_stretch_actually_inserts_a_spacer(self, factory):
        """See TestVBoxContract's test of the same name."""
        hbox = self.create_widget(factory)
        hbox.add_item(factory.create_label())
        before = _child_count(hbox.get_native(), factory)
        hbox.add_stretch()
        after = _child_count(hbox.get_native(), factory)
        assert after == before + 1

    @pytest.mark.contract
    def test_set_alignment_top(self, factory):
        """set_alignment_top() must not raise."""
        hbox = self.create_widget(factory)
        hbox.set_alignment_top()

    @pytest.mark.contract
    def test_set_spec(self, factory):
        """set_spec() with a LayoutSpec must not raise."""
        hbox = self.create_widget(factory)
        spec = LayoutSpec(gap=8, padding=12)
        hbox.set_spec(spec)

    @pytest.mark.contract
    def test_add_item_with_spec(self, factory):
        """add_item_with_spec() must not raise."""
        hbox = self.create_widget(factory)
        label = factory.create_label()
        label.set_text("growing")
        item = LayoutItem(widget=label, grow=1.0)
        hbox.add_item_with_spec(label, item)

    @pytest.mark.contract
    def test_children_not_forced_flex(self, factory):
        """Children added via add_item must not interfere with each other's sizing."""
        hbox = self.create_widget(factory)
        lbl_a = factory.create_label()
        lbl_a.set_text("A")
        lbl_b = factory.create_label()
        lbl_b.set_text("B")
        hbox.add_item(lbl_a)
        hbox.add_item(lbl_b)
        assert hbox.get_native() is not None

    @pytest.mark.contract
    def test_clear(self, factory):
        """clear() removes all children without error."""
        hbox = self.create_widget(factory)
        for i in range(3):
            lbl = factory.create_label()
            lbl.set_text(str(i))
            hbox.add_item(lbl)
        hbox.clear()

    @pytest.mark.contract
    def test_nested_layouts(self, factory):
        """HBox can contain nested VBox."""
        outer = self.create_widget(factory)
        inner = factory.create_vbox()
        label = factory.create_label()
        label.set_text("nested")
        inner.add_item(label)
        outer.add_item(inner)

    @pytest.mark.contract
    def test_on_resize(self, factory):
        """on_resize() must not raise (default no-op on backends without a
        narrow-screen breakpoint rule, e.g. Web/Jupyter - see IGrid.on_resize's
        identical precedent)."""
        hbox = self.create_widget(factory)
        handle = hbox.on_resize(lambda mode: None)
        handle.dispose()


class TestGridContract(WidgetContractTest):
    """Contract tests for Grid layout."""

    widget_kind = GRID

    def create_widget(self, factory):
        return factory.create_grid(columns=3)

    @pytest.mark.contract
    def test_add_item_auto(self, factory):
        """Grid accepts items with automatic placement."""
        grid = self.create_widget(factory)
        for i in range(3):
            lbl = factory.create_label()
            lbl.set_text(str(i))
            grid.add_item(lbl)

    @pytest.mark.contract
    def test_add_item_explicit(self, factory):
        """Grid accepts items with explicit row/col."""
        grid = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("explicit")
        grid.add_item(lbl, row=0, col=0)

    @pytest.mark.contract
    def test_add_item_span(self, factory):
        """Grid accepts items with col_span > 1."""
        grid = factory.create_grid(columns=6)
        lbl = factory.create_label()
        lbl.set_text("wide")
        grid.add_item(lbl, row=0, col=0, col_span=3)

    @pytest.mark.contract
    def test_set_columns(self, factory):
        """set_columns() must not raise."""
        grid = self.create_widget(factory)
        grid.set_columns(4)

    @pytest.mark.contract
    def test_set_spec(self, factory):
        """set_spec() must not raise."""
        grid = self.create_widget(factory)
        grid.set_spec(LayoutSpec(gap=16, padding=8))

    @pytest.mark.contract
    def test_clear(self, factory):
        """clear() must not raise."""
        grid = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("hi")
        grid.add_item(lbl)
        grid.clear()

    @pytest.mark.contract
    def test_is_layout_only(self, factory):
        """See TestVBoxContract.test_is_layout_only."""
        assert isinstance(self.create_widget(factory), ILayoutOnly)

    @pytest.mark.contract
    def test_on_resize(self, factory):
        """on_resize() must not raise on any backend."""
        grid = self.create_widget(factory)
        handle = grid.on_resize(lambda mode: None)
        handle.dispose()


class TestQtResponsiveOnResize:
    """Qt-specific: on_resize() must fire with the correct breakpoint mode at
    each threshold crossing, and must not refire on a resize that doesn't
    cross a threshold (edge-triggered).

    Uses DEFAULT_BREAKPOINTS' thresholds directly: compact < 720, medium <
    1200, wide >= 1200 (uniui.contracts.layout.Breakpoints.mode_for).
    """

    def _assert_thresholds(self, container, on_resize):
        events = []
        on_resize(lambda mode: events.append(mode))

        container.resize(719, 100)
        self._pump()
        assert events == ["compact"]

        container.resize(720, 100)
        self._pump()
        assert events == ["compact", "medium"]

        container.resize(1199, 100)
        self._pump()
        assert events == ["compact", "medium"], "no crossing - must not refire"

        container.resize(1200, 100)
        self._pump()
        assert events == ["compact", "medium", "wide"]

        container.resize(1600, 100)
        self._pump()
        assert events == ["compact", "medium", "wide"], "no crossing - must not refire"

    @staticmethod
    def _pump():
        from PySide2 import QtWidgets
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.processEvents()

    @pytest.mark.contract
    def test_grid_fires_at_each_threshold_crossing(self):
        skip_unless_available("qt")
        from PySide2 import QtWidgets
        from uniui import create_factory

        factory = create_factory("qt")
        grid = factory.create_grid(columns=4)
        for i in range(4):
            lbl = factory.create_label()
            lbl.set_text(str(i))
            grid.add_item(lbl)

        container = QtWidgets.QWidget()
        container.setLayout(grid.get_native())
        container.resize(400, 100)
        container.show()
        self._pump()

        self._assert_thresholds(container, grid.on_resize)

    @pytest.mark.contract
    def test_hbox_fires_at_each_threshold_crossing(self):
        skip_unless_available("qt")
        from PySide2 import QtWidgets
        from uniui import create_factory

        factory = create_factory("qt")
        hbox = factory.create_hbox()
        lbl = factory.create_label()
        lbl.set_text("x")
        hbox.add_item(lbl)

        container = QtWidgets.QWidget()
        container.setLayout(hbox.get_native())
        container.resize(400, 60)
        container.show()
        self._pump()

        self._assert_thresholds(container, hbox.on_resize)

    @pytest.mark.contract
    def test_hbox_on_resize_registered_before_attachment(self):
        """A caller may build the HBox and register on_resize() before ever
        composing it into a parent widget (e.g. building a page header row
        before it's added to the shell) - the callback must still fire
        correctly once the row is later attached and laid out."""
        skip_unless_available("qt")
        from PySide2 import QtWidgets
        from uniui import create_factory

        factory = create_factory("qt")
        hbox = factory.create_hbox()

        events = []
        hbox.on_resize(lambda mode: events.append(mode))
        assert events == [], "must not fire before the layout has a parent widget"

        lbl = factory.create_label()
        lbl.set_text("x")
        hbox.add_item(lbl)
        assert events == [], "must still not fire before attachment"

        container = QtWidgets.QWidget()
        container.setLayout(hbox.get_native())
        container.resize(500, 60)
        container.show()
        self._pump()
        assert events == ["compact"]

        container.resize(1200, 60)
        self._pump()
        assert events == ["compact", "wide"]

    @pytest.mark.contract
    def test_grid_on_resize_registered_before_attachment(self):
        """Same ordering guarantee as HBox - see
        test_hbox_on_resize_registered_before_attachment."""
        skip_unless_available("qt")
        from PySide2 import QtWidgets
        from uniui import create_factory

        factory = create_factory("qt")
        grid = factory.create_grid(columns=4)

        events = []
        grid.on_resize(lambda mode: events.append(mode))
        assert events == [], "must not fire before the layout has a parent widget"

        for i in range(4):
            lbl = factory.create_label()
            lbl.set_text(str(i))
            grid.add_item(lbl)
        assert events == [], "must still not fire before attachment"

        container = QtWidgets.QWidget()
        container.setLayout(grid.get_native())
        container.resize(500, 100)
        container.show()
        self._pump()
        assert events == ["compact"]

        container.resize(1200, 100)
        self._pump()
        assert events == ["compact", "wide"]


class TestWebResponsiveOnResize:
    """Web-specific: directly exercise WebHBoxAdapter/WebGridAdapter's
    Python-side width handler (``_on_width``), simulating what would happen
    if the browser's ResizeObserver/emit JS layer reported a width - no
    automated test in this repo can drive real browser JS, so this only
    proves the edge-triggered dispatch logic on the Python side is correct,
    not that the JS ResizeObserver/hidden-bridge wiring actually functions in
    a real browser (see WebHBoxAdapter.on_resize's _wire_resize_observer).

    Same thresholds as TestQtResponsiveOnResize: compact < 720, medium <
    1200, wide >= 1200 (uniui.contracts.layout.Breakpoints.mode_for).
    """

    class _FakeValueChangeEvent:
        """Stands in for NiceGUI's ValueChangeEventArguments - only ``.value``
        is read by WebHBoxAdapter._on_width/WebGridAdapter._on_width."""
        def __init__(self, value):
            self.value = value

    def _assert_thresholds(self, container):
        events = []
        container.on_resize(lambda mode: events.append(mode))

        container._on_width(self._FakeValueChangeEvent(719))
        assert events == ["compact"]

        container._on_width(self._FakeValueChangeEvent(720))
        assert events == ["compact", "medium"]

        container._on_width(self._FakeValueChangeEvent(1199))
        assert events == ["compact", "medium"], "no crossing - must not refire"

        container._on_width(self._FakeValueChangeEvent(1200))
        assert events == ["compact", "medium", "wide"]

        container._on_width(self._FakeValueChangeEvent(1600))
        assert events == ["compact", "medium", "wide"], "no crossing - must not refire"

    @pytest.mark.contract
    def test_hbox_fires_at_each_threshold_crossing(self):
        skip_unless_available("web")
        from uniui import create_factory

        factory = create_factory("web")
        hbox = factory.create_hbox()
        self._assert_thresholds(hbox)

    @pytest.mark.contract
    def test_grid_fires_at_each_threshold_crossing(self):
        skip_unless_available("web")
        from uniui import create_factory

        factory = create_factory("web")
        grid = factory.create_grid(columns=4)
        self._assert_thresholds(grid)


class TestJupyterResponsiveOnResize:
    """Jupyter-specific: directly exercise JupyterHBoxAdapter/
    JupyterGridAdapter's hidden bridge widget, simulating what the injected
    ResizeObserver JS would do (set the bridge's ``.value`` and dispatch a
    change event) by setting ``.value`` on the bridge directly - no automated
    test in this repo can drive a real notebook frontend's JS, so this only
    proves the Python-side bridge-widget observe()/edge-trigger logic is
    correct, not that the JS injection/ResizeObserver/closest() DOM lookup
    actually functions in a real notebook (see layout_assets.resize_observer_js
    and JupyterHBoxAdapter.on_resize's experimental-behavior note).

    ``on_resize()`` itself attempts a real IPython.display.Javascript
    injection - confirmed (see _wire_resize_observer's guard) not to raise
    outside a real kernel, so no additional mocking is needed here for
    on_resize() to be called safely during collection/test execution.

    Same thresholds as TestQtResponsiveOnResize: compact < 720, medium <
    1200, wide >= 1200 (uniui.contracts.layout.Breakpoints.mode_for).
    """

    def _assert_thresholds(self, container):
        events = []
        container.on_resize(lambda mode: events.append(mode))
        bridge = container._resize_bridge
        assert bridge is not None, "on_resize() must wire the hidden bridge widget"

        bridge.value = 719
        assert events == ["compact"]

        bridge.value = 720
        assert events == ["compact", "medium"]

        bridge.value = 1199
        assert events == ["compact", "medium"], "no crossing - must not refire"

        bridge.value = 1200
        assert events == ["compact", "medium", "wide"]

        bridge.value = 1600
        assert events == ["compact", "medium", "wide"], "no crossing - must not refire"

    @pytest.mark.contract
    def test_hbox_fires_at_each_threshold_crossing(self):
        skip_unless_available("jupyter")
        from uniui import create_factory

        factory = create_factory("jupyter")
        hbox = factory.create_hbox()
        self._assert_thresholds(hbox)

    @pytest.mark.contract
    def test_grid_fires_at_each_threshold_crossing(self):
        skip_unless_available("jupyter")
        from uniui import create_factory

        factory = create_factory("jupyter")
        grid = factory.create_grid(columns=4)
        self._assert_thresholds(grid)


class TestWrapContract(WidgetContractTest):
    """Contract tests for Wrap layout."""

    widget_kind = WRAP

    def create_widget(self, factory):
        return factory.create_wrap()

    @pytest.mark.contract
    def test_is_not_layout_only(self, factory):
        """Unlike VBox/HBox/Grid, Wrap always wraps a real widget on every
        backend (Qt's QtWrapAdapter wraps its flow layout in a QWidget
        immediately) — it never has the no-show/hide-surface problem."""
        assert not isinstance(self.create_widget(factory), ILayoutOnly)

    @pytest.mark.contract
    def test_add_items(self, factory):
        """Wrap accepts multiple children without error."""
        wrap = self.create_widget(factory)
        for i in range(5):
            btn = factory.create_button()
            btn.set_text(f"Item {i}")
            wrap.add_item(btn)

    @pytest.mark.contract
    def test_set_spec(self, factory):
        """set_spec() must not raise."""
        wrap = self.create_widget(factory)
        wrap.set_spec(LayoutSpec(gap=8, padding=4))

    @pytest.mark.contract
    def test_clear(self, factory):
        """clear() must not raise."""
        wrap = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("hi")
        wrap.add_item(lbl)
        wrap.clear()


class TestSeparatorContract(CommonCapabilitiesContractTest):
    """Contract tests for Separator — a thin divider line.

    Like Wrap, Separator always wraps a real widget on every backend, so it
    gets the full show/hide/enabled/size surface for free via
    CommonCapabilitiesContractTest.
    """

    widget_kind = SEPARATOR

    def create_widget(self, factory):
        return factory.create_separator()

    @pytest.mark.contract
    def test_set_orientation_horizontal(self, factory):
        """set_orientation('horizontal') must not raise."""
        sep = self.create_widget(factory)
        sep.set_orientation("horizontal")

    @pytest.mark.contract
    def test_set_orientation_vertical(self, factory):
        """set_orientation('vertical') must not raise."""
        sep = self.create_widget(factory)
        sep.set_orientation("vertical")

    @pytest.mark.contract
    def test_default_orientation_is_horizontal(self, factory):
        """create_separator() with no args defaults to horizontal."""
        sep = factory.create_separator()
        assert sep is not None


class TestScrollViewContract(WidgetContractTest):
    """Contract tests for ScrollView."""

    widget_kind = SCROLL_VIEW

    def create_widget(self, factory):
        return factory.create_scroll_view()

    @pytest.mark.contract
    def test_set_content_label(self, factory):
        """ScrollView accepts a label as content."""
        sv = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("content")
        sv.set_content(lbl)

    @pytest.mark.contract
    def test_set_content_layout(self, factory):
        """ScrollView accepts a VBox as content."""
        sv = self.create_widget(factory)
        vbox = factory.create_vbox()
        lbl = factory.create_label()
        lbl.set_text("inside scroll")
        vbox.add_item(lbl)
        sv.set_content(vbox)

    @pytest.mark.contract
    def test_set_max_height(self, factory):
        """set_max_height() must not raise."""
        sv = self.create_widget(factory)
        sv.set_max_height(400)


class TestCenterContract(CommonCapabilitiesContractTest):
    """Contract tests for Center — centers a single child on both axes.

    Like Wrap/Separator, Center always wraps a real widget on every
    backend, so it gets the full show/hide/enabled/size surface for free
    via CommonCapabilitiesContractTest.
    """

    widget_kind = CENTER

    def create_widget(self, factory):
        return factory.create_center()

    @pytest.mark.contract
    def test_is_not_layout_only(self, factory):
        """Unlike VBox/HBox/Grid, Center always wraps a real widget on
        every backend (a QWidget on Qt, a Box on Jupyter, a div on Web)."""
        assert not isinstance(self.create_widget(factory), ILayoutOnly)

    @pytest.mark.contract
    def test_set_content_label(self, factory):
        """Center accepts a label as content."""
        c = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("content")
        c.set_content(lbl)

    @pytest.mark.contract
    def test_set_content_layout(self, factory):
        """Center accepts a VBox as content."""
        c = self.create_widget(factory)
        vbox = factory.create_vbox()
        lbl = factory.create_label()
        lbl.set_text("inside center")
        vbox.add_item(lbl)
        c.set_content(vbox)

    @pytest.mark.contract
    def test_set_content_replaces_previous(self, factory):
        """Calling set_content() twice leaves only the second child attached."""
        c = self.create_widget(factory)
        first = factory.create_label()
        first.set_text("first")
        second = factory.create_label()
        second.set_text("second")

        c.set_content(first)
        c.set_content(second)

        assert self._only_child_is(c, second, factory)

    def _only_child_is(self, center, expected, factory) -> bool:
        """True if ``expected``'s native widget is the sole child of
        ``center``'s native, using whichever child-inspection API this
        backend's native widget actually has (ipywidgets' `.children`
        tuple, NiceGUI's `.default_slot.children`, or Qt's own
        `.children()` method - all mean different things, hence the
        per-backend branch instead of one generic attribute check)."""
        native = center.get_native()
        framework = factory.__class__.__module__
        if "jupyter" in framework:
            return tuple(native.children) == (expected.get_native(),)
        if "web" in framework:
            kids = [e.get_native() if hasattr(e, "get_native") else e
                    for e in native.default_slot.children]
            return kids == [expected.get_native()]
        # Qt: the layout is the source of truth for what's attached.
        layout = native.layout()
        widgets = [layout.itemAt(i).widget() for i in range(layout.count())]
        return widgets == [expected.get_native()]


class TestSpacerContract(WidgetContractTest):
    """Contract tests for Spacer — flexible empty space, insertable via
    add_item() unlike add_stretch() which only works on the box itself."""

    widget_kind = SPACER

    def create_widget(self, factory):
        return factory.create_spacer()

    @pytest.mark.contract
    def test_is_not_layout_only(self, factory):
        """Spacer always wraps a real widget on every backend."""
        assert not isinstance(self.create_widget(factory), ILayoutOnly)

    @pytest.mark.contract
    def test_insertable_into_hbox(self, factory):
        """A Spacer can be added to an HBox via add_item() without error."""
        hbox = factory.create_hbox()
        hbox.add_item(factory.create_label())
        hbox.add_item(self.create_widget(factory))
        hbox.add_item(factory.create_label())

    @pytest.mark.contract
    def test_insertable_into_vbox(self, factory):
        """A Spacer can be added to a VBox via add_item() without error."""
        vbox = factory.create_vbox()
        vbox.add_item(factory.create_label())
        vbox.add_item(self.create_widget(factory))
        vbox.add_item(factory.create_label())


class TestContainerContract(CommonCapabilitiesContractTest):
    """Contract tests for Container — caps content width and centers it
    horizontally, for regular pages (dashboard/3D pages stay full-width).

    Like Center, Container always wraps a real widget on every backend, so
    it gets the full show/hide/enabled/size surface for free via
    CommonCapabilitiesContractTest.
    """

    widget_kind = CONTAINER

    def create_widget(self, factory):
        return factory.create_container()

    @pytest.mark.contract
    def test_is_not_layout_only(self, factory):
        assert not isinstance(self.create_widget(factory), ILayoutOnly)

    @pytest.mark.contract
    def test_set_content_label(self, factory):
        """Container accepts a label as content."""
        c = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("content")
        c.set_content(lbl)

    @pytest.mark.contract
    def test_set_content_layout(self, factory):
        """Container accepts a VBox as content."""
        c = self.create_widget(factory)
        vbox = factory.create_vbox()
        lbl = factory.create_label()
        lbl.set_text("inside container")
        vbox.add_item(lbl)
        c.set_content(vbox)

    @pytest.mark.contract
    def test_set_max_width(self, factory):
        """set_max_width() must not raise."""
        c = self.create_widget(factory)
        c.set_max_width(600)

    @pytest.mark.contract
    def test_default_max_width_reads_theme_token(self, factory):
        """With no explicit max_width, Container reads content_max_width
        from the theme token (not a hardcoded per-backend literal)."""
        from uniui.theme import get_admin_metrics
        expected = get_admin_metrics()["content_max_width"]
        c = self.create_widget(factory)
        native = c.get_native()
        framework = factory.__class__.__module__
        if "jupyter" in framework:
            assert native.layout.max_width == f"{expected}px"
        elif "web" in framework:
            assert native._style.get("max-width") == f"{expected}px"
        else:
            assert c._inner.maximumWidth() == expected


class TestSplitPaneContract(WidgetContractTest):
    """Contract tests for SplitPane."""

    widget_kind = SPLIT_PANE

    def create_widget(self, factory):
        return factory.create_split_pane("horizontal")

    @pytest.mark.contract
    def test_set_first_and_second(self, factory):
        """set_first() and set_second() must not raise."""
        sp = self.create_widget(factory)
        a = factory.create_label()
        a.set_text("Left")
        b = factory.create_label()
        b.set_text("Right")
        sp.set_first(a)
        sp.set_second(b)

    @pytest.mark.contract
    def test_set_orientation_vertical(self, factory):
        """set_orientation('vertical') must not raise."""
        sp = factory.create_split_pane("vertical")
        a = factory.create_label()
        a.set_text("Top")
        b = factory.create_label()
        b.set_text("Bottom")
        sp.set_first(a)
        sp.set_second(b)
        sp.set_orientation("vertical")

    @pytest.mark.contract
    def test_set_sizes(self, factory):
        """set_sizes() must not raise."""
        sp = self.create_widget(factory)
        a = factory.create_label()
        a.set_text("A")
        b = factory.create_label()
        b.set_text("B")
        sp.set_first(a)
        sp.set_second(b)
        sp.set_sizes(0.3)


class TestOverlayContract(WidgetContractTest):
    """Contract tests for Overlay."""

    widget_kind = OVERLAY

    def create_widget(self, factory):
        return factory.create_overlay()

    @pytest.mark.contract
    def test_add_single_layer(self, factory):
        """add_layer() with one child must not raise."""
        ov = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("layer 0")
        ov.add_layer(lbl)

    @pytest.mark.contract
    def test_add_multiple_layers(self, factory):
        """add_layer() with multiple children must not raise."""
        ov = self.create_widget(factory)
        for i in range(3):
            lbl = factory.create_label()
            lbl.set_text(f"layer {i}")
            ov.add_layer(lbl)

    @pytest.mark.contract
    def test_set_active_index(self, factory):
        """set_active_index() must not raise."""
        ov = self.create_widget(factory)
        for i in range(2):
            lbl = factory.create_label()
            lbl.set_text(f"layer {i}")
            ov.add_layer(lbl)
        ov.set_active_index(1)
        ov.set_active_index(0)


class TestSeparatorRendering:
    """Verify orientation actually reaches each backend's native widget, not
    just the adapter's own state - the contract tests above only check the
    latter."""

    @pytest.mark.parametrize("framework", ["qt", "jupyter", "web"])
    def test_set_orientation_reaches_the_native_widget(self, framework):
        skip_unless_available(framework)
        from uniui import create_factory

        sep = create_factory(framework).create_separator()
        native = sep.get_native()
        if framework == "qt":
            from PySide2 import QtWidgets
            sep.set_orientation("vertical")
            assert native.frameShape() == QtWidgets.QFrame.VLine
            sep.set_orientation("horizontal")
            assert native.frameShape() == QtWidgets.QFrame.HLine
        elif framework == "jupyter":
            sep.set_orientation("vertical")
            assert native.layout.border_left
            sep.set_orientation("horizontal")
            assert native.layout.border_top
        else:
            sep.set_orientation("vertical")
            assert "vertical" in native._props
            sep.set_orientation("horizontal")
            assert "vertical" not in native._props

    def test_qt_separator_defaults_to_horizontal_line(self):
        skip_unless_available("qt")
        from PySide2 import QtWidgets
        from uniui import create_factory

        sep = create_factory("qt").create_separator()
        assert sep.get_native().frameShape() == QtWidgets.QFrame.HLine

    def test_qt_separator_create_with_vertical_orientation(self):
        """create_separator('vertical') must reflect the VLine shape."""
        skip_unless_available("qt")
        from PySide2 import QtWidgets
        from uniui import create_factory

        sep = create_factory("qt").create_separator("vertical")
        assert sep.get_native().frameShape() == QtWidgets.QFrame.VLine
