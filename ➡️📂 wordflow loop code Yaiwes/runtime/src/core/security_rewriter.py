"""Static safety gate and benign neutralizer for candidate Python code.

No candidate code is executed here. High-risk calls are replaced with a
deterministic fail-closed RuntimeError so the harmful operation cannot run.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Tuple

RISKY_CALLS = {
    "eval": "DYNAMIC_EVAL",
    "exec": "DYNAMIC_EXEC",
    "os.system": "SHELL_EXEC",
    "subprocess.call": "SUBPROCESS_EXEC",
    "subprocess.run": "SUBPROCESS_EXEC",
    "subprocess.Popen": "SUBPROCESS_EXEC",
    "shutil.rmtree": "RECURSIVE_DELETE",
    "os.remove": "FILE_DELETE",
    "os.unlink": "FILE_DELETE",
}


@dataclass(frozen=True)
class SafetyAssessment:
    verdict: str
    reason_codes: Tuple[str, ...]


def _call_name(node: ast.Call) -> str:
    fn = node.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        parts = [fn.attr]
        current = fn.value
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def assess_python(source: str) -> SafetyAssessment:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return SafetyAssessment("BLOCK_AND_REVIEW", ("SYNTAX_ERROR",))
    risks = sorted(
        {
            RISKY_CALLS[name]
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            for name in [_call_name(node)]
            if name in RISKY_CALLS
        }
    )
    return SafetyAssessment(
        "BLOCK_AND_REVIEW" if risks else "ALLOW_STATIC_REVIEW",
        tuple(risks or ["NO_BLOCKLIST_MATCH"]),
    )


class _Neutralizer(ast.NodeTransformer):
    def visit_Call(self, node: ast.Call):
        self.generic_visit(node)
        name = _call_name(node)
        if name in RISKY_CALLS:
            return ast.copy_location(
                ast.Call(
                    func=ast.Name(id="_yaiwes_blocked_operation", ctx=ast.Load()),
                    args=[ast.Constant(RISKY_CALLS[name])],
                    keywords=[],
                ),
                node,
            )
        return node


def neutralize_python(source: str) -> tuple[str, Tuple[str, ...]]:
    tree = ast.parse(source)
    before = assess_python(source)
    if before.verdict != "BLOCK_AND_REVIEW":
        return source, ()
    helper = ast.parse(
        "def _yaiwes_blocked_operation(reason):\n"
        "    raise RuntimeError('BLOCKED_UNSAFE_OPERATION:' + str(reason))\n"
    ).body[0]
    tree = _Neutralizer().visit(tree)
    ast.fix_missing_locations(tree)
    tree.body.insert(0, helper)
    return ast.unparse(tree) + "\n", before.reason_codes
