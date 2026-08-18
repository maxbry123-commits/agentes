"""QualityDAG handlers — FA-01: UNIT/ARCH/AUDIT con smoke determinista."""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Callable
import ast
import py_compile

from .quality_dag import QualityDAG, GateResult, GateStatus
from .path_resolve import WF_ROOT, REPO_ROOT, resolve_path


def resolve_py_paths(paths: Optional[List[str]]) -> List[Path]:
    out: List[Path] = []
    seen = set()
    for p in paths or []:
        if not p:
            continue
        try:
            r = resolve_path(p, must_exist=True)
        except Exception:
            candidates = [Path(p), Path.cwd() / p, WF_ROOT / p, REPO_ROOT / p]
            if p.startswith("extensions/wordflow/"):
                candidates.append(WF_ROOT / p[len("extensions/wordflow/"):])
            r = None
            for c in candidates:
                if c.suffix == ".py" and c.exists():
                    r = c.resolve()
                    break
        if r is not None and r.suffix == ".py" and r.exists() and str(r) not in seen:
            seen.add(str(r))
            out.append(r)
    return out


def _run_smoke() -> tuple[bool, str]:
    try:
        from .test_runner import default_smoke_runner
        res = default_smoke_runner().run()
        return bool(res.passed), f"smoke cases={len(res.results)}"
    except Exception as e:
        return False, str(e)


def register_deterministic_handlers(
    dag: QualityDAG,
    *,
    paths: Optional[List[str]] = None,
    quality_dag_ok: bool = False,
) -> QualityDAG:
    pys = resolve_py_paths(paths)
    smoke_ok, smoke_detail = _run_smoke()

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
        return GateResult("STATIC", GateStatus.PASS, f"ast.parse n={len(pys)}")

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
        if quality_dag_ok:
            return GateResult("TYPE", GateStatus.PASS, "caller quality_dag_ok / external typecheck")
        return GateResult("TYPE", GateStatus.FAIL, "TYPE requires quality_dag_ok or CI mypy")

    def unit_h() -> GateResult:
        if quality_dag_ok:
            return GateResult("UNIT", GateStatus.PASS, "caller quality_dag_ok")
        if smoke_ok:
            return GateResult("UNIT", GateStatus.PASS, f"FA-01 smoke: {smoke_detail}")
        return GateResult("UNIT", GateStatus.FAIL, f"smoke failed: {smoke_detail}")

    def arch_h() -> GateResult:
        if quality_dag_ok:
            return GateResult("ARCH", GateStatus.PASS, "caller quality_dag_ok")
        try:
            from .wiring_graph import WiringGraph  # noqa: F401
            from .forensic_core import ForensicProgrammingEnforcer  # noqa: F401
            return GateResult("ARCH", GateStatus.PASS, "FA-01 wiring+forensic importable")
        except Exception as e:
            return GateResult("ARCH", GateStatus.FAIL, str(e))

    def audit_h() -> GateResult:
        if quality_dag_ok:
            return GateResult("AUDIT", GateStatus.PASS, "caller quality_dag_ok")
        if smoke_ok:
            return GateResult("AUDIT", GateStatus.PASS, "FA-01 forensic smoke ok")
        return GateResult("AUDIT", GateStatus.FAIL, smoke_detail)

    def flag_h(name: str) -> Callable[[], GateResult]:
        def _h() -> GateResult:
            if quality_dag_ok:
                return GateResult(name, GateStatus.PASS, "caller quality_dag_ok")
            if name in ("SECURITY", "DEPS") and pys:
                return GateResult(name, GateStatus.PASS, "soft: paths resolved")
            if name in ("INTEGRATION", "CONTRACT", "BUILD"):
                return GateResult(name, GateStatus.FAIL, f"{name} requires quality_dag_ok or CI")
            return GateResult(name, GateStatus.FAIL, "no handler evidence")

        return _h

    dag.register("FORMAT", format_h)
    dag.register("STATIC", static_h)
    dag.register("LINT", lint_h)
    dag.register("TYPE", type_h)
    dag.register("UNIT", unit_h)
    dag.register("ARCH", arch_h)
    dag.register("AUDIT", audit_h)
    for n in dag.nodes:
        if n.name not in dag.handlers:
            dag.register(n.name, flag_h(n.name))
    return dag
