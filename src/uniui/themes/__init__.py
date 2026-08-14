"""Bundled theme JSON files, loaded by :mod:`uniui.theme` at import time.

This package holds data, not code — the JSON files are the source of truth
for every built-in theme's color tokens. It exists as a proper Python
subpackage (rather than a loose ``themes/`` directory) so
``importlib.resources.read_text("uniui.themes", "<name>.json")`` can locate
the files no matter how UniUI was installed — wheel, sdist, or editable
install — not just when running from a source checkout.
"""
