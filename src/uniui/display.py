"""
Display and theme refresh.

Shows a UniUI layout in a window (Qt/wx/Tk) or inline (Jupyter).
Also handles theme refresh: auto-detects framework and reapplies colors.

Public API:
- show_ui(layout, title, width, height) — display the UI
- refresh_theme(root_widget) — reapply current theme to all widgets
- toggle_theme_and_refresh() — toggle dark/light and refresh the active UI
"""
import sys
from .theme import THEME, toggle_theme as _toggle_theme

T = THEME

# Module-level root widget, set automatically by show_ui() at display time
_root_widget = None


# ============================================================================
# Qt Stylesheet Generator
# ============================================================================

def _generate_qt_stylesheet():
    """Generate Qt stylesheet from current THEME values."""
    r = T["border_radius"]
    return f"""
        QWidget {{
            background-color: {T["bg"]};
            font-family: "{T["font_family"]}";
            font-size: {T["font_size"]}pt;
        }}
        QLabel {{
            color: {T.get("fg_muted", T["fg"])};
            font-weight: 600;
            font-size: {T["font_size"]}pt;
            background: transparent;
        }}

        /* ── Display input ── */
        QLineEdit {{
            background-color: {T["bg_input"]};
            color: {T["fg"]};
            border: 2px solid {T["border"]};
            border-radius: {r}px;
            padding: 6px 10px;
            font-size: {T["font_size"]}pt;
            font-weight: 600;
            font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
        }}
        QLineEdit:focus {{
            border: 2px solid {T["accent"]};
        }}

        /* ── History text area ── */
        QTextEdit {{
            background-color: {T["bg_input"]};
            color: {T.get("fg_muted", T["fg"])};
            border: 1px solid {T["border"]};
            border-radius: {r}px;
            padding: {T["padding_inner"]}px;
            font-family: "Cascadia Code", "Consolas", monospace;
            font-size: 9pt;
        }}
        QTextEdit:focus {{
            border: 1px solid {T["accent"]};
        }}

        /* ── Base / numeric buttons ── */
        QPushButton {{
            background-color: {T["accent"]};
            color: {T["fg_button"]};
            border: none;
            border-radius: {r}px;
            padding: 5px 4px;
            font-size: 12pt;
            font-weight: 600;
            min-height: 32px;
        }}
        QPushButton:hover {{
            background-color: {T["accent_hover"]};
        }}
        QPushButton:pressed {{
            background-color: {T["accent_press"]};
        }}

        /* ── Operator buttons (+, −, ×, ÷, (, ), =num) ── */
        QPushButton[btntype="op"] {{
            background-color: {T.get("accent_op", T["accent"])};
        }}
        QPushButton[btntype="op"]:hover {{
            background-color: {T.get("accent_op_hover", T["accent_hover"])};
        }}
        QPushButton[btntype="op"]:pressed {{
            background-color: {T.get("accent_op_press", T["accent_press"])};
        }}

        /* ── Scientific buttons (sin, cos, tan, log, ln, √, xʸ, x², π, e) ── */
        QPushButton[btntype="sci"] {{
            background-color: {T.get("accent_sci", T["accent"])};
            font-size: 11pt;
        }}
        QPushButton[btntype="sci"]:hover {{
            background-color: {T.get("accent_sci_hover", T["accent_hover"])};
        }}
        QPushButton[btntype="sci"]:pressed {{
            background-color: {T.get("accent_sci_press", T["accent_press"])};
        }}

        /* ── Action buttons (=, C) ── */
        QPushButton[btntype="action"] {{
            background-color: {T.get("accent_action", T["accent"])};
            font-size: 14pt;
        }}
        QPushButton[btntype="action"]:hover {{
            background-color: {T.get("accent_action_hover", T["accent_hover"])};
        }}
        QPushButton[btntype="action"]:pressed {{
            background-color: {T.get("accent_action_press", T["accent_press"])};
        }}

        /* ── Neutral buttons (Dark Mode toggle, Clr Hist, ⌫) ── */
        QPushButton[btntype="neutral"] {{
            background-color: {T.get("accent_neutral", "#334155")};
            font-size: 10pt;
        }}
        QPushButton[btntype="neutral"]:hover {{
            background-color: {T.get("accent_neutral_hover", "#475569")};
        }}
        QPushButton[btntype="neutral"]:pressed {{
            background-color: {T.get("accent_neutral_press", "#64748b")};
        }}

        QComboBox {{
            background-color: {T["bg_input"]};
            color: {T["fg"]};
            border: 1px solid {T["border"]};
            border-radius: {r}px;
            padding: 4px {T["padding_inner"]}px;
        }}
        QComboBox:focus {{
            border: 1px solid {T["accent"]};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {T["bg_input"]};
            color: {T["fg"]};
            selection-background-color: {T["accent"]};
            selection-color: {T["fg_button"]};
        }}

        QGroupBox {{
            background-color: {T["bg_input"]};
            border: 1px solid {T["border"]};
            border-radius: {r}px;
            margin-top: 18px;
            padding: 12px {T["padding_inner"]}px {T["padding_inner"]}px {T["padding_inner"]}px;
            font-weight: bold;
            font-size: 9pt;
            color: {T.get("fg_muted", T["fg"])};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: {T.get("fg_muted", T["fg"])};
            font-size: 9pt;
        }}
    """


# ============================================================================
# Unified Theme Refresh (auto-detect framework)
# ============================================================================

def refresh_theme(root_widget):
    """Refresh UI theme on root_widget, auto-detecting the framework.

    Args:
        root_widget: The root widget stored by display.py at show-time.
    """
    if root_widget is None:
        return

    # Qt
    try:
        from PySide2.QtWidgets import QWidget
        if isinstance(root_widget, QWidget):
            refresh_theme_qt(root_widget)
            return
    except ImportError:
        pass

    # Tk
    try:
        import tkinter as tk
        if isinstance(root_widget, tk.Widget):
            refresh_theme_tk(root_widget.winfo_toplevel())
            return
    except ImportError:
        pass

    # wx
    try:
        import wx
        if isinstance(root_widget, wx.Window):
            refresh_theme_wx(root_widget)
            return
    except ImportError:
        pass

    # Jupyter
    try:
        import ipywidgets
        if isinstance(root_widget, ipywidgets.Widget):
            from .jupyter import refresh_theme_jupyter
            refresh_theme_jupyter(root_widget)
            return
    except ImportError:
        pass


def toggle_theme_and_refresh():
    """Toggle dark/light theme and refresh the active UI.

    Returns:
        bool: True if now dark mode.

    Example:
        dark_mode_button = Button("Dark Mode")
        dark_mode_button.connect(toggle_theme_and_refresh)
    """
    is_dark = _toggle_theme()
    refresh_theme(_root_widget)
    return is_dark


# ============================================================================
# Per-Framework Theme Refresh Functions
# ============================================================================

def refresh_theme_qt(root_widget):
    """Refresh Qt widget tree with current THEME values."""
    root_widget.setStyleSheet(_generate_qt_stylesheet())


def refresh_theme_tk(root):
    """Refresh Tkinter widget tree with current THEME values."""
    import tkinter as tk
    from tkinter import ttk

    def _refresh(w):
        try:
            cls_name = w.winfo_class()
            if cls_name == 'Frame':
                w.config(bg=T["bg"])
            elif cls_name == 'Labelframe':
                w.config(bg=T["bg"], fg=T["fg"])
            elif cls_name == 'Label':
                w.config(bg=T["bg"], fg=T["fg"])
            elif cls_name == 'Entry':
                w.config(bg=T["bg_input"], fg=T["fg"],
                         insertbackground=T["accent"],
                         highlightcolor=T["accent"],
                         highlightbackground=T["border"])
            elif cls_name == 'Canvas':
                # Canvas-based rounded button (TkPushButton)
                if hasattr(w, 'refresh_colors'):
                    try: w.config(bg=T['bg'])
                    except Exception: pass
                    w.refresh_colors()
            elif cls_name == 'Text':
                w.config(bg=T["bg_input"], fg=T["fg"],
                         highlightcolor=T["accent"],
                         highlightbackground=T["border"])
        except tk.TclError:
            pass
        for child in w.winfo_children():
            _refresh(child)

    # Update ttk style for Combobox
    style = ttk.Style()
    style.configure('TCombobox',
                    fieldbackground=T["bg_input"],
                    background=T["bg_input"],
                    foreground=T["fg"])

    root.config(bg=T["bg"])
    _refresh(root)


def refresh_theme_wx(panel):
    """Refresh wxPython widget tree with current THEME values."""
    import wx

    def _hex_to_wx(hex_color):
        h = hex_color.lstrip('#')
        return wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def _refresh(window):
        if hasattr(window, '_btntype'):
            # Owner-draw button: paint handler reads THEME directly on next Refresh()
            pass
        elif isinstance(window, wx.Button):
            # Fallback for any legacy native wx.Button
            window.SetBackgroundColour(_hex_to_wx(T["accent"]))
            window.SetForegroundColour(_hex_to_wx(T["fg_button"]))
        elif isinstance(window, (wx.TextCtrl, wx.Choice, wx.ComboBox)):
            window.SetBackgroundColour(_hex_to_wx(T["bg_input"]))
            window.SetForegroundColour(_hex_to_wx(T["fg"]))
        elif isinstance(window, wx.StaticBox):
            window.SetForegroundColour(_hex_to_wx(T["fg_muted"]))
            window.SetBackgroundColour(_hex_to_wx(T["bg"]))
        elif isinstance(window, wx.StaticText):
            window.SetForegroundColour(_hex_to_wx(T["fg"]))
            window.SetBackgroundColour(_hex_to_wx(T["bg"]))
        elif isinstance(window, wx.Panel):
            window.SetBackgroundColour(_hex_to_wx(T["bg"]))

        window.Refresh()

        for child in window.GetChildren():
            _refresh(child)

    panel.SetBackgroundColour(_hex_to_wx(T["bg"]))
    _refresh(panel)
    panel.Refresh()
    parent = panel.GetParent()
    parent.SetBackgroundColour(_hex_to_wx(T["bg"]))
    parent.Refresh()


class UniversalDisplay:
    """
    Universal UI display.

    Responsibility: automatically select the correct display method based on container type.
    Uses the strategy pattern.
    """

    @staticmethod
    def show(container, title="App", width=500, height=400):
        """
        Display a UI container (auto-detects framework).

        Args:
            container: UI container (VBox/HBox etc.)
            title: window title
            width: window width
            height: window height
        """
        native = container.get_native()

        # Store root widget reference at module level for theme refresh
        def _set_refresh_root(root_widget):
            global _root_widget
            _root_widget = root_widget

        # Try each display method in order (order matters)
        # Tkinter check must come before Qt, as Qt can interfere with Tkinter
        if UniversalDisplay._show_tkinter(native, title, width, height, _set_refresh_root):
            return

        if UniversalDisplay._show_qt(native, title, width, height, _set_refresh_root):
            return

        if UniversalDisplay._show_jupyter(native, _set_refresh_root):
            return

        if UniversalDisplay._show_wx(native, title, width, height, _set_refresh_root):
            return

        raise RuntimeError("Unrecognized UI framework!")

    # ========================================================================
    # Qt/PySide2 display
    # ========================================================================

    @staticmethod
    def _show_qt(native, title, width, height, _set_refresh_root=None):
        """Qt display method"""
        try:
            from PySide2.QtWidgets import QWidget, QApplication, QLayout
            from PySide2.QtGui import QFont
            from PySide2.QtCore import Qt

            # Check if it's a Qt layout
            if isinstance(native, QLayout):
                # Create QApplication if not already running
                app = QApplication.instance()
                if app is None:
                    app = QApplication(sys.argv)

                # Set application-wide font
                font = QFont(T["font_family"], T["font_size"])
                app.setFont(font)

                # Create the window
                widget = QWidget()
                widget.setLayout(native)
                widget.setWindowTitle(title)
                widget.setMinimumSize(width, height)

                # Add padding to the main widget
                p = T["padding"]
                widget.setContentsMargins(p, p, p, p)

                # Set modern stylesheet for better appearance
                widget.setStyleSheet(_generate_qt_stylesheet())

                # Set layout spacing for consistent appearance
                def apply_layout_spacing(layout):
                    """Recursively set spacing on all layouts"""
                    if layout is not None:
                        layout.setSpacing(T["spacing"])
                        pi = T["padding_inner"]
                        layout.setContentsMargins(pi, pi, pi, pi)
                        for i in range(layout.count()):
                            item = layout.itemAt(i)
                            if item.layout():
                                apply_layout_spacing(item.layout())
                            elif item.widget():
                                child_layout = item.widget().layout()
                                if child_layout:
                                    apply_layout_spacing(child_layout)

                apply_layout_spacing(native)

                # Store root widget reference for theme refresh
                if _set_refresh_root:
                    _set_refresh_root(widget)

                widget.show()

                # Run the event loop
                sys.exit(app.exec_())
                return True

        except (ImportError, AttributeError):
            pass

        return False

    # ========================================================================
    # Jupyter display
    # ========================================================================

    @staticmethod
    def _show_jupyter(native, _set_refresh_root=None):
        """Jupyter display method"""
        try:
            from IPython.display import display
            import ipywidgets

            # Check if it's an ipywidgets widget
            if isinstance(native, (ipywidgets.Widget, ipywidgets.Box)):
                # Store root widget reference for theme refresh
                if _set_refresh_root:
                    _set_refresh_root(native)

                # Apply initial theme
                from .jupyter import refresh_theme_jupyter
                refresh_theme_jupyter(native)

                display(native)
                return True

        except (ImportError, AttributeError):
            pass

        return False

    # ========================================================================
    # Tkinter display
    # ========================================================================

    @staticmethod
    def _show_tkinter(native, title, width=420, height=700, _set_refresh_root=None):
        """Tkinter display method"""
        try:
            import tkinter as tk

            # Check for virtual layout containers (TkVBoxLayout/TkHBoxLayout)
            # These have a build() method to create actual tk widgets
            if hasattr(native, 'build') and callable(native.build):
                # Get or create root window
                root = tk._default_root
                if root is None:
                    root = tk.Tk()
                root.title(title)
                root.geometry(f"{width}x{height}")
                root.resizable(False, True)   # fixed width, resizable height
                root.deiconify()

                # Build the widget tree with root as parent
                frame = native.build(root, is_root=True)
                frame.pack(fill='both', expand=True)

                # Store root widget reference for theme refresh
                if _set_refresh_root:
                    _set_refresh_root(frame)

                root.mainloop()
                return True

            # Fallback: check if it's a regular Tkinter widget
            if isinstance(native, tk.Widget):
                root = native.winfo_toplevel()
                root.title(title)
                root.geometry(f"{width}x{height}")
                root.resizable(False, True)
                root.deiconify()

                if isinstance(native, tk.Frame):
                    native.pack(fill='both', expand=True)

                # Store root widget reference for theme refresh
                if _set_refresh_root:
                    _set_refresh_root(native)

                root.mainloop()
                return True

        except (ImportError, AttributeError, tk.TclError):
            pass

        return False

    # ========================================================================
    # wxPython display
    # ========================================================================

    @staticmethod
    def _show_wx(native, title, width, height, _set_refresh_root=None):
        """wxPython display method"""
        try:
            import wx

            # Check if it's a wx.Sizer
            if isinstance(native, wx.Sizer):
                # Create app and window
                app = wx.App.Get()
                if not app:
                    app = wx.App()

                frame = wx.Frame(None, title=title, size=(width, height))
                panel = wx.Panel(frame)

                # Set panel background color
                h = T["bg"].lstrip('#')
                panel.SetBackgroundColour(wx.Colour(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)))

                # Reparent all widgets in the sizer to the panel
                def reparent_sizer_items(sizer, parent):
                    """Recursively reparent all widgets in a sizer to the given parent window"""
                    # Handle StaticBoxSizer: reparent the StaticBox itself
                    if isinstance(sizer, wx.StaticBoxSizer):
                        static_box = sizer.GetStaticBox()
                        if static_box:
                            static_box.Reparent(parent)
                    for item in sizer.GetChildren():
                        if item.IsWindow():
                            window = item.GetWindow()
                            window.Reparent(parent)
                            # Set better font for widgets
                            if isinstance(window, (wx.StaticText, wx.TextCtrl, wx.Button, wx.ComboBox, wx.Choice)):
                                font = window.GetFont()
                                font.SetPointSize(T["font_size"])
                                window.SetFont(font)
                        elif item.IsSizer():
                            reparent_sizer_items(item.GetSizer(), parent)

                reparent_sizer_items(native, panel)

                # Wrap with outer padding sizer so content has breathing room
                outer = wx.BoxSizer(wx.VERTICAL)
                outer.Add(native, 1, wx.EXPAND | wx.ALL, 6)
                panel.SetSizer(outer)

                # Destroy the factory's hidden temp parent frame (if any)
                for w in wx.GetTopLevelWindows():
                    if w is not frame and isinstance(w, wx.Frame) and not w.IsShown():
                        w.Destroy()

                # Add padding around the content
                panel.Layout()

                # Store root widget reference for theme refresh
                if _set_refresh_root:
                    _set_refresh_root(panel)

                frame.Centre()
                frame.Show()

                app.MainLoop()
                return True

        except (ImportError, AttributeError):
            pass

        return False


# ============================================================================
# Convenience functions
# ============================================================================

def show_ui(container, title="App", width=500, height=400):
    """
    Convenience function to display a UI.

    Args:
        container: UI container
        title: window title
        width: window width
        height: window height

    Example:
        vbox = factory.createVBox()
        vbox.addItem(label)
        show_ui(vbox, "My App")
    """
    UniversalDisplay.show(container, title, width, height)


# ============================================================================
# Framework-specific convenience functions
# ============================================================================

def show_qt(container, title="Qt App", width=500, height=400):
    """Force display using Qt"""
    from PySide2.QtWidgets import QWidget, QApplication
    import sys

    # Create QApplication first
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create the window
    widget = QWidget()
    widget.setLayout(container.get_native())
    widget.setWindowTitle(title)
    widget.setMinimumSize(width, height)
    widget.show()

    # Run the event loop
    sys.exit(app.exec_())


def show_jupyter(container):
    """Force display using Jupyter"""
    from IPython.display import display
    display(container.get_native())


def show_tkinter(container, title="Tkinter App"):
    """Force display using Tkinter"""
    import tkinter as tk

    native = container.get_native()
    if isinstance(native, tk.Frame):
        root = native.winfo_toplevel()
        root.title(title)
        root.mainloop()


def show_wx(container, title="wxPython App", width=500, height=400):
    """Force display using wxPython"""
    import wx

    app = wx.App.Get()
    if not app:
        app = wx.App()

    frame = wx.Frame(None, title=title, size=(width, height))
    panel = wx.Panel(frame)
    panel.SetSizer(container.get_native())

    frame.Centre()
    frame.Show()

    app.MainLoop()


# ============================================================================
# Usage example
# ============================================================================

if __name__ == "__main__":
    """
    Usage example:

    from uniui import create_factory
    from uniui.display import show_ui

    # Create UI
    factory = create_factory()
    vbox = factory.create_vbox()

    label = factory.create_label()
    label.set_text("Hello!")
    vbox.add_item(label)

    # Display (auto-detect framework)
    show_ui(vbox, "My App")

    # Or force a specific framework
    show_qt(vbox, "Qt App")
    show_jupyter(vbox)
    show_tkinter(vbox, "Tk App")
    show_wx(vbox, "wx App")
    """
    print(__doc__)
