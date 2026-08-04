"""Qt QSS fragments shared by more than one Admin component.

Per-component QSS lives with its component. What stays here is the QSS with
more than one owner: the scrollbar rules (which ``qt_style`` also serves to
the plain controls) and the card frame (shared by Card and Drawer).

Every builder reads the live palette at call time, so a theme switch is picked
up simply by calling them again.
"""
from __future__ import annotations

from .runtime import C, M

_SCROLLBAR_TEMPLATE = """
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: %(scrollbar)s;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: %(scrollbar)s;
    border-radius: 4px;
    min-width: 28px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }
"""


def scrollbar_rules() -> str:
    """Scrollbar QSS for the active theme.

    Widgets that set a stylesheet on themselves stop inheriting an ancestor's
    scrollbar rules, so every such widget has to embed these directly.
    """
    return _SCROLLBAR_TEMPLATE % C


def card_style() -> str:
    return f"""
    QFrame[card="1"] {{
        background: {C['surface']};
        border: 1px solid {C['border']};
        border-radius: {M['radius_large']}px;
    }}
"""
