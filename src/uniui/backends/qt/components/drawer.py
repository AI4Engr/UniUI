"""Qt IDrawer: a side panel that slides in over the shell."""
from __future__ import annotations

from PySide2 import QtCore, QtWidgets

from ...._adapter_mixins import EnableMixin, SizeMixin, VisibilityMixin
from ....components import IDrawer
from ..effects import motion_duration
from ..icons import admin_icon
from ..runtime import C, as_widget, clear_layout, track_themed

class QtDrawerAdapter(VisibilityMixin, EnableMixin, SizeMixin, IDrawer):
    def __init__(self):
        self._dialog = QtWidgets.QDialog()
        self._dialog.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint)
        self._dialog.setModal(False)
        self._dialog.setFixedWidth(360)
        self._dialog.setProperty("adminDrawer", "1")
        layout = QtWidgets.QVBoxLayout(self._dialog)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(16)
        header = QtWidgets.QHBoxLayout()
        self._title = QtWidgets.QLabel("")
        self._title.setProperty("drawerTitle", "1")
        self._close_button = QtWidgets.QToolButton()
        self._close_button.setIcon(admin_icon("close", C["text_muted"], 20))
        self._close_button.setAccessibleName("Close drawer")
        self._close_button.clicked.connect(self.close)
        header.addWidget(self._title, stretch=1)
        header.addWidget(self._close_button)
        self._content = QtWidgets.QWidget()
        self._content_layout = QtWidgets.QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(header)
        layout.addWidget(self._content, stretch=1)
        self._open = False
        self._animation = None
        track_themed(self, self._dialog)
        self.apply_theme()

    def get_native(self): return self._dialog
    def set_title(self, title: str) -> None: self._title.setText(str(title))
    def set_content(self, widget) -> None:
        clear_layout(self._content_layout)
        self._content_layout.addWidget(as_widget(widget))
    def open(self) -> None:
        parent = QtWidgets.QApplication.activeWindow()
        if parent is not None and parent is not self._dialog:
            self._dialog.setParent(
                parent, QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint
            )
            height = parent.height()
            target = QtCore.QRect(parent.width() - 360, 0, 360, height)
            start = QtCore.QRect(parent.width(), 0, 360, height)
        else:
            screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
            target = QtCore.QRect(screen.right() - 359, screen.top(), 360, screen.height())
            start = QtCore.QRect(screen.right() + 1, screen.top(), 360, screen.height())
        self._dialog.setGeometry(start)
        self._dialog.show(); self._dialog.raise_()
        self._animate_geometry(start, target)
        self._open = True
    def close(self) -> None:
        if not self._dialog.isVisible():
            self._open = False; return
        start = self._dialog.geometry()
        target = QtCore.QRect(start.right() + 1, start.top(), start.width(), start.height())
        animation = self._animate_geometry(start, target)
        animation.finished.connect(self._dialog.hide)
        self._open = False
    def toggle(self) -> None: self.close() if self._open else self.open()
    def is_open(self) -> bool: return self._open
    def _animate_geometry(self, start, end):
        animation = QtCore.QPropertyAnimation(self._dialog, b"geometry", self._dialog)
        animation.setStartValue(start); animation.setEndValue(end)
        animation.setDuration(motion_duration(190))
        animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        animation.start(); self._animation = animation
        return animation
    def apply_theme(self) -> None:
        self._dialog.setStyleSheet(
            f"QDialog[adminDrawer='1'] {{background:{C['surface']};"
            f"border-left:1px solid {C['border']};}}"
            f"QLabel[drawerTitle='1'] {{color:{C['text']};font-size:18px;"
            "font-weight:700;background:transparent;}"
            "QToolButton {background:transparent;border:none;padding:5px;}"
            f"QToolButton:hover {{background:{C['surface_subtle']};border-radius:8px;}}"
        )
        self._close_button.setIcon(admin_icon("close", C["text_muted"], 20))
