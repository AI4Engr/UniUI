# UniUI
**Write once, run anywhere.** A unified Python UI API across Qt, Web, and Jupyter.

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

Same code. Desktop, browser, or notebook. Zero UI rewrites.

---

## Why UniUI?

**Real-world scenarios:**

1. **Qt → Jupyter**: Your Qt app works, but colleagues want to test it in Jupyter notebooks
2. **Desktop → Web**: Run the same UI in a browser with the NiceGUI-powered Web backend
3. **Web → Standalone**: Serve the application on a local network or deployment host

**The problem:** Desktop, browser, and notebook UI libraries have different APIs. Switching means rewriting everything.

**The solution:** UniUI gives them one API. Change frameworks with a single line.


---

## Install

```bash
pip install -e .
```

Then install any backend you want:

```bash
pip install PySide2    # Qt
pip install ipywidgets # Jupyter
pip install -e ".[web]" # Web (NiceGUI, Python 3.10+)
```

## Widgets

| Widget | Qt | Web | Jupyter |
|--------|:--:|:---:|:-------:|
| Label | + | + | + |
| Button | + | + | + |
| LineEdit | + | + | + |
| TextArea | + | + | + |
| ComboBox | + | + | + |
| Dropdown | + | + | + |
| GroupBox | + | + | + |
| TabWidget | + | + | + |
| HBox / VBox | + | + | + |
| Image | + | + | + |

## Features

- **Dark mode** built-in with one-click toggle
- **GroupBox** with titled borders on all platforms
- **HBox/VBox** flex layouts that work everywhere
- **Event system** - `button.connect(callback)` across all backends
- **Value parsing** - `input.get_value()` with automatic type conversion

## Example: Hello World

```bash
python hello.py              # auto-detect
python hello.py --ui qt      # Qt
python hello.py --ui web     # Web; opens http://127.0.0.1:8080
python hello.py --ui web --host 0.0.0.0 --port 9000 --no-browser
```

In Jupyter notebook:

```python
from hello import create_hello
from uniui.display import show_ui

show_ui(create_hello("jupyter"), "Hello UniUI")
```

## Web runtime

The public backend name is `web`; NiceGUI is an internal implementation detail.

```bash
python hello.py --ui web
python sysmon.py --ui web --port 9000
python quick_start.py --ui web --host 0.0.0.0 --port 9000 --no-browser
```

Defaults can also be set with `UNIUI_WEB_HOST`, `UNIUI_WEB_PORT`, and
`UNIUI_WEB_BROWSER`. Binding to `0.0.0.0` exposes the service to the local
network; production deployments should place it behind an authenticated HTTPS
reverse proxy. Multiple browser sessions currently share the same application
state.

NiceGUI supports running from Jupyter Notebooks. UniUI's existing `jupyter`
backend remains available for ipywidgets output; validating and integrating the
NiceGUI Notebook execution path for `--ui web` is tracked in the TODO.

## Project Structure

```
src/uniui/
    __init__.py     # Public API, framework selection, UniUI facade
    core.py         # Widget interfaces, factory interface, exceptions
    display.py      # show_ui(), refresh_theme(), schedule_after()
    theme.py        # Dark/light theme system and design tokens
    qt.py           # Qt/PySide2 backend
    web.py          # Web backend (NiceGUI)
    jupyter.py      # Jupyter/ipywidgets backend
    strategies.py   # Value parsing strategies
    wx.py           # wxPython backend (legacy, unsupported)
    tk.py           # Tkinter backend (legacy, unsupported)
```

Official backends: **Qt** and **Jupyter**. The `wx` and `tk` backends are
frozen legacy code — they receive no new features and are excluded from main
CI. Auto-detection and the `--ui` flag still accept `wx` and `tk` for
backward compatibility.

## Testing

Run the full default test suite with:

```bash
pytest
```

The suite includes:

- Contract tests for the public widget API on the default backend
- Display/theme dispatch tests
- Optional Web and Jupyter backend smoke tests when installed
- Web server lifecycle tests for `hello.py` and `sysmon.py`
- External Qt smoke tests through a separate Python interpreter when a PySide2 environment is available

Notes:

- Optional backend checks skip automatically when that backend dependency is unavailable
- The public backend name is `web`; application code does not depend directly on NiceGUI
- Web application state is currently shared by simultaneous browser sessions
- In this repository, Qt smoke coverage can be delegated to a Python 3.11 interpreter that has `PySide2` installed, even if the main test runner uses Python 3.12
- If you want Qt to run in the main process too, install `PySide2` into the same interpreter that runs `pytest`

## License

MIT
