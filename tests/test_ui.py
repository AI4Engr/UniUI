"""
Unified test file - demonstrates the refactored widgets system.
Supports multiple run modes.

Usage:
    python tests/test_ui.py                    # auto-detect framework
    python tests/test_ui.py --ui qt            # use Qt
    python tests/test_ui.py --mode simple      # simple mode
    python tests/test_ui.py --mode advanced    # advanced mode

Jupyter:
    from tests.test_ui import create_test_ui
    from uniui.display import show_ui
    show_ui(create_test_ui("jupyter", "simple"), "Simple Test", 600, 450)
"""
from uniui import use, VBox, HBox, Label, Button, LineEdit, TextArea, GroupBox, Dropdown, ComboBox
from uniui.display import show_ui, toggle_theme_and_refresh


def _set_btn_type(btn, btntype):
    """Set button visual category for Qt (stylesheet property) and wx (owner-draw)."""
    native = btn.get_native()
    try:
        native.setProperty("btntype", btntype)
        native.style().unpolish(native)
        native.style().polish(native)
    except Exception:
        pass
    try:
        if hasattr(native, 'set_btntype'):
            native.set_btntype(btntype)
    except Exception:
        pass


# ============================================================================
# Mode 1: Simple test
# ============================================================================

def _build_simple_ui():
    """Build simple test UI, returns root layout."""
    count = [0]

    title = Label(" Simple Test - VBox & HBox")
    input_field = LineEdit()
    btn_click = Button("Click Me")
    _set_btn_type(btn_click, "action")
    btn_clear = Button("Clear")
    _set_btn_type(btn_clear, "neutral")
    output = TextArea()
    output.set_maximum_height(150)
    status = Label("Status: Ready")

    def on_click():
        count[0] += 1
        name = input_field.get_text() or "Anonymous"
        msg = f"[{count[0]}] {name} clicked the button"
        output.append(msg)
        status.set_text(f"Status: {count[0]} click(s)")

    def on_clear():
        output.clear()
        status.set_text("Status: Cleared")
        count[0] = 0

    btn_click.connect(on_click)
    btn_clear.connect(on_clear)

    btn_row = HBox(btn_click, btn_clear)
    return VBox(title, input_field, btn_row, output, status)


# ============================================================================
# Mode 2: Advanced test
# ============================================================================

def _build_advanced_ui():
    """Build advanced test UI, returns root layout."""
    title = Label(" Advanced Test - Multiple Widgets")

    name_input = LineEdit()
    email_input = LineEdit()
    type_dropdown = Dropdown(["Option 1", "Option 2", "Option 3"])
    combo = ComboBox(["Apple", "Banana", "Orange"])

    btn_submit = Button("Submit")
    _set_btn_type(btn_submit, "action")
    btn_clear = Button("Clear")
    _set_btn_type(btn_clear, "neutral")

    output = TextArea()
    output.set_maximum_height(120)

    def on_submit():
        name = name_input.get_text()
        email = email_input.get_text()
        type_val = type_dropdown.get_text()
        fruit = combo.get_text()
        info = f"Form submitted:\n  Name: {name}\n  Email: {email}\n  Type: {type_val}\n  Fruit: {fruit}"
        output.append(info)
        output.append("---")

    def on_clear():
        name_input.set_text("")
        email_input.set_text("")
        output.clear()

    btn_submit.connect(on_submit)
    btn_clear.connect(on_clear)

    def _form_row(label_text, widget):
        lbl = Label(label_text)
        lbl.set_fixed_width(80)
        return HBox(lbl, widget)

    return VBox(
        title,
        _form_row("Name:", name_input),
        _form_row("Email:", email_input),
        _form_row("Type:", type_dropdown),
        _form_row("Fruit:", combo),
        HBox(btn_submit, btn_clear),
        output,
    )


# ============================================================================
# Public factory function
# ============================================================================

def create_test_ui(framework="auto", mode="simple"):
    """Create test UI.

    Args:
        framework: 'auto', 'qt', 'jupyter', 'wx', or 'tk'
        mode: 'simple' or 'advanced'

    Returns:
        The root layout container
    """
    use(framework)

    dark_mode_btn = Button("\u2600  Light Mode")
    _set_btn_type(dark_mode_btn, "neutral")

    def on_dark_mode():
        is_dark = toggle_theme_and_refresh()
        dark_mode_btn.set_text("\u2600  Light Mode" if is_dark else "\U0001f319  Dark Mode")

    dark_mode_btn.connect(on_dark_mode)

    if mode == "advanced":
        content = _build_advanced_ui()
    else:
        content = _build_simple_ui()

    title_row = HBox(Label("Widget Test" if mode == "simple" else "Advanced Test"))
    title_row.add_stretch()
    title_row.add_item(dark_mode_btn)

    return VBox(title_row, content)


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    import argparse
    from uniui import parse_args_ui

    parser = argparse.ArgumentParser(description='UniUI test runner')
    parser.add_argument('--ui', choices=['auto', 'qt', 'jupyter', 'wx', 'tk'], default='auto')
    parser.add_argument('--mode', choices=['simple', 'advanced'], default='simple')
    args = parser.parse_args()

    layout = create_test_ui(args.ui, args.mode)
    title = "Simple Test" if args.mode == "simple" else "Advanced Test"
    show_ui(layout, title, 600, 450)
