"""CSS helpers shared by the two browser backends (Jupyter and Web).

Only *fragments* live here: design-token custom properties, metric custom
properties, and icon-mask rule bodies. Complete selectors deliberately do not,
because the two DOMs are different in ways that have already caused bugs -
ipywidgets wraps every child in its own node, so a rule that sizes a flex item
in NiceGUI reaches the wrong element under Jupyter.

Nothing here imports a toolkit, so this module is safe for either backend (and
for tests) to import.
"""
from __future__ import annotations

from typing import Dict, Iterable, Mapping, Optional

from .icons import ADMIN_ICON_NAMES, css_mask


#: Prefix for every generated custom property.
VAR_PREFIX = "--uniui-"


def token_variables(palette: Mapping[str, str]) -> Dict[str, str]:
    """Map a palette onto ``--uniui-<token>`` custom properties.

    The palette keys are used verbatim, so ``text_muted`` becomes
    ``--uniui-text_muted``. That underscore spelling is load-bearing: the
    existing stylesheets reference ``var(--uniui-text_muted)``.
    """
    return {f"{VAR_PREFIX}{key}": str(value) for key, value in palette.items()}


def metric_variables(metrics: Mapping[str, int]) -> Dict[str, str]:
    """Map design metrics onto the ``--uniui-*`` properties the CSS expects.

    Only the metrics the browser stylesheets actually reference are emitted.
    Note the *hyphenated* names here, unlike the underscore-preserving token
    names above - that difference is pre-existing in the stylesheets and is
    preserved rather than tidied, because renaming would mean touching every
    ``var()`` reference in both backends.
    """
    padding = metrics["content_padding"]
    return {
        f"{VAR_PREFIX}header-height": f"{metrics['header_height']}px",
        f"{VAR_PREFIX}footer-height": f"{metrics['footer_height']}px",
        f"{VAR_PREFIX}shell-bars":
            f"{metrics['header_height'] + metrics['footer_height']}px",
        f"{VAR_PREFIX}sidebar-collapsed": f"{metrics['sidebar_collapsed']}px",
        f"{VAR_PREFIX}control-height": f"{metrics['control_height']}px",
        f"{VAR_PREFIX}stat-value-size": f"{metrics['stat_value_size']}px",
        f"{VAR_PREFIX}stat-label-size": f"{metrics['stat_label_size']}px",
        f"{VAR_PREFIX}sidebar-edge-width": f"{metrics['sidebar_edge_width']}px",
        f"{VAR_PREFIX}content-padding":
            f"{padding}px {padding + 4}px {padding + 4}px",
        f"{VAR_PREFIX}card-padding":
            f"{metrics['card_padding']}px {metrics['card_padding'] + 2}px",
        f"{VAR_PREFIX}card-gap": f"{metrics['card_gap']}px",
        f"{VAR_PREFIX}section-gap": f"{metrics['section_gap']}px",
    }


def declarations(variables: Mapping[str, str]) -> str:
    """Join custom properties into a ``;``-separated declaration string.

    No trailing semicolon: both call sites embed the result where one would be
    redundant (inside a rule body, or as an inline ``style`` attribute).
    """
    return ";".join(f"{name}:{value}" for name, value in variables.items())


def palette_declarations(palette: Mapping[str, str]) -> str:
    """Shorthand for the common ``declarations(token_variables(...))`` pair."""
    return declarations(token_variables(palette))


def icon_mask_rules(
    template: str, names: Optional[Iterable[str]] = None,
) -> str:
    """Build icon-mask rules from a per-icon selector ``template``.

    ``template`` is formatted with ``name`` and ``mask``; the caller supplies
    the selector because Jupyter targets ``button::before`` while the Web
    backend targets its own ``.uniui-svg-icon`` span and Quasar's
    ``.q-btn__content::before``.
    """
    return "".join(
        template.format(name=name, mask=css_mask(name))
        for name in (ADMIN_ICON_NAMES if names is None else names)
    )


__all__ = [
    "VAR_PREFIX",
    "declarations",
    "icon_mask_rules",
    "metric_variables",
    "palette_declarations",
    "token_variables",
]
