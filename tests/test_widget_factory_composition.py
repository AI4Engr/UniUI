"""QtWidgetFactory/JupyterWidgetFactory/NiceGUIWidgetFactory used to gain their
Card/Table/AppShell/... methods via runtime setattr() inside a `_register()`
call, invoked as an import side effect.  That meant the methods were invisible
to static analysis (IDE jump-to-definition, type checkers, `vars()` on the
base class) and any real ImportError inside qt.py/jupyter.py/web.py during
that registration was silently swallowed by a bare `except ImportError: pass`.

They're explicit subclasses now: ``backends/<name>/primitives/factory.py``
defines a private _Base*WidgetFactory with the required + layout methods, and
``backends/<name>/factory.py`` defines the public factory class the rest of the
app actually uses, adding Card/Table/AppShell/etc. as real class-body methods.

The public factory classes are still reachable from the root
``*_components.py`` modules, which re-export them for backwards compatibility,
but those modules no longer define anything.
"""

import pytest


COMPONENT_METHODS = (
    "createCard", "createStatCard", "createMetricList", "createTable",
    "createSidebar", "createAppShell", "createBreadcrumb", "createGauge",
    "createChart", "createDrawer",
)


def _assert_methods_born_in_class_body(cls, methods):
    """A method's __qualname__ is only "ClassName.method_name" when it was
    defined with `def` inside that class's body.  `ClassName.x = lambda ...`
    or `setattr(ClassName, "x", some_function)` — the actual shape of the old
    `_register()` — produce a function whose __qualname__ still points at
    wherever it was *written*, not at the class it got attached to. `vars()`
    can't tell these apart: both end up in `cls.__dict__` either way.
    """
    own = vars(cls)
    for name in methods:
        assert name in own, f"{name} is not on the class at all"
        qualname = own[name].__qualname__
        assert qualname == f"{cls.__name__}.{name}", (
            f"{name} exists but was not defined in {cls.__name__}'s class "
            f"body (__qualname__={qualname!r}) — looks patched in"
        )


def test_qt_component_methods_are_defined_on_the_class_not_patched_in():
    pytest.importorskip("PySide2")
    from uniui.qt_components import QtWidgetFactory

    _assert_methods_born_in_class_body(QtWidgetFactory, COMPONENT_METHODS)


def test_jupyter_component_methods_are_defined_on_the_class_not_patched_in():
    pytest.importorskip("ipywidgets")
    from uniui.jupyter_components import JupyterWidgetFactory

    _assert_methods_born_in_class_body(JupyterWidgetFactory, COMPONENT_METHODS)


def test_web_component_methods_are_defined_on_the_class_not_patched_in():
    pytest.importorskip("nicegui")
    from uniui.web_components import NiceGUIWidgetFactory

    _assert_methods_born_in_class_body(NiceGUIWidgetFactory, COMPONENT_METHODS)


def test_base_factories_do_not_carry_component_methods():
    """The split point: base classes get only the required + layout widgets."""
    pytest.importorskip("PySide2")
    from uniui.qt import _BaseQtWidgetFactory

    own_methods = vars(_BaseQtWidgetFactory)
    for name in COMPONENT_METHODS:
        assert name not in own_methods, (
            f"{name} leaked onto the base factory; it belongs on the "
            f"qt_components subclass"
        )


def test_qt_widget_factory_subclasses_the_base_factory():
    pytest.importorskip("PySide2")
    from uniui.qt import _BaseQtWidgetFactory
    from uniui.qt_components import QtWidgetFactory

    assert issubclass(QtWidgetFactory, _BaseQtWidgetFactory)


def test_create_factory_returns_the_component_capable_subclass():
    pytest.importorskip("PySide2")
    import uniui

    factory = uniui.create_factory("qt")

    # create_card() would raise NotSupportedError if the base class' stub had
    # not been overridden by the subclass.
    card = factory.create_card()
    assert type(card).__name__ == "QtCardAdapter"


def test_a_real_import_error_in_the_qt_backend_is_no_longer_swallowed(monkeypatch):
    """The old code: `try: from uniui.qt import QtWidgetFactory ... except
    ImportError: pass`.  A genuine failure inside the Qt backend used to vanish
    with no trace.  Nothing in the factory chain wraps its imports in a
    try/except, so a broken backend now surfaces as a real traceback.

    The break is applied to ``backends.qt.primitives`` rather than ``uniui.qt``
    because that is what the factory actually depends on now: the canonical
    chain is ``registry -> backends.qt.factory -> primitives + components``,
    and ``uniui.qt`` is a leaf compatibility module nothing imports.
    """
    pytest.importorskip("PySide2")
    import sys

    for name in list(sys.modules):
        if name == "uniui.backends.qt" or name.startswith("uniui.backends.qt."):
            monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.delitem(sys.modules, "uniui.qt_components", raising=False)

    real_import = __import__

    def broken_import(name, *args, **kwargs):
        if name == "uniui.backends.qt.primitives":
            raise ImportError("simulated failure deep inside primitives")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", broken_import)

    with pytest.raises(ImportError, match="simulated failure"):
        import uniui.qt_components  # noqa: F401


def test_registry_reaches_factories_without_the_compat_modules(monkeypatch):
    """The canonical chain must not route through the root shims.

    Breaking every root compatibility module must leave ``create_factory('qt')``
    working. This is the structural guarantee of the split: production code
    depends on ``backends/<name>/factory.py``, and ``qt.py`` /
    ``qt_components.py`` exist only for external callers.
    """
    pytest.importorskip("PySide2")
    import sys

    shims = ("uniui.qt", "uniui.qt_components")
    for name in shims:
        monkeypatch.delitem(sys.modules, name, raising=False)
    for name in list(sys.modules):
        if name == "uniui.backends.qt" or name.startswith("uniui.backends.qt."):
            monkeypatch.delitem(sys.modules, name, raising=False)

    real_import = __import__

    def broken_import(name, *args, **kwargs):
        if name in shims:
            raise ImportError(f"{name} must not be on the canonical path")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", broken_import)

    from uniui.backends.registry import _create_factory

    factory = _create_factory("qt")
    assert type(factory).__name__ == "QtWidgetFactory"
    assert type(factory.create_card()).__name__ == "QtCardAdapter"
