"""Backend-independent contracts: exceptions, layout models, widget interfaces.

Split out of the former monolithic ``uniui.core``. ``uniui.core`` still
re-exports every name from here, so ``from uniui.core import *`` - which every
backend does - keeps working unchanged.
"""

from __future__ import annotations

from .exceptions import (
    ConfigurationError, InvalidValueError, NotSupportedError,
    UniUIException, WidgetCreationError,
)
from .layout import (
    Breakpoints, DEFAULT_BREAKPOINTS, LayoutItem, LayoutSpec, SizeSpec,
)
from .widgets import (
    IButton, IComboBox, IDropdown, IGrid, IGroupBox, IHBoxLayout, IImage,
    ILabel, ILayoutOnly, ILineEdit, IOverlay, IScrollView, ISplitPane,
    ITabWidget, ITextArea, IVBoxLayout, IWidget, IWidgetFactory, IWrap,
)
