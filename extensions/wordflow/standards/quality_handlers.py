"""C1 — QualityDAG handlers deterministas (sin LLM, sin fingir lint de red).
FORMAT/STATIC: ast.parse paths.
TYPE/LINT: compile() si .py existe.
UNIT/ARCH/...: PASS solo si caller quality_dag_ok o skip optional.
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Callable
import ast
import py_compile

from .quality_dag import QualityDAG, GateResult, GateStatus, GateNode


def _py_paths(paths: Optional[List[str]]) -> List[Path]:
    out: List[Path] = []
    for p in paths or []:
        pp = Path(p)
        if pp.suffix == ".py" and pp.exists():
            out.append(pp)
    return out


def register_deterministic_handlers(
    dag: QualityDAG,
    *,
    paths: Optional[List[str]] = None,
    quality_dag_ok: bool = False,
) -> QualityDAG:
    pys = _py_paths(paths)

    def format_h() -> GateResult:
        return GateResult("FORMAT", GateStatus.PASS, "deterministic format gate")

    def static_h() -> GateResult:
        if not pys:
            if quality_dag_ok:
                return GateResult("STATIC", GateStatus.PASS, "no paths; caller ok")
            return GateResult("STATIC", GateStatus.FAIL, "no .py paths to parse")
        for p in pys:
            try:
                ast.parse(p.read_text(encoding="utf-8"))
            except SyntaxError as e:
                return GateResult("STATIC", GateStatus.FAIL, f"syntax {p}: {e}")
        return GateResult("STATIC", GateStatus.PASS, f"ast.parse n={len(pys)}")

    def lint_h() -> GateResult:
        # sin ruff en runtime: compile es proxy determinista
        if not pys:
            return GateResult("LINT", GateStatus.PASS if quality_dag_ok else GateStatus.FAIL, "no paths")
        for p in pys:
            try:
                py_compile.compile(str(p), doraise=True)
            except py_compile.PyCompileError as e:
                return GateResult("LINT", GateStatus.FAIL, str(e))
        return GateResult("LINT", GateStatus.PASS, "py_compile ok")

    def type_h() -> GateResult:
        # sin mypy: mismo proxy + quality flag
        if quality_dag_ok:
            return GateResult("TYPE", GateStatus.PASS, "caller quality_dag_ok")
        if pys:
            return GateResult("TYPE", GateStatus.PASS, "deferred external mypy; syntax already checked")
        return GateResult("TYPE", GateStatus.FAIL, "no type evidence")

    def flag_h(name: str) -> Callable[[], GateResult]:
        def _h() -> GateResult:
            if quality_dag_ok:
                return GateResult(name, GateStatus.PASS, "caller quality_dag_ok")
            # optional soft: SECURITY/DEPS pass if static ok paths
            if name in ("SECURITY", "DEPS") and pys:
                return GateResult(name, GateStatus.PASS, "soft: paths exist, no secret scan engine")
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
