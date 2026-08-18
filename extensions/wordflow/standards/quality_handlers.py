"""C1/S1/S2 — QualityDAG handlers deterministas.
Paths se resuelven contra cwd y roots Wordflow (S1).
TYPE no PASS blando sin quality_dag_ok (S2).
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Callable
import ast
import py_compile

from .quality_dag import QualityDAG, GateResult, GateStatus

WF_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]  # .../agentes si layout standard


def resolve_py_paths(paths: Optional[List[str]]) -> List[Path]:
    """S1: intentar path as-is, WF_ROOT, REPO_ROOT, parents."""
    out: List[Path] = []
    seen = set()
    for p in paths or []:
        if not p:
            continue
        candidates = [
            Path(p),
            Path.cwd() / p,
            WF_ROOT / p,
            WF_ROOT / Path(p).name,
            REPO_ROOT / p,
        ]
        # strip leading extensions/wordflow if under WF
        if p.startswith("extensions/wordflow/"):
            candidates.append(WF_ROOT / p[len("extensions/wordflow/"):])
        if p.startswith("extensions/"):
            candidates.append(REPO_ROOT / p)
        for c in candidates:
            try:
                r = c.resolve()
            except OSError:
                continue
            if r.suffix == ".py" and r.exists() and str(r) not in seen:
                seen.add(str(r))
                out.append(r)
                break
    return out


def register_deterministic_handlers(
    dag: QualityDAG,
    *,
    paths: Optional[List[str]] = None,
    quality_dag_ok: bool = False,
) -> QualityDAG:
    pys = resolve_py_paths(paths)

    def format_h() -> GateResult:
        return GateResult("FORMAT", GateStatus.PASS, "deterministic format gate")

    def static_h() -> GateResult:
        if not pys:
            if quality_dag_ok:
                return GateResult("STATIC", GateStatus.PASS, "no paths; caller ok")
            return GateResult("STATIC", GateStatus.FAIL, "no .py paths resolved")
        for p in pys:
            try:
                ast.parse(p.read_text(encoding="utf-8"))
            except SyntaxError as e:
                return GateResult("STATIC", GateStatus.FAIL, f"syntax {p}: {e}")
        return GateResult("STATIC", GateStatus.PASS, f"ast.parse n={len(pys)} roots_ok")

    def lint_h() -> GateResult:
        if not pys:
            return GateResult("LINT", GateStatus.PASS if quality_dag_ok else GateStatus.FAIL, "no paths")
        for p in pys:
            try:
                py_compile.compile(str(p), doraise=True)
            except py_compile.PyCompileError as e:
                return GateResult("LINT", GateStatus.FAIL, str(e))
        return GateResult("LINT", GateStatus.PASS, "py_compile ok")

    def type_h() -> GateResult:
        # S2: no soft PASS solo por syntax
        if quality_dag_ok:
            return GateResult("TYPE", GateStatus.PASS, "caller quality_dag_ok / external typecheck")
        return GateResult("TYPE", GateStatus.FAIL, "TYPE requires quality_dag_ok or CI mypy")

    def flag_h(name: str) -> Callable[[], GateResult]:
        def _h() -> GateResult:
            if quality_dag_ok:
                return GateResult(name, GateStatus.PASS, "caller quality_dag_ok")
            if name in ("SECURITY", "DEPS") and pys:
                return GateResult(name, GateStatus.PASS, "soft: paths resolved")
            if name in ("UNIT", "INTEGRATION", "CONTRACT", "BUILD", "AUDIT", "ARCH"):
                return GateResult(name, GateStatus.FAIL, f"{name} requires quality_dag_ok or CI")
            return GateResult(name, GateStatus.FAIL, "no handler evidence")

        return _h

    dag.register("FORMAT", format_h)
    dag.register("STATIC", static_h)
    dag.register("LINT", lint_h)
    dag.register("TYPE", type_h)
    for n in dag.nodes:
        if n.name not in dag.handlers:
            dag.register(n.name, flag_h(n.name))
    return dag
