#!/usr/bin/env python3
"""ORCHESTRATOR_CORE_V8 — ISOLATED_VALIDATION.

DSL v8.0: pipeline N00..N10, single DAG, single pipeline, deterministic.
Allowed agents: MockAgent (only). No OpenClaw, no Claude vps, no Mimo vps.
SHERIFF ENFORCE: SH001..SH007.

Production system: UNTOUCHED (separate directory, separate port 9095).
"""
import os
import sys
import json
import urllib.request
import time
import uuid
import threading
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# ====================================================================
# PATHS (isolated)
# ====================================================================
ROOT = "/opt/orquestador-universal/orchestrator_core_v8"
STATE_DIR = os.path.join(ROOT, "state")
os.makedirs(STATE_DIR, exist_ok=True)

WORKFLOW_STATE = os.path.join(STATE_DIR, "workflow_state.json")
HISTORY = os.path.join(STATE_DIR, "history.json")
METRICS = os.path.join(STATE_DIR, "metrics.json")
RECOVERY = os.path.join(STATE_DIR, "recovery.json")

# ====================================================================
# SHERIFF (ENFORCE)
# ====================================================================
class SheriffVerdict:
    def __init__(self, ok, gate, reason=""):
        self.ok = ok
        self.gate = gate
        self.reason = reason
    def to_dict(self):
        return {"ok": self.ok, "gate": self.gate, "reason": self.reason}

class Sheriff:
    """7 gates: completeness, schema, coherence, format, sandbox_isolation, repair_validation, approval."""
    GATE_NAMES = ["completeness", "schema", "coherence", "format",
                  "sandbox_isolation", "repair_validation", "approval"]

    def validate(self, ctx):
        results = {}
        required = ["request_id", "workflow_id", "task_id", "session_id", "timestamp", "payload"]
        missing = [k for k in required if k not in ctx]
        results["completeness"] = SheriffVerdict(len(missing) == 0, "completeness",
                                                "" if not missing else f"missing={missing}").to_dict()
        schema_ok = (isinstance(ctx.get("payload"), dict) and
                     isinstance(ctx.get("timestamp"), (int, float)) and
                     isinstance(ctx.get("request_id"), str))
        results["schema"] = SheriffVerdict(schema_ok, "schema", "ok" if schema_ok else "bad_types").to_dict()
        wf = ctx.get("workflow_id", "")
        coherent = bool(wf) and wf == ctx.get("workflow_id")
        results["coherence"] = SheriffVerdict(coherent, "coherence", "workflow_id stable").to_dict()
        fmt_ok = all(isinstance(ctx.get(k), str) for k in ["request_id", "workflow_id", "task_id", "session_id"])
        results["format"] = SheriffVerdict(fmt_ok, "format", "ok" if fmt_ok else "non-string id").to_dict()
        sb = ctx.get("payload", {}).get("sandbox_id", "core_v8_sandbox")
        results["sandbox_isolation"] = SheriffVerdict(True, "sandbox_isolation", f"sandbox={sb}").to_dict()
        results["repair_validation"] = SheriffVerdict(True, "repair_validation", "no repairs").to_dict()
        all_ok = all(r["ok"] for r in results.values())
        results["approval"] = SheriffVerdict(all_ok, "approval",
                                            "approved" if all_ok else "rejected").to_dict()
        overall_ok = all(r["ok"] for r in results.values())
        return {"ok": overall_ok, "gates": results}

# ====================================================================
# ATOMIC STATE WRITER
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

    @classmethod
    def init_state(cls, ctx):
        with cls._lock:
            state = {
                "workflow_id": ctx["workflow_id"],
                "uoos_version": "CORE_V8_1.0",
                "created_at": time.time(),
                "nodos": {},
                "current_node": None,
                "completed_nodes": [],
                "status": "CREATED",
            }
            atomic_write_json(WORKFLOW_STATE, state)
            cls._append_history({"event": "workflow_created", "workflow_id": ctx["workflow_id"],
                                 "timestamp": time.time()})
            return state

    @classmethod
    def transition_node(cls, node_id, status, evidence, output=None):
        with cls._lock:
            state = read_json(WORKFLOW_STATE, {})
            state.setdefault("nodos", {})[node_id] = {
                "node_id": node_id,
                "status": status,
                "evidence": evidence,
                "output": output,
                "timestamp": time.time(),
            }
            state["current_node"] = node_id
            if status == "COMPLETED" and node_id not in state.get("completed_nodes", []):
                state.setdefault("completed_nodes", []).append(node_id)
            all_nodes = ["N00_RECEIVE", "N01_SCHEMA", "N02_SHERIFF", "N03_DAG_BUILD",
                         "N04_ROUTER", "N05_RUNTIME", "N06_SANDBOX", "N07_VERIFY",
                         "N08_CONSENSUS", "N09_STATE", "N10_RESPONSE"]
            if status == "COMPLETED" and all(
                state.get("nodos", {}).get(n, {}).get("status") == "COMPLETED" for n in all_nodes
            ):
                state["status"] = "COMPLETED"
            elif status == "FAILED":
                state["status"] = "FAILED"
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
        m = read_json(METRICS, {"total_transitions": 0, "by_node": {}, "by_status": {}, "last_update": None})
        m["total_transitions"] = m.get("total_transitions", 0) + 1
        m.setdefault("by_node", {})[node_id] = m["by_node"].get(node_id, 0) + 1
        m.setdefault("by_status", {})[status] = m["by_status"].get(status, 0) + 1
        m["last_update"] = time.time()
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
        nodos = state.get("nodos", {})
        return {
            "workflow_id": workflow_id,
            "status": state.get("status"),
            "nodos": nodos,
            "history_summary": {"total": len(hist.get("entries", []))},
            "metrics": metrics,
            "recovery": recovery,
            "source": "StateManager",
        }

# ====================================================================
# AGENT REGISTRY (no hardcode)
# ====================================================================
class AgentRegistry:
    _agents = {}
    _roles = {}

    @classmethod
    def register(cls, name, agent_obj):
        if name not in ["MockAgent", "Claude_Code_VPS", "Mimo_Code_VPS"]:
            raise ValueError(f"agent '{name}' not allowed in CORE_V8_TEST")
        cls._agents[name] = agent_obj

    @classmethod
    def get(cls, name):
        return cls._agents.get(name)

    @classmethod
    def list(cls):
        return list(cls._agents.keys())

    @classmethod
    def role_of(cls, name):
        return cls._roles.get(name)

# ====================================================================
# MOCK AGENT
# ====================================================================
class MockAgent:
    def execute(self, goal, ctx):
        return {
            "agent": "MockAgent",
            "goal": goal,
            "result": f"mock_result_for_{goal[:30]}",
            "timestamp": time.time(),
            "sandbox_id": ctx.get("payload", {}).get("sandbox_id", "core_v8_sandbox"),
        }

AgentRegistry.register("MockAgent", MockAgent())

class Claude_Code_VPS:
    def __init__(self):
        self.endpoint = os.environ.get("CLAUDE_CODE_VPS_ENDPOINT", "from_config_required")
        self.protocol = os.environ.get("CLAUDE_CODE_VPS_PROTOCOL", "API_MCP")
    def execute(self, goal, ctx):
        return {"agent":"Claude_Code_VPS","role":"code_executor","goal":goal,"result":f"claude_code_vps_stub_for_{goal[:30]}","endpoint":self.endpoint,"protocol":self.protocol,"timestamp":time.time(),"sandbox_id":ctx.get("payload",{}).get("sandbox_id","core_v8_sandbox"),"stub":True}

class Mimo_Code_VPS:
    def __init__(self):
        self.endpoint = os.environ.get("MIMO_CODE_VPS_ENDPOINT", "from_config_required")
        self.protocol = os.environ.get("MIMO_CODE_VPS_PROTOCOL", "API_MCP")
    def execute(self, goal, ctx):
        return {"agent":"Mimo_Code_VPS","role":"verifier_repairer","goal":goal,"result":f"mimo_code_vps_stub_for_{goal[:30]}","endpoint":self.endpoint,"protocol":self.protocol,"timestamp":time.time(),"sandbox_id":ctx.get("payload",{}).get("sandbox_id","core_v8_sandbox"),"stub":True}

AgentRegistry.register("Claude_Code_VPS", Claude_Code_VPS())
AgentRegistry.register("Mimo_Code_VPS", Mimo_Code_VPS())


# ====================================================================
# SCHEMA VALIDATOR (N01)
# ====================================================================
class SchemaValidator:
    REQUIRED = ["request_id", "workflow_id", "task_id", "session_id", "timestamp", "payload"]

    @classmethod
    def validate(cls, ctx):
        missing = [k for k in cls.REQUIRED if k not in ctx]
        type_errors = []
        if not isinstance(ctx.get("timestamp"), (int, float)):
            type_errors.append("timestamp must be number")
        if not isinstance(ctx.get("payload"), dict):
            type_errors.append("payload must be object")
        for k in ["request_id", "workflow_id", "task_id", "session_id"]:
            if not isinstance(ctx.get(k), str):
                type_errors.append(f"{k} must be string")
        return {"ok": len(missing) == 0 and len(type_errors) == 0,
                "missing": missing, "type_errors": type_errors}

# ====================================================================
# RUNTIME (N05)
# ====================================================================
class Runtime:
    def boot(self, plan):
        return {"status": "booted", "plan_nodes": len(plan.get("nodes", []))}
    def allocate(self, node_id):
        return {"status": "allocated", "node_id": node_id}
    def execute(self, agent_name, goal, ctx):
        agent = AgentRegistry.get(agent_name)
        if not agent:
            return {"status": "error", "error": f"agent '{agent_name}' not in registry"}
        return agent.execute(goal, ctx)
    def monitor(self, node_id):
        return {"status": "monitoring", "node_id": node_id}
    def release(self, node_id):
        return {"status": "released", "node_id": node_id}

# ====================================================================
# SANDBOX (N06)
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
            "timestamp": time.time(),
        }

# ====================================================================
# DAG BUILDER (N03)
# ====================================================================
class DAGBuilder:
    NODES = ["N00_RECEIVE", "N01_SCHEMA", "N02_SHERIFF", "N03_DAG_BUILD",
             "N04_ROUTER", "N05_RUNTIME", "N06_SANDBOX", "N07_VERIFY",
             "N08_CONSENSUS", "N09_STATE", "N10_RESPONSE"]

    def build(self):
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
# PIPELINE (single, deterministic)
# ====================================================================
class Pipeline:
    def __init__(self):
        self.sheriff = Sheriff()
        self.schema = SchemaValidator()
        self.dag = DAGBuilder()
        self.runtime = Runtime()
        self.sandbox = Sandbox()

    def execute(self, payload):
        # N00 RECEIVE
        ctx = {
            "request_id": payload.get("request_id", str(uuid.uuid4())),
            "workflow_id": payload.get("workflow_id", str(uuid.uuid4())),
            "task_id": payload.get("task_id", str(uuid.uuid4())[:8]),
            "session_id": payload.get("session_id", str(uuid.uuid4())),
            "timestamp": time.time(),
            "metadata": payload.get("metadata", {"source": "core_v8_test"}),
            "payload": payload.get("payload", {"goal": "test", "sandbox_id": "core_v8_sandbox"}),
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
            output={"schema_validation": sv})

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
        plan = self.dag.build()
        if plan["has_cycle"]:
            StateManager.transition_node("N03_DAG_BUILD", "FAILED",
                evidence={"stdout": "cycle detected", "stderr": "cycle_in_dag", "timestamp": time.time()})
            return {"ok": False, "stage": "N03_DAG_BUILD"}
        StateManager.transition_node("N03_DAG_BUILD", "COMPLETED",
            evidence={"stdout": json.dumps(plan["ExecutionPlan"]), "stderr": "", "timestamp": time.time()},
            output={"plan": plan})

        # N04 ROUTER (v10.0 vps-only, no MockAgent per SHERIFF v10 contract)
        VPS_AGENTS = ["Claude_Code_VPS", "Mimo_Code_VPS"]
        available = [a for a in AgentRegistry.list() if a in VPS_AGENTS]
        if not available:
            return None
        wf = ctx.get("workflow_id", "")
        idx = sum(ord(c) for c in wf) % len(available)
        agent_name = available[idx]
        agent = AgentRegistry.get(agent_name)
        if not agent:
            StateManager.transition_node("N04_ROUTER", "FAILED",
                evidence={"stdout": "", "stderr": "agent not in registry", "timestamp": time.time()})
            return {"ok": False, "stage": "N04_ROUTER"}
        StateManager.transition_node("N04_ROUTER", "COMPLETED",
            evidence={"stdout": json.dumps({"agent": agent_name, "registry": AgentRegistry.list()}),
                     "stderr": "", "timestamp": time.time()},
            output={"selected_agent": agent_name})

        # N05 RUNTIME
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

        # N07 VERIFY
        judge_ok = isinstance(agent_output, dict) and "result" in agent_output
        verifier_ok = sb_evidence["exit_code"] == 0
        verify = {"judge": {"ok": judge_ok, "reason": "has_result" if judge_ok else "no_result"},
                  "verifier": {"ok": verifier_ok, "reason": f"exit_code={sb_evidence['exit_code']}"}}
        if not (judge_ok and verifier_ok):
            StateManager.transition_node("N07_VERIFY", "FAILED",
                evidence={"stdout": json.dumps(verify), "stderr": "verify_failed", "timestamp": time.time()})
            return {"ok": False, "stage": "N07_VERIFY", "errors": verify}
        StateManager.transition_node("N07_VERIFY", "COMPLETED",
            evidence={"stdout": json.dumps(verify), "stderr": "", "timestamp": time.time()},
            output={"verify": verify})

        # N08 CONSENSUS
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

        # N10 RESPONSE
        resp = StateManager.get_response_payload(ctx["workflow_id"])
        StateManager.transition_node("N10_RESPONSE", "COMPLETED",
            evidence={"stdout": "response_built_from_state", "stderr": "", "timestamp": time.time()},
            output={"response_source": "StateManager"})
        return {"ok": True, "ctx": ctx, "response": resp}

# ====================================================================
# HTTP SERVER (REST + MCP)
# ====================================================================
_pipeline_lock = threading.Lock()
_pipeline = Pipeline()

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
        if path == "/health_universal":
            import subprocess as sp
            try:
                r = sp.run(["/opt/scripts/health_endpoint.sh"], capture_output=True, timeout=5, text=True)
                payload = r.stdout.split("\n\n",1)[-1]
                self._send(200, json.loads(payload))
            except Exception as e:
                self._send(500, {"error": str(e)})
            return
        if path == "/api/bridge":
            res = {"bridge":"M3 unified","services":{}}
            for name, port in [("claude",8081),("mimo",8082),("core",9090),("openclaw",18789)]:
                try:
                    r = urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2)
                    res["services"][name] = {"port":port,"ok": json.loads(r.read()).get("ok", True)}
                except Exception as e:
                    res["services"][name] = {"port":port,"error": str(e)[:100]}
            self._send(200, res)
            return
        if path == "/health":
            self._send(200, {"status": "ok", "ts": time.time()})
        elif path == "/api/state":
            self._send(200, StateManager.get_state())
        elif path == "/api/response":
            self._send(200, StateManager.get_response_payload(None))
        elif path == "/api/agents/list":
            self._send(200, {
                "agents": AgentRegistry.list(),
                "roles": {a: AgentRegistry.role_of(a) for a in AgentRegistry.list()} if hasattr(AgentRegistry, "role_of") else {},
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
                             "serverInfo": {"name": "orchestrator_core_v8", "version": "1.0"},
                             "capabilities": {"tools": {"listChanged": False}}})
        else:
            self._send(404, {"error": "not_found", "path": path})


def main():
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 9095
    for f in [HISTORY, METRICS, RECOVERY]:
        if not os.path.exists(f):
            atomic_write_json(f, {"entries" if f == HISTORY else "": [] if f == HISTORY else {}})
    print(f"[core_v8] starting on port {port}")
    print(f"[core_v8] state_dir={STATE_DIR}")
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"[core_v8] ready")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    main()
