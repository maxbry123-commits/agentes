 <-universal/orchestrator/orchestrator.py 2>/dev/null
"""
orchestrator.py — Loop Engine + Goal/Scope Lock + DSL/DAG + 10 Loops.

Implementa:
- G1: Goal Lock (hash en workflow_state)
- G2: Scope Lock (sandbox_id por nodo)
- G3-G10: enforcement vía componentes
- 10 Loops: L1-L10 (definidos en docs/LOOP_ENGINE.md)
- 16 Razonamiento R1-R16
- 16 Recuperación F1-F16 (delegado a repair.RepairEngine)
"""
import os
import re
import time
import signal
import hashlib
import threading
import json
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from orchestrator.state import WorkflowState, atomic_write_json
from orchestrator.sentinel import Sentinel
from orchestrator.sandbox import SandboxSupervisor
from orchestrator.router import Router
from orchestrator.sheriff import Sheriff, Verdict, SheriffVerdict
from orchestrator.juez import Judge
from orchestrator.consensus import Consensus
from orchestrator.repair import RepairEngine


ORCHESTRATOR_VERSION = "orchestrator-universal-v1.0"


_shutdown_event = threading.Event()


def install_shutdown_handlers() -> None:
    def _handler(signum, frame):
        _shutdown_event.set()
    try:
        signal.signal(signal.SIGTERM, _handler)
        signal.signal(signal.SIGINT, _handler)
    except (ValueError, OSError):
        pass


def is_shutting_down() -> bool:
    return _shutdown_event.is_set()


# ============================================================================
# DSL Engine: decorador @node
# ============================================================================

def node(node_id: str, depends_on: Optional[List[str]] = None,
         gate: Optional[str] = None, sandbox: Optional[str] = None,
         repair_max: int = 2):
    depends_on = depends_on or []
    def decorator(func: Callable) -> Callable:
        func._node_id = node_id
        func._node_depends_on = depends_on
        func._node_gate = gate
        func._node_sandbox = sandbox
        func._node_repair_max = repair_max
        func._is_node = True
        return func
    return decorator


# ============================================================================
# DAG Engine
# ============================================================================

class DAGEngine:
    def __init__(self):
        self.graph = {}
        self.nodes: Dict[str, Callable] = {}

    def add_node(self, func: Callable) -> None:
        nid = func._node_id
        self.nodes[nid] = func
        for dep in func._node_depends_on:
            self.graph.setdefault(dep, []).append(nid)
        self.graph.setdefault(nid, [])

    def topological_order(self) -> List[str]:
        visited = set()
        order = []
        def visit(n):
            if n in visited:
                return
            visited.add(n)
            for dep in self.nodes[n]._node_depends_on:
                visit(dep)
            order.append(n)
        for n in self.nodes:
            visit(n)
        return order

    def has_cycles(self) -> bool:
        try:
            self.topological_order()
            return False
        except RecursionError:
            return True


# ============================================================================
# Orquestador principal: 10 Loops
# ============================================================================

class Orchestrator:
    """Loop Engine: ejecuta L1..L10 con multi-agente y sandboxes."""

    def __init__(self, template: dict, work_dir: str = "/tmp/orch_work",
                 director_input_fn: Optional[Callable[[str, str], Verdict]] = None,
                 consensus_mode: str = "fast"):
        install_shutdown_handlers()
        self.template = template
        self.work_dir = work_dir
        self.consensus_mode = consensus_mode  # "single" | "fast" | "full"
        self._director_input = director_input_fn

        # Componentes
        self.sentinel = Sentinel()
        self.supervisor = SandboxSupervisor(sentinel=self.sentinel)
        self.router = Router(self.supervisor, sentinel=self.sentinel)
        self.sheriff = Sheriff(sentinel=self.sentinel)
        self.judge = Judge(sentinel=self.sentinel)

        # Estado
        self.state = WorkflowState(input_data=template)
        os.makedirs(work_dir, exist_ok=True)

        # Agentes (se crean en L3)
        self.claude = None
        self.mimo = None
        self.opencode = None

        # Repair engine (se inicializa en L3)
        self.repair_engine = None

        # DSL/DAG: registro de loops como nodos
        self.dag = DAGEngine()
        self._register_loops()

    def _register_loops(self) -> None:
        loops = [
            (self.L1_goal_lock, []),
            (self.L2_consensus_plan, ["L1_goal_lock"]),
            (self.L3_assign_sandboxes, ["L2_consensus_plan"]),
            (self.L4_execute, ["L3_assign_sandboxes"]),
            (self.L5_verify, ["L4_execute"]),
            (self.L6_repair_if_needed, ["L5_verify"]),
            (self.L7_validate, ["L5_verify", "L6_repair_if_needed"]),
            (self.L8_repair_loop, ["L7_validate"]),
            (self.L9_sentinel_watch, ["L8_repair_loop"]),
            (self.L10_juez, ["L9_sentinel_watch"]),
        ]
        for func, deps in loops:
            underlying = func.__func__  # bound method → underlying function
            underlying._node_depends_on = deps
            self.dag.add_node(underlying)

    # ------------------------------------------------------------------------
    # L1 — Goal Lock + Plan
    # ------------------------------------------------------------------------
    @node(node_id="L1_goal_lock")
    def L1_goal_lock(self) -> dict:
        # R1: parsear plantilla
        objetivo = self.template.get("objetivo", "")
        if not objetivo:
            return {"status": "fail", "reason": "sin_objetivo",
                    "required_fields": ["status", "goal_hash"]}
        # R2: Goal Lock
        if not self.state.goal_hash:
            self.state.goal_hash = hashlib.sha256(objetivo.encode()).hexdigest()[:16]
        # R3: Scope Lock (sandbox_id se asigna en L3, aquí solo dejamos preparado)
        # R4: cargar memoria relevante (último estado del goal similar)
        memory_loaded = self._load_memory(objetivo)
        # R5: construir DSL (ya hecho en _register_loops)
        # R6: DAG (ya construido)
        # R7: validar DAG
        if self.dag.has_cycles():
            return {"status": "fail", "reason": "dag_has_cycles",
                    "required_fields": ["status"]}
        self.state.persist()
        return {
            "status": "ok",
            "goal_hash": self.state.goal_hash,
            "objetivo": objetivo,
            "plan": self.template.get("planificar", []),
            "tareas": self.template.get("tareas", []),
            "metas": self.template.get("metas", []),
            "proposito": self.template.get("proposito", ""),
            "refutaciones": self.template.get("refutaciones", []),
            "dag_order": self.dag.topological_order(),
            "memory_loaded": memory_loaded,
            "required_fields": ["status", "goal_hash", "objetivo"],
        }

    def _load_memory(self, objetivo: str) -> dict:
        """R4: carga contexto de goals similares desde el historial de estados."""
        memory = {"previous_goals": [], "patterns": []}
        state_dir = os.path.dirname(self.state.STATE_PATH) or "."
        if not os.path.isdir(state_dir):
            return memory
        # busca workflows previos
        for fname in os.listdir(state_dir):
            if fname.startswith("workflow_state") and fname.endswith(".json"):
                try:
                    with open(os.path.join(state_dir, fname)) as f:
                        prev = json.load(f)
                    prev_goal = (prev.get("input_data") or {}).get("objetivo", "")
                    if prev_goal and prev_goal != objetivo:
                        memory["previous_goals"].append({
                            "goal": prev_goal[:80],
                            "status": prev.get("node_results", {}).get("L10_juez", {}).get("status"),
                            "completed": prev.get("completed_nodes", []),
                        })
                        if len(memory["previous_goals"]) >= 5:
                            break
                except Exception:
                    continue
        if self.sentinel:
            self.sentinel.log({"event": "memory_loaded", "count": len(memory["previous_goals"])})
        return memory

    def _build_injection_prompt(self, loop_id: str) -> dict:
        """R9: construye el prompt a inyectar al sandbox (goal + contexto + skills)."""
        prompt = {
            "goal": self.template.get("objetivo", ""),
            "loop_id": loop_id,
            "plan": self.template.get("planificar", []),
            "metas": self.template.get("metas", []),
            "proposito": self.template.get("proposito", ""),
            "refutaciones": self.template.get("refutaciones", []),
            "sandbox_id": self.state.current_node or loop_id,
            "goal_hash": self.state.goal_hash,
        }
        if self.sentinel:
            self.sentinel.log({"event": "prompt_injected", "loop_id": loop_id,
                               "goal_hash": self.state.goal_hash})
        return prompt

    # ------------------------------------------------------------------------
    # L2 — Consensus Plan
    # ------------------------------------------------------------------------
    @node(node_id="L2_consensus_plan", depends_on=["L1_goal_lock"])
    def L2_consensus_plan(self) -> dict:
        if self.consensus_mode == "single":
            return {"status": "ok", "consensus_mode": "single",
                    "proposals": [], "chosen": None,
                    "required_fields": ["status"]}
        # crear 3 sandboxes para consensus
        agents = []
        for agent_type in ["claude_code", "mimo_code", "opencode"]:
            try:
                a = self.router.get_agent(agent_type, self.work_dir)
                agents.append(a)
            except Exception as e:
                self.sentinel.log({"event": "consensus_agent_init_failed",
                                   "agent": agent_type, "error": str(e)})
        if len(agents) < 2:
            return {"status": "ok", "consensus_mode": "fast",
                    "reason": "no_enough_agents_fallback",
                    "proposals": [], "chosen": None,
                    "required_fields": ["status"]}
        consensus = Consensus(agents[:3] if self.consensus_mode == "full" else agents[:2],
                             sentinel=self.sentinel)
        result = consensus.propose(
            self.template.get("objetivo", ""),
            {"plan": self.template.get("planificar", []),
             "constraints": self.template.get("metas", [])}
        )
        if result["escalate"]:
            return {"status": "fail", "reason": "consensus_escalate",
                    "proposals": result["proposals"],
                    "required_fields": ["status"]}
        return {
            "status": "ok",
            "consensus_mode": self.consensus_mode,
            "agreement": result["agreement"],
            "chosen_agent": result["chosen"]["agent"] if result["chosen"] else None,
            "proposals_count": len(result["proposals"]),
            "required_fields": ["status", "chosen_agent"],
        }

    # ------------------------------------------------------------------------
    # L3 — Asignar Sandboxes
    # ------------------------------------------------------------------------
    @node(node_id="L3_assign_sandboxes", depends_on=["L2_consensus_plan"])
    def L3_assign_sandboxes(self) -> dict:
        try:
            self.claude = self.router.get_agent("claude_code", self.work_dir,
                                                sandbox_id="sbx-claude-execute")
            self.mimo = self.router.get_agent("mimo_code", self.work_dir,
                                              sandbox_id="sbx-mimo-verify")
            self.opencode = self.router.get_agent("opencode", self.work_dir,
                                                  sandbox_id="sbx-opencode-fallback")
        except Exception as e:
            return {"status": "fail", "reason": f"agent_init_failed:{e}",
                    "required_fields": ["status"]}
        # repair engine usa mimo
        self.repair_engine = RepairEngine(
            mimo_agent=self.mimo,
            sentinel=self.sentinel,
            on_escalate=self._escalate_to_director,
            max_repairs=2,
        )
        # arrancar sandboxes
        started = []
        for agent in [self.claude, self.mimo, self.opencode]:
            if agent and agent.sandbox:
                if agent.sandbox.start():
                    started.append(agent.agent_type)
        return {
            "status": "ok",
            "started_agents": started,
            "sandbox_count": len(started),
            "required_fields": ["status", "started_agents"],
        }

    # ------------------------------------------------------------------------
    # L4 — EXECUTE (Claude Code)
    # ------------------------------------------------------------------------
    @node(node_id="L4_execute", depends_on=["L3_assign_sandboxes"])
    def L4_execute(self) -> dict:
        if not self.claude:
            return {"status": "fail", "reason": "claude_not_initialized",
                    "required_fields": ["status"]}
        # R9: inyectar prompt al sandbox (goal + contexto + skills)
        prompt = self._build_injection_prompt("L4_execute")
        result = self.claude.execute(
            self.template.get("objetivo", ""),
            {
                "plan": self.template.get("planificar", []),
                "constraints": self.template.get("metas", []),
                "timeout_s": 300,
                "injected_prompt": prompt,
            }
        )
        if not result.success:
            return {"status": "fail", "reason": result.error or "execute_failed",
                    "sandbox_id": self.claude.sandbox.config.sandbox_id,
                    "required_fields": ["status"]}
        # guardar diff en context para L5
        self.state.node_results["L4_diff"] = result.diff
        return {
            "status": "ok",
            "agent": "claude_code",
            "diff_length": len(result.diff),
            "duration_s": result.duration_s,
            "tokens_used": result.tokens_used,
            "sandbox_id": self.claude.sandbox.config.sandbox_id,
            "required_fields": ["status", "agent", "diff_length"],
        }

    # ------------------------------------------------------------------------
    # L5 — VERIFY (Mimo Code)
    # ------------------------------------------------------------------------
    @node(node_id="L5_verify", depends_on=["L4_execute"])
    def L5_verify(self) -> dict:
        if not self.mimo:
            return {"status": "fail", "reason": "mimo_not_initialized",
                    "required_fields": ["status"]}
        diff = self.state.node_results.get("L4_diff", "")
        result = self.mimo.verify(diff, {"verify_timeout_s": 120})
        self.state.node_results["L5_pass"] = result.success
        self.state.node_results["L5_error"] = result.error
        if result.success:
            return {
                "status": "ok",
                "stage": "verify",
                "pytest_pass": True,
                "duration_s": result.duration_s,
                "sandbox_id": self.mimo.sandbox.config.sandbox_id,
                "required_fields": ["status", "stage"],
            }
        return {
            "status": "fail",
            "stage": "verify",
            "pytest_pass": False,
            "error": result.error[:500],
            "duration_s": result.duration_s,
            "sandbox_id": self.mimo.sandbox.config.sandbox_id,
            "required_fields": ["status", "stage"],
        }

    # ------------------------------------------------------------------------
    # L6 — REPAIR si L5 falló
    # ------------------------------------------------------------------------
    @node(node_id="L6_repair_if_needed", depends_on=["L5_verify"])
    def L6_repair_if_needed(self) -> dict:
        if self.state.node_results.get("L5_pass"):
            return {"status": "ok", "skipped": True,
                    "reason": "L5_passed_no_repair_needed",
                    "required_fields": ["status"]}
        if not self.repair_engine:
            return {"status": "fail", "reason": "repair_engine_not_init",
                    "required_fields": ["status"]}
        original_diff = self.state.node_results.get("L4_diff", "")
        error = self.state.node_results.get("L5_error", "verify_failed")
        result = self.repair_engine.run(
            "L6_repair_if_needed", original_diff, error, self.state,
            {"work_dir": self.work_dir}
        )
        if result.get("recovered"):
            self.state.node_results["L4_diff"] = result["diff"]
            return {
                "status": "ok",
                "stage": "repair",
                "recovered": True,
                "attempts": result.get("attempts", 1),
                "required_fields": ["status", "stage", "recovered"],
            }
        if result.get("escalated"):
            return {
                "status": "fail",
                "stage": "repair",
                "escalated": True,
                "error": result.get("error", "")[:300],
                "required_fields": ["status", "stage"],
            }
        return {
            "status": "fail",
            "stage": "repair",
            "retry": True,
            "attempts": result.get("attempts", 1),
            "error": result.get("error", "")[:300],
            "required_fields": ["status", "stage"],
        }

    # ------------------------------------------------------------------------
    # L7 — VALIDATE (Mimo Code: lint, format, type-check)
    # ------------------------------------------------------------------------
    @node(node_id="L7_validate", depends_on=["L5_verify", "L6_repair_if_needed"])
    def L7_validate(self) -> dict:
        if not self.mimo:
            return {"status": "fail", "reason": "mimo_not_initialized",
                    "required_fields": ["status"]}
        diff = self.state.node_results.get("L4_diff", "")
        result = self.mimo.validate(diff, {"validate_timeout_s": 60})
        if result.success:
            return {
                "status": "ok",
                "stage": "validate",
                "checks": result.output.get("checks", {}),
                "duration_s": result.duration_s,
                "sandbox_id": self.mimo.sandbox.config.sandbox_id,
                "required_fields": ["status", "stage"],
            }
        return {
            "status": "fail",
            "stage": "validate",
            "checks": result.output.get("checks", {}),
            "error": result.error[:500],
            "required_fields": ["status", "stage"],
        }

    # ------------------------------------------------------------------------
    # L8 — Repair loop (max 2 ciclos de L6→L7)
    # ------------------------------------------------------------------------
    @node(node_id="L8_repair_loop", depends_on=["L7_validate"])
    def L8_repair_loop(self) -> dict:
        # L7 ya se ejecutó; si L7 falló, L6 ya intentó reparar.
        # Si L6 también falló, repair_counts[node] >= 2 → escala
        l7_result = self.state.node_results.get("L7_validate", {})
        if l7_result.get("status") == "ok":
            return {
                "status": "ok",
                "stage": "repair_loop",
                "validate_passed": True,
                "repair_count": self.state.repair_counts.get("L6_repair_if_needed", 0),
                "required_fields": ["status", "validate_passed"],
            }
        # Si L7 falló, es F15 → escalate
        if self.state.repair_counts.get("L6_repair_if_needed", 0) >= 2:
            return {
                "status": "fail",
                "stage": "repair_loop",
                "escalated": True,
                "reason": "max_repairs_exhausted",
                "required_fields": ["status", "stage"],
            }
        return {
            "status": "fail",
            "stage": "repair_loop",
            "validate_passed": False,
            "repair_count": self.state.repair_counts.get("L6_repair_if_needed", 0),
            "required_fields": ["status", "validate_passed"],
        }

    # ------------------------------------------------------------------------
    # L9 — Sentinel + OpenManus
    # ------------------------------------------------------------------------
    @node(node_id="L9_sentinel_watch", depends_on=["L8_repair_loop"])
    def L9_sentinel_watch(self) -> dict:
        metrics = self.sentinel.get_metrics()
        openmanus = self.sentinel.watch_openmanus(self.state)
        # G4: persistir métricas
        self.state.metrics = metrics
        healthy = (len(metrics["deadlocks"]) == 0 and openmanus["healthy"])
        return {
            "status": "ok" if healthy else "fail",
            "metrics": metrics,
            "openmanus": openmanus,
            "required_fields": ["status", "metrics"],
        }

    # ------------------------------------------------------------------------
    # L10 — Juez: 3 simulaciones + baseline
    # ------------------------------------------------------------------------
    @node(node_id="L10_juez", depends_on=["L9_sentinel_watch"])
    def L10_juez(self) -> dict:
        # target: el resultado de L8
        target = self.state.node_results.get("L8_repair_loop", {"status": "fail"})
        sims = self.judge.run_simulations(target, sandbox=None)
        all_go = sims["all_passed"]
        return {
            "status": "ok" if all_go else "fail",
            "simulations": sims["simulations"],
            "all_passed": all_go,
            "baseline_written": sims["baseline_written"],
            "required_fields": ["status", "simulations"],
        }

    # ------------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------------
    def run(self) -> dict:
        """Ejecuta los 10 loops en orden."""
        order = self.dag.topological_order()
        # map node_id → bound method
        method_map = {
            "L1_goal_lock": self.L1_goal_lock,
            "L2_consensus_plan": self.L2_consensus_plan,
            "L3_assign_sandboxes": self.L3_assign_sandboxes,
            "L4_execute": self.L4_execute,
            "L5_verify": self.L5_verify,
            "L6_repair_if_needed": self.L6_repair_if_needed,
            "L7_validate": self.L7_validate,
            "L8_repair_loop": self.L8_repair_loop,
            "L9_sentinel_watch": self.L9_sentinel_watch,
            "L10_juez": self.L10_juez,
        }
        for node_id in order:
            if is_shutting_down():
                self.state.add_error("shutdown_detected")
                self.state.persist()
                return self._result("shutdown", order)
            self.state.current_node = node_id
            self.sentinel.log({"event": "node_start", "node_id": node_id})
            func = self.dag.nodes[node_id]
            method = method_map[node_id]
            try:
                result = method()
                self.state.node_results[node_id] = result
                # gate
                if func._node_gate:
                    v = self.sheriff.validate(result, func._node_gate, self.state,
                                              func._node_repair_max)
                    if v.verdict == Verdict.NO_GO:
                        result["status"] = "fail"
                        result["gate_reason"] = v.reason
                        self.state.add_error(f"{node_id}: {v.reason}")
                if result.get("status") == "ok":
                    self.state.completed_nodes.append(node_id)
                self.state.persist()
            except Exception as e:
                self.state.add_error(f"{node_id}_exception:{e}")
                self.state.node_results[node_id] = {
                    "status": "fail", "exception": str(e),
                    "required_fields": ["status"]
                }
                self.state.persist()
        # G10: STOP limpio
        self._cleanup()
        return self._result("done", order)

    def _cleanup(self) -> None:
        try:
            self.supervisor.destroy_all()
        except Exception as e:
            self.sentinel.log({"event": "cleanup_failed", "error": str(e)})

    def _escalate_to_director(self, node_id: str, attempts: int, state) -> None:
        self.sentinel.log({"event": "escalation_to_director",
                           "node_id": node_id, "attempts": attempts})
        # escribir a DLQ
        dlq_path = "dead_letter.json"
        dlq = []
        if os.path.exists(dlq_path):
            try:
                with open(dlq_path) as f:
                    dlq = json.load(f)
            except Exception:
                dlq = []
        dlq.append({
            "node_id": node_id, "attempts": attempts,
            "input_snapshot": self.template, "ts": time.time(),
        })
        try:
            atomic_write_json(dlq_path, dlq)
        except Exception:
            pass

    def _result(self, status: str, order: List[str]) -> dict:
        return {
            "status": status,
            "completed_nodes": self.state.completed_nodes,
            "node_results": self.state.node_results,
            "errors": self.state.errors,
            "metrics": self.sentinel.get_metrics(),
            "goal_hash": self.state.goal_hash,
            "order": order,
        }


# ============================================================================
# API pública
# ============================================================================

def run_orchestrator(template: dict, work_dir: str = "/tmp/orch_work",
                     director_input_fn: Optional[Callable[[str, str], Verdict]] = None,
                     consensus_mode: str = "fast") -> dict:
    """Función principal: ejecuta el orquestador universal con los 10 loops."""
    orch = Orchestrator(template, work_dir=work_dir,
                        director_input_fn=director_input_fn,
                        consensus_mode=consensus_mode)
    return orch.run()
root@vmi3428294:~# echo 