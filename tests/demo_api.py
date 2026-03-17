"""
API Demo - demonstrates all available widgets and methods.
Useful for learning and reference.

Run: python demo_api.py
"""
from uniui import create_factory


def demo_all_widgets():
    """Demonstrate all widgets"""
    print(" Creating factory...")
    factory = create_factory('auto')

    print("\n Creating widgets:")

    # 1. Label
    print("  - Label")
    label = factory.create_label()
    label.set_text("This is a label")
    label.set_fixed_width(200)

    # 2. Button
    print("  - Button")
    button = factory.create_button()
    button.set_text("Click Button")
    button.connect(lambda: print("     Button clicked"))

    # 3. LineEdit
    print("  - LineEdit")
    line_edit = factory.create_line_edit()
    line_edit.set_text("Enter text")
    line_edit.set_value(123.45)  # can also set numeric value
    print(f"     get_text(): {line_edit.get_text()}")
    print(f"     get_value(): {line_edit.get_value()}")

    # 4. TextArea
    print("  - TextArea")
    text_area = factory.create_text_area()
    text_area.set_text("Line 1")
    text_area.append("Line 2")
    text_area.set_maximum_height(100)

    # 5. ComboBox
    print("  - ComboBox (editable dropdown)")
    combo = factory.create_combo_box()
    combo.add_item("Option A")
    combo.add_item("Option B")
    combo.set_selection("Option A")
    print(f"     get_text(): {combo.get_text()}")

    # 6. Dropdown
    print("  - Dropdown (read-only)")
    dropdown = factory.create_dropdown()
    dropdown.set_value(["Option 1", "Option 2", "Option 3"])
    print(f"     get_text(): {dropdown.get_text()}")

    # 7. VBox
    print("  - VBox (vertical layout)")
    vbox = factory.create_vbox()
    vbox.add_item(label)
    vbox.add_item(button)
    vbox.add_stretch()

    # 8. HBox
    print("  - HBox (horizontal layout)")
    hbox = factory.create_hbox()
    hbox.add_item(combo)
    hbox.add_item(dropdown)

    # 9. TabWidget
    print("  - TabWidget")
    tab = factory.create_tab_widget()
    tab.add_tab(vbox, "Tab 1")
    tab.add_tab(hbox, "Tab 2")
    print(f"     get_current_index(): {tab.get_current_index()}")

    print("\n All widgets created successfully")

    # Build the full UI
    main = factory.create_vbox()
    main.add_item(label)
    main.add_item(line_edit)
    main.add_item(button)
    main.add_item(text_area)

    button_row = factory.create_hbox()
    button_row.add_item(combo)
    button_row.add_item(dropdown)
    main.add_item(button_row)

    main.add_item(tab)

    return main


def main():
    """Main function"""
    container = demo_all_widgets()

    print("\n Displaying UI...")

    # Use the universal display helper
    from uniui.display import show_ui
    show_ui(container, "API Demo", 500, 600)


if __name__ == "__main__":
    main()
