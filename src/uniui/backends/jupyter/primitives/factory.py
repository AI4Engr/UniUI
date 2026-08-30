"""The base Jupyter widget factory for primitive controls.

``backends.jupyter.factory.JupyterWidgetFactory`` subclasses this to add the
Admin components, so a plain notebook never imports them.

Importing this module wraps every ``create*`` method via
:func:`_mark_created_widgets`. That is a one-shot, in-place mutation of the
class - calling it a second time would double-wrap every method, so the
``uniui.jupyter`` shim re-exports the result rather than re-applying it.
"""
from __future__ import annotations

from ....core import *
import ipywidgets as widgets
from .inputs import (
    JupyterCheckboxAdapter, JupyterComboBox, JupyterComboBoxAdapter,
    JupyterButtonAdapter, JupyterDropdown, JupyterDropdownAdapter,
    JupyterLineEdit, JupyterLineEditAdapter, JupyterNumberInputAdapter,
    JupyterPushButton, JupyterRadioGroupAdapter, JupyterSwitchAdapter,
    JupyterTextarea, JupyterTextAreaAdapter,
)
from .layouts import (
    JupyterGrid, JupyterGridAdapter, JupyterHBoxAdapter, JupyterHBoxLayout,
    JupyterOverlay, JupyterOverlayAdapter, JupyterScrollView,
    JupyterScrollViewAdapter, JupyterSplitPane, JupyterSplitPaneAdapter,
    JupyterTabWidget, JupyterTabWidgetAdapter, JupyterVBoxAdapter,
    JupyterVBoxLayout, JupyterWrap, JupyterWrapAdapter,
)
from .text import (
    JupyterGroupBox, JupyterGroupBoxAdapter, JupyterImage,
    JupyterImageAdapter, JupyterLabel, JupyterLabelAdapter,
)


class _BaseJupyterWidgetFactory(IWidgetFactory):
    """
    Base Jupyter Widget Factory — the core widgets every Jupyter app gets.

    backends.jupyter.factory.JupyterWidgetFactory subclasses this to add
    Card/Table/AppShell/etc.  create_factory() always returns that subclass;
    this base class is an internal split point, not something callers
    construct directly.

    Creates native Jupyter widgets and wraps them in adapters
    """

    def createLabel(self) -> ILabel:
        native = JupyterLabel()
        return JupyterLabelAdapter(native)

    def createButton(self) -> IButton:
        native = JupyterPushButton()
        return JupyterButtonAdapter(native)

    def createLineEdit(self) -> ILineEdit:
        native = JupyterLineEdit()
        return JupyterLineEditAdapter(native)

    def createTextArea(self) -> ITextArea:
        native = JupyterTextarea()
        return JupyterTextAreaAdapter(native)

    def createComboBox(self) -> IComboBox:
        native = JupyterComboBox()
        return JupyterComboBoxAdapter(native)

    def createDropdown(self) -> IDropdown:
        native = JupyterDropdown()
        return JupyterDropdownAdapter(native)

    def createCheckbox(self) -> ICheckbox:
        native = widgets.Checkbox(indent=False)
        return JupyterCheckboxAdapter(native)

    def createSwitch(self) -> ISwitch:
        native = widgets.ToggleButton()
        return JupyterSwitchAdapter(native)

    def createRadioGroup(self) -> IRadioGroup:
        native = widgets.RadioButtons(options=())
        return JupyterRadioGroupAdapter(native)

    def createNumberInput(self) -> INumberInput:
        native = widgets.BoundedFloatText(value=0, min=0, max=100, step=1)
        return JupyterNumberInputAdapter(native)

    def createVBox(self) -> IVBoxLayout:
        native = widgets.VBox()
        return JupyterVBoxAdapter(native)

    def createHBox(self) -> IHBoxLayout:
        native = widgets.HBox(layout=widgets.Layout(
            display="flex", flex_flow="row", width="100%",
        ))
        return JupyterHBoxAdapter(native)

    def createTabWidget(self) -> ITabWidget:
        native = JupyterTabWidget()
        return JupyterTabWidgetAdapter(native)

    def createImage(self) -> IImage:
        native = JupyterImage()
        return JupyterImageAdapter(native)

    def createGroupBox(self) -> IGroupBox:
        native = JupyterGroupBox()
        return JupyterGroupBoxAdapter(native)

    def createGrid(self, columns: int = 12) -> IGrid:
        return JupyterGridAdapter(columns)

    def createWrap(self) -> IWrap:
        return JupyterWrapAdapter()

    def createScrollView(self) -> IScrollView:
        return JupyterScrollViewAdapter()

    def createSplitPane(self, orientation: str = "horizontal") -> ISplitPane:
        return JupyterSplitPaneAdapter(orientation)

    def createOverlay(self) -> IOverlay:
        return JupyterOverlayAdapter()
def _mark_created_widgets(factory_class) -> None:
    """Tag every widget the factory creates so the base stylesheet reaches it.

    Wrapping the methods in one place keeps new create* methods covered without
    each having to remember the marker class.
    """
    import functools

    for name in [n for n in vars(factory_class) if n.startswith("create")]:
        original = getattr(factory_class, name)

        @functools.wraps(original)
        def marked(self, *args, _original=original, **kwargs):
            widget = _original(self, *args, **kwargs)
            # Imported lazily: styles -> ..runtime -> ..components -> this module.
            from .styles import mark
            mark(widget)
            return widget

        setattr(factory_class, name, marked)

_mark_created_widgets(_BaseJupyterWidgetFactory)
