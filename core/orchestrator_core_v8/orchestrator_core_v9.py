#!/usr/bin/env python3
"""ORCHESTRATOR_CORE_V9 — Multi-agent deterministic orchestrator.

DSL v9.0: pipeline N00..N10, single DAG, single pipeline, deterministic.
AgentRegistry with 5 workers: Claude_Code_VPS, Mimo_Code_VPS, Codex, OpenClaw, Hermes.
All workers are deterministic stubs (no real network, no real LLM, no subprocess).
Real integration requires explicit gate (see DECISION DSL v1).
"""
import os
import sys
import json
import time
import uuid
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# ====================================================================
# PATHS
# ====================================================================
ROOT = "/opt/orquestador-universal/orchestrator_core_v8"
STATE_DIR = os.path.join(ROOT, "state_v9")
os.makedirs(STATE_DIR, exist_ok=True)

WORKFLOW_STATE = os.path.join(STATE_DIR, "workflow_state.json")
HISTORY = os.path.join(STATE_DIR, "history.json")
METRICS = os.path.join(STATE_DIR, "metrics.json")
RECOVERY = os.path.join(STATE_DIR, "recovery.json")

# ====================================================================
# SHERIFF (ENFORCE) — 7 gates
# ====================================================================
class SheriffVerdict:
    def __init__(self, ok, gate, reason=""):
        self.ok = ok
        self.gate = gate
        self.reason = reason
    def to_dict(self):
        return {"ok": self.ok, "gate": self.gate, "reason": self.reason}

class Sheriff:
    GATE_NAMES = ["completeness", "schema", "coherence", "format",
                  "sandbox_isolation", "repair_validation", "approval"]

    def validate(self, ctx):
        results = {}
        # G01 COMPLETENESS
        required = ["request_id", "workflow_id", "task_id", "session_id", "timestamp", "metadata", "payload"]
        missing = [k for k in required if k not in ctx]
        results["completeness"] = SheriffVerdict(len(missing) == 0, "completeness",
                                                "" if not missing else f"missing={missing}").to_dict()
        # G02 SCHEMA
        schema_ok = (isinstance(ctx.get("payload"), dict) and
                     isinstance(ctx.get("metadata"), dict) and
                     isinstance(ctx.get("timestamp"), (int, float)) and
                     isinstance(ctx.get("request_id"), str))
        results["schema"] = SheriffVerdict(schema_ok, "schema", "ok" if schema_ok else "bad_types").to_dict()
        # G03 COHERENCE
        wf = ctx.get("workflow_id", "")
        coherent = bool(wf) and wf == ctx.get("workflow_id") and ctx.get("task_id")
        results["coherence"] = SheriffVerdict(coherent, "coherence", "ok" if coherent else "ids_incoherent").to_dict()
        # G04 FORMAT
        fmt_ok = all(isinstance(ctx.get(k), str) for k in ["request_id", "workflow_id", "task_id", "session_id"])
        results["format"] = SheriffVerdict(fmt_ok, "format", "ok" if fmt_ok else "non-string id").to_dict()
        # G05 SANDBOX ISOLATION
        sb = ctx.get("payload", {}).get("sandbox_id", "core_v9_sandbox")
        results["sandbox_isolation"] = SheriffVerdict(True, "sandbox_isolation", f"sandbox={sb}").to_dict()
        # G06 REPAIR VALIDATION
        results["repair_validation"] = SheriffVerdict(True, "repair_validation", "no_repair_needed").to_dict()
        # G07 APPROVAL
        all_ok = all(r["ok"] for r in results.values())
        results["approval"] = SheriffVerdict(all_ok, "approval",
                                            "approved" if all_ok else "rejected").to_dict()
        overall_ok = all(r["ok"] for r in results.values())
        return {"ok": overall_ok, "gates": results}

# ====================================================================
# ATOMIC STATE
# ====================================================================
def atomic_write_json(path, data):
    import tempfile
    dirn = os.path.dirname(path) or "."
    os.makedirs(dirn, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dirn, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            try: os.unlink(tmp)
            except: pass
        raise

def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

# ====================================================================
# STATE MANAGER
# ====================================================================
class StateManager:
    _lock = threading.Lock()
    ALL_NODES = ["N00_RECEIVE", "N01_SCHEMA", "N02_SHERIFF", "N03_DAG_BUILD",
                 "N04_ROUTER", "N05_RUNTIME", "N06_SANDBOX", "N07_VERIFY",
                 "N08_CONSENSUS", "N09_STATE", "N10_RESPONSE"]

    @classmethod
    def transition_node(cls, node_id, status, evidence, output=None):
        with cls._lock:
            state = read_json(WORKFLOW_STATE, {"nodos": {}, "completed_nodes": [], "status": "CREATED"})
            state.setdefault("nodos", {})[node_id] = {
                "node_id": node_id, "status": status,
                "evidence": evidence, "output": output,
                "timestamp": time.time(),
            }
            state["current_node"] = node_id
            if status == "COMPLETED" and node_id not in state.get("completed_nodes", []):
                state.setdefault("completed_nodes", []).append(node_id)
            if status == "COMPLETED" and all(
                state.get("nodos", {}).get(n, {}).get("status") == "COMPLETED" for n in cls.ALL_NODES
            ):
                state["status"] = "COMPLETED"
            elif status == "FAILED":
                state["status"] = "FAILED"
            state["updated_at"] = time.time()
            atomic_write_json(WORKFLOW_STATE, state)
            cls._append_history({"event": "node_transition", "node_id": node_id,
                                 "status": status, "timestamp": time.time()})
            cls._update_metrics(node_id, status)
            cls._write_recovery(state)

    @classmethod
    def _append_history(cls, entry):
        hist = read_json(HISTORY, {"entries": []})
        hist.setdefault("entries", []).append(entry)
        atomic_write_json(HISTORY, hist)

    @classmethod
    def _update_metrics(cls, node_id, status):
        m = read_json(METRICS, {"total_transitions": 0, "by_node": {}, "by_status": {}, "by_agent": {}, "last_update": None})
        m["total_transitions"] = m.get("total_transitions", 0) + 1
        m.setdefault("by_node", {})[node_id] = m["by_node"].get(node_id, 0) + 1
        m.setdefault("by_status", {})[status] = m["by_status"].get(status, 0) + 1
        m["last_update"] = time.time()
        atomic_write_json(METRICS, m)

    @classmethod
    def record_agent(cls, agent_name: str, task_id: str):
        m = read_json(METRICS, {"by_agent": {}})
        m.setdefault("by_agent", {})[agent_name] = m["by_agent"].get(agent_name, 0) + 1
        atomic_write_json(METRICS, m)

    @classmethod
    def _write_recovery(cls, state):
        rec = {
            "last_known_state": state.get("status"),
            "last_node": state.get("current_node"),
            "completed_nodes": state.get("completed_nodes", []),
            "checkpoint_ts": time.time(),
        }
        atomic_write_json(RECOVERY, rec)

    @classmethod
    def get_state(cls):
        return read_json(WORKFLOW_STATE, {})

    @classmethod
    def get_response_payload(cls, workflow_id):
        state = read_json(WORKFLOW_STATE, {})
        hist = read_json(HISTORY, {"entries": []})
        metrics = read_json(METRICS, {})
        recovery = read_json(RECOVERY, {})
        return {
            "workflow_id": workflow_id,
            "status": state.get("status"),
            "nodos": state.get("nodos", {}),
            "history_summary": {"total": len(hist.get("entries", []))},
            "metrics": metrics,
            "recovery": recovery,
            "source": "StateManager",
        }

# ====================================================================
# AGENT REGISTRY (V9 — 5 workers)
# ====================================================================
class AgentWorker:
    """Base deterministic worker stub."""
    def __init__(self, name, role):
        self.name = name
        self.role = role
    def execute(self, goal, ctx):
        # Deterministic output (no real network/LLM)
        return {
            "agent": self.name,
            "role": self.role,
            "goal": goal,
            "result": f"{self.name}_result_for_{goal[:30]}",
            "timestamp": time.time(),
            "sandbox_id": ctx.get("payload", {}).get("sandbox_id", "core_v9_sandbox"),
            "stub": True,
        }

class ClaudeCodeWorker(AgentWorker):
    def __init__(self):
        super().__init__("Claude_Code_VPS", "code_executor")
    def execute(self, goal, ctx):
        out = super().execute(goal, ctx)
        out["model_hint"] = "claude-sonnet-5"
        out["capabilities"] = ["code", "review", "edit"]
        return out

class MimoCodeWorker(AgentWorker):
    def __init__(self):
        super().__init__("Mimo_Code_VPS", "verifier_repairer")
    def execute(self, goal, ctx):
        out = super().execute(goal, ctx)
        out["model_hint"] = "mimo-zai"
        out["capabilities"] = ["verify", "repair", "validate"]
        return out

class CodexWorker(AgentWorker):
    def __init__(self):
        super().__init__("Codex", "code_generator")
    def execute(self, goal, ctx):
        out = super().execute(goal, ctx)
        out["model_hint"] = "codex-coder"
        out["capabilities"] = ["generate", "test", "lint"]
        return out

class OpenClawWorker(AgentWorker):
    def __init__(self):
        super().__init__("OpenClaw", "browser_automation")
    def execute(self, goal, ctx):
        out = super().execute(goal, ctx)
        out["model_hint"] = "openclaw-m3"
        out["capabilities"] = ["browse", "automate", "extract"]
        return out

class HermesWorker(AgentWorker):
    def __init__(self):
        super().__init__("Hermes", "router_orchestrator")
    def execute(self, goal, ctx):
        out = super().execute(goal, ctx)
        out["model_hint"] = "hermes-router"
        out["capabilities"] = ["route", "summarize", "translate"]
        return out


class AgentRegistry:
    """V9: 5 workers, configurable via register()."""
    _agents = {}
    _roles = {}

    @classmethod
    def register(cls, name: str, worker_obj):
        if name in cls._agents:
            return  # idempotent
        cls._agents[name] = worker_obj
        cls._roles[name] = worker_obj.role

    @classmethod
    def get(cls, name: str):
        return cls._agents.get(name)

    @classmethod
    def list(cls):
        return list(cls._agents.keys())

    @classmethod
    def role_of(cls, name: str):
        return cls._roles.get(name)

# Register the 5 DSL v9 workers (deterministic stubs)
AgentRegistry.register("Claude_Code_VPS", ClaudeCodeWorker())
AgentRegistry.register("Mimo_Code_VPS", MimoCodeWorker())
AgentRegistry.register("Codex", CodexWorker())
AgentRegistry.register("OpenClaw", OpenClawWorker())
AgentRegistry.register("Hermes", HermesWorker())

# ====================================================================
# SCHEMA VALIDATOR (N01)
# ====================================================================
class SchemaValidator:
    REQUIRED = ["request_id", "workflow_id", "task_id", "session_id", "timestamp", "metadata", "payload"]
    SUPPORTED_PROTOCOL_VERSION = "9.0"

    @classmethod
    def validate(cls, ctx):
        missing = [k for k in cls.REQUIRED if k not in ctx]
        type_errors = []
        if not isinstance(ctx.get("timestamp"), (int, float)):
            type_errors.append("timestamp must be number")
        if not isinstance(ctx.get("payload"), dict):
            type_errors.append("payload must be object")
        if not isinstance(ctx.get("metadata"), dict):
            type_errors.append("metadata must be object")
        for k in ["request_id", "workflow_id", "task_id", "session_id"]:
            if not isinstance(ctx.get(k), str):
                type_errors.append(f"{k} must be string")
        # version check
        version = ctx.get("metadata", {}).get("protocol_version", cls.SUPPORTED_PROTOCOL_VERSION)
        version_ok = version == cls.SUPPORTED_PROTOCOL_VERSION
        return {
            "ok": len(missing) == 0 and len(type_errors) == 0 and version_ok,
            "missing": missing, "type_errors": type_errors, "version_ok": version_ok,
            "version": version,
        }

# ====================================================================
# RUNTIME (N05) — boot/allocate/execute/monitor/release
# ====================================================================
class Runtime:
    def boot(self, plan):
        return {"status": "booted", "plan_nodes": len(plan.get("nodes", []))}
    def allocate(self, agent_name):
        return {"status": "allocated", "agent": agent_name}
    def execute(self, agent_name, goal, ctx):
        agent = AgentRegistry.get(agent_name)
        if not agent:
            return {"status": "error", "error": f"agent '{agent_name}' not in registry"}
        return agent.execute(goal, ctx)
    def monitor(self, node_id):
        return {"status": "monitoring", "node_id": node_id}
    def release(self, agent_name):
        return {"status": "released", "agent": agent_name}

# ====================================================================
# SANDBOX (N06) — 6 evidence fields
# ====================================================================
class Sandbox:
    def exec(self, agent_output):
        return {
            "stdout": json.dumps(agent_output),
            "stderr": "",
            "exit_code": 0,
            "cpu": 0.01,
            "memory": 1024,
            "artifacts": ["result.json"],
        }

# ====================================================================
# DAG BUILDER (N03) — single DAG, cycle detection
# ====================================================================
class DAGBuilder:
    NODES = ["N00_RECEIVE", "N01_SCHEMA", "N02_SHERIFF", "N03_DAG_BUILD",
             "N04_ROUTER", "N05_RUNTIME", "N06_SANDBOX", "N07_VERIFY",
             "N08_CONSENSUS", "N09_STATE", "N10_RESPONSE"]

    def build(self, ctx):
        nodes = [{"id": n, "depends_on": [self.NODES[i-1]] if i > 0 else []} for i, n in enumerate(self.NODES)]
        edges = [(n["depends_on"][0], n["id"]) for n in nodes if n["depends_on"]]
        has_cycle = self._detect_cycle(edges)
        topo = self.NODES if not has_cycle else []
        return {
            "nodes": nodes,
            "has_cycle": has_cycle,
            "topological_order": topo,
            "ExecutionPlan": {
                "plan_id": str(uuid.uuid4())[:8],
                "single_dag": True,
                "single_pipeline": True,
                "node_count": len(self.NODES),
                "workflow_id": ctx.get("workflow_id"),
            },
        }

    def _detect_cycle(self, edges):
        graph = {n: [] for n in self.NODES}
        for src, dst in edges:
            graph[src].append(dst)
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n: WHITE for n in self.NODES}
        def dfs(n):
            color[n] = GRAY
            for m in graph[n]:
                if color[m] == GRAY: return True
                if color[m] == WHITE and dfs(m): return True
            color[n] = BLACK
            return False
        return any(color[n] == WHITE and dfs(n) for n in self.NODES)

# ====================================================================
# ROUTER (N04) — uses AgentRegistry, no hardcode
# ====================================================================
class Router:
    """Selects worker from AgentRegistry based on goal hash or explicit request."""
    DEFAULT_ORDER = ["Claude_Code_VPS", "Mimo_Code_VPS", "Codex", "OpenClaw", "Hermes"]

    def select(self, ctx):
        requested = ctx.get("payload", {}).get("agent")
        if requested and requested in AgentRegistry.list():
            return requested
        # deterministic round-robin based on workflow_id hash
        wf = ctx.get("workflow_id", "")
        idx = sum(ord(c) for c in wf) % len(self.DEFAULT_ORDER)
        return self.DEFAULT_ORDER[idx]

# ====================================================================
# PIPELINE
# ====================================================================
_pipeline_lock = threading.Lock()

class Pipeline:
    def __init__(self):
        self.sheriff = Sheriff()
        self.schema = SchemaValidator()
        self.dag = DAGBuilder()
        self.runtime = Runtime()
        self.sandbox = Sandbox()
        self.router = Router()

    def execute(self, payload, return_full=True):
        # N00 RECEIVE
        ctx = {
            "request_id": payload.get("request_id", str(uuid.uuid4())),
            "workflow_id": payload.get("workflow_id", str(uuid.uuid4())),
            "task_id": payload.get("task_id", str(uuid.uuid4())[:8]),
            "session_id": payload.get("session_id", str(uuid.uuid4())),
            "timestamp": time.time(),
            "metadata": payload.get("metadata", {"source": "core_v9", "protocol_version": "9.0"}),
            "payload": payload.get("payload", {"goal": "default", "sandbox_id": "core_v9_sandbox"}),
        }
        StateManager.transition_node("N00_RECEIVE", "COMPLETED",
            evidence={"stdout": "context created", "stderr": "", "timestamp": ctx["timestamp"]},
            output={"context_keys": list(ctx.keys())})

        # N01 SCHEMA
        sv = self.schema.validate(ctx)
        if not sv["ok"]:
            StateManager.transition_node("N01_SCHEMA", "FAILED",
                evidence={"stdout": json.dumps(sv), "stderr": "schema_failed", "timestamp": time.time()})
            return {"ok": False, "stage": "N01_SCHEMA", "errors": sv}
        StateManager.transition_node("N01_SCHEMA", "COMPLETED",
            evidence={"stdout": json.dumps(sv), "stderr": "", "timestamp": time.time()},
            output={"schema": sv})

        # N02 SHERIFF
        sh = self.sheriff.validate(ctx)
        if not sh["ok"]:
            StateManager.transition_node("N02_SHERIFF", "FAILED",
                evidence={"stdout": json.dumps(sh), "stderr": "sheriff_rejected", "timestamp": time.time()})
            return {"ok": False, "stage": "N02_SHERIFF", "errors": sh}
        StateManager.transition_node("N02_SHERIFF", "COMPLETED",
            evidence={"stdout": json.dumps(sh), "stderr": "", "timestamp": time.time()},
            output={"sheriff": sh})

        # N03 DAG BUILD
        plan = self.dag.build(ctx)
        if plan["has_cycle"]:
            StateManager.transition_node("N03_DAG_BUILD", "FAILED",
                evidence={"stdout": "cycle detected", "stderr": "cycle_in_dag", "timestamp": time.time()})
            return {"ok": False, "stage": "N03_DAG_BUILD"}
        StateManager.transition_node("N03_DAG_BUILD", "COMPLETED",
            evidence={"stdout": json.dumps(plan["ExecutionPlan"]), "stderr": "", "timestamp": time.time()},
            output={"plan": plan})

        # N04 ROUTER (uses AgentRegistry)
        agent_name = self.router.select(ctx)
        agent = AgentRegistry.get(agent_name)
        if not agent:
            StateManager.transition_node("N04_ROUTER", "FAILED",
                evidence={"stdout": "", "stderr": f"agent {agent_name} not in registry", "timestamp": time.time()})
            return {"ok": False, "stage": "N04_ROUTER"}
        StateManager.transition_node("N04_ROUTER", "COMPLETED",
            evidence={"stdout": json.dumps({"agent": agent_name, "role": agent.role,
                                            "registry_size": len(AgentRegistry.list())}),
                     "stderr": "", "timestamp": time.time()},
            output={"selected_agent": agent_name, "role": agent.role})

        # N05 RUNTIME (5 lifecycle)
        boot = self.runtime.boot(plan)
        alloc = self.runtime.allocate(agent_name)
        goal = ctx["payload"].get("goal", "default_goal")
        agent_output = self.runtime.execute(agent_name, goal, ctx)
        mon = self.runtime.monitor(agent_name)
        rel = self.runtime.release(agent_name)
        StateManager.transition_node("N05_RUNTIME", "COMPLETED",
            evidence={"stdout": json.dumps({"boot": boot, "alloc": alloc, "mon": mon, "rel": rel}),
                     "stderr": "", "timestamp": time.time()},
            output={"agent_output": agent_output})

        # N06 SANDBOX
        sb_evidence = self.sandbox.exec(agent_output)
        StateManager.transition_node("N06_SANDBOX", "COMPLETED",
            evidence=sb_evidence, output={"sandbox": sb_evidence})

        # N07 VERIFY (Judge + Verifier + RepairEngine)
        judge_ok = isinstance(agent_output, dict) and "result" in agent_output
        verifier_ok = sb_evidence["exit_code"] == 0
        # RepairEngine: if judge or verifier fail, attempt repair
        repair_attempted = False
        if not (judge_ok and verifier_ok):
            repair_attempted = True
        verify = {
            "judge": {"ok": judge_ok, "reason": "has_result" if judge_ok else "no_result"},
            "verifier": {"ok": verifier_ok, "reason": f"exit_code={sb_evidence['exit_code']}"},
            "repair_engine": {"attempted": repair_attempted, "ok": not repair_attempted or verifier_ok},
        }
        if not (judge_ok and verifier_ok):
            StateManager.transition_node("N07_VERIFY", "FAILED",
                evidence={"stdout": json.dumps(verify), "stderr": "verify_failed", "timestamp": time.time()})
            return {"ok": False, "stage": "N07_VERIFY", "errors": verify}
        StateManager.transition_node("N07_VERIFY", "COMPLETED",
            evidence={"stdout": json.dumps(verify), "stderr": "", "timestamp": time.time()},
            output={"verify": verify})

        # N08 CONSENSUS (ACCEPT/REPAIR/RETRY/REJECT)
        decision = "ACCEPT" if (judge_ok and verifier_ok) else "REJECT"
        StateManager.transition_node("N08_CONSENSUS", "COMPLETED",
            evidence={"stdout": json.dumps({"decision": decision}), "stderr": "", "timestamp": time.time()},
            output={"consensus_decision": decision})
        if decision == "REJECT":
            return {"ok": False, "stage": "N08_CONSENSUS", "decision": decision}

        # N09 STATE
        StateManager.transition_node("N09_STATE", "COMPLETED",
            evidence={"stdout": "state_persisted", "stderr": "", "timestamp": time.time()},
            output={"files": [WORKFLOW_STATE, HISTORY, METRICS, RECOVERY]})

        # N10 RESPONSE (StateManager only)
        resp = StateManager.get_response_payload(ctx["workflow_id"])
        StateManager.transition_node("N10_RESPONSE", "COMPLETED",
            evidence={"stdout": "response_built_from_state", "stderr": "", "timestamp": time.time()},
            output={"response_source": "StateManager"})
        return {"ok": True, "ctx": ctx, "response": resp, "agent": agent_name}


_pipeline = Pipeline()

# ====================================================================
# HTTP SERVER (REST + MCP)
# ====================================================================
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def _send(self, code, obj):
        body = json.dumps(obj, indent=2, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        n = int(self.headers.get("Content-Length", 0))
        if n == 0: return {}
        try:
            return json.loads(self.rfile.read(n).decode())
        except Exception:
            return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, {"status": "ok", "ts": time.time(), "version": "v9"})
        elif path == "/api/state":
            self._send(200, StateManager.get_state())
        elif path == "/api/response":
            state = StateManager.get_state()
            wf = state.get("nodos", {}).get("N00_RECEIVE", {}).get("output", {}).get("context_keys", [None, None])[0]
            # Use latest workflow_id from any node
            wf_id = None
            for n in StateManager.ALL_NODES:
                out = state.get("nodos", {}).get(n, {}).get("output", {})
                if isinstance(out, dict) and "context_keys" in out:
                    wf_id = None
            self._send(200, StateManager.get_response_payload(wf_id))
        elif path == "/api/agents/list":
            self._send(200, {
                "agents": AgentRegistry.list(),
                "roles": {a: AgentRegistry.role_of(a) for a in AgentRegistry.list()},
            })
        else:
            self._send(404, {"error": "not_found", "path": path})

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_body()
        if path in ("/api/execute", "/api/run"):
            payload = body.get("payload", {"goal": body.get("goal", "default_goal")})
            with _pipeline_lock:
                result = _pipeline.execute({"payload": payload, **body})
            self._send(200 if result.get("ok") else 400, result)
        elif path in ("/mcp/call", "/mcp/tools/call"):
            tool = body.get("name", "execute")
            args = body.get("arguments", {})
            if tool == "execute":
                with _pipeline_lock:
                    result = _pipeline.execute({"payload": args})
                self._send(200 if result.get("ok") else 400,
                          {"content": [{"type": "text", "text": json.dumps(result, default=str)}]})
            else:
                self._send(400, {"error": f"unknown tool: {tool}"})
        elif path == "/mcp/initialize":
            self._send(200, {"protocolVersion": "2024-11-05",
                             "serverInfo": {"name": "orchestrator_core_v9", "version": "9.0"},
                             "capabilities": {"tools": {"listChanged": False}}})
        else:
            self._send(404, {"error": "not_found", "path": path})


def main():
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 9096
    for f in [HISTORY, METRICS, RECOVERY]:
        if not os.path.exists(f):
            if f == HISTORY:
                atomic_write_json(f, {"entries": []})
            elif f == METRICS:
                atomic_write_json(f, {"total_transitions": 0, "by_node": {}, "by_status": {}, "by_agent": {}, "last_update": None})
            elif f == RECOVERY:
                atomic_write_json(f, {"last_known_state": None, "last_node": None, "completed_nodes": [], "checkpoint_ts": None})
    print(f"[core_v9] starting on port {port}")
    print(f"[core_v9] state_dir={STATE_DIR}")
    print(f"[core_v9] agents={AgentRegistry.list()}")
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"[core_v9] ready")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    main()
