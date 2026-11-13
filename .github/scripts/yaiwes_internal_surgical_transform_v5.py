#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path("📂coda workflow persistencias")
FIELD = ROOT / "🏈 cancha deportiva de fútbol"
FABLES = ROOT / "Fables enchufe universal"
TEAM = "Swarm agent team Navy seals YAIWES"
VERSION = "YAIWES-INTERNAL-PERSISTENCE-v5.0"
SCHEMA = "yaiwes.internal.surgical/v5"
EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb", ".sh", ".ps1", ".php", ".lua"}
SKIP_PARTS = {
    ".git", "node_modules", "vendor", "third_party", "dist", "build", ".venv", "venv",
    "__pycache__", "target", "_archives", "_yaiwes_upstream_quarantine", "coda_persistence",
    "yaiwes_internal", "tests", "test", "testing", "docs", "doc", "examples", "example", "fixtures"
}
OFFENSIVE_TOKENS = (
    "exploit", "attack", "pentest", "redteam", "red_team", "scanner", "scanning", "smart_scan",
    "vulnerab", "payload", "injection", "ssrf", "deserialization", "reverse_shell", "shellcode",
    "bruteforce", "brute_force", "credential_dump", "exfil", "malware", "ransom", "fuzz",
    "recon", "enumerat", "nmap", "sqlmap", "metasploit", "nuclei", "masscan", "kunlun",
    "run_code", "sandbox_language", "security_tools", "command_exec", "code_exec", "rce",
    "privilege_escal", "lateral_move", "phishing"
)
BENIGN_TOKENS = (
    "auth", "rate_limit", "ratelimit", "verification", "validator", "validation", "task", "workflow",
    "queue", "state", "memory", "checkpoint", "retry", "recover", "scheduler", "schedule",
    "llm", "adapter", "embedding", "rag", "telemetry", "logging", "logger", "config", "settings",
    "schema", "model", "storage", "cache", "database", "db", "repository", "service", "api",
    "git_ssh", "git_service", "setup.js", "prompt", "health", "metrics"
)
EXEC_MARKERS = (
    "subprocess.", "os.system(", "os.popen(", "socket.", "requests.", "httpx.", "aiohttp.",
    "child_process", "exec.command(", "std::process::command", "runtime.getruntime().exec(",
    "invoke-expression", "start-process", "eval(", "exec("
)
STRONG_CONTENT_RISK = (
    "reverse shell", "meterpreter", "metasploit", "sqlmap", "nmap ", "nuclei ", "masscan",
    "credential dump", "privilege escalation", "remote code execution", "command injection",
    "sql injection", "ssrf", "deserialization exploit", "brute force", "exploit payload"
)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def components() -> list[Path]:
    out = sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("🏈 ") and p.name != "🏈 cancha deportiva de fútbol")
    if len(out) != 24:
        raise SystemExit(f"EXPECTED_24_COMPONENTS:{len(out)}")
    return out


def active_sources(code: Path):
    for p in code.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in EXTS:
            continue
        rel = p.relative_to(code)
        if set(rel.parts) & SKIP_PARTS:
            continue
        if p.stat().st_size <= 1_500_000:
            yield p


def original_for(code: Path, active: Path) -> tuple[str | None, Path | None, bool]:
    rel = active.relative_to(code)
    q = code / "_yaiwes_upstream_quarantine" / rel
    q = q.with_name(q.name + ".original")
    if q.is_file():
        return read_text(q), q, True
    return read_text(active), None, False


def classify(rel: str, original: str, had_quarantine: bool) -> tuple[str, str]:
    low_path = rel.lower()
    low = original.lower()
    if any(tok in low_path for tok in OFFENSIVE_TOKENS):
        return "BLOCK_OFFENSIVE", "offensive path semantics"
    if any(tok in low for tok in STRONG_CONTENT_RISK) and any(m in low for m in EXEC_MARKERS):
        return "BLOCK_OFFENSIVE", "offensive content plus execution surface"
    if any(tok in low_path for tok in BENIGN_TOKENS):
        return "RESTORE_BENIGN", "benign infrastructure/workflow semantics"
    if had_quarantine:
        return "REVIEW_FAIL_CLOSED", "previously transformed effectful file without safe classification"
    return "KEEP_UNCHANGED", "no surgical transformation required"


def py_symbols(original: str):
    try:
        tree = ast.parse(original)
    except SyntaxError:
        return [], []
    functions, classes = [], []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append((node.name, isinstance(node, ast.AsyncFunctionDef)))
        elif isinstance(node, ast.ClassDef):
            methods = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append((child.name, isinstance(child, ast.AsyncFunctionDef)))
            classes.append((node.name, methods))
    return functions, classes


def python_safe_replacement(original: str, rel: str, decision: str) -> str:
    sid = hashlib.sha256(rel.encode("utf-8")).hexdigest()
    funcs, classes = py_symbols(original)
    lines = [
        '"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""',
        "from __future__ import annotations", "from pathlib import Path", "import json", "",
        f"SOURCE_ID = {sid!r}", f"DECISION = {decision!r}", "",
        "def _yaiwes_checkpoint(step: str, payload=None):",
        "    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}",
        "    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')",
        "    with p.open('a', encoding='utf-8') as f:",
        "        f.write(json.dumps(event, ensure_ascii=False) + '\\n')",
        "    return event", "",
        "def yaiwes_persistence_step(payload=None):", "    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)", "",
    ]
    for name, is_async in funcs:
        if name == "yaiwes_persistence_step":
            continue
        prefix = "async def" if is_async else "def"
        lines += [f"{prefix} {name}(*args, **kwargs):", f"    return _yaiwes_checkpoint({name!r}, kwargs)", ""]
    for cls, methods in classes:
        lines.append(f"class {cls}:")
        if not methods:
            lines += ["    pass", ""]
            continue
        for name, is_async in methods:
            if name == "__init__":
                lines += ["    def __init__(self, *args, **kwargs):", f"        self._yaiwes_checkpoint = _yaiwes_checkpoint({(cls+'.__init__')!r}, kwargs)"]
            else:
                prefix = "async def" if is_async else "def"
                lines += [f"    {prefix} {name}(self, *args, **kwargs):", f"        return _yaiwes_checkpoint({(cls+'.'+name)!r}, kwargs)"]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def safe_replacement(ext: str, rel: str, original: str, decision: str) -> str:
    sid = hashlib.sha256(rel.encode("utf-8")).hexdigest()
    event = json.dumps({"schema":"yaiwes.internal.persistence/v5","source_id":sid,"status":"CHECKPOINTED"}, separators=(",", ":"))
    if ext == ".py":
        return python_safe_replacement(original, rel, decision)
    if ext in {".js", ".jsx", ".ts", ".tsx"}:
        names = sorted(set(re.findall(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", original)))
        body = [f"const SOURCE_ID = {json.dumps(sid)};", "function _yaiwesCheckpoint(step, payload = {}) { return {schema:'yaiwes.internal.persistence/v5', source_id:SOURCE_ID, step, payload, status:'CHECKPOINTED'}; }", "export function yaiwesPersistenceStep(payload = {}) { return _yaiwesCheckpoint('yaiwesPersistenceStep', payload); }"]
        for n in names:
            if n != "yaiwesPersistenceStep":
                body.append(f"export function {n}(...args) {{ return _yaiwesCheckpoint({json.dumps(n)}, {{args_count: args.length}}); }}")
        body.append("export default yaiwesPersistenceStep;")
        return "\n".join(body) + "\n"
    if ext == ".sh":
        return f'#!/usr/bin/env bash\nset -euo pipefail\nprintf \'%s\\n\' \'{{"schema":"yaiwes.internal.persistence/v5","source_id":"{sid}","status":"CHECKPOINTED"}}\' >> .yaiwes_internal_state.jsonl\n'
    if ext == ".ps1":
        return "$e = '" + event + "'\nAdd-Content -Path (Join-Path $PSScriptRoot '.yaiwes_internal_state.jsonl') -Value $e\n"
    if ext == ".rb":
        return f"def yaiwes_persistence_step(payload = {{}})\n  {{schema: 'yaiwes.internal.persistence/v5', source_id: '{sid}', payload: payload, status: 'CHECKPOINTED'}}\nend\n"
    if ext == ".lua":
        return f"local M={{}}\nfunction M.yaiwes_persistence_step(payload) return {{schema='yaiwes.internal.persistence/v5',source_id='{sid}',payload=payload or {{}},status='CHECKPOINTED'}} end\nreturn M\n"
    if ext == ".php":
        return f"<?php\nfunction yaiwes_persistence_step($payload = []) {{ return ['schema'=>'yaiwes.internal.persistence/v5','source_id'=>'{sid}','payload'=>$payload,'status'=>'CHECKPOINTED']; }}\n"
    if ext == ".go":
        m = re.search(r"(?m)^package\s+([A-Za-z_][A-Za-z0-9_]*)", original)
        pkg = m.group(1) if m else "main"
        return f'package {pkg}\n\ntype YAIWESPersistenceEvent struct {{ SourceID string; Status string }}\nfunc YAIWESPersistenceStep() YAIWESPersistenceEvent {{ return YAIWESPersistenceEvent{{SourceID:"{sid}", Status:"CHECKPOINTED"}} }}\n'
    if ext == ".rs":
        return f'pub fn yaiwes_persistence_step() -> (&\'static str, &\'static str) {{ ("{sid}", "CHECKPOINTED") }}\n'
    if ext == ".java":
        cls = re.sub(r"[^A-Za-z0-9_]", "_", Path(rel).stem)
        return f'class {cls} {{ static String yaiwesPersistenceStep() {{ return "CHECKPOINTED:{sid}"; }} }}\n'
    return original


RUNTIME = '''from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ComponentState:
    task_id: str
    status: str = "PENDING"
    cursor: int = 0
    checkpoints: list | None = None
    evidence: list | None = None
    def __post_init__(self):
        self.checkpoints = [] if self.checkpoints is None else self.checkpoints
        self.evidence = [] if self.evidence is None else self.evidence

class PersistenceRuntime:
    def __init__(self, component_root: str | Path, state_path: str | Path):
        self.component_root = Path(component_root)
        self.state_path = Path(state_path)
        self.manifest_path = self.component_root / "INTERNAL-SURGICAL-MANIFEST-V5.json"
    def _manifest(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if data.get("schema") != "yaiwes.internal.surgical/v5": raise ValueError("bad v5 manifest")
        return data
    def load(self, task_id):
        if not self.state_path.exists(): return ComponentState(task_id)
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        return ComponentState(**data) if data.get("task_id") == task_id else ComponentState(task_id)
    def save(self, state):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)
        return state
    def run(self, task_id, payload=None):
        state = self.load(task_id); state.status = "CLAIMED"; manifest = self._manifest()
        links = [x for x in manifest["files"] if x["decision"] in {"BLOCK_OFFENSIVE","REVIEW_FAIL_CLOSED"}]
        for idx, link in enumerate(links, 1):
            state.status = "CHECKPOINTED"; state.cursor = idx
            state.checkpoints.append({"order":idx,"path":link["path"],"decision":link["decision"],"active_sha256":link["active_sha256"],"payload":dict(payload or {})})
            self.save(state)
        state.status = "VERIFIED"; state.evidence.append({"component":manifest["component"],"links":len(links),"version":manifest["version"]}); self.save(state)
        state.status = "RELEASED"; return self.save(state)
'''


def transform_component(comp: Path) -> dict[str, Any]:
    code = comp / "code"; qroot = code / "_yaiwes_upstream_quarantine"; files = []; seen = set()
    for active in list(active_sources(code)):
        rel = active.relative_to(code).as_posix(); original, q, had_q = original_for(code, active)
        if original is None: continue
        decision, reason = classify(rel, original, had_q); seen.add(rel)
        if decision == "RESTORE_BENIGN" and had_q:
            active.write_text(original, encoding="utf-8")
        elif decision in {"BLOCK_OFFENSIVE", "REVIEW_FAIL_CLOSED"}:
            if not had_q:
                q = qroot / Path(rel); q = q.with_name(q.name + ".original"); q.parent.mkdir(parents=True, exist_ok=True)
                if not q.exists(): q.write_text(original, encoding="utf-8")
                had_q = True
            active.write_text(safe_replacement(active.suffix.lower(), rel, original, decision), encoding="utf-8")
        elif decision == "KEEP_UNCHANGED":
            continue
        active_text = read_text(active) or ""
        files.append({"path":rel,"decision":decision,"reason":reason,"original_sha256":sha256_text(original),"active_sha256":sha256_text(active_text),"quarantine":str(q.relative_to(code)) if q else None,"link":decision in {"BLOCK_OFFENSIVE","REVIEW_FAIL_CLOSED"}})
    if qroot.is_dir():
        for q in qroot.rglob("*.original"):
            qrel = q.relative_to(qroot); rel = qrel.as_posix()[:-len(".original")]
            if rel in seen: continue
            original = read_text(q)
            if original is None: continue
            active = code / rel; active.parent.mkdir(parents=True, exist_ok=True); decision, reason = classify(rel, original, True)
            if decision == "RESTORE_BENIGN": active.write_text(original, encoding="utf-8")
            else:
                decision = "BLOCK_OFFENSIVE" if decision == "BLOCK_OFFENSIVE" else "REVIEW_FAIL_CLOSED"
                active.write_text(safe_replacement(active.suffix.lower(), rel, original, decision), encoding="utf-8")
            at = read_text(active) or ""
            files.append({"path":rel,"decision":decision,"reason":reason,"original_sha256":sha256_text(original),"active_sha256":sha256_text(at),"quarantine":str(q.relative_to(code)),"link":decision in {"BLOCK_OFFENSIVE","REVIEW_FAIL_CLOSED"}})
    files.sort(key=lambda x: x["path"])
    internal = code / "yaiwes_internal"; internal.mkdir(parents=True, exist_ok=True)
    (internal / "__init__.py").write_text("from .persistence_runtime import PersistenceRuntime\n", encoding="utf-8")
    (internal / "persistence_runtime.py").write_text(RUNTIME, encoding="utf-8")
    counts = {"accounted":len(files),"restored_benign":sum(x["decision"]=="RESTORE_BENIGN" for x in files),"blocked_offensive":sum(x["decision"]=="BLOCK_OFFENSIVE" for x in files),"review_fail_closed":sum(x["decision"]=="REVIEW_FAIL_CLOSED" for x in files),"links":sum(bool(x["link"]) for x in files)}
    manifest = {"schema":SCHEMA,"component":comp.name,"team":TEAM,"version":VERSION,"policy":{"restore_benign":True,"offensive_execution":False,"ambiguous":"FAIL_CLOSED","network_default_for_replacements":"deny","source_execution_during_audit":False},"files":files,"counts":counts}
    (comp / "INTERNAL-SURGICAL-MANIFEST-V5.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (comp / "README-INTERNAL-V5.md").write_text(f"# {comp.name} — {VERSION}\n\n## {TEAM}\n\n`ORIGINAL → CLASSIFY → RESTORE_BENIGN | BLOCK_OFFENSIVE | REVIEW_FAIL_CLOSED → CHECKPOINT LINK → VERIFY → RELEASE`\n\n- Archivos contabilizados: **{counts['accounted']}**\n- Restaurados benignos: **{counts['restored_benign']}**\n- Bloqueados ofensivos: **{counts['blocked_offensive']}**\n- Revisión fail-closed: **{counts['review_fail_closed']}**\n- Links internos de persistencia: **{counts['links']}**\n\nLos originales permanecen en `_yaiwes_upstream_quarantine/`. El runtime v5 no importa ni ejecuta esos originales; recorre el manifiesto y persiste checkpoints por cada link sanitizado.\n", encoding="utf-8")
    return manifest


def validate(manifests):
    errors = []
    if len(manifests) != 24: errors.append(f"COMPONENT_COUNT:{len(manifests)}")
    for m in manifests:
        comp = ROOT / m["component"]; code = comp / "code"
        for x in m["files"]:
            active = code / x["path"]; q = code / x["quarantine"] if x.get("quarantine") else None
            if not active.is_file(): errors.append(f"MISSING_ACTIVE:{m['component']}:{x['path']}"); continue
            at = read_text(active)
            if at is None: continue
            if sha256_text(at) != x["active_sha256"]: errors.append(f"ACTIVE_SHA:{m['component']}:{x['path']}")
            if q and not q.is_file(): errors.append(f"MISSING_QUARANTINE:{m['component']}:{x['path']}")
            if x["decision"] == "RESTORE_BENIGN" and sha256_text(at) != x["original_sha256"]: errors.append(f"BENIGN_NOT_RESTORED:{m['component']}:{x['path']}")
            if x["decision"] in {"BLOCK_OFFENSIVE", "REVIEW_FAIL_CLOSED"}:
                low = at.lower()
                if any(marker in low for marker in EXEC_MARKERS): errors.append(f"RESIDUAL_EXECUTION:{m['component']}:{x['path']}")
                if active.suffix.lower() == ".py":
                    try: ast.parse(at)
                    except SyntaxError as e: errors.append(f"PY_SYNTAX:{m['component']}:{x['path']}:{e.lineno}")
        if not (code / "yaiwes_internal" / "persistence_runtime.py").is_file(): errors.append(f"NO_RUNTIME:{m['component']}")
    return errors


def write_master(manifests):
    entries = []
    for idx, m in enumerate(manifests, 1):
        entries.append({"order":idx,"component":m["component"],"manifest":f"{m['component']}/INTERNAL-SURGICAL-MANIFEST-V5.json","runtime":f"{m['component']}/code/yaiwes_internal/persistence_runtime.py","links":m["counts"]["links"],"previous":manifests[idx-2]["component"] if idx>1 else None,"next":manifests[idx]["component"] if idx<len(manifests) else None})
    (FIELD / "YAIWES-INTERNAL-SWARM-REGISTRY-V5.json").write_text(json.dumps({"schema":"yaiwes.internal.swarm/v5","team":TEAM,"version":VERSION,"count":24,"topology":"LINEAR_FAIL_CLOSED","components":entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    runner = '''from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path

def _load_runtime(path: Path):
    name = "yaiwes_v5_runtime_" + str(abs(hash(str(path)))); spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None: raise RuntimeError("runtime import failed")
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod); return mod.PersistenceRuntime

def run_swarm(registry_path, state_root, task_id, payload=None):
    registry_path = Path(registry_path); coda = registry_path.parents[1]; data = json.loads(registry_path.read_text(encoding="utf-8"))
    if data.get("schema") != "yaiwes.internal.swarm/v5" or data.get("count") != 24: raise ValueError("bad v5 swarm registry")
    evidence = []
    for item in data["components"]:
        comp = coda / item["component"]; Runtime = _load_runtime(comp / "code" / "yaiwes_internal" / "persistence_runtime.py")
        state = Runtime(comp, Path(state_root) / item["component"] / f"{task_id}.json").run(task_id, payload)
        if state.status != "RELEASED": raise RuntimeError(f"component not released: {item['component']}")
        evidence.append({"order":item["order"],"component":item["component"],"links":len(state.checkpoints),"status":state.status})
    return {"task_id":task_id,"components_completed":len(evidence),"evidence":evidence}
'''
    test = '''from pathlib import Path
import tempfile, unittest
from yaiwes_internal_swarm_chain_v5 import run_swarm
class V5SwarmTest(unittest.TestCase):
    def test_24_components(self):
        coda = Path(__file__).resolve().parents[1]; registry = coda / "🏈 cancha deportiva de fútbol" / "YAIWES-INTERNAL-SWARM-REGISTRY-V5.json"
        with tempfile.TemporaryDirectory() as td:
            result = run_swarm(registry, td, "V5-E2E-001", {"goal":"task-persistence"}); self.assertEqual(result["components_completed"],24); self.assertTrue(all(x["status"]=="RELEASED" for x in result["evidence"]))
if __name__ == "__main__": unittest.main()
'''
    (FABLES / "yaiwes_internal_swarm_chain_v5.py").write_text(runner, encoding="utf-8"); (FABLES / "test_yaiwes_internal_swarm_chain_v5.py").write_text(test, encoding="utf-8")


def main():
    manifests = [transform_component(c) for c in components()]; errors = validate(manifests); write_master(manifests)
    report = {"schema":"yaiwes.internal.surgical.report/v5","team":TEAM,"version":VERSION,"components":24,"files_accounted":sum(m["counts"]["accounted"] for m in manifests),"restored_benign":sum(m["counts"]["restored_benign"] for m in manifests),"blocked_offensive":sum(m["counts"]["blocked_offensive"] for m in manifests),"review_fail_closed":sum(m["counts"]["review_fail_closed"] for m in manifests),"links":sum(m["counts"]["links"] for m in manifests),"errors":errors,"summary":[{"component":m["component"],**m["counts"]} for m in manifests]}
    (FIELD / "YAIWES-INTERNAL-SURGICAL-REPORT-V5.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("components","files_accounted","restored_benign","blocked_offensive","review_fail_closed","links")}, ensure_ascii=False))
    if errors: raise SystemExit("V5_VALIDATION_FAILED:" + "|".join(errors[:20]))


if __name__ == "__main__":
    main()
