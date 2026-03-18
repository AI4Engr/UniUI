# UniUI
**Write once, run anywhere.** A unified Python GUI API across Qt, Jupyter, wxPython and Tkinter.

```python
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
```

Same code. Four backends. Zero changes.

---

## Why UniUI?

**Real-world scenarios:**

1. **Qt → Jupyter**: Your Qt app works, but colleagues want to test it in Jupyter notebooks
2. **Jupyter → Standalone**: Your Jupyter app needs to run on machines without Python — package it as a Qt .exe with PyInstaller
3. **Desktop → Web**: Run your desktop UI in the browser via Jupyter/ipywidgets with minimal changes

**The problem:** Python has Qt, Jupyter, wxPython and Tkinter — each with different APIs. Switching means rewriting everything.

**The solution:** UniUI gives you one API for all four backends. Change frameworks with a single line.

---

## Install

```bash
pip install -e .
```

Then install any backend you want:

```bash
pip install PySide2    # Qt
pip install wxPython   # wx
pip install ipywidgets # Jupyter
# Tkinter is built-in
```

## Widgets

| Widget | Qt | wx | Tk | Jupyter |
|--------|:--:|:--:|:--:|:-------:|
| Label | + | + | + | + |
| Button | + | + | + | + |
| LineEdit | + | + | + | + |
| TextArea | + | + | + | + |
| ComboBox | + | + | + | + |
| Dropdown | + | + | + | + |
| GroupBox | + | + | + | + |
| TabWidget | + | + | + | + |
| HBox / VBox | + | + | + | + |
| Image | + | + | + | + |

## Features

- **Dark mode** built-in with one-click toggle
- **GroupBox** with titled borders on all platforms
- **HBox/VBox** flex layouts that work everywhere
- **Event system** - `button.connect(callback)` across all backends
- **Value parsing** - `input.get_value()` with automatic type conversion

## Example: Hello World

```bash
python hello.py              # auto-detect (Qt > wx > Tk)
python hello.py --ui qt      # Qt
python hello.py --ui wx      # wxPython
python hello.py --ui tk      # Tkinter
```

In Jupyter notebook:

```python
from hello import create_hello
from uniui.display import show_ui

show_ui(create_hello("jupyter"), "Hello UniUI")
```

## Project Structure

```
src/uniui/
    __init__.py     # Public API, UniUI facade
    core.py         # Interfaces, WidgetKind enum
    display.py      # show_ui(), refresh_theme()
    theme.py        # Dark/light theme system
    qt.py           # Qt/PySide2 backend
    wx.py           # wxPython backend
    tk.py           # Tkinter backend
    jupyter.py      # Jupyter/ipywidgets backend
    strategies.py   # Value parsing strategies
    # Platform auto-detection lives in __init__.py
```

## Testing

Run the full default test suite with:

```bash
pytest
```

The suite includes:

- Contract tests for the public widget API on the default backend
- Display/theme dispatch tests
- Optional backend smoke tests for wxPython and Jupyter when installed
- External Qt smoke tests through a separate Python interpreter when a PySide2 environment is available

Notes:

- Tkinter is exercised by the main `pytest` run in the current environment
- Optional backend checks skip automatically when that backend dependency is unavailable
- In this repository, Qt smoke coverage can be delegated to a Python 3.11 interpreter that has `PySide2` installed, even if the main test runner uses Python 3.12
- If you want Qt to run in the main process too, install `PySide2` into the same interpreter that runs `pytest`

## License

MIT
