"""
统一测试文件 - 展示重构后的 widgets 系统
支持多种运行模式

运行方式
    python tests/test_ui.py                    # 自动检测框架
    python tests/test_ui.py --ui qt            # 使用 Qt
    python tests/test_ui.py --mode simple      # 简单模式
    python tests/test_ui.py --mode advanced    # 高级模式

Jupyter:
    from tests.test_ui import create_test_ui
    from uniui.display import show_ui
    show_ui(create_test_ui("jupyter", "simple"), "简单测试", 600, 450)
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
# 模式 1: 简单测试
# ============================================================================

def _build_simple_ui():
    """构建简单测试 UI，返回根布局。"""
    count = [0]

    title = Label(" 简单测试 - VBox & HBox")
    input_field = LineEdit()
    btn_click = Button("点击我")
    _set_btn_type(btn_click, "action")
    btn_clear = Button("清空")
    _set_btn_type(btn_clear, "neutral")
    output = TextArea()
    output.set_maximum_height(150)
    status = Label("状态: 就绪")

    def on_click():
        count[0] += 1
        name = input_field.get_text() or "匿名"
        msg = f"[{count[0]}] {name} 点击了按钮"
        output.append(msg)
        status.set_text(f"状态: 点击 {count[0]} 次")

    def on_clear():
        output.clear()
        status.set_text("状态: 已清空")
        count[0] = 0

    btn_click.connect(on_click)
    btn_clear.connect(on_clear)

    btn_row = HBox(btn_click, btn_clear)
    return VBox(title, input_field, btn_row, output, status)


# ============================================================================
# 模式 2: 高级测试
# ============================================================================

def _build_advanced_ui():
    """构建高级测试 UI，返回根布局。"""
    title = Label(" 高级测试 - 多种组件")

    name_input = LineEdit()
    email_input = LineEdit()
    type_dropdown = Dropdown(["选项 1", "选项 2", "选项 3"])
    combo = ComboBox(["苹果", "香蕉", "橙子"])

    btn_submit = Button("提交")
    _set_btn_type(btn_submit, "action")
    btn_clear = Button("清空")
    _set_btn_type(btn_clear, "neutral")

    output = TextArea()
    output.set_maximum_height(120)

    def on_submit():
        name = name_input.get_text()
        email = email_input.get_text()
        type_val = type_dropdown.get_text()
        fruit = combo.get_text()
        info = f"表单提交:\n  姓名: {name}\n  邮箱: {email}\n  类型: {type_val}\n  水果: {fruit}"
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
        _form_row("姓名:", name_input),
        _form_row("邮箱:", email_input),
        _form_row("类型:", type_dropdown),
        _form_row("水果:", combo),
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
# 主程序
# ============================================================================

if __name__ == "__main__":
    import argparse
    from uniui import parse_args_ui

    parser = argparse.ArgumentParser(description='统一测试程序')
    parser.add_argument('--ui', choices=['auto', 'qt', 'jupyter', 'wx', 'tk'], default='auto')
    parser.add_argument('--mode', choices=['simple', 'advanced'], default='simple')
    args = parser.parse_args()

    layout = create_test_ui(args.ui, args.mode)
    title = "简单测试" if args.mode == "simple" else "高级测试"
    show_ui(layout, title, 600, 450)
