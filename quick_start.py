"""
BMI Calculator - Quick Start Example
Simple BMI calculator demonstrating UniUI declarative API

Usage:
    python quick_start.py           # Auto-detect (Qt > wx > Tk)
    python quick_start.py --ui qt   # Force Qt
    python quick_start.py --ui wx   # Force wxPython
    python quick_start.py --ui tk   # Force Tkinter

Jupyter Notebook:
    from quick_start import create_bmi_ui
    from uniui.display import show_ui
    show_ui(create_bmi_ui("jupyter"), "BMI Calculator", 400, 500)
"""
from uniui import use, VBox, HBox, Label, Button, LineEdit, Dropdown, GroupBox
from uniui.display import show_ui, toggle_theme_and_refresh


def create_bmi_ui(framework="auto"):
    """Create BMI Calculator UI.

    Args:
        framework: 'auto', 'qt', 'jupyter', 'wx', or 'tk'

    Returns:
        The root layout container, ready for show_ui()
    """
    use(framework)

    # --- Widgets ---
    dark_mode_button = Button("Dark Mode")
    unit_dropdown = Dropdown(["Metric (kg/cm)", "Imperial (lb/in)"])
    gender_dropdown = Dropdown(["Male", "Female"])
    weight_input = LineEdit("70")
    height_input = LineEdit("175")
    calculate_button = Button("Calculate BMI")
    result_label = Label("Please enter weight and height")

    # --- Labels ---
    weight_label = Label("Weight (kg):")
    height_label = Label("Height (cm):")

    # --- Layout ---
    title_row = HBox(Label("=== BMI Calculator ==="))
    title_row.add_stretch()
    title_row.add_item(dark_mode_button)

    input_group = GroupBox("Input Information", layout=VBox(
        HBox(
            VBox(Label("Unit System:"), unit_dropdown),
            VBox(Label("Gender:"), gender_dropdown),
        ),
        HBox(
            VBox(weight_label, weight_input),
            VBox(height_label, height_input),
        ),
    ))

    result_group = GroupBox("Result", layout=VBox(result_label))

    main_layout = VBox(title_row, input_group, calculate_button, result_group)

    # --- Callbacks ---
    def update_unit_labels():
        unit = unit_dropdown.get_text()
        if "Metric" in unit:
            weight_label.set_text("Weight (kg):")
            height_label.set_text("Height (cm):")
        else:
            weight_label.set_text("Weight (lb):")
            height_label.set_text("Height (in):")

    def handle_calculate():
        try:
            unit = unit_dropdown.get_text()
            gender = gender_dropdown.get_text()
            weight = weight_input.get_value()
            height = height_input.get_value()

            if weight <= 0 or height <= 0:
                result_label.set_text("Please enter valid values")
                return

            if "Metric" in unit:
                bmi = weight / (height / 100) ** 2
            else:
                bmi = (weight / height ** 2) * 703

            if gender == "Male":
                if bmi < 18.5:    category = "Underweight"
                elif bmi < 25:    category = "Normal"
                elif bmi < 30:    category = "Overweight"
                else:             category = "Obese"
            else:
                if bmi < 18.5:    category = "Underweight"
                elif bmi < 24:    category = "Normal"
                elif bmi < 28:    category = "Overweight"
                else:             category = "Obese"

            result_label.set_text(f"BMI: {bmi:.1f} ({category}) - {gender}")
        except Exception as e:
            result_label.set_text(f"Calculation error: {e}")

    def handle_dark_mode():
        now_dark = toggle_theme_and_refresh()
        dark_mode_button.set_text("Light Mode" if now_dark else "Dark Mode")

    # Connect events
    calculate_button.connect(handle_calculate)
    unit_dropdown.on_change(update_unit_labels)
    gender_dropdown.on_change(handle_calculate)
    dark_mode_button.connect(handle_dark_mode)

    # Initialize
    update_unit_labels()
    handle_calculate()

    return main_layout


if __name__ == "__main__":
    from uniui import parse_args_ui
    layout = create_bmi_ui(parse_args_ui())
    show_ui(layout, "BMI Calculator", 400, 500)
