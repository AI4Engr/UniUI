"""
US Credit Card Information Form Example
Demonstrates how to create a form with input fields and display results

Usage:
    python tests/credit_card.py           # Auto-detect UI
    python tests/credit_card.py --ui qt   # Qt
    python tests/credit_card.py --ui wx   # wxPython
    python tests/credit_card.py --ui tk   # Tkinter

Jupyter:
    from tests.credit_card import create_credit_card_ui
    from uniui.display import show_ui
    show_ui(create_credit_card_ui("jupyter"), "Credit Card Form", 500, 600)
"""
from uniui import use, VBox, HBox, Label, Button, LineEdit, TextArea, GroupBox, Dropdown
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


US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
    "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]


def create_credit_card_ui(framework="auto"):
    """Create credit card information form UI.

    Args:
        framework: 'auto', 'qt', 'jupyter', 'wx', or 'tk'

    Returns:
        The root layout container
    """
    use(framework)

    # --- Widgets ---
    dark_mode_btn = Button("\u2600  Light Mode")
    _set_btn_type(dark_mode_btn, "neutral")

    name_input = LineEdit("John Doe")
    card_input = LineEdit("4532-1234-5678-9010")
    address_input = LineEdit("123 Main Street")
    city_input = LineEdit("New York")
    state_dropdown = Dropdown(US_STATES)

    result_display = TextArea("Click 'Submit' to display card information here.")
    result_display.set_maximum_height(120)

    submit_btn = Button("Submit")
    _set_btn_type(submit_btn, "action")

    # --- Callbacks ---
    def on_submit():
        name = name_input.get_text()
        card_number = card_input.get_text()
        address = address_input.get_text()
        city = city_input.get_text()
        state = state_dropdown.get_text()
        info_text = (
            f"Credit Card Information:\n"
            f"==========================\n"
            f"Cardholder Name: {name}\n"
            f"Card Number:     {card_number}\n"
            f"Street Address:  {address}\n"
            f"City:            {city}\n"
            f"State:           {state}\n"
            f"=========================="
        )
        result_display.set_text(info_text)

    def on_dark_mode():
        is_dark = toggle_theme_and_refresh()
        dark_mode_btn.set_text("\u2600  Light Mode" if is_dark else "\U0001f319  Dark Mode")

    submit_btn.connect(on_submit)
    dark_mode_btn.connect(on_dark_mode)

    # --- Layout ---
    title_row = HBox(Label("US Credit Card Information"))
    title_row.add_stretch()
    title_row.add_item(dark_mode_btn)

    form_layout = VBox(
        Label("Cardholder Name:"), name_input,
        Label("Card Number:"), card_input,
        Label("Street Address:"), address_input,
        Label("City:"), city_input,
        Label("State:"), state_dropdown,
    )
    form_group = GroupBox("Card Details", layout=form_layout)

    result_group = GroupBox("Result", layout=VBox(result_display))

    main_layout = VBox(
        title_row,
        form_group,
        submit_btn,
        result_group,
    )

    return main_layout


if __name__ == "__main__":
    from uniui import parse_args_ui
    layout = create_credit_card_ui(parse_args_ui())
    show_ui(layout, "Credit Card Form", 500, 600)
