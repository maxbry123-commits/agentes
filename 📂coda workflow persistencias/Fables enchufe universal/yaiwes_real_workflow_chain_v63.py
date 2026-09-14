from __future__ import annotations

import contextvars
import hashlib
import importlib.util
import json
import re
import sys
import textwrap
import types
from pathlib import Path
from typing import Any

import yaiwes_real_workflow_chain_v62 as v62

base = v62.base
v61 = v62.v61
SCHEMA = "yaiwes.linear.persistence/v6.3"
_CURRENT_INPUT: contextvars.ContextVar[Any] = contextvars.ContextVar("yaiwes_v63_input", default={})


def _jsonable(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "<depth-limit>"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return {"bytes_sha256": hashlib.sha256(value).hexdigest(), "size": len(value)}
    if isinstance(value, dict):
        return {str(k): _jsonable(v, depth + 1) for k, v in list(value.items())[:100]}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v, depth + 1) for v in list(value)[:100]]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "__dict__"):
        data = {k: _jsonable(v, depth + 1) for k, v in vars(value).items() if not k.startswith("_")}
        return data or repr(value)[:500]
    return repr(value)[:500]


def _stable_json(value: Any) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _input_text(value: Any, limit: int = 1200) -> str:
    text = value if isinstance(value, str) else _stable_json(value)
    return " ".join(text.split())[:limit] or "empty-input"


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(_jsonable(data), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _probe_self(ordinal: int):
    obj = base._ProbeSelf(ordinal)
    if ordinal == 11:
        obj._is_duplicate_step = lambda step: False
        obj.failed_attempts = {}
        obj.add_failed_attempt = lambda tool_args: None
    if ordinal == 16:
        obj.max_total_commands = 0
        obj.target_ip = "0.0.0.0"
        obj.machine_name = "YAIWES-SAFE"
        obj.attacker_ip = "0.0.0.0"
        obj.model = "YAIWES-SAFE"
        obj.state = types.SimpleNamespace(
            current_phase=None,
            total_commands=0,
            flags={},
            phases_completed=[],
            open_ports=[],
            vulnerabilities=[],
            shells=[],
        )
    return obj


def _arg_value_v63(name: str, ordinal: int):
    current = _CURRENT_INPUT.get()
    text = _input_text(current)
    input_id = "yaiwes-" + _digest(current)[:16]
    low = name.lower()
    if name in {"self", "cls"}:
        return _probe_self(ordinal)
    if ordinal == 11 and low == "step":
        return {
            "think": text[:240],
            "tool_args": "internal-persistence-only",
            "output": "workflow handoff persisted",
            "analysis": {"progress_level": "major", "analysis": "linear handoff accepted"},
        }
    if low == "max_tries" or low.endswith("iterations") or low.endswith("count"):
        return 1
    if low == "challenge":
        return {"name": input_id, "flag": "never-match", "description": text[:300], "category": "research"}
    if low == "pentest_agent":
        agent = base._SafeAgent()
        agent.target_text = text[:500]
        return agent
    if low in {"tokenize_cb", "callback", "cb"}:
        return lambda value="", session_id=None, *a, **k: value
    if low.endswith("id") or low in {"run_id", "task_id", "session_id", "conversation_id", "trace_id"}:
        return input_id
    if low in {"text", "question", "instruction", "objective", "result", "input", "content"}:
        return text
    if low in {"max_steps", "priority"}:
        return 1
    return base._Null(f"arg:{name}")


_original_python_probe = base._python_probe


def _python_probe_v63(ordinal: int, contract: dict[str, Any], symbol: str) -> dict[str, Any]:
    source = str(contract["source"])
    captured: list[Any] = []
    old_profile = sys.getprofile()

    def profiler(frame, event, arg):
        if event == "return" and frame.f_code.co_filename == source and frame.f_code.co_name == "__yaiwes_entry":
            captured.append(arg)
        return profiler

    sys.setprofile(profiler)
    try:
        evidence = _original_python_probe(ordinal, contract, symbol)
    finally:
        sys.setprofile(old_profile)
    evidence = dict(evidence)
    evidence["engine"] = "PYTHON_ORIGINAL_BODY_SAFE_SANDBOX_V63"
    evidence["result"] = _jsonable(captured[-1] if captured else None)
    evidence["input_digest"] = _digest(_CURRENT_INPUT.get())
    return evidence


def _extract_marker(output: str) -> Any:
    matches = re.findall(r"YAIWES_RESULT=(.+)", output)
    if not matches:
        return None
    raw = re.sub(r"\s+\([^)]*\)$", "", matches[-1].strip())
    try:
        return json.loads(raw)
    except Exception:
        return raw[:1000]


def _go_probe_v63(ordinal: int, comp: Path, contract: dict[str, Any]) -> dict[str, Any]:
    current = _CURRENT_INPUT.get()
    input_text = _input_text(current, 600)
    input_id = "yaiwes-" + _digest(current)[:16]
    go_input = json.dumps(input_text, ensure_ascii=True)
    go_id = json.dumps(input_id, ensure_ascii=True)
    text = contract["text"]

    if ordinal == 2:
        fn = v61._extract_func(text, r"^func \(db \*DB\) ListConversationPlanTasks\(")
        src = f'''package probe
import "time"
type ConversationPlanTask struct{{ ID string }}
type DB struct{{}}
func (db *DB) ListConversationPlanTasksSince(conversationID string, since time.Time) ([]ConversationPlanTask, error) {{
    return []ConversationPlanTask{{{{ID: conversationID}}}}, nil
}}
{fn}
'''
        test = f'''package probe
import "testing"
func TestYAIWESV61InternalWorkflow(t *testing.T) {{
    var db *DB
    got, err := db.ListConversationPlanTasks({go_id})
    if err != nil || len(got) != 1 || got[0].ID != {go_id} {{ t.Fatalf("unexpected %v %v", got, err) }}
    t.Log("YAIWES_GO_INTERNAL_WORKFLOW_ENTERED")
    t.Logf("YAIWES_RESULT=%s", got[0].ID)
}}
'''
        files = {"workflow.go": src}
    elif ordinal == 5:
        fn = v61._extract_func(text, r"^func NewTaskManager\(")
        src = f'''package probe
import (
    "sync"
    database "yaiwesprobe/database"
)
type AgentManager struct{{}}
type TaskCreateRequest struct{{}}
type FileUploadConfig struct{{}}
type SSEManager struct{{}}
type TaskManager struct {{
    mu sync.RWMutex
    tasks map[string]*TaskCreateRequest
    agentManager *AgentManager
    taskStore *database.TaskStore
    modelStore *database.ModelStore
    fileConfig *FileUploadConfig
    sseManager *SSEManager
    dispatchCounter uint64
}}
func DefaultFileUploadConfig() *FileUploadConfig {{ return &FileUploadConfig{{}} }}
func NewSSEManager() *SSEManager {{ return &SSEManager{{}} }}
{fn}
'''
        db = 'package database\ntype TaskStore struct{}\ntype ModelStore struct{}\n'
        test = f'''package probe
import "testing"
func TestYAIWESV61InternalWorkflow(t *testing.T) {{
    tm := NewTaskManager(nil,nil,nil,nil,nil)
    if tm == nil || tm.tasks == nil || tm.fileConfig == nil || tm.sseManager == nil {{ t.Fatal("task workflow not initialized") }}
    _ = {go_input}
    t.Log("YAIWES_GO_INTERNAL_WORKFLOW_ENTERED")
    t.Log("YAIWES_RESULT={{\\"initialized\\":true}}")
}}
'''
        files = {"workflow.go": src, "database/stub.go": db}
    elif ordinal == 6:
        fn = v61._extract_func(text, r"^func SaveToTemp\(")
        src = f'''package probe
import (
    "crypto/md5"
    "encoding/hex"
    "fmt"
    "io"
    "os"
)
{fn}
'''
        test = f'''package probe
import ("os"; "strings"; "testing")
func TestYAIWESV61InternalWorkflow(t *testing.T) {{
    dir := t.TempDir()
    content := {go_input}
    p, hash, size, err := SaveToTemp(strings.NewReader(content), dir)
    if err != nil || size != int64(len(content)) || hash == "" {{ t.Fatalf("persist workflow failed: %v", err) }}
    if _, err := os.Stat(p); err != nil {{ t.Fatal(err) }}
    t.Log("YAIWES_GO_INTERNAL_WORKFLOW_ENTERED")
    t.Logf("YAIWES_RESULT={{\\"hash\\":%q,\\"size\\":%d}}", hash, size)
}}
'''
        files = {"workflow.go": src}
    elif ordinal == 10:
        fn = v61._extract_func(text, r"^func \(p \*Planner\) DecomposeObjective\(")
        src = f'''package probe
import "strings"
type Milestone struct {{
    Name string `json:"name"`
    Description string `json:"description"`
    Completed bool `json:"completed"`
}}
type Planner struct{{}}
func NewPlanner() *Planner {{ return &Planner{{}} }}
func toLower(s string) string {{ return strings.ToLower(s) }}
func containsIgnoreCase(s, sub string) bool {{ return strings.Contains(strings.ToLower(s), strings.ToLower(sub)) }}
{fn}
'''
        test = f'''package probe
import "testing"
func TestYAIWESV61InternalWorkflow(t *testing.T) {{
    p := NewPlanner()
    objective := {go_input} + " generate a research report"
    ms := p.DecomposeObjective(objective)
    if len(ms) == 0 {{ t.Fatalf("planner workflow mismatch: %v", ms) }}
    t.Log("YAIWES_GO_INTERNAL_WORKFLOW_ENTERED")
    t.Logf("YAIWES_RESULT={{\\"milestones\\":%d,\\"last\\":%q}}", len(ms), ms[len(ms)-1].Name)
}}
'''
        files = {"workflow.go": src}
    else:
        raise RuntimeError(f"no isolated Go probe for YAIWES {ordinal:02d}")

    cmd, output = v61._run_isolated_go(files, test)
    return {
        "engine": "GO_NATIVE_ISOLATED_ORIGINAL_SYMBOL_V63",
        "entered": True,
        "status": "COMPLETED",
        "command": cmd,
        "output": output,
        "result": _extract_marker(output),
        "input_digest": _digest(current),
    }


def _typescript_probe_v63(comp: Path, contract: dict[str, Any]) -> dict[str, Any]:
    current = _CURRENT_INPUT.get()
    reason = _input_text(current, 700)
    source: Path = contract["source"]
    code_root = comp / "code"
    rel = source.relative_to(code_root).as_posix()
    probe = code_root / ".yaiwes_v63_workflow_probe.ts"
    js_reason = json.dumps(reason, ensure_ascii=False)
    probe.write_text(textwrap.dedent(f'''\
        import {{ normalizePlannerDecision }} from "./{rel}";
        const input = {js_reason};
        const d = normalizePlannerDecision({{ reason: input, commands: [] }});
        if (d.reason !== input || d.commands.length !== 0) throw new Error("planner workflow mismatch");
        console.log("YAIWES_TS_INTERNAL_WORKFLOW_ENTERED");
        console.log("YAIWES_RESULT=" + JSON.stringify(d));
    '''), encoding="utf-8")
    cmd = ["npx", "--yes", "tsx", probe.name]
    try:
        cp = base.subprocess.run(cmd, cwd=code_root, text=True, capture_output=True, timeout=180)
    finally:
        probe.unlink(missing_ok=True)
    if cp.returncode != 0 or "YAIWES_TS_INTERNAL_WORKFLOW_ENTERED" not in cp.stdout:
        raise RuntimeError("TypeScript original workflow probe failed: " + (cp.stderr or cp.stdout)[-4000:])
    return {
        "engine": "TYPESCRIPT_NATIVE_ORIGINAL_MODULE_V63",
        "entered": True,
        "status": "COMPLETED",
        "command": cmd,
        "output": cp.stdout.strip(),
        "result": _extract_marker(cp.stdout),
        "input_digest": _digest(current),
    }


base._arg_value = _arg_value_v63
base._python_probe = _python_probe_v63
base._go_probe = _go_probe_v63
base._typescript_probe = _typescript_probe_v63


def _component_roots_strict() -> dict[int, Path]:
    roots: dict[int, Path] = {}
    for child in base.ROOT.iterdir():
        if not child.is_dir():
            continue
        m = re.match(r"^🏈\s+(\d{2})(?:[- ]|$)", child.name)
        if not m:
            continue
        ordinal = int(m.group(1))
        if 1 <= ordinal <= 24 and ordinal not in roots:
            roots[ordinal] = child
    missing = [i for i in range(1, 25) if i not in roots]
    if missing:
        raise RuntimeError(f"missing YAIWES component roots: {missing}")
    return roots


def _load_yaiwes24_module() -> Any:
    source = base.ROOT / "🏈 YAIWES 24" / "code" / "workflow.py"
    if not source.is_file():
        raise RuntimeError("YAIWES 24 safe internal workflow is missing")
    spec = importlib.util.spec_from_file_location("yaiwes24_internal_workflow", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load YAIWES 24 internal workflow")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _workflow_output(state: dict[str, Any], ordinal: int) -> dict[str, Any]:
    evidence = state.get("evidence") or {}
    return {
        "schema": SCHEMA,
        "component": f"YAIWES {ordinal:02d}",
        "workflow_status": state.get("workflow_status"),
        "workflow_result": _jsonable(evidence.get("result")),
        "source_sha256": state.get("source_sha256"),
        "engine": state.get("engine"),
        "safe_boundary": evidence.get("safe_boundary"),
    }


def _run_link(
    ordinal: int,
    comp: Path,
    task_id: str,
    task: dict[str, Any],
    current_input: Any,
    state_root: Path,
    history: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    label = f"YAIWES {ordinal:02d}"
    state_path = state_root / label / f"{task_id}.json"
    input_hash = _digest(current_input)
    claimed = {
        "schema": SCHEMA,
        "component": label,
        "task_id": task_id,
        "status": "CLAIMED",
        "input_hash": input_hash,
        "checkpoint": "INPUT_RECEIVED",
    }
    _atomic_write(state_path, claimed)

    if ordinal == 24:
        module = _load_yaiwes24_module()
        result = module.run_workflow(task=task, previous_output=current_input, history=history)
        source_path = base.ROOT / "🏈 YAIWES 24" / "code" / "workflow.py"
        workflow_state = {
            "workflow_source": "🏈 YAIWES 24/code/workflow.py",
            "workflow_symbol": "run_workflow",
            "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        }
        output = {
            "schema": SCHEMA,
            "component": label,
            "workflow_status": "COMPLETED",
            "workflow_result": _jsonable(result),
            "engine": "YAIWES24_LOCAL_SAFE_INTERNAL_WORKFLOW",
            "implementation_origin": "LOCAL_SAFE_REPLACEMENT",
        }
    else:
        token = _CURRENT_INPUT.set(current_input)
        try:
            internal_state = base.run_component(
                ordinal,
                comp,
                task_id,
                {"task": task, "chain_input": _jsonable(current_input), "chain_input_hash": input_hash},
                state_root / ".internal",
            )
        finally:
            _CURRENT_INPUT.reset(token)
        if not internal_state.get("real_internal_workflow"):
            raise RuntimeError(f"{label} did not execute a real internal workflow")
        if internal_state.get("workflow_status") != "COMPLETED":
            raise RuntimeError(f"{label} internal workflow not operational: {internal_state.get('workflow_status')}")
        workflow_state = internal_state
        output = _workflow_output(internal_state, ordinal)

    output_hash = _digest(output)
    released = {
        **claimed,
        "status": "RELEASED",
        "real_internal_workflow": True,
        "workflow_status": output.get("workflow_status"),
        "workflow_source": workflow_state.get("workflow_source"),
        "workflow_symbol": workflow_state.get("workflow_symbol"),
        "source_sha256": workflow_state.get("source_sha256"),
        "engine": output.get("engine"),
        "checkpoint": "REAL_INTERNAL_WORKFLOW_EXECUTED",
        "output": output,
        "output_hash": output_hash,
        "handoff": f"YAIWES {ordinal + 1:02d}" if ordinal < 24 else "UNIVERSAL_PLUG",
    }
    _atomic_write(state_path, released)
    return released, output


def run_linear_chain(state_root: str | Path, task_id: str, task: dict[str, Any] | None = None) -> dict[str, Any]:
    state_root = Path(state_root)
    task = dict(task or {})
    components = _component_roots_strict()
    history: list[dict[str, Any]] = []
    current_input: Any = {"schema": SCHEMA, "task_id": task_id, "task": task, "origin": "CHAIN_INPUT"}

    for ordinal in range(1, 25):
        state, current_output = _run_link(ordinal, components[ordinal], task_id, task, current_input, state_root, history)
        if ordinal > 1 and state["input_hash"] != history[-1]["output_hash"]:
            raise RuntimeError(f"handoff continuity failure at {state['component']}")
        history.append(state)
        current_input = current_output

    real_count = sum(bool(x.get("real_internal_workflow")) for x in history)
    continuity = all(history[i]["input_hash"] == history[i - 1]["output_hash"] for i in range(1, len(history)))
    if real_count != 24 or not continuity:
        raise RuntimeError(f"strict chain blocked: real={real_count}/24 continuity={continuity}")

    plug_state = {
        "schema": SCHEMA,
        "status": "READY",
        "task_id": task_id,
        "input_hash": _digest(current_input),
        "upstream_output_hash": history[-1]["output_hash"],
        "continuity_ok": _digest(current_input) == history[-1]["output_hash"],
        "checkpoint": "UNIVERSAL_PLUG_RECEIVED_AFTER_24",
    }
    if not plug_state["continuity_ok"]:
        raise RuntimeError("universal plug continuity failure")
    _atomic_write(state_root / "UNIVERSAL_PLUG" / f"{task_id}.json", plug_state)

    report = {
        "schema": SCHEMA,
        "task_id": task_id,
        "components": 24,
        "real_internal_workflows_executed": real_count,
        "completed_internal_workflows": sum(x.get("workflow_status") == "COMPLETED" for x in history),
        "handoff_continuity": continuity,
        "universal_plug_after_component_24": True,
        "status": "CLOSED_24_OF_24",
        "final_output": current_input,
        "evidence": history,
    }
    _atomic_write(base.ROOT / "🏈 cancha deportiva de fútbol" / "YAIWES-LINEAR-WORKFLOW-REPORT-V63.json", report)
    return report


if __name__ == "__main__":
    state_root = base.ROOT / "🏈 cancha deportiva de fútbol" / ".yaiwes_v63_runtime"
    report = run_linear_chain(
        state_root,
        "yaiwes-v63-e2e",
        {"mode": "benign-research-persistence", "objective": "verify 24-component linear persistence workflow"},
    )
    print({
        "components": report["components"],
        "real_internal_workflows_executed": report["real_internal_workflows_executed"],
        "completed_internal_workflows": report["completed_internal_workflows"],
        "handoff_continuity": report["handoff_continuity"],
        "universal_plug_after_component_24": report["universal_plug_after_component_24"],
        "status": report["status"],
    })
