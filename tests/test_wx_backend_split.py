"""The wx backend split, verified without wxPython installed.

wxPython is not available in this environment, so ``import uniui.wx`` raises
and none of the usual runtime checks can run. Rather than skip verification
silently, these tests stub ``wx`` with a module whose every attribute is a
fresh subclassable type. That is enough to execute the class bodies
(``class WxLabel(wx.StaticText)``) and the factory, which is what the split
actually put at risk: names dropped across the new module boundaries.

This does NOT verify wx *behaviour* - no real widget is ever constructed.
It verifies that the re-export surface and the cross-module wiring survived
the move.
"""
from __future__ import annotations

import importlib
import sys
import types

import pytest


class _Stub:
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, name):
        return _Stub()

    def __call__(self, *a, **k):
        return _Stub()


class _StubWxModule(types.ModuleType):
    """Hands out a distinct subclassable type per attribute, memoised.

    Memoising matters: ``wx.BoxSizer`` must be the *same* class each time or
    the ``isinstance`` checks inside the layout adapters would compare against
    a different type on every access.
    """

    def __getattr__(self, name):
        made = type(
            name,
            (object,),
            {"__init__": lambda s, *a, **k: None,
             "__getattr__": lambda s, n: _Stub()},
        )
        setattr(self, name, made)
        return made


@pytest.fixture
def wx_modules(monkeypatch):
    """Import ``uniui.wx`` against a stubbed wxPython."""
    monkeypatch.setitem(sys.modules, "wx", _StubWxModule("wx"))
    for name in [m for m in sys.modules if m.startswith("uniui.wx")
                 or m.startswith("uniui.backends.wx")]:
        monkeypatch.delitem(sys.modules, name, raising=False)
    shim = importlib.import_module("uniui.wx")
    primitives = importlib.import_module("uniui.backends.wx.primitives")
    return shim, primitives


#: Every name the flat pre-split ``uniui.wx`` exposed that the shim must keep.
#: ``_hex_to_wx`` and ``_WxGroupPanel`` are private but were reachable as
#: module attributes, so dropping them would still be a breaking change.
EXPECTED = [
    "WxButtonAdapter", "WxComboBox", "WxComboBoxAdapter", "WxDropdown",
    "WxDropdownAdapter", "WxGroupBox", "WxGroupBoxAdapter", "WxHBoxLayout",
    "WxHBoxLayoutAdapter", "WxImage", "WxImageAdapter", "WxLabel",
    "WxLabelAdapter", "WxLineEdit", "WxLineEditAdapter", "WxPushButton",
    "WxTabWidget", "WxTabWidgetAdapter", "WxTextAreaAdapter", "WxTextarea",
    "WxVBoxLayout", "WxVBoxLayoutAdapter", "WxWidgetFactory",
    "_WxGroupPanel", "_hex_to_wx",
]


@pytest.mark.parametrize("name", EXPECTED)
def test_the_shim_still_exports(name, wx_modules):
    shim, primitives = wx_modules
    assert hasattr(shim, name), f"uniui.wx no longer exports {name}"
    # Same object, not a copy - patching one must affect the other.
    assert getattr(shim, name) is getattr(primitives, name)


def test_the_shim_shares_the_live_theme_dict(wx_modules):
    """``T`` must alias THEME, which is mutated in place on a theme switch."""
    from uniui.theme import THEME
    shim, _ = wx_modules
    assert shim.T is THEME


def test_the_factory_resolves_every_primitive(wx_modules):
    """Catches names left dangling across the new module boundaries.

    The factory imports from all three leaf modules; a typo or a missed
    export shows up here as an ImportError or AttributeError.
    """
    shim, _ = wx_modules
    factory = shim.WxWidgetFactory
    # This legacy backend exposes camelCase only, unlike the maintained ones.
    for method in ("createLabel", "createButton", "createLineEdit",
                   "createTextArea", "createComboBox", "createDropdown",
                   "createVBox", "createHBox", "createTabWidget",
                   "createImage", "createGroupBox"):
        assert callable(getattr(factory, method, None)), \
            f"WxWidgetFactory.{method} is missing"


def test_importing_primitives_first_also_works(monkeypatch):
    """Import order must not matter - that is how the tk cycle surfaced."""
    monkeypatch.setitem(sys.modules, "wx", _StubWxModule("wx"))
    for name in [m for m in sys.modules if m.startswith("uniui.wx")
                 or m.startswith("uniui.backends.wx")]:
        monkeypatch.delitem(sys.modules, name, raising=False)
    primitives = importlib.import_module("uniui.backends.wx.primitives")
    shim = importlib.import_module("uniui.wx")
    assert shim.WxWidgetFactory is primitives.WxWidgetFactory
