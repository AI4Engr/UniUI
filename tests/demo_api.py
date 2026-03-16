"""
API 演示 - 展示所有可用的组件和方法
用于学习和参考

运行: python demo_api.py
"""
from uniui import create_factory


def demo_all_widgets():
    """演示所有组件"""
    print(" 创建工厂...")
    factory = create_factory('auto')

    print("\n 创建组件:")

    # 1. Label
    print("  - Label (标签)")
    label = factory.create_label()
    label.set_text("这是标签")
    label.set_fixed_width(200)

    # 2. Button
    print("  - Button (按钮)")
    button = factory.create_button()
    button.set_text("点击按钮")
    button.connect(lambda: print("     按钮被点击"))

    # 3. LineEdit
    print("  - LineEdit (输入框)")
    line_edit = factory.create_line_edit()
    line_edit.set_text("输入文本")
    line_edit.set_value(123.45)  # 也可以设置数字
    print(f"     get_text(): {line_edit.get_text()}")
    print(f"     get_value(): {line_edit.get_value()}")

    # 4. TextArea
    print("  - TextArea (文本区域)")
    text_area = factory.create_text_area()
    text_area.set_text("第一行")
    text_area.append("第二行")
    text_area.set_maximum_height(100)

    # 5. ComboBox
    print("  - ComboBox (可编辑下拉框)")
    combo = factory.create_combo_box()
    combo.add_item("选项A")
    combo.add_item("选项B")
    combo.set_selection("选项A")
    print(f"     get_text(): {combo.get_text()}")

    # 6. Dropdown
    print("  - Dropdown (下拉列表)")
    dropdown = factory.create_dropdown()
    dropdown.set_value(["选项1", "选项2", "选项3"])
    print(f"     get_text(): {dropdown.get_text()}")

    # 7. VBox
    print("  - VBox (垂直布局)")
    vbox = factory.create_vbox()
    vbox.add_item(label)
    vbox.add_item(button)
    vbox.add_stretch()

    # 8. HBox
    print("  - HBox (水平布局)")
    hbox = factory.create_hbox()
    hbox.add_item(combo)
    hbox.add_item(dropdown)

    # 9. TabWidget
    print("  - TabWidget (选项卡)")
    tab = factory.create_tab_widget()
    tab.add_tab(vbox, "选项卡1")
    tab.add_tab(hbox, "选项卡2")
    print(f"     get_current_index(): {tab.get_current_index()}")

    print("\n 所有组件创建成功")

    # 构建完整 UI
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
    """主函数"""
    container = demo_all_widgets()

    print("\n 显示 UI...")

    # 使用通用显示器
    from uniui.display import show_ui
    show_ui(container, "API 演示", 500, 600)


if __name__ == "__main__":
    main()
