"""Static safety gate for user-supplied Output backend code.

`executor.py` owns the subprocess; this file owns the verdict on whether the
code may run without asking the user first. The gate is allowlist-shaped: code
may import a data-shaping module and touch its ordinary attributes, and that is
all. Every other way of getting hold of a module the allowlist withholds (a bare
handle the sandbox preamble binds, an attribute chain that lands on a module, a
dunder walk, an attribute name spelled as a string) is a warning, so it reaches
the user as a consent prompt instead of auto-running.
"""

import ast
import importlib
import types
from typing import Dict, List, Optional, Set

# Modules backend code is allowed to import. This is not an OS-level jail, so keep the list to "data shaping" libraries; no I/O, no networking, no subprocess. It pairs with cwd=tempdir + minimal env so the blast radius stays small.
ALLOWED_MODULES = frozenset({
    "json", "math", "re", "datetime", "collections", "itertools",
    "functools", "statistics", "decimal", "fractions", "random",
    "string", "textwrap", "unicodedata", "csv", "copy", "enum",
    "dataclasses", "typing", "abc", "numbers", "uuid", "hashlib",
    "base64", "binascii", "operator", "heapq", "bisect", "array",
})

# Builtins that punch holes through the allowlist or do I/O. Most are also deleted off `builtins` inside the subprocess; exec/compile/__import__ can't be, because the import machinery runs on them.
P_BLOCKED_BUILTINS = frozenset({
    "exec", "eval", "compile", "__import__", "open", "input",
    "breakpoint", "exit", "quit",
})

# These hand back a live namespace dict, which is every blocked name again through a different door. Warned about but never deleted: library code calls them constantly, and a scrubbed `builtins` would break `import csv` itself.
P_NAMESPACE_BUILTINS = frozenset({"vars", "globals", "locals"})

# Spell an attribute as a string and the AST can't read it, so these are allowed only with a plain literal that would have passed written out longhand.
P_DYNAMIC_ATTR_BUILTINS = frozenset({"getattr", "setattr", "delattr"})

# Modules the executor preamble binds into the user's namespace with no import. `json` stays usable (it is allowlisted anyway); these three were the free handles that made the whole allowlist decorative.
P_SANDBOX_MODULE_HANDLES = frozenset({"sys", "io", "builtins"})

# Dunders that hold a reference to nothing at all, and `if __name__ == "__main__"` is far too common to punish.
P_INERT_DUNDERS = frozenset({"__name__", "__file__", "__doc__"})


class UnsafeCodeError(Exception):
    """Raised when the static gate rejects user-supplied backend code."""


def p_is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def p_dotted_chain(node: ast.expr) -> Optional[List[str]]:
    """['json', 'codecs', 'open'] for `json.codecs.open`; None when the chain
    doesn't start at a plain name."""
    parts: List[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    parts.reverse()
    return parts


def p_resolved_module(chain: List[str], aliases: Dict[str, str]) -> Optional[str]:
    """The name of the module an attribute chain resolves to, or None if it
    resolves to something that isn't a module.

    `json.codecs` is a module and `datetime.time` is a class, and only the live
    object knows which; matching attribute names against a list of module names
    would flag both. So resolve against the module actually imported. Safe to
    import here because `aliases` only ever holds allowlisted stdlib roots.
    """
    root = aliases.get(chain[0])
    if root is None:
        return None
    try:
        value: object = importlib.import_module(root)
        for attr in chain[1:]:
            value = getattr(value, attr)
    except Exception:
        return None
    return value.__name__ if isinstance(value, types.ModuleType) else None


def p_module_aliases(tree: ast.Module) -> Dict[str, str]:
    """Local name -> allowlisted module it holds. Plain assignment counts, so
    `m = json` doesn't launder `m.codecs` past the chain check. Modules outside
    the allowlist are never recorded, which is what keeps the resolver above
    from importing anything a hostile file names."""
    aliases: Dict[str, str] = {"json": "json"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in ALLOWED_MODULES:
                    aliases[alias.asname or root] = root
    assigns = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)]
    for _ in range(len(assigns)):
        before = len(aliases)
        for node in assigns:
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            chain = p_dotted_chain(node.value)
            resolved = p_resolved_module(chain, aliases) if chain else None
            if resolved and resolved.split(".")[0] in ALLOWED_MODULES:
                aliases[node.targets[0].id] = resolved
        if len(aliases) == before:
            break
    return aliases


def p_dunder_warning(attr: str, prefix: str) -> Optional[str]:
    if p_is_dunder(attr) and attr not in P_INERT_DUNDERS:
        return f"Uses dunder '{prefix}{attr}', which walks the object graph past the allowlist"
    return None


def p_attribute_warning(chain: List[str], aliases: Dict[str, str]) -> Optional[str]:
    """The verdict on one resolved attribute chain, dunders first."""
    for attr in chain[1:]:
        dunder = p_dunder_warning(attr, ".")
        if dunder:
            return dunder
    for depth in range(2, len(chain) + 1):
        reached = p_resolved_module(chain[:depth], aliases)
        if reached and reached.split(".")[0] not in ALLOWED_MODULES:
            return f"Reaches module '{reached}' via '{'.'.join(chain[:depth])}' (outside the safe-data-shaping allowlist)"
    return None


def p_call_warning(node: ast.Call, aliases: Dict[str, str]) -> Optional[str]:
    if not isinstance(node.func, ast.Name):
        return None
    name = node.func.id
    if name in P_BLOCKED_BUILTINS:
        return f"Calls builtin '{name}()' which can escape the sandbox"
    if name in P_NAMESPACE_BUILTINS:
        return f"Calls '{name}()', which hands back the sandbox's own namespace"
    if name not in P_DYNAMIC_ATTR_BUILTINS:
        return None
    attr = node.args[1] if len(node.args) > 1 else None
    if not isinstance(attr, ast.Constant) or not isinstance(attr.value, str):
        return f"Computes an attribute name for '{name}()', which can spell any escape as a string"
    base = p_dotted_chain(node.args[0])
    if base is None:
        return p_dunder_warning(attr.value, ".")
    return p_attribute_warning(base + [attr.value], aliases)


def p_star_import_warning(module: str, aliases: Dict[str, str]) -> Optional[str]:
    """`from json import *` binds whatever json's __all__ names, which is a
    short list of functions today but is not ours to assume."""
    try:
        imported = importlib.import_module(module)
    except Exception:
        return None
    names = getattr(imported, "__all__", None) or [n for n in dir(imported) if not n.startswith("_")]
    for name in names:
        warning = p_attribute_warning([module, str(name)], aliases)
        if warning:
            return warning
    return None


def get_code_warnings(code: str) -> List[str]:
    """Return human-readable warnings for every static risk, without raising.

    `/api/outputs/execute` surfaces these in the run dialog, so an Output that
    genuinely needs `pandas` gets a "review and click Run Anyway" affordance
    instead of a silent 500. An empty list is what buys the no-prompt auto-run
    path, so anything that could reach past the allowlist has to land in it. A
    syntax error is reported as a warning rather than raised, so the dialog can
    show it next to the code.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"Syntax error: {e}"]

    aliases = p_module_aliases(tree)
    warnings: List[str] = []
    seen: Set[str] = set()

    def note(msg: Optional[str]) -> None:
        if msg and msg not in seen:
            seen.add(msg)
            warnings.append(msg)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_MODULES:
                    note(f"Imports '{alias.name}' (outside the safe-data-shaping allowlist)")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root not in ALLOWED_MODULES:
                note(f"Imports from '{node.module}' (outside the safe-data-shaping allowlist)")
                continue
            for alias in node.names:
                if alias.name == "*":
                    note(p_star_import_warning(root, aliases))
                else:
                    note(p_attribute_warning([root, alias.name], aliases))
        elif isinstance(node, ast.Call):
            note(p_call_warning(node, aliases))
        elif isinstance(node, ast.Attribute):
            chain = p_dotted_chain(node)
            note(p_attribute_warning(chain, aliases) if chain else p_dunder_warning(node.attr, "."))
        elif isinstance(node, ast.Name):
            if node.id in P_SANDBOX_MODULE_HANDLES:
                note(f"References '{node.id}', a live module the sandbox binds but the allowlist withholds")
            else:
                note(p_dunder_warning(node.id, ""))
    return warnings


def validate_code_safety(code: str) -> None:
    """Raise UnsafeCodeError on the first static risk. The strict wrapper around
    get_code_warnings, for callers with no user to ask."""
    warnings = get_code_warnings(code)
    if warnings:
        raise UnsafeCodeError(warnings[0])
