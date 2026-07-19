"""
test_verify_all.py — 4 verificaciones + 3 simulaciones por cada archivo .py.

Por cada archivo:
- 4 CHECKS: importa OK, sintaxis OK, clases/funciones públicas existen, líneas > 50
- 3 SIMS: ejecutan funcionalidad real con asserts
"""
import os
import sys
import ast
import json
import tempfile
import traceback
from pathlib import Path

ORCH = Path("/workspace/orchestrator-universal")
sys.path.insert(0, str(ORCH))

FILES = [
    "orchestrator/orchestrator.py",
    "orchestrator/state.py",
    "orchestrator/sandbox.py",
    "orchestrator/sheriff.py",
    "orchestrator/sentinel.py",
    "orchestrator/juez.py",
    "orchestrator/consensus.py",
    "orchestrator/repair.py",
    "orchestrator/router.py",
    "orchestrator/agents/claude_code.py",
    "orchestrator/agents/mimo_code.py",
    "orchestrator/agents/opencode.py",
]


def parse_module(rel_path: str):
    """Check 1: sintaxis AST válida"""
    full = ORCH / rel_path
    src = full.read_text()
    try:
        tree = ast.parse(src)
        return True, len(src.splitlines()), tree
    except SyntaxError as e:
        return False, 0, None


def get_public_names(tree):
    """Check 3: nombres públicos (clases, funciones, constantes)"""
    if tree is None:
        return []
    names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.append(("def", node.name))
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    names.append(("const", t.id))
    return names


def import_module(rel_path: str):
    """Check 1: import dinámico"""
    try:
        mod_name = rel_path.replace("/", ".").replace(".py", "")
        __import__(mod_name)
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:100]}"


def verify_file(rel_path: str) -> dict:
    """4 checks + 3 sims para un archivo."""
    full = ORCH / rel_path
    if not full.exists():
        return {"file": rel_path, "error": "NOT_FOUND"}
    results = {
        "file": rel_path,
        "checks": {},
        "sims": {},
    }
    # CHECK 1: sintaxis
    syntax_ok, lines, tree = parse_module(rel_path)
    results["checks"]["syntax"] = "PASS" if syntax_ok else f"FAIL"
    # CHECK 2: lines > 50
    results["checks"]["lines"] = "PASS" if lines > 50 else f"FAIL ({lines} líneas)"
    # CHECK 3: nombres públicos
    pub = get_public_names(tree)
    has_public = len(pub) > 0
    results["checks"]["public_names"] = f"PASS ({len(pub)})" if has_public else "FAIL"
    # CHECK 4: import
    imp_ok, imp_err = import_module(rel_path)
    results["checks"]["import"] = "PASS" if imp_ok else f"FAIL: {imp_err}"
    return results


# ============================================================================
# SIMULACIONES POR ARCHIVO
# ============================================================================

def sims_orchestrator():
    """3 sims para orchestrator.py"""
    from orchestrator.orchestrator import Orchestrator, run_orchestrator, DAGEngine, node
    sims = []
    # Sim 1: 10 loops
    orch = Orchestrator({"objetivo": "test"}, consensus_mode="single")
    order = orch.dag.topological_order()
    sims.append(("10_loops_present", len(order) == 10))
    # Sim 2: dag sin ciclos
    sims.append(("no_cycles", not orch.dag.has_cycles()))
    # Sim 3: L1 goal lock produce hash
    r = orch.L1_goal_lock()
    sims.append(("L1_goal_hash_present", r.get("status") == "ok" and "goal_hash" in r))
    return sims


def sims_state():
    """3 sims para state.py"""
    from orchestrator.state import WorkflowState, atomic_write_json, hash_goal
    sims = []
    # Sim 1: hash_goal determinístico
    sims.append(("hash_deterministic", hash_goal("x") == hash_goal("x")))
    # Sim 2: goal lock crea hash
    s = WorkflowState(input_data={"objetivo": "build API"})
    sims.append(("goal_lock_creates_hash", len(s.goal_hash) == 16))
    # Sim 3: atomic write + read
    p = "/tmp/_test_state_sim.json"
    atomic_write_json(p, {"k": [1, 2]})
    with open(p) as f:
        sims.append(("atomic_write_readable", json.load(f) == {"k": [1, 2]}))
    os.remove(p)
    return sims


def sims_sandbox():
    """3 sims para sandbox.py"""
    from orchestrator.sandbox import CircuitBreaker, SandboxConfig, SandboxSupervisor
    sims = []
    # Sim 1: circuit breaker abre
    cb = CircuitBreaker("t", failure_threshold=3, cooldown=10)
    for _ in range(3):
        cb.record_failure()
    sims.append(("cb_opens", cb.state == "open"))
    # Sim 2: SandboxConfig tiene campos
    cfg = SandboxConfig(sandbox_id="x", agent_type="claude_code",
                        image="img:latest", work_dir="/tmp")
    sims.append(("config_has_fields",
                 cfg.sandbox_id == "x" and cfg.cpu_limit == 1.0))
    # Sim 3: Supervisor tiene destroy_all
    sup = SandboxSupervisor()
    sims.append(("supervisor_has_destroy", hasattr(sup, "destroy_all")))
    return sims


def sims_sheriff():
    """3 sims para sheriff.py"""
    from orchestrator.sheriff import Sheriff, Validador, Verificador, Verdict
    sims = []
    # Sim 1: 6 gates
    sh = Sheriff()
    sims.append(("6_gates", len(sh.gates) == 6))
    # Sim 2: validador detecta missing
    v = Validador().validate({"a": 1}, ["a", "b"])
    sims.append(("validador_detects_missing", not v["valid"] and "b" in v["missing"]))
    # Sim 3: sheriff rechaza status weird
    r = sh.validate({"status": "weird"}, "completitud", None)
    sims.append(("sheriff_rejects_bad_status", r.verdict == Verdict.NO_GO))
    return sims


def sims_sentinel():
    """3 sims para sentinel.py"""
    from orchestrator.sentinel import Sentinel
    sims = []
    s = Sentinel()
    # Sim 1: log cuenta eventos
    s.log({"event": "x", "node_id": "n1"})
    s.log({"event": "x", "node_id": "n1"})
    sims.append(("log_counts_events", s.get_metrics()["total_events"] == 2))
    # Sim 2: detecta loops
    for _ in range(10):
        s.log({"event": "y", "node_id": "loop"})
    sims.append(("detects_loops", "loop" in s.detect_loops()))
    # Sim 3: openmanus
    r = s.watch_openmanus(None)
    sims.append(("openmanus_returns_dict",
                 "alerts" in r and "healthy" in r and "rate_per_s" in r))
    return sims


def sims_juez():
    """3 sims para juez.py"""
    from orchestrator.juez import Judge
    sims = []
    j = Judge()
    # Sim 1: real pasa con status ok
    r = j.run_simulations({"status": "ok"})
    sims.append(("real_pass_ok", r["simulations"]["real"]["verdict"] == "GO"))
    # Sim 2: adversarial detecta TODO
    r = j.run_simulations({"status": "ok", "x": "TODO"})
    sims.append(("adv_detects_todo", r["simulations"]["adversarial"]["verdict"] == "NO_GO"))
    # Sim 3: regression sin baseline es GO
    r = j.run_simulations({"status": "ok"})
    sims.append(("regression_no_baseline_go", r["simulations"]["regression"]["verdict"] == "GO"))
    return sims


def sims_consensus():
    """3 sims para consensus.py"""
    from orchestrator.consensus import Consensus
    from orchestrator.agents import BaseAgent, AgentResult
    sims = []

    class A(BaseAgent):
        def __init__(self, ok=True):
            super().__init__("a", sandbox=None)
            self.ok = ok
        def execute(self, g, c):
            return AgentResult(self.ok, {"p": "x"} if self.ok else {}, "" if self.ok else "fail", 0, 0, "")
        def verify(self, d, c): return AgentResult(True, {}, "", 0, 0, "")
        def validate(self, d, c): return AgentResult(True, {}, "", 0, 0, "")
        def repair(self, o, e, c): return AgentResult(True, {}, "", 0, 0, "")

    # Sim 1: 2-de-3 con 3 ok
    c = Consensus([A(True), A(True), A(True)])
    r = c.propose("g", {})
    sims.append(("3_ok_picks_winner", r["chosen"] is not None and not r["escalate"]))
    # Sim 2: 2 ok + 1 fail
    c = Consensus([A(True), A(True), A(False)])
    r = c.propose("g", {})
    sims.append(("2_ok_1_fail_picks", r["chosen"] is not None))
    # Sim 3: agreement
    c = Consensus([A(True), A(False)])
    r = c.propose("g", {})
    sims.append(("agreement_half", r["agreement"] == 0.5))
    return sims


def sims_repair():
    """3 sims para repair.py"""
    from orchestrator.repair import RepairEngine
    from orchestrator.state import WorkflowState
    from orchestrator.agents import BaseAgent, AgentResult

    class OK(BaseAgent):
        def __init__(self): super().__init__("ok", sandbox=None)
        def execute(self, g, c): return AgentResult(True, {}, "", 0, 0, "")
        def verify(self, d, c): return AgentResult(True, {}, "", 0, 0, "")
        def validate(self, d, c): return AgentResult(True, {}, "", 0, 0, "")
        def repair(self, o, e, c): return AgentResult(True, {}, "", 0, 0, "--- a/x\n+++ b/x\n")

    class Fail(BaseAgent):
        def __init__(self): super().__init__("f", sandbox=None)
        def execute(self, g, c): return AgentResult(False, {}, "f", 0, 0, "")
        def verify(self, d, c): return AgentResult(False, {}, "f", 0, 0, "")
        def validate(self, d, c): return AgentResult(False, {}, "f", 0, 0, "")
        def repair(self, o, e, c): return AgentResult(False, {}, "f", 0, 0, "")

    sims = []
    # Sim 1: recover con OK
    s = WorkflowState(input_data={"objetivo": "x"})
    e = RepairEngine(mimo_agent=OK(), max_repairs=2)
    r = e.run("N1", "d", "e", s, {})
    sims.append(("recover_with_ok", r.get("recovered") is True))
    # Sim 2: F10 _cleanup_artifacts existe
    sims.append(("f10_method_exists", hasattr(e, "_cleanup_artifacts")))
    # Sim 3: _classify detecta timeout
    sims.append(("classify_timeout", e._classify("timeout occurred") == "timeout"))
    return sims


def sims_router():
    """3 sims para router.py"""
    from orchestrator.router import Router, AGENT_IMAGES
    sims = []
    # Sim 1: tiene imágenes de 3 agentes
    sims.append(("3_agent_types", len(AGENT_IMAGES) == 3))
    # Sim 2: contiene los 3 nombres
    names = set(AGENT_IMAGES.keys())
    sims.append(("has_all_3_names",
                 "claude_code" in names and "mimo_code" in names and "opencode" in names))
    # Sim 3: Router tiene get_agent
    from orchestrator.sandbox import SandboxSupervisor
    from orchestrator.sentinel import Sentinel
    r = Router(SandboxSupervisor(), Sentinel())
    sims.append(("router_has_get_agent", hasattr(r, "get_agent")))
    return sims


def sims_claude_code():
    """3 sims para claude_code.py"""
    from orchestrator.agents.claude_code import ClaudeCodeAgent
    sims = []
    a = ClaudeCodeAgent(sandbox=None)
    # Sim 1: tiene agent_type
    sims.append(("agent_type", a.agent_type == "claude_code"))
    # Sim 2: tiene execute/verify/validate
    sims.append(("has_methods", all(hasattr(a, m) for m in ["execute", "verify", "validate"])))
    # Sim 3: _extract_diff extrae bloques ```diff```
    diff = a._extract_diff("texto\n```diff\n--- a/x\n+++ b/x\n```\nmás texto")
    sims.append(("extract_diff", "--- a/x" in diff))
    return sims


def sims_mimo_code():
    """3 sims para mimo_code.py"""
    from orchestrator.agents.mimo_code import MimoCodeAgent
    sims = []
    a = MimoCodeAgent(sandbox=None)
    # Sim 1: agent_type
    sims.append(("agent_type", a.agent_type == "mimo_code"))
    # Sim 2: tiene los 3 roles (verify/validate/repair)
    sims.append(("has_3_roles", all(hasattr(a, m) for m in ["verify", "validate", "repair"])))
    # Sim 3: extract_diff
    diff = a._extract_diff("```diff\n--- a/x\n+++ b/x\n```")
    sims.append(("extract_diff", "--- a/x" in diff))
    return sims


def sims_opencode():
    """3 sims para opencode.py"""
    from orchestrator.agents.opencode import OpenCodeAgent
    sims = []
    a = OpenCodeAgent(sandbox=None)
    # Sim 1: agent_type
    sims.append(("agent_type", a.agent_type == "opencode"))
    # Sim 2: tiene execute
    sims.append(("has_execute", hasattr(a, "execute")))
    # Sim 3: extract_diff
    diff = a._extract_diff("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-x\n+y")
    sims.append(("extract_diff", "--- a/x" in diff))
    return sims


SIM_FUNCS = {
    "orchestrator/orchestrator.py": sims_orchestrator,
    "orchestrator/state.py": sims_state,
    "orchestrator/sandbox.py": sims_sandbox,
    "orchestrator/sheriff.py": sims_sheriff,
    "orchestrator/sentinel.py": sims_sentinel,
    "orchestrator/juez.py": sims_juez,
    "orchestrator/consensus.py": sims_consensus,
    "orchestrator/repair.py": sims_repair,
    "orchestrator/router.py": sims_router,
    "orchestrator/agents/claude_code.py": sims_claude_code,
    "orchestrator/agents/mimo_code.py": sims_mimo_code,
    "orchestrator/agents/opencode.py": sims_opencode,
}


def main():
    print("=" * 70)
    print("VERIFICACIÓN COMPLETA: 4 checks + 3 sims POR ARCHIVO")
    print("=" * 70)
    total_check_pass = 0
    total_check_fail = 0
    total_sim_pass = 0
    total_sim_fail = 0
    for f in FILES:
        print(f"\n--- {f} ---")
        # 4 checks
        r = verify_file(f)
        for k, v in r["checks"].items():
            ok = v == "PASS" or v.startswith("PASS")
            mark = "OK " if ok else "FAIL"
            print(f"  CHECK {k:20s}: {mark}  {v}")
            if ok:
                total_check_pass += 1
            else:
                total_check_fail += 1
        # 3 sims
        if f in SIM_FUNCS:
            try:
                sims = SIM_FUNCS[f]()
                for name, ok in sims:
                    mark = "OK " if ok else "FAIL"
                    print(f"  SIM   {name:24s}: {mark}")
                    if ok:
                        total_sim_pass += 1
                    else:
                        total_sim_fail += 1
            except Exception as e:
                print(f"  SIM   EXCEPTION: {type(e).__name__}: {str(e)[:80]}")
                total_sim_fail += 3

    print("\n" + "=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    total_files = len(FILES)
    total_checks = total_check_pass + total_check_fail
    total_sims = total_sim_pass + total_sim_fail
    print(f"  Archivos verificados:  {total_files}/12")
    print(f"  Checks:                {total_check_pass}/{total_checks} OK")
    print(f"  Sims:                  {total_sim_pass}/{total_sims} OK")
    print(f"  TOTAL:                 {total_check_pass + total_sim_pass}/{total_checks + total_sims}")
    pct = (total_check_pass + total_sim_pass) / max(1, total_checks + total_sims) * 100
    print(f"  Porcentaje:            {pct:.1f}%")
    if total_check_fail == 0 and total_sim_fail == 0:
        print("\n  *** 100% VERIFICADO ***")


if __name__ == "__main__":
    main()
