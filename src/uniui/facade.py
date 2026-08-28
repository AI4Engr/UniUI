"""Convenience constructors and the legacy ``UniUI`` facade class.

Every function here is sugar over the active factory: they exist so callers can
write ``Label("hi")`` instead of ``_get_factory().create_label()``. They are
re-exported from ``uniui`` and that remains the documented import path.

``_get_factory`` is imported as a *function* and called per construction, never
bound to a factory instance at import time - ``use()`` swaps the active backend
underneath us, and a bound instance would silently keep building widgets for
the previous one.
"""

from __future__ import annotations

from .backends.registry import _create_factory, _get_factory
from .components import (
    IAppShell, IBadge, IBreadcrumb, ICard, IChart, IDrawer, IGauge,
    IMetricList, IProgressBar, ISidebar, IStatCard, ITable,
)
from .core import (
    IButton, IComboBox, IDropdown, IGrid, IGroupBox, IHBoxLayout, IImage,
    ILabel, ILineEdit, IOverlay, IScrollView, ISplitPane, ITabWidget,
    ITextArea, IVBoxLayout, IWidget, IWrap, LayoutSpec,
)


def Label(text: str = "") -> ILabel:
    """Create a label widget"""
    label = _get_factory().create_label()
    if text:
        label.set_text(text)
    return label


def Button(text: str = "", on_click=None) -> IButton:
    """Create a button widget"""
    button = _get_factory().create_button()
    if text:
        button.set_text(text)
    if on_click:
        button.connect(on_click)
    return button


def LineEdit(text: str = "", on_change=None) -> ILineEdit:
    """Create a line edit widget"""
    line_edit = _get_factory().create_line_edit()
    if text:
        line_edit.set_text(text)
    if on_change:
        line_edit.on_change(on_change)
    return line_edit


def TextArea(text: str = "", on_change=None) -> ITextArea:
    """Create a text area widget"""
    text_area = _get_factory().create_text_area()
    if text:
        text_area.set_text(text)
    if on_change:
        text_area.on_change(on_change)
    return text_area


def ComboBox(items=None, on_change=None) -> IComboBox:
    """Create a combo box widget"""
    combo = _get_factory().create_combo_box()
    if items:
        for item in items:
            combo.add_item(item)
    if on_change:
        combo.on_change(on_change)
    return combo


def Dropdown(items=None, on_change=None) -> IDropdown:
    """Create a dropdown widget"""
    dropdown = _get_factory().create_dropdown()
    if items:
        for item in items:
            dropdown.add_item(item)
    if on_change:
        dropdown.on_change(on_change)
    return dropdown


def VBox(*children) -> IVBoxLayout:
    """Create a vertical box layout"""
    vbox = _get_factory().create_vbox()
    for child in children:
        if child is not None:
            vbox.add_item(child)
    return vbox


def HBox(*children) -> IHBoxLayout:
    """Create a horizontal box layout"""
    hbox = _get_factory().create_hbox()
    for child in children:
        if child is not None:
            hbox.add_item(child)
    return hbox


def Column(*children, spec: LayoutSpec = None) -> IVBoxLayout:
    """Create a vertical column layout (alias for VBox with optional LayoutSpec)"""
    col = _get_factory().create_vbox()
    if spec is not None:
        col.set_spec(spec)
    for child in children:
        if child is not None:
            col.add_item(child)
    return col


def Row(*children, spec: LayoutSpec = None) -> IHBoxLayout:
    """Create a horizontal row layout (alias for HBox with optional LayoutSpec)"""
    row = _get_factory().create_hbox()
    if spec is not None:
        row.set_spec(spec)
    for child in children:
        if child is not None:
            row.add_item(child)
    return row


def Grid(columns: int = 12, spec: LayoutSpec = None) -> IGrid:
    """Create a grid layout with the given number of columns."""
    grid = _get_factory().create_grid(columns)
    if spec is not None:
        grid.set_spec(spec)
    return grid


def Wrap(spec: LayoutSpec = None) -> IWrap:
    """Create a wrapping flow layout."""
    wrap = _get_factory().create_wrap()
    if spec is not None:
        wrap.set_spec(spec)
    return wrap


def ScrollView(content=None, max_height: int = None) -> IScrollView:
    """Create a scrollable container. Optionally set initial content and max height."""
    sv = _get_factory().create_scroll_view()
    if max_height is not None:
        sv.set_max_height(max_height)
    if content is not None:
        sv.set_content(content)
    return sv


def SplitPane(first=None, second=None, orientation: str = "horizontal",
              ratio: float = 0.5) -> ISplitPane:
    """Create a two-pane split container."""
    sp = _get_factory().create_split_pane(orientation)
    if first is not None:
        sp.set_first(first)
    if second is not None:
        sp.set_second(second)
    sp.set_sizes(ratio)
    return sp


def Overlay(*layers) -> IOverlay:
    """Create a stacked overlay container. First layer is active by default."""
    ov = _get_factory().create_overlay()
    for layer in layers:
        if layer is not None:
            ov.add_layer(layer)
    return ov


def Card(title: str = "", subtitle: str = "", content=None) -> ICard:
    """Create a titled card container."""
    card = _get_factory().create_card()
    if title:
        card.set_title(title)
    if subtitle:
        card.set_subtitle(subtitle)
    if content is not None:
        card.set_content(content)
    return card


def StatCard(label: str = "", value: str = "", unit: str = "",
             trend: float = 0.0, status: str = "ok") -> IStatCard:
    """Create a metric stat card."""
    sc = _get_factory().create_stat_card()
    if label:
        sc.set_label(label)
    if value:
        sc.set_value(value)
    if unit:
        sc.set_unit(unit)
    sc.set_trend(trend)
    sc.set_status(status)
    return sc


def MetricList(items=None) -> IMetricList:
    """Create a compact key/value metric list."""
    ml = _get_factory().create_metric_list()
    if items is not None:
        ml.set_items(items)
    return ml


def Badge(text: str = "", status: str = "neutral") -> IBadge:
    """Create a small status pill."""
    badge = _get_factory().create_badge()
    if text:
        badge.set_text(text)
    badge.set_status(status)
    return badge


def ProgressBar(value: float = 0, status: str = "neutral") -> IProgressBar:
    """Create a progress bar."""
    bar = _get_factory().create_progress_bar()
    bar.set_value(value)
    bar.set_status(status)
    return bar


def Table(columns=None, rows=None) -> ITable:
    """Create a data table."""
    tbl = _get_factory().create_table()
    if columns is not None:
        tbl.set_columns(columns)
    if rows is not None:
        tbl.set_rows(rows)
    return tbl


def Sidebar() -> ISidebar:
    """Create a navigation sidebar."""
    return _get_factory().create_sidebar()


def AppShell(header=None, sidebar=None, content=None, footer=None) -> IAppShell:
    """Create an application shell."""
    shell = _get_factory().create_app_shell()
    if header is not None:
        shell.set_header(header)
    if sidebar is not None:
        shell.set_sidebar(sidebar)
    if content is not None:
        shell.set_content(content)
    if footer is not None:
        shell.set_footer(footer)
    return shell


def Breadcrumb(items=None) -> IBreadcrumb:
    """Create a breadcrumb navigation widget."""
    bc = _get_factory().create_breadcrumb()
    if items is not None:
        bc.set_items(items)
    return bc


def Gauge(label: str = "", value: float = 0.0, unit: str = "",
          minimum: float = 0.0, maximum: float = 100.0,
          status: str = "ok") -> IGauge:
    gauge = _get_factory().create_gauge()
    gauge.set_range(minimum, maximum)
    gauge.set_label(label)
    gauge.set_unit(unit)
    gauge.set_status(status)
    gauge.set_value(value)
    return gauge


def Chart(chart_type: str = "line", title: str = "", x=None,
          series=None, max_points: int = 120, **options) -> IChart:
    if "type" in options:
        chart_type = options.pop("type")
    if options:
        unknown = ", ".join(sorted(options))
        raise TypeError(f"Unknown Chart option(s): {unknown}")
    chart = _get_factory().create_chart()
    chart.set_type(chart_type)
    chart.set_title(title)
    chart.set_max_points(max_points)
    chart.set_data(list(x or []), list(series or []))
    return chart


def Drawer(title: str = "", content=None) -> IDrawer:
    drawer = _get_factory().create_drawer()
    drawer.set_title(title)
    if content is not None:
        drawer.set_content(content)
    return drawer


def TabWidget() -> ITabWidget:
    """Create a tab widget"""
    return _get_factory().create_tab_widget()


def GroupBox(title: str = "", layout=None) -> IGroupBox:
    """Create a group box widget"""
    group = _get_factory().create_group_box()
    if title:
        group.set_title(title)
    if layout:
        group.set_layout(layout)
    return group


def Image(path: str = "") -> IImage:
    """Create an image widget"""
    image = _get_factory().create_image()
    if path:
        image.set_image(path)
    return image


class UniUI:
    """Backward compatible UniUI facade class"""

    _KIND_MAP = {
        'label':       'create_label',
        'button':      'create_button',
        'line_edit':   'create_line_edit',
        'text_area':   'create_text_area',
        'combo_box':   'create_combo_box',
        'dropdown':    'create_dropdown',
        'vbox':        'create_vbox',
        'hbox':        'create_hbox',
        'tab_widget':  'create_tab_widget',
        'group_box':   'create_group_box',
        'image':       'create_image',
        'grid':        'create_grid',
        'wrap':        'create_wrap',
        'scroll_view': 'create_scroll_view',
        'split_pane':  'create_split_pane',
        'overlay':     'create_overlay',
    }

    def __init__(self, framework: str = 'auto'):
        self._framework = framework
        self._factory = _create_factory(framework)

    @property
    def framework(self) -> str:
        return self._framework

    def create(self, kind: str) -> IWidget:
        """Create a widget by kind string"""
        method = self._KIND_MAP.get(kind)
        if method is None:
            raise ValueError(f"Unknown widget kind: {kind}")
        return getattr(self._factory, method)()

    def label(self) -> ILabel:        return self._factory.create_label()
    def button(self) -> IButton:      return self._factory.create_button()
    def line_edit(self) -> ILineEdit: return self._factory.create_line_edit()
    def text_area(self) -> ITextArea: return self._factory.create_text_area()
    def combo_box(self) -> IComboBox: return self._factory.create_combo_box()
    def dropdown(self) -> IDropdown:  return self._factory.create_dropdown()
    def vbox(self) -> IVBoxLayout:    return self._factory.create_vbox()
    def hbox(self) -> IHBoxLayout:    return self._factory.create_hbox()
    def tab_widget(self) -> ITabWidget: return self._factory.create_tab_widget()
    def group_box(self) -> IGroupBox: return self._factory.create_group_box()
    def image(self) -> IImage:        return self._factory.create_image()
