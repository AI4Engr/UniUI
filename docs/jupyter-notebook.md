# Jupyter Notebook UI Fix

## Symptom

In a Notebook, the Admin header and sidebar worked, but the Dashboard content
was blank. Routing and the Python widget tree were correct.

## Root cause

Some Notebook frontends accepted the custom container models but failed to
render their views. Individual sections rendered correctly, and the same
children rendered correctly inside a new standard `ipywidgets.VBox`.

## Fix

- Use standard `ipywidgets.VBox`, `HBox`, and `Box` containers.
- Keep routing state in `JupyterOverlayAdapter`.
- Mount only the active route.
- Wrap composite route pages in a clean standard `VBox` while reusing their
  original children and state.
- Make AppShell sizing explicit with inline flex layouts.
- Remove the problematic `max-width` and `margin: auto` rule from the page
  widget root.

## Notebook usage

Restart the Kernel, then run:

```python
import os
import sys

for path in ("src", "examples"):
    path = os.path.join(os.getcwd(), path)
    if path not in sys.path:
        sys.path.insert(0, path)

from admin_demo import create_admin_ui
from uniui.display import show_ui

ui = create_admin_ui("jupyter")
show_ui(ui, "UniUI Admin Demo", 1180, 780)
```

Optional Python-side diagnostics:

```python
print(ui.debug_report())
```

The report should include:

```text
content=VBox
page=VBox wrapped=True
```

## Verification

Jupyter Admin and routing tests: **37 passed**.

Main files:

- `src/uniui/jupyter.py`
- `src/uniui/jupyter_admin.py`
- `tests/test_jupyter_admin.py`
