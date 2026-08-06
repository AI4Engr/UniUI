"""Every name a primitives module uses must actually be bound in it.

Splitting a large backend module drops module-level imports silently: the
moved code still *reads* ``urlopen`` or ``html_lib``, but the ``import`` line
stayed behind in the original file. Nothing fails until a user hits the one
code path that touches it, and the existing suite happened to cover none of
them - a live ``NameError`` in ``QtImageAdapter.set_source`` survived a full
green run this way.

This checks the binding statically, so it covers branches the suite never
executes and needs no toolkit installed.
"""
from __future__ import annotations

import ast
import builtins
import os

import pytest

import uniui.core as core

SRC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "uniui")

#: The three supported backends. The legacy tk and wx backends were removed.
BACKENDS = ["qt", "jupyter", "web"]

#: ``from ...core import *`` binds these, which no AST walk can see.
STAR_NAMES = {n for n in dir(core) if not n.startswith("_")}
BUILTINS = set(dir(builtins))


def _primitive_modules():
    for backend in BACKENDS:
        directory = os.path.join(SRC, "backends", backend, "primitives")
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if name.endswith(".py"):
                yield backend, name, os.path.join(directory, name)


def _bound_names(tree):
    """Collect every name the module binds, by any means."""
    bound = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    bound |= STAR_NAMES
                else:
                    bound.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                bound.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            bound.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        elif isinstance(node, ast.Global):
            bound.update(node.names)
    return bound


@pytest.mark.parametrize(
    "backend,filename,path",
    list(_primitive_modules()),
    ids=lambda v: v if isinstance(v, str) and not os.sep in str(v) else "",
)
def test_every_used_name_is_bound(backend, filename, path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    used = {
        n.id for n in ast.walk(tree)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    }
    unbound = sorted(used - _bound_names(tree) - BUILTINS)
    assert not unbound, (
        f"{backend}/{filename} uses names it never binds: {unbound}. "
        "A module-level import probably stayed behind in the original file."
    )
