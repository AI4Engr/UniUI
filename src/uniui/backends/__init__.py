"""Per-backend implementation packages.

Each subpackage holds one backend's widgets, styles, and factory. Importing
this package must not import any GUI toolkit: the toolkit only arrives when
you reach into a specific backend, which is what keeps ``import uniui`` free
of PySide2, NiceGUI, and ipywidgets.
"""
