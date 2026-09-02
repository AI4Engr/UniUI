"""Resize-observer bridge script for the Jupyter Grid/HBox ``on_resize()``.

Kept in its own module rather than inside ``layouts.py``, matching the
``app_shell_assets.py`` convention: importing the layout adapters should not
carry an embedded JavaScript template along with it, and the JS stays
greppable as JS.

Same DOM-traversal idiom as ``app_shell_assets.SPLITTER_HTML``: raw inline JS
reaches into the DOM via ``closest()``/``querySelector()``, sets a hidden
ipywidgets input's ``.value``, and dispatches a ``change`` event so the
Python-side ``.observe()`` on that hidden widget picks it up. The difference
here is that the JS attaches itself once, automatically, via a
``ResizeObserver`` - the existing precedent (``SPLITTER_HTML``'s drag handle)
is pointer-driven (``onpointerdown``/``onpointerup``), not automatic.

**Experimental**: cross-notebook-frontend behavior of ``ResizeObserver`` plus
this ``closest()``/``querySelector()`` DOM trick is unverified across every
notebook renderer (VS Code notebook, JupyterLab, nbviewer, classic Notebook).
If the injected script never runs (notebook trust settings, timing, a
renderer that doesn't execute ``IPython.display.Javascript`` at all),
``on_resize()`` simply never fires - matching the contract's existing
"no-op is an acceptable failure mode" philosophy for backend gaps elsewhere
in this codebase, not a crash.
"""
from __future__ import annotations


def resize_observer_js(container_class: str, bridge_class: str) -> str:
    """Build the injected script for one Grid/HBox instance.

    ``container_class`` uniquely identifies this instance's container element
    (via ``add_class()``) so the script finds the right DOM node even with
    multiple Grid/HBox instances using ``on_resize()`` on the same page.
    ``bridge_class`` identifies this instance's hidden bridge widget the same
    way ``uniui-sidebar-width-bridge`` identifies the AppShell's.
    """
    return f"""
(() => {{
    const container = document.querySelector('.{container_class}');
    if (!container) return;
    const bridge = container.querySelector('.{bridge_class} input');
    if (!bridge) return;
    if (container.dataset.uniuiResizeObserved) return;
    container.dataset.uniuiResizeObserved = '1';
    let timer = null;
    const report = () => {{
        const width = Math.round(container.getBoundingClientRect().width);
        bridge.value = String(width);
        bridge.dispatchEvent(new Event('change', {{bubbles: true}}));
    }};
    const observer = new ResizeObserver(() => {{
        if (timer !== null) clearTimeout(timer);
        timer = setTimeout(report, 100);
    }});
    observer.observe(container);
}})();
"""
