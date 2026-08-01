"""
Pure model tests for SizeSpec, LayoutSpec, LayoutItem, Breakpoints.

These tests have no backend dependency — they test the data layer only.
"""
from uniui.core import SizeSpec, LayoutSpec, LayoutItem, Breakpoints, DEFAULT_BREAKPOINTS


def test_size_spec_auto():
    s = SizeSpec.auto()
    assert s.value is None
    assert s.grow == 0.0


def test_size_spec_fill():
    s = SizeSpec.fill()
    assert s.value == "fill"
    assert s.grow == 1.0
    assert s.shrink == 1.0


def test_size_spec_fixed():
    s = SizeSpec.fixed(200)
    assert s.value == 200
    assert s.grow == 0.0
    assert s.shrink == 0.0


def test_size_spec_pct():
    s = SizeSpec.pct(50)
    assert s.value == "50%"


def test_layout_spec_defaults():
    spec = LayoutSpec()
    assert spec.gap == 0
    assert spec.padding == 0
    assert spec.wrap is False
    assert spec.align == "start"
    assert spec.cross_align == "start"


def test_layout_spec_custom():
    spec = LayoutSpec(gap=16, padding=24, wrap=True, align="center")
    assert spec.gap == 16
    assert spec.padding == 24
    assert spec.wrap is True
    assert spec.align == "center"


def test_layout_item_defaults():
    sentinel = object()
    item = LayoutItem(widget=sentinel)
    assert item.widget is sentinel
    assert item.grow == 0.0
    assert item.shrink == 1.0
    assert item.span == 1
    assert item.key is None


def test_layout_item_grow():
    sentinel = object()
    item = LayoutItem(widget=sentinel, grow=2.0, key="header")
    assert item.grow == 2.0
    assert item.key == "header"


def test_breakpoints_defaults():
    bp = Breakpoints()
    assert bp.compact == 720
    assert bp.medium == 1200


def test_breakpoints_mode_compact():
    bp = Breakpoints()
    assert bp.mode_for(0) == "compact"
    assert bp.mode_for(500) == "compact"
    assert bp.mode_for(719) == "compact"


def test_breakpoints_mode_medium():
    bp = Breakpoints()
    assert bp.mode_for(720) == "medium"
    assert bp.mode_for(900) == "medium"
    assert bp.mode_for(1199) == "medium"


def test_breakpoints_mode_wide():
    bp = Breakpoints()
    assert bp.mode_for(1200) == "wide"
    assert bp.mode_for(1440) == "wide"
    assert bp.mode_for(2560) == "wide"


def test_breakpoints_custom():
    bp = Breakpoints(compact=480, medium=960)
    assert bp.mode_for(479) == "compact"
    assert bp.mode_for(480) == "medium"
    assert bp.mode_for(960) == "wide"


def test_default_breakpoints_instance():
    assert DEFAULT_BREAKPOINTS.compact == 720
    assert DEFAULT_BREAKPOINTS.medium == 1200
