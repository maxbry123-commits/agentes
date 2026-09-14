"""The public edge vendors the desktop sandbox's static gate, and a gate that
only gets tightened on the desktop leaves the internet-facing copy open. So the
two files must stay byte-identical below their docstrings; SECURITY.md has
carried "drift risk" as an open note on this pair since the edge shipped.

Run:
    backend/.venv/bin/python -m pytest backend/tests/test_edge_sandbox_mirrors_backend.py -v
"""

import ast
from pathlib import Path

P_ROOT = Path(__file__).resolve().parents[2]
P_DESKTOP = P_ROOT / "backend" / "apps" / "outputs" / "code_safety.py"
P_EDGE = P_ROOT / "openswarm-edge" / "app" / "code_safety.py"


def p_body(path: Path) -> str:
    """The file with its module docstring (the only licensed difference) removed."""
    source = path.read_text()
    docstring = ast.parse(source).body[0]
    return "".join(source.splitlines(keepends=True)[docstring.end_lineno:])


def test_edge_gate_is_a_verbatim_copy_of_the_desktop_gate() -> None:
    assert p_body(P_EDGE) == p_body(P_DESKTOP), (
        "openswarm-edge/app/code_safety.py has drifted from "
        "backend/apps/outputs/code_safety.py; re-copy it below the docstring."
    )
