"""Base widget styling belongs to the library, not to examples/.

Before qt_style existed, the QSS for ordinary controls (QComboBox, QTabWidget,
QLineEdit, ...) lived in examples/admin_demo.py, so an application built
directly on the Qt backend got unstyled native widgets.  These tests pin the
styling to the library and keep it following the admin theme.
"""

import pytest


pytestmark = pytest.mark.qt


BASE_SELECTORS = (
    "QPushButton",
    "QLineEdit",
    "QComboBox",
    "QTabBar::tab",
    "QScrollBar::handle:vertical",
)


def test_factory_styles_the_application_without_touching_examples():
    pytest.importorskip("PySide2")
    import uniui

    uniui.use("qt")
    factory = uniui._get_factory()

    qss = factory.app.styleSheet()
    for selector in BASE_SELECTORS:
        assert selector in qss, f"{selector} is unstyled for plain Qt apps"


def test_base_stylesheet_has_no_unsubstituted_placeholders():
    pytest.importorskip("PySide2")
    from uniui.qt_style import base_stylesheet, scrollbar_stylesheet

    for qss in (base_stylesheet(), scrollbar_stylesheet()):
        assert "%(" not in qss


def test_base_style_follows_the_admin_theme():
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.qt_components import set_admin_theme
    from uniui.qt_style import apply_app_style, base_stylesheet

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    apply_app_style(app)
    try:
        set_admin_theme(False)
        light_sheet, light_app = base_stylesheet(), app.styleSheet()
        set_admin_theme(True)

        assert base_stylesheet() != light_sheet
        # set_admin_theme must restyle already-styled targets in place.
        assert app.styleSheet() != light_app
    finally:
        set_admin_theme(False)


def test_self_styled_widgets_embed_their_own_scrollbar_rules():
    """QTableWidget calls setStyleSheet() on itself.

    That shadows the application stylesheet for its subtree, so the table has to
    carry scrollbar rules directly or it falls back to the native scrollbar with
    arrow buttons.
    """
    pytest.importorskip("PySide2")
    from PySide2 import QtWidgets
    from uniui.qt_components import QtTableAdapter

    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    qss = QtTableAdapter()._table.styleSheet()

    assert "QScrollBar::handle:vertical" in qss
    # Zero-sized arrow buttons are what keep the scrollbar flat.
    assert "QScrollBar::add-line:vertical" in qss


def test_metric_list_reports_unsupported_rather_than_attribute_error():
    """create_metric_list() had an alias but no base stub, so it raised
    AttributeError instead of NotSupportedError on backends without admin."""
    from uniui.core import NotSupportedError
    from uniui.tk import TkWidgetFactory

    factory = TkWidgetFactory.__new__(TkWidgetFactory)
    with pytest.raises(NotSupportedError):
        factory.create_metric_list()
