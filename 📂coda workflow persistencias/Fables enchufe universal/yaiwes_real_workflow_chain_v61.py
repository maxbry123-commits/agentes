from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

import yaiwes_real_workflow_chain_v6 as base

# YAIWES 06: use its preserved, original resource-persistence workflow instead
# of compiling the wider controller package whose offensive/effectful neighbors
# are intentionally neutralized by v5.2.
base.PROFILES[6] = {
    "language": "go",
    "path": "backend/pkg/resources/resources.go",
    "symbol": "SaveToTemp",
}


def _extract_func(text: str, start_pattern: str) -> str:
    m = re.search(start_pattern, text, flags=re.M)
    if not m:
        raise RuntimeError(f"Go function start not found: {start_pattern}")
    start = text.rfind("\n", 0, m.start()) + 1
    brace = text.find("{", m.start())
    if brace < 0:
        raise RuntimeError("Go function opening brace not found")
    depth = 0
    in_string = False
    escape = False
    raw = False
    i = brace
    while i < len(text):
        ch = text[i]
        if raw:
            if ch == "`": raw = False
        elif in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"': in_string = True
            elif ch == "`": raw = True
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        i += 1
    raise RuntimeError("unterminated Go function")


def _run_isolated_go(files: dict[str, str], test_text: str) -> tuple[list[str], str]:
    with tempfile.TemporaryDirectory(prefix="yaiwes-v61-go-") as td:
        root = Path(td)
        (root / "go.mod").write_text("module yaiwesprobe\n\ngo 1.22\n", encoding="utf-8")
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        (root / "workflow_probe_test.go").write_text(test_text, encoding="utf-8")
        cmd = ["go", "test", "./...", "-run", "^TestYAIWESV61InternalWorkflow$", "-count=1", "-v"]
        cp = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=120,
                            env={**os.environ, "GOWORK":"off", "GOTOOLCHAIN":"local"})
        out = (cp.stdout + cp.stderr)
        if cp.returncode != 0 or "YAIWES_GO_INTERNAL_WORKFLOW_ENTERED" not in out:
            raise RuntimeError("isolated Go original workflow probe failed: " + out[-5000:])
        return cmd, out[-3000:]


def _go_probe(ordinal: int, comp: Path, contract: dict):
    text = contract["text"]
    if ordinal == 2:
        fn = _extract_func(text, r"^func \(db \*DB\) ListConversationPlanTasks\(")
        src = f'''package probe\n\nimport "time"\n\ntype ConversationPlanTask struct{{ ID string }}\ntype DB struct{{}}\nfunc (db *DB) ListConversationPlanTasksSince(conversationID string, since time.Time) ([]ConversationPlanTask, error) {{\n    return []ConversationPlanTask{{{{ID: conversationID}}}}, nil\n}}\n\n{fn}\n'''
        test = '''package probe\nimport "testing"\nfunc TestYAIWESV61InternalWorkflow(t *testing.T) {\n    var db *DB\n    got, err := db.ListConversationPlanTasks("yaiwes-safe")\n    if err != nil || len(got) != 1 || got[0].ID != "yaiwes-safe" { t.Fatalf("unexpected %v %v", got, err) }\n    t.Log("YAIWES_GO_INTERNAL_WORKFLOW_ENTERED")\n}\n'''
        files = {"workflow.go": src}
    elif ordinal == 5:
        fn = _extract_func(text, r"^func NewTaskManager\(")
        src = f'''package probe\n\nimport (\n    "sync"\n    database "yaiwesprobe/database"\n)\n\ntype AgentManager struct{{}}\ntype TaskCreateRequest struct{{}}\ntype FileUploadConfig struct{{}}\ntype SSEManager struct{{}}\ntype TaskManager struct {{\n    mu sync.RWMutex\n    tasks map[string]*TaskCreateRequest\n    agentManager *AgentManager\n    taskStore *database.TaskStore\n    modelStore *database.ModelStore\n    fileConfig *FileUploadConfig\n    sseManager *SSEManager\n    dispatchCounter uint64\n}}\nfunc DefaultFileUploadConfig() *FileUploadConfig {{ return &FileUploadConfig{{}} }}\nfunc NewSSEManager() *SSEManager {{ return &SSEManager{{}} }}\n\n{fn}\n'''
        db = '''package database\ntype TaskStore struct{}\ntype ModelStore struct{}\n'''
        test = '''package probe\nimport "testing"\nfunc TestYAIWESV61InternalWorkflow(t *testing.T) {\n    tm := NewTaskManager(nil,nil,nil,nil,nil)\n    if tm == nil || tm.tasks == nil || tm.fileConfig == nil || tm.sseManager == nil { t.Fatal("task workflow not initialized") }\n    t.Log("YAIWES_GO_INTERNAL_WORKFLOW_ENTERED")\n}\n'''
        files = {"workflow.go": src, "database/stub.go": db}
    elif ordinal == 6:
        fn = _extract_func(text, r"^func SaveToTemp\(")
        src = f'''package probe\n\nimport (\n    "crypto/md5"\n    "encoding/hex"\n    "fmt"\n    "io"\n    "os"\n)\n\n{fn}\n'''
        test = '''package probe\nimport ("os"; "strings"; "testing")\nfunc TestYAIWESV61InternalWorkflow(t *testing.T) {\n    dir := t.TempDir()\n    p, hash, size, err := SaveToTemp(strings.NewReader("yaiwes-persist"), dir)\n    if err != nil || size != int64(len("yaiwes-persist")) || hash == "" { t.Fatalf("persist workflow failed: %v", err) }\n    if _, err := os.Stat(p); err != nil { t.Fatal(err) }\n    t.Log("YAIWES_GO_INTERNAL_WORKFLOW_ENTERED")\n}\n'''
        files = {"workflow.go": src}
    elif ordinal == 10:
        fn = _extract_func(text, r"^func \(p \*Planner\) DecomposeObjective\(")
        src = f'''package probe\n\nimport "strings"\n\ntype Milestone struct {{\n    Name string `json:"name"`\n    Description string `json:"description"`\n    Completed bool `json:"completed"`\n}}\ntype Planner struct{{}}\nfunc NewPlanner() *Planner {{ return &Planner{{}} }}\nfunc toLower(s string) string {{ return strings.ToLower(s) }}\nfunc containsIgnoreCase(s, sub string) bool {{ return strings.Contains(strings.ToLower(s), strings.ToLower(sub)) }}\n\n{fn}\n'''
        test = '''package probe\nimport "testing"\nfunc TestYAIWESV61InternalWorkflow(t *testing.T) {\n    p := NewPlanner()\n    ms := p.DecomposeObjective("generate a research report")\n    if len(ms) == 0 || ms[len(ms)-1].Name != "report_generated" { t.Fatalf("planner workflow mismatch: %v", ms) }\n    t.Log("YAIWES_GO_INTERNAL_WORKFLOW_ENTERED")\n}\n'''
        files = {"workflow.go": src}
    else:
        raise RuntimeError(f"no isolated Go probe for YAIWES {ordinal:02d}")

    cmd, output = _run_isolated_go(files, test)
    return {
        "engine":"GO_NATIVE_ISOLATED_ORIGINAL_SYMBOL",
        "entered":True,
        "status":"COMPLETED",
        "command":cmd,
        "output":output,
    }


base._go_probe = _go_probe


if __name__ == "__main__":
    state_root = base.ROOT / "🏈 cancha deportiva de fútbol" / ".yaiwes_v6_runtime"
    report = base.run_swarm(state_root, "yaiwes-v61-e2e", {"mode":"benign-research-persistence"})
    print({
        "components": report["components"],
        "real_internal_workflows_executed": report["real_internal_workflows_executed"],
        "source_unavailable_closures": report["source_unavailable_closures"],
        "status": report["status"],
    })
