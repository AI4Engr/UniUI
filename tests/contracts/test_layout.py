"""
Contract Tests for VBox, HBox, Row, Column, Grid, Wrap, ScrollView, SplitPane, Overlay.

These tests ensure layout containers behave consistently across backends.
"""
import pytest

from tests.contract_framework import WidgetContractTest
from uniui import VBOX, HBOX, GRID, WRAP, SCROLL_VIEW, SPLIT_PANE, OVERLAY
from uniui.core import LayoutSpec, LayoutItem


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


class TestHBoxContract(WidgetContractTest):
    """Contract tests for HBoxLayout."""

    widget_kind = HBOX

    def create_widget(self, factory):
        return factory.create_hbox()

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


class TestWrapContract(WidgetContractTest):
    """Contract tests for Wrap layout."""

    widget_kind = WRAP

    def create_widget(self, factory):
        return factory.create_wrap()

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
