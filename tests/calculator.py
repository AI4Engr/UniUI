"""
Scientific Calculator
Demonstrates advanced layout with grid-like button arrangement using DSL API

Features:
- Basic arithmetic operations
- Scientific functions (sin, cos, tan, log, sqrt, power)
- Constants (π, e)
- Expression evaluation with brackets
- Calculation history
- Dark mode toggle

Usage:
    python tests/calculator.py           # Auto-detect UI
    python tests/calculator.py --ui qt   # Qt
    python tests/calculator.py --ui wx   # wxPython
    python tests/calculator.py --ui tk   # Tkinter

Jupyter:
    from tests.calculator import create_calculator_ui
    from uniui.display import show_ui
    show_ui(create_calculator_ui("jupyter"), "Calculator", 400, 600)
"""
import math
from uniui import use, VBox, HBox, Label, Button, LineEdit, TextArea, GroupBox
from uniui.display import show_ui, toggle_theme_and_refresh


def _set_btn_type(btn, btntype):
    """Set button visual category for Qt (stylesheet property) and wx (owner-draw)."""
    native = btn.get_native()
    # Qt: dynamic property drives stylesheet selectors
    try:
        native.setProperty("btntype", btntype)
        native.style().unpolish(native)
        native.style().polish(native)
    except Exception:
        pass
    # wx: owner-draw paint handler reads _btntype directly
    try:
        if hasattr(native, 'set_btntype'):
            native.set_btntype(btntype)
    except Exception:
        pass


def create_calculator_ui(framework="auto"):
    """Create scientific calculator UI.

    Args:
        framework: 'auto', 'qt', 'jupyter', 'wx', or 'tk'

    Returns:
        The root layout container
    """
    use(framework)

    # --- State ---
    expression = ""
    history_lines = []

    # --- Widgets ---
    dark_mode_btn = Button("☀  Light Mode")
    display = LineEdit("")
    display.set_fixed_height(46)
    history_area = TextArea("")
    history_area.set_maximum_height(70)

    # Helper to create a button
    def make_button(text):
        btn = Button(text)
        return btn

    # Button grid - scientific calculator layout
    btn_clear = make_button("C")
    btn_back = make_button("⌫")
    btn_open_paren = make_button("(")
    btn_close_paren = make_button(")")

    btn_sin = make_button("sin")
    btn_cos = make_button("cos")
    btn_tan = make_button("tan")
    btn_log = make_button("log")

    btn_ln = make_button("ln")
    btn_sqrt = make_button("√")
    btn_power = make_button("xʸ")
    btn_square = make_button("x²")

    btn_pi = make_button("π")
    btn_e = make_button("e")
    btn_div = make_button("÷")
    btn_mul = make_button("×")

    btn_7 = make_button("7")
    btn_8 = make_button("8")
    btn_9 = make_button("9")
    btn_sub = make_button("−")

    btn_4 = make_button("4")
    btn_5 = make_button("5")
    btn_6 = make_button("6")
    btn_add = make_button("+")

    btn_1 = make_button("1")
    btn_2 = make_button("2")
    btn_3 = make_button("3")
    btn_equals = make_button("=")

    btn_0 = make_button("0")
    btn_dot = make_button(".")
    btn_neg = make_button("±")
    btn_clear_hist = make_button("Clr Hist")

    # --- Assign button visual categories ---
    # Action: bright orange for C and =
    _set_btn_type(btn_clear, "action")
    _set_btn_type(btn_equals, "action")

    # Neutral: subtle slate for dark-mode toggle, backspace, clear history
    _set_btn_type(dark_mode_btn, "neutral")
    _set_btn_type(btn_back, "neutral")
    _set_btn_type(btn_clear_hist, "neutral")

    # Operator: teal for arithmetic operators and parentheses
    for b in [btn_add, btn_sub, btn_mul, btn_div,
              btn_open_paren, btn_close_paren, btn_neg, btn_dot]:
        _set_btn_type(b, "op")

    # Scientific: violet for all scientific functions and constants
    for b in [btn_sin, btn_cos, btn_tan, btn_log, btn_ln,
              btn_sqrt, btn_power, btn_square, btn_pi, btn_e]:
        _set_btn_type(b, "sci")

    # Numeric buttons: default indigo (no explicit type needed — falls back to base QPushButton)

    # --- Layout ---
    title_row = HBox(Label("Scientific Calculator"))
    title_row.add_stretch()
    title_row.add_item(dark_mode_btn)

    # Display group
    display_group = GroupBox("Display", layout=VBox(display))

    # Button grid - using nested HBox/VBox
    buttons_layout = VBox(
        HBox(btn_clear, btn_back, btn_open_paren, btn_close_paren),
        HBox(btn_sin, btn_cos, btn_tan, btn_log),
        HBox(btn_ln, btn_sqrt, btn_power, btn_square),
        HBox(btn_pi, btn_e, btn_div, btn_mul),
        HBox(btn_7, btn_8, btn_9, btn_sub),
        HBox(btn_4, btn_5, btn_6, btn_add),
        HBox(btn_1, btn_2, btn_3, btn_equals),
        HBox(btn_0, btn_dot, btn_neg, btn_clear_hist),
    )

    buttons_group = GroupBox("Keypad", layout=buttons_layout)

    # History group
    history_group = GroupBox("History", layout=VBox(history_area))

    main_layout = VBox(title_row, display_group, buttons_group, history_group)

    # --- Helper Functions ---
    def update_display():
        """Update display with current expression"""
        display.set_text(expression)

    def add_to_history(expr, result):
        """Add calculation to history"""
        history_lines.append(f"{expr} = {result}")
        if len(history_lines) > 10:
            history_lines.pop(0)
        history_area.set_text("\n".join(history_lines))

    def append_char(char):
        """Append character to expression"""
        nonlocal expression
        expression += char
        update_display()

    def evaluate_expression():
        """Evaluate current expression and show result"""
        nonlocal expression
        if not expression:
            return

        try:
            # Replace special symbols with Python operators
            eval_expr = expression
            eval_expr = eval_expr.replace("×", "*")
            eval_expr = eval_expr.replace("÷", "/")
            eval_expr = eval_expr.replace("−", "-")
            eval_expr = eval_expr.replace("π", str(math.pi))
            eval_expr = eval_expr.replace("e", str(math.e))
            eval_expr = eval_expr.replace("√", "math.sqrt")
            eval_expr = eval_expr.replace("xʸ", "**")

            # Handle scientific functions
            eval_expr = eval_expr.replace("sin", "math.sin")
            eval_expr = eval_expr.replace("cos", "math.cos")
            eval_expr = eval_expr.replace("tan", "math.tan")
            eval_expr = eval_expr.replace("log", "math.log10")
            eval_expr = eval_expr.replace("ln", "math.log")

            result = eval(eval_expr)
            result_str = f"{result:.10g}"  # Remove trailing zeros

            add_to_history(expression, result_str)
            expression = result_str
            update_display()

        except Exception as e:
            add_to_history(expression, f"Error: {e}")
            expression = ""
            update_display()

    # --- Button Callbacks ---
    def on_number(num):
        return lambda: append_char(num)

    def on_operator(op):
        return lambda: append_char(op)

    def on_function(func):
        return lambda: append_char(f"{func}(")

    def on_clear():
        nonlocal expression
        expression = ""
        update_display()

    def on_backspace():
        nonlocal expression
        if expression:
            expression = expression[:-1]
            update_display()

    def on_negate():
        nonlocal expression
        if expression and expression[0] == "-":
            expression = expression[1:]
        else:
            expression = "-" + expression
        update_display()

    def on_clear_history():
        history_lines.clear()
        history_area.set_text("")

    def on_dark_mode():
        is_dark = toggle_theme_and_refresh()
        dark_mode_btn.set_text("☀  Light Mode" if is_dark else "🌙  Dark Mode")

    # Connect number buttons
    btn_0.connect(on_number("0"))
    btn_1.connect(on_number("1"))
    btn_2.connect(on_number("2"))
    btn_3.connect(on_number("3"))
    btn_4.connect(on_number("4"))
    btn_5.connect(on_number("5"))
    btn_6.connect(on_number("6"))
    btn_7.connect(on_number("7"))
    btn_8.connect(on_number("8"))
    btn_9.connect(on_number("9"))
    btn_dot.connect(on_number("."))

    # Connect operators
    btn_add.connect(on_operator("+"))
    btn_sub.connect(on_operator("−"))
    btn_mul.connect(on_operator("×"))
    btn_div.connect(on_operator("÷"))
    btn_open_paren.connect(on_operator("("))
    btn_close_paren.connect(on_operator(")"))

    # Connect scientific functions
    btn_sin.connect(on_function("sin"))
    btn_cos.connect(on_function("cos"))
    btn_tan.connect(on_function("tan"))
    btn_log.connect(on_function("log"))
    btn_ln.connect(on_function("ln"))
    btn_sqrt.connect(on_function("√"))
    btn_power.connect(on_operator("**"))
    btn_square.connect(on_operator("**2"))

    # Connect constants
    btn_pi.connect(on_operator("π"))
    btn_e.connect(on_operator("e"))

    # Connect control buttons
    btn_clear.connect(on_clear)
    btn_back.connect(on_backspace)
    btn_neg.connect(on_negate)
    btn_equals.connect(evaluate_expression)
    btn_clear_hist.connect(on_clear_history)
    dark_mode_btn.connect(on_dark_mode)

    # Initialize display
    update_display()

    return main_layout


if __name__ == "__main__":
    from uniui import parse_args_ui
    layout = create_calculator_ui(parse_args_ui())
    # Slightly taller to ensure history panel remains visible across backends (wx needs a bit more space)
    show_ui(layout, "Scientific Calculator", 360, 640)
