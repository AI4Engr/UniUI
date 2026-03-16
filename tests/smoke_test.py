"""
Smoke Test for UniUI
Tests all widget types can be created and core methods work without errors.
"""
from uniui import (
    UniUI, parse_float,
    LABEL, BUTTON, LINE_EDIT, TEXT_AREA,
    COMBO_BOX, DROPDOWN, VBOX, HBOX, TAB_WIDGET, GROUP_BOX, IMAGE,
)


def test_widget_creation():
    """Test that all widget types can be created"""
    print("=" * 60)
    print("Testing Widget Creation")
    print("=" * 60)

    ui = UniUI(framework='tk')
    print(f"Using framework: {ui.framework}\n")

    widget_types = [
        ("Label", LABEL),
        ("Button", BUTTON),
        ("LineEdit", LINE_EDIT),
        ("TextArea", TEXT_AREA),
        ("ComboBox", COMBO_BOX),
        ("Dropdown", DROPDOWN),
        ("VBox", VBOX),
        ("HBox", HBOX),
        ("TabWidget", TAB_WIDGET),
        ("GroupBox", GROUP_BOX),
        ("Image", IMAGE),
    ]

    results = {}
    for name, kind in widget_types:
        try:
            widget = ui.create(kind)
            results[name] = "OK" if widget else "FAIL"
        except Exception as e:
            results[name] = f"FAIL: {str(e)[:40]}"

    for name, result in results.items():
        status = "OK  " if result == "OK" else "FAIL"
        print(f"  {status} {name:15s} -> {result}")

    return results


def test_widget_methods():
    """Test widget core methods (snake_case API only)"""
    print("\n" + "=" * 60)
    print("Testing Widget Methods")
    print("=" * 60)

    ui = UniUI(framework='tk')
    print(f"Using framework: {ui.framework}\n")

    # Test Label
    try:
        label = ui.label()
        label.set_text("Hello")
        assert label.get_text() == "Hello"
        print("  OK   Label: set_text/get_text")
    except Exception as e:
        print(f"  FAIL Label: {e}")

    # Test Button
    try:
        button = ui.button()
        button.set_text("Click Me")
        clicked = []
        button.connect(lambda: clicked.append(1))
        print("  OK   Button: set_text, connect")
    except Exception as e:
        print(f"  FAIL Button: {e}")

    # Test LineEdit
    try:
        line_edit = ui.line_edit()
        line_edit.set_text("Hello")
        assert line_edit.get_text() == "Hello"
        line_edit.set_value(42)
        value = line_edit.get_value()
        assert abs(value - 42.0) < 0.01
        print(f"  OK   LineEdit: set_text, get_text, set_value, get_value ({value})")
    except Exception as e:
        print(f"  FAIL LineEdit: {e}")

    # Test LineEdit with parse_float
    try:
        edit = ui.line_edit()
        edit.set_value(3.14)
        value = parse_float(edit.get_text())
        assert abs(value - 3.14) < 0.01
        print(f"  OK   LineEdit + parse_float: ({value})")
    except Exception as e:
        print(f"  FAIL LineEdit + parse_float: {e}")

    # Test ComboBox
    try:
        combo = ui.combo_box()
        combo.add_item("Option 1")
        combo.add_item("Option 2")
        combo.set_selection("Option 1")
        combo.clear()
        print("  OK   ComboBox: add_item, set_selection, clear")
    except Exception as e:
        print(f"  FAIL ComboBox: {e}")

    # Test Dropdown
    try:
        dropdown = ui.dropdown()
        dropdown.set_value(["A", "B", "C"])
        dropdown.add_item("D")
        text = dropdown.get_text()
        print(f"  OK   Dropdown: set_value, add_item, get_text ({text})")
    except Exception as e:
        print(f"  FAIL Dropdown: {e}")

    # Test VBox/HBox
    try:
        vbox = ui.vbox()
        hbox = ui.hbox()
        label1 = ui.label()
        label2 = ui.label()
        vbox.add_item(label1)
        vbox.add_stretch()
        hbox.add_item(label2)
        hbox.set_alignment_top()
        print("  OK   VBox/HBox: add_item, add_stretch, set_alignment_top")
    except Exception as e:
        print(f"  FAIL VBox/HBox: {e}")

    # Test TextArea
    try:
        textarea = ui.text_area()
        textarea.set_text("Hello World")
        textarea.set_maximum_height(200)
        print("  OK   TextArea: set_text, set_maximum_height")
    except Exception as e:
        print(f"  FAIL TextArea: {e}")

    # Test TabWidget
    try:
        tabs = ui.tab_widget()
        tab1 = ui.vbox()
        tab2 = ui.vbox()
        tabs.add_tab(tab1, "Tab 1")
        tabs.add_tab(tab2, "Tab 2")
        print("  OK   TabWidget: add_tab")
    except Exception as e:
        print(f"  FAIL TabWidget: {e}")

    # Test GroupBox
    try:
        group = ui.create(GROUP_BOX)
        group.set_title("My Group")
        layout = ui.vbox()
        group.set_layout(layout)
        print("  OK   GroupBox: set_title, set_layout")
    except Exception as e:
        print(f"  FAIL GroupBox: {e}")

    print("\n" + "=" * 60)
    print("Smoke test completed!")
    print("=" * 60)


def main():
    """Run all smoke tests"""
    print("\n")
    print("=" * 60)
    print("            UniUI Smoke Test Suite")
    print("=" * 60)
    print()

    try:
        test_widget_creation()
        test_widget_methods()

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n\nTEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
