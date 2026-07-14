# Custom Instructions for GitHub Copilot (Codex)

## Legacy Backends Notice

The `wxPython` (wx) and `Tkinter` (tk) backends in the UniUI project are **legacy** and **unsupported**.

### Guidelines:
- **Do not** write code to add new widgets, features, or styling enhancements for `src/uniui/wx.py` or `src/uniui/tk.py`.
- Focus all coding, refactoring, and development efforts on the active backends: **Qt** (`src/uniui/qt.py`) and **Jupyter** (`src/uniui/jupyter.py`).
- Do not suggest or autocomplete code changes that extend the functionality of the legacy backends.
