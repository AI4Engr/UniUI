"""The contracts split preserved core.py's behaviour and surface.

Two things nearly went wrong here and both were silent:

1. Slicing classes out of ``core.py`` by ``node.lineno`` drops the decorator
   line, because ``lineno`` for a decorated class points at ``class``, not at
   ``@dataclass``. The classes still imported fine; they just stopped being
   dataclasses, so ``SizeSpec(value=1)`` raised "takes no arguments".
2. The 26 hand-written snake_case forwarders were replaced by generated ones.
   A naive camelCase-to-snake_case rule yields ``create_v_box``, silently
   breaking the long-published ``create_vbox``.
"""
from __future__ import annotations

import dataclasses

import pytest

from uniui.contracts.layout import (
    DEFAULT_BREAKPOINTS, Breakpoints, LayoutItem, LayoutSpec, SizeSpec,
)
from uniui.contracts.widgets import _SNAKE_ALIASES, IWidgetFactory
from uniui.core import IWidgetFactory as CoreFactory


@pytest.mark.parametrize("cls", [SizeSpec, LayoutSpec, LayoutItem, Breakpoints])
def test_layout_models_are_still_dataclasses(cls):
    """Catches a dropped ``@dataclass`` decorator during the move."""
    assert dataclasses.is_dataclass(cls), (
        f"{cls.__name__} lost its @dataclass decorator - it was probably "
        "sliced from the source starting at the 'class' line."
    )


def test_layout_models_still_accept_keyword_construction():
    """The symptom a dropped decorator actually produces."""
    assert SizeSpec.fixed(200).value == 200
    assert SizeSpec(value=3).value == 3
    assert DEFAULT_BREAKPOINTS.compact == 720


def test_core_reexports_the_same_factory_object():
    """``from uniui.core import *`` must reach the real class, not a copy."""
    assert CoreFactory is IWidgetFactory


@pytest.mark.parametrize("camel,snake", sorted(_SNAKE_ALIASES.items()))
def test_every_camel_method_has_its_snake_alias(camel, snake):
    assert callable(getattr(IWidgetFactory, camel, None))
    assert callable(getattr(IWidgetFactory, snake, None))


def test_the_irregular_layout_aliases_are_not_regularised():
    """``createVBox`` maps to ``create_vbox``, never ``create_v_box``."""
    assert _SNAKE_ALIASES["createVBox"] == "create_vbox"
    assert _SNAKE_ALIASES["createHBox"] == "create_hbox"
    assert not hasattr(IWidgetFactory, "create_v_box")
    assert not hasattr(IWidgetFactory, "create_h_box")


def test_snake_alias_dispatches_to_the_subclass_override():
    """The forwarder must resolve on ``self``, not bind the base method."""

    class Fake(IWidgetFactory):
        def createLabel(self): return "overridden"
        def createButton(self): return None
        def createLineEdit(self): return None
        def createTextArea(self): return None
        def createComboBox(self): return None
        def createDropdown(self): return None
        def createVBox(self): return "vbox"
        def createHBox(self): return None
        def createTabWidget(self): return None
        def createImage(self): return None
        def createGrid(self, columns: int = 12): return f"grid:{columns}"
        def createSplitPane(self, orientation: str = "horizontal"):
            return f"split:{orientation}"

    fake = Fake()
    assert fake.create_label() == "overridden"
    assert fake.create_vbox() == "vbox"
    # Arguments must survive the hop, positionally and by keyword.
    assert fake.create_grid(4) == "grid:4"
    assert fake.create_grid() == "grid:12"
    assert fake.create_split_pane(orientation="vertical") == "split:vertical"


def test_unsupported_widgets_still_raise_through_the_alias():
    from uniui.core import NotSupportedError

    class Bare(IWidgetFactory):
        def createLabel(self): return None
        def createButton(self): return None
        def createLineEdit(self): return None
        def createTextArea(self): return None
        def createComboBox(self): return None
        def createDropdown(self): return None
        def createVBox(self): return None
        def createHBox(self): return None
        def createTabWidget(self): return None
        def createImage(self): return None

    with pytest.raises(NotSupportedError):
        Bare().create_gauge()
