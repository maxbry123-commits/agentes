"""Python code safety analyser using AST parsing + NodeVisitor.

Replaces the regex-based _DANGEROUS_PYTHON_PATTERNS approach.
Analyses the AST, not the text — bypasses via string concatenation,
getattr, chr(), __import__(), etc. are detected at the call-site level.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import ClassVar

__all__ = ["Violation", "analyse_python", "is_safe_python"]


@dataclass
class Violation:
    lineno: int
    col_offset: int
    rule: str
    detail: str


PERMITTED_CALLS: frozenset[str] = frozenset(
    {
        "print",
        "len",
        "range",
        "enumerate",
        "zip",
        "map",
        "filter",
        "sorted",
        "reversed",
        "list",
        "dict",
        "set",
        "tuple",
        "str",
        "int",
        "float",
        "bool",
        "type",
        "isinstance",
        "issubclass",
        "hasattr",
        "repr",
        "dir",
        "help",
        "id",
        "hash",
        "abs",
        "round",
        "min",
        "max",
        "sum",
        "any",
        "all",
        "ord",
        "chr",
        "hex",
        "oct",
        "bin",
        "format",
        "input",
        "open",
        "json.loads",
        "json.dumps",
        "json.load",
        "json.dump",
        "pathlib.Path",
        "datetime.datetime",
        "datetime.date",
        "datetime.time",
        "datetime.timedelta",
        "collections.defaultdict",
        "collections.Counter",
        "collections.OrderedDict",
        "itertools.chain",
        "itertools.product",
        "functools.partial",
        "math.sqrt",
        "math.floor",
        "math.ceil",
        "re.compile",
        "re.search",
        "re.match",
        "re.findall",
        "re.sub",
    }
)

DANGEROUS_MODULES: frozenset[str] = frozenset(
    {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "socket",
        "ctypes",
        "signal",
        "multiprocessing",
        "threading",
        "importlib",
        "runpy",
        "code",
        "codeop",
        "pty",
        "tty",
        "termios",
        "fcntl",
        "resource",
        "mmap",
        "pickle",
        "marshal",
        "shelve",
        "tempfile",
        "webbrowser",
        "http.server",
        "xmlrpc",
        "ftplib",
        "smtplib",
        "telnetlib",
        "poplib",
        "imaplib",
        "nntplib",
    }
)

DANGEROUS_BUILTINS: frozenset[str] = frozenset(
    {
        "exec",
        "eval",
        "compile",
        "__import__",
        "globals",
        "locals",
        "breakpoint",
    }
)


class _ASTGuardVisitor(ast.NodeVisitor):
    """Traverse the AST and collect Violations."""

    DANGEROUS_MODULES: ClassVar[frozenset[str]] = DANGEROUS_MODULES
    DANGEROUS_BUILTINS: ClassVar[frozenset[str]] = DANGEROUS_BUILTINS

    def __init__(self, strict: bool = False) -> None:
        self.violations: list[Violation] = []
        self.strict = strict

    # --- Import checks ---

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            top = alias.name.split(".")[0]
            if top in self.DANGEROUS_MODULES:
                self.violations.append(
                    Violation(
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        rule="dangerous-import",
                        detail=f"Import of restricted module: {alias.name!r}",
                    )
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        top = module.split(".")[0]
        if top in self.DANGEROUS_MODULES:
            self.violations.append(
                Violation(
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    rule="dangerous-import-from",
                    detail=f"Import from restricted module: {module!r}",
                )
            )
        self.generic_visit(node)

    # --- Call checks ---

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func

        # exec()/eval()/compile()/__import__() as bare names
        if isinstance(func, ast.Name) and func.id in self.DANGEROUS_BUILTINS:
            self.violations.append(
                Violation(
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    rule="dangerous-builtin",
                    detail=f"Call to dangerous builtin: {func.id!r}",
                )
            )

        # getattr(os, ...) / getattr(sys, ...) — bypass detection
        _GETATTR_BLOCKED = self.DANGEROUS_MODULES | {"__builtins__", "builtins"}
        if isinstance(func, ast.Name) and func.id == "getattr" and len(node.args) >= 1:
            first = node.args[0]
            if isinstance(first, ast.Name) and first.id in _GETATTR_BLOCKED:
                self.violations.append(
                    Violation(
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        rule="dangerous-getattr",
                        detail=(
                            f"getattr() on restricted module {first.id!r}"
                            " — bypasses import restrictions."
                        ),
                    )
                )

        # setattr(os, ...) — same bypass risk
        if isinstance(func, ast.Name) and func.id == "setattr" and len(node.args) >= 1:
            first = node.args[0]
            if isinstance(first, ast.Name) and first.id in self.DANGEROUS_MODULES:
                self.violations.append(
                    Violation(
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        rule="dangerous-setattr",
                        detail=f"setattr() on restricted module {first.id!r}.",
                    )
                )

        # Attribute access on dangerous modules: os.system, subprocess.run, etc.
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in self.DANGEROUS_MODULES
        ):
            self.violations.append(
                Violation(
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    rule="dangerous-call",
                    detail=f"Call to {func.value.id!r}.{func.attr!r} on restricted module.",
                )
            )

        # __import__("os") as attribute call: builtins.__import__
        if isinstance(func, ast.Attribute) and func.attr == "__import__":
            self.violations.append(
                Violation(
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    rule="dangerous-dunder-import",
                    detail="Call to __import__ attribute — dynamic import bypass.",
                )
            )

        self.generic_visit(node)

    # --- Dunder attribute access ---

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Block access to __subclasses__, __bases__, __mro__ — class hierarchy escape
        if node.attr in ("__subclasses__", "__bases__", "__mro__", "__class__") and self.strict:
            self.violations.append(
                Violation(
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    rule="dangerous-dunder-access",
                    detail=(
                        f"Access to {node.attr!r} — potential sandbox escape via class hierarchy."
                    ),
                )
            )
        self.generic_visit(node)


def analyse_python(source: str, strict: bool = False) -> list[Violation]:
    """Parse *source* as Python code and return a list of security Violations.

    Returns an empty list if the source is safe.
    Raises SyntaxError if the source cannot be parsed.
    """
    tree = ast.parse(source, mode="exec")
    visitor = _ASTGuardVisitor(strict=strict)
    visitor.visit(tree)
    return visitor.violations


def is_safe_python(source: str, strict: bool = False) -> bool:
    """Return True only if ``analyse_python`` finds zero violations."""
    try:
        return len(analyse_python(source, strict=strict)) == 0
    except SyntaxError:
        return False  # unparseable code is treated as unsafe
