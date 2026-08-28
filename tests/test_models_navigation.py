"""Unit tests for the shared navigation and breadcrumb models.

Backend-independent by design: this module must not import a GUI toolkit at
import time. The ``TestBackendsAgree`` class does import backends, but only
inside tests guarded by ``importorskip``.
"""
import pytest

from uniui.models.navigation import (
    SIDEBAR_COLLAPSED,
    SIDEBAR_EXPANDED,
    SIDEBAR_MAX,
    SIDEBAR_MIN,
    BreadcrumbModel,
    Crumb,
    NavItem,
    NavigationModel,
    clamp_width,
)

ITEMS = [
    ("dashboard", "Dashboard", "dashboard"),
    ("users", "Users", "users"),
    ("settings", "Settings", "settings"),
]


def _model(items=ITEMS):
    model = NavigationModel()
    for key, label, icon in items:
        model.add_item(key, label, icon)
    return model


class TestNavItem:
    def test_add_item_returns_the_item_it_stored(self):
        model = NavigationModel()
        item = model.add_item("k", "Label", "icon")
        assert item == NavItem("k", "Label", "icon")
        assert model.items == [item]

    def test_fields_are_coerced_to_strings(self):
        """Keys arrive from user route tables and are not always strings."""
        item = NavigationModel().add_item(1, 2, 3)
        assert item == NavItem("1", "2", "3")

    def test_icon_defaults_to_blank(self):
        assert NavigationModel().add_item("k", "Label").icon == ""

    @pytest.mark.parametrize(
        "label,expected", [("Users", "U"), ("dashboard", "D"), ("", "?")]
    )
    def test_initial_is_an_uppercase_first_character(self, label, expected):
        assert NavItem("k", label, "").initial() == expected


class TestLookup:
    def test_index_of_finds_the_row(self):
        assert _model().index_of("users") == 1

    def test_index_of_missing_key_is_negative_one(self):
        assert _model().index_of("nope") == -1

    def test_item_at_returns_the_item(self):
        assert _model().item_at(2).key == "settings"

    @pytest.mark.parametrize("index", [-1, -3, 3, 99])
    def test_item_at_out_of_range_returns_none(self, index):
        """``-1`` is what a list widget reports for "selection cleared", so it
        must not be read as "the last item"."""
        assert _model().item_at(index) is None

    def test_keys_preserves_insertion_order(self):
        assert _model().keys == ["dashboard", "users", "settings"]

    def test_len_and_iteration(self):
        model = _model()
        assert len(model) == 3
        assert [item.key for item in model] == model.keys


class TestGroups:
    def test_add_group_returns_a_group_item(self):
        model = NavigationModel()
        item = model.add_group("Section")
        assert item.is_group is True
        assert item.key == ""
        assert item.label == "Section"

    def test_regular_items_are_not_groups(self):
        assert _model().items[0].is_group is False

    def test_group_counts_toward_len_and_appears_in_items(self):
        model = _model()
        model.add_group("Section")
        assert len(model) == 4
        assert model.items[-1].label == "Section"

    def test_index_of_never_matches_a_group_even_by_blank_key(self):
        model = _model()
        model.add_group("Section")
        assert model.index_of("") == -1

    def test_index_of_still_finds_a_real_item_after_a_group(self):
        model = _model()
        model.add_group("Section")
        model.add_item("reports", "Reports", "reports")
        assert model.index_of("reports") == 4

    def test_set_active_cannot_target_a_group(self):
        model = _model()
        model.add_group("Section")
        assert model.set_active("") is False
        assert model.active == ""

    def test_is_active_is_false_for_a_group(self):
        model = _model()
        model.add_group("Section")
        model.set_active("users")
        group = model.items[-1]
        assert not model.is_active(group.key)

    def test_group_label_is_hidden_when_collapsed(self):
        model = _model()
        group = model.add_group("Section")
        assert model.label_for(group) == "Section"
        model.set_collapsed(True)
        assert model.label_for(group) == ""


class TestActive:
    def test_no_item_is_active_initially(self):
        model = _model()
        assert model.active == ""
        assert not model.is_active("dashboard")

    def test_set_active_marks_a_known_key(self):
        model = _model()
        assert model.set_active("users") is True
        assert model.active == "users"
        assert model.is_active("users")
        assert not model.is_active("dashboard")

    def test_unknown_key_is_rejected_and_keeps_the_previous_selection(self):
        """The core cross-backend fix.

        Qt guarded on membership and so ignored a bad key. Jupyter and Web
        looped every button, removing the highlight from all of them - which
        left the sidebar with nothing selected and stored the bogus key as
        active. Ignoring it is the reading that keeps the UI coherent.
        """
        model = _model()
        model.set_active("users")
        assert model.set_active("mystery") is False
        assert model.active == "users"
        assert model.is_active("users")

    def test_empty_key_is_not_active_even_when_active_is_blank(self):
        """Guards the ``"" == ""`` trap: with nothing selected, an item whose
        key is blank must not light up."""
        model = NavigationModel()
        model.add_item("", "Blank", "")
        assert not model.is_active("")


class TestCollapsed:
    def test_expanded_by_default(self):
        model = _model()
        assert model.collapsed is False
        assert model.width == SIDEBAR_EXPANDED

    def test_collapsing_switches_the_width(self):
        model = _model()
        model.set_collapsed(True)
        assert model.collapsed is True
        assert model.width == SIDEBAR_COLLAPSED

    def test_collapsed_flag_is_coerced_to_bool(self):
        model = _model()
        model.set_collapsed(1)
        assert model.collapsed is True

    def test_label_is_hidden_when_collapsed(self):
        model = _model()
        item = model.items[0]
        assert model.label_for(item) == "Dashboard"
        model.set_collapsed(True)
        assert model.label_for(item) == ""


class TestClampWidth:
    def test_a_width_in_range_passes_through(self):
        assert clamp_width(200) == 200

    def test_below_minimum_is_raised(self):
        assert clamp_width(10) == SIDEBAR_MIN

    def test_above_maximum_is_lowered(self):
        assert clamp_width(9999) == SIDEBAR_MAX

    def test_fixed_allows_the_collapsed_width(self):
        """Collapsing pins the sidebar below the normal minimum, so the fixed
        case has to use a lower floor or the collapse would be clamped away."""
        assert clamp_width(SIDEBAR_COLLAPSED, fixed=True) == SIDEBAR_COLLAPSED
        assert clamp_width(SIDEBAR_COLLAPSED) == SIDEBAR_MIN

    def test_fixed_still_caps_at_the_maximum(self):
        assert clamp_width(9999, fixed=True) == SIDEBAR_MAX

    def test_floats_and_strings_are_coerced(self):
        assert clamp_width(200.7) == 200
        assert clamp_width("200") == 200

    def test_the_range_is_internally_consistent(self):
        assert SIDEBAR_COLLAPSED < SIDEBAR_MIN <= SIDEBAR_EXPANDED <= SIDEBAR_MAX


class TestBreadcrumb:
    TRAIL = [
        {"label": "Home", "path": "/"},
        {"label": "Users", "path": "/users"},
        {"label": "Alice", "path": "/users/1"},
    ]

    def test_the_last_crumb_is_never_a_link(self):
        """It points at the page you are already on."""
        model = BreadcrumbModel()
        model.set_items(self.TRAIL)
        assert [c.is_link for c in model] == [True, True, False]

    def test_a_crumb_without_a_path_is_not_a_link(self):
        model = BreadcrumbModel()
        model.set_items([{"label": "Home"}, {"label": "X", "path": "/x"}])
        assert [c.is_link for c in model] == [False, False]

    def test_a_single_crumb_is_not_a_link(self):
        model = BreadcrumbModel()
        model.set_items([{"label": "Home", "path": "/"}])
        assert model.items[0].is_link is False

    def test_set_items_replaces_the_previous_trail(self):
        model = BreadcrumbModel()
        model.set_items(self.TRAIL)
        model.set_items([{"label": "Solo"}])
        assert len(model) == 1
        assert model.items[0].label == "Solo"

    def test_empty_trail(self):
        model = BreadcrumbModel()
        model.set_items([])
        assert len(model) == 0
        assert list(model) == []

    def test_missing_label_becomes_blank_not_none(self):
        assert Crumb({}).label == ""

    def test_a_none_path_is_treated_as_absent(self):
        assert Crumb({"label": "X", "path": None}).is_link is False

    def test_set_items_accepts_any_iterable(self):
        model = BreadcrumbModel()
        model.set_items(iter(self.TRAIL))
        assert len(model) == 3

    def test_separator_is_shared(self):
        assert BreadcrumbModel.SEPARATOR == "›"


class TestBackendsAgree:
    """Every backend must resolve navigation state the same way.

    Before the shared model these had drifted: ``set_active`` with an unknown
    key kept the selection in Qt but cleared every highlight in the browser
    backends, and the width clamp was written four separate times.
    """

    @staticmethod
    def _qt():
        """The QtWidgets module, with a QApplication guaranteed to exist."""
        pytest.importorskip("PySide2")
        from PySide2 import QtWidgets

        QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        return QtWidgets

    def test_qt_named_icon_does_not_leak_into_the_item_text(self):
        """Regression: the icon-name-vs-real-icon check used to be a
        hand-maintained set of three names that fell out of sync with the
        real icon registry (ADMIN_ICON_NAMES) - any icon added later (e.g.
        "components") rendered as literal text glued onto the label instead
        of becoming a real icon."""
        self._qt()
        from uniui.qt_components import QtSidebarAdapter
        from uniui.icons import ADMIN_ICON_NAMES

        sidebar = QtSidebarAdapter()
        for name in ADMIN_ICON_NAMES:
            sidebar.add_item(name, name.title(), name)
        for i, name in enumerate(ADMIN_ICON_NAMES):
            assert sidebar._list.item(i).text() == name.title()

    def test_qt_ignores_an_unknown_active_key(self):
        self._qt()
        from uniui.qt_components import QtSidebarAdapter

        sidebar = QtSidebarAdapter()
        for key, label, icon in ITEMS:
            sidebar.add_item(key, label, icon)
        sidebar.set_active("users")
        sidebar.set_active("mystery")
        assert sidebar._list.currentRow() == 1
        assert sidebar._model.active == "users"

    def test_jupyter_ignores_an_unknown_active_key(self):
        """Previously this cleared every ``uniui-active`` class."""
        pytest.importorskip("ipywidgets")
        from uniui.jupyter_components import JupyterSidebarAdapter

        sidebar = JupyterSidebarAdapter()
        for key, label, icon in ITEMS:
            sidebar.add_item(key, label, icon)
        sidebar.set_active("users")
        sidebar.set_active("mystery")
        classes = [list(b._dom_classes) for b in sidebar._buttons]
        assert "uniui-active" in classes[1]
        assert [c for c in classes if "uniui-active" in c] == [classes[1]]
        assert sidebar._model.active == "users"

    def test_jupyter_hides_labels_when_collapsed(self):
        pytest.importorskip("ipywidgets")
        from uniui.jupyter_components import JupyterSidebarAdapter

        sidebar = JupyterSidebarAdapter()
        for key, label, icon in ITEMS:
            sidebar.add_item(key, label, icon)
        assert [b.description for b in sidebar._buttons] == [
            "Dashboard", "Users", "Settings"
        ]
        sidebar.set_collapsed(True)
        assert [b.description for b in sidebar._buttons] == ["", "", ""]

    def test_qt_group_header_is_not_clickable(self):
        self._qt()
        from uniui.qt_components import QtSidebarAdapter

        sidebar = QtSidebarAdapter()
        sidebar.add_item("dashboard", "Dashboard", "dashboard")
        sidebar.add_group("Admin")
        sidebar.add_item("settings", "Settings", "settings")
        item = sidebar._list.item(1)
        from PySide2 import QtCore
        assert not (item.flags() & QtCore.Qt.ItemIsSelectable)
        assert not (item.flags() & QtCore.Qt.ItemIsEnabled)

    def test_qt_group_header_shows_the_label_uppercased(self):
        self._qt()
        from uniui.qt_components import QtSidebarAdapter

        sidebar = QtSidebarAdapter()
        sidebar.add_group("admin tools")
        assert sidebar._list.item(0).text() == "ADMIN TOOLS"

    def test_qt_group_header_blanks_when_collapsed(self):
        self._qt()
        from uniui.qt_components import QtSidebarAdapter

        sidebar = QtSidebarAdapter()
        sidebar.add_group("Admin")
        sidebar.set_collapsed(True)
        assert sidebar._list.item(0).text() == ""

    def test_qt_group_does_not_shift_real_item_selection(self):
        self._qt()
        from uniui.qt_components import QtSidebarAdapter

        sidebar = QtSidebarAdapter()
        sidebar.add_item("dashboard", "Dashboard", "dashboard")
        sidebar.add_group("Admin")
        sidebar.add_item("settings", "Settings", "settings")
        sidebar.set_active("settings")
        assert sidebar._list.currentRow() == 2

    def test_jupyter_group_header_renders_the_label_uppercased(self):
        pytest.importorskip("ipywidgets")
        from uniui.jupyter_components import JupyterSidebarAdapter

        sidebar = JupyterSidebarAdapter()
        sidebar.add_group("admin tools")
        assert "ADMIN TOOLS" in sidebar._buttons[0].value

    def test_jupyter_group_header_blanks_when_collapsed(self):
        pytest.importorskip("ipywidgets")
        from uniui.jupyter_components import JupyterSidebarAdapter

        sidebar = JupyterSidebarAdapter()
        sidebar.add_group("Admin")
        sidebar.set_collapsed(True)
        assert sidebar._buttons[0].value == ""

    def test_jupyter_group_is_never_marked_active(self):
        pytest.importorskip("ipywidgets")
        from uniui.jupyter_components import JupyterSidebarAdapter

        sidebar = JupyterSidebarAdapter()
        sidebar.add_item("dashboard", "Dashboard", "dashboard")
        sidebar.add_group("Admin")
        sidebar.set_active("dashboard")
        assert "uniui-active" not in sidebar._buttons[1]._dom_classes

    def test_web_group_header_renders_the_label_uppercased(self):
        pytest.importorskip("nicegui")
        from uniui.web_components import WebSidebarAdapter

        sidebar = WebSidebarAdapter()
        sidebar.add_group("admin tools")
        assert sidebar._buttons[0].text == "ADMIN TOOLS"

    def test_web_group_gets_the_collapsed_class_like_every_button(self):
        pytest.importorskip("nicegui")
        from uniui.web_components import WebSidebarAdapter

        sidebar = WebSidebarAdapter()
        sidebar.add_group("Admin")
        sidebar.set_collapsed(True)
        assert "uniui-collapsed" in sidebar._buttons[0]._classes

    def test_jupyter_collapsed_width_matches_the_model(self):
        pytest.importorskip("ipywidgets")
        from uniui.jupyter_components import JupyterSidebarAdapter

        sidebar = JupyterSidebarAdapter()
        sidebar.set_collapsed(True)
        assert sidebar._native.layout.width == f"{SIDEBAR_COLLAPSED}px"
        sidebar.set_collapsed(False)
        assert sidebar._native.layout.width == f"{SIDEBAR_EXPANDED}px"

    def test_jupyter_set_width_clamps(self):
        pytest.importorskip("ipywidgets")
        from uniui.jupyter_components import JupyterSidebarAdapter

        sidebar = JupyterSidebarAdapter()
        sidebar.set_width(9999)
        assert sidebar._native.layout.width == f"{SIDEBAR_MAX}px"
        sidebar.set_width(1)
        assert sidebar._native.layout.width == f"{SIDEBAR_MIN}px"

    def test_qt_breadcrumb_links_all_but_the_last(self):
        QtWidgets = self._qt()
        from uniui.qt_components import QtBreadcrumbAdapter

        crumbs = QtBreadcrumbAdapter()
        crumbs.set_items(TestBreadcrumb.TRAIL)
        buttons = crumbs.get_native().findChildren(QtWidgets.QPushButton)
        assert [b.text() for b in buttons] == ["Home", "Users"]

    def test_jupyter_breadcrumb_links_all_but_the_last(self):
        pytest.importorskip("ipywidgets")
        import ipywidgets as widgets

        from uniui.jupyter_components import JupyterBreadcrumbAdapter

        crumbs = JupyterBreadcrumbAdapter()
        crumbs.set_items(TestBreadcrumb.TRAIL)
        buttons = [
            child for child in crumbs.get_native().children
            if isinstance(child, widgets.Button)
        ]
        assert [b.description for b in buttons] == ["Home", "Users"]

    def test_qt_breadcrumb_click_reports_the_path(self):
        QtWidgets = self._qt()
        from uniui.qt_components import QtBreadcrumbAdapter

        seen = []
        crumbs = QtBreadcrumbAdapter()
        crumbs.on_click(seen.append)
        crumbs.set_items(TestBreadcrumb.TRAIL)
        buttons = crumbs.get_native().findChildren(QtWidgets.QPushButton)
        buttons[1].click()
        assert seen == ["/users"]

    def test_jupyter_breadcrumb_click_reports_the_path(self):
        """Pins the late-binding trap in the click lambda: every button must
        carry its own path, not the last crumb's."""
        pytest.importorskip("ipywidgets")
        import ipywidgets as widgets

        from uniui.jupyter_components import JupyterBreadcrumbAdapter

        seen = []
        crumbs = JupyterBreadcrumbAdapter()
        crumbs.on_click(seen.append)
        crumbs.set_items(TestBreadcrumb.TRAIL)
        buttons = [
            child for child in crumbs.get_native().children
            if isinstance(child, widgets.Button)
        ]
        buttons[0].click()
        buttons[1].click()
        assert seen == ["/", "/users"]
