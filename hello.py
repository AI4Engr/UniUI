"""
UniUI Hello World (Declarative API)

Desktop:
    python hello.py              # auto-detect (Qt > wx > Tk)
    python hello.py --ui qt      # Qt
    python hello.py --ui wx      # wxPython
    python hello.py --ui tk      # Tkinter

Jupyter Notebook:
    from hello import create_hello
    from uniui.display import show_ui
    show_ui(create_hello("jupyter"), "Hello UniUI")

Declarative API:
    from uniui import use, VBox, Label, Button
    use("qt")
    layout = VBox(Label("Hello"), Button("OK"))
"""
from uniui import use, VBox, Label, Button
from uniui.display import show_ui


def create_hello(framework="auto"):
    use(framework)

    message = Label("Hello, UniUI!")

    return VBox(
        message,
        Button("Click Me", on_click=lambda: message.set_text("Clicked!")),
    )


if __name__ == "__main__":
    from uniui import parse_args_ui
    layout = create_hello(parse_args_ui())
    show_ui(layout, "Hello UniUI")
