#!/usr/bin/env python3
# Trigger internal 24-component transform run v3.
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path("📂coda workflow persistencias")
FIELD = ROOT / "🏈 cancha deportiva de fútbol"
MODE = os.environ.get("YAIWES_MODE", "AUDIT").upper()
TEAM = "Swarm agent team Navy seals YAIWES"
EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb", ".sh", ".ps1", ".php", ".lua"}
SKIP = {".git", "node_modules", "vendor", "third_party", "dist", "build", ".venv", "venv", "__pycache__", "target", "_archives", "_yaiwes_upstream_quarantine", "coda_persistence", "yaiwes_internal", "tests", "test", "testing", "docs", "doc", "examples", "example", "fixtures"}
SIDE_EFFECT_MARKERS = (
    "subprocess.", "os.system(", "os.popen(", "socket.", "requests.", "httpx.", "aiohttp.",
    "child_process", "exec.command(", "std::process::command", "runtime.getruntime().exec(",
    "invoke-expression", "start-process"
)


def components():
    xs = sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("🏈 ") and p.name != "🏈 cancha deportiva de fútbol")
    if len(xs) != 24:
        raise SystemExit(f"EXPECTED_24:{len(xs)}")
    return xs


def sources(code: Path):
    for p in code.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in EXTS:
            continue
        if set(p.relative_to(code).parts) & SKIP:
            continue
        if p.stat().st_size <= 1_500_000:
            yield p


def text(p):
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return None


def has_side_effect(s: str) -> bool:
    low = s.lower()
    return any(m in low for m in SIDE_EFFECT_MARKERS)


def safe_python(original: str, rel: str):
    try:
        tree = ast.parse(original)
    except SyntaxError:
        return original, 0
    lines = original.splitlines(keepends=True)
    candidates = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.body:
            continue
        seg = ast.get_source_segment(original, node) or ""
        if not has_side_effect(seg):
            continue
        start = node.body[0].lineno - 1
        end = getattr(node.body[-1], "end_lineno", node.body[-1].lineno) or node.body[-1].lineno
        candidates.append((start, end, node))
    selected = []
    for start, end, node in sorted(candidates, key=lambda x: (x[0], -x[1])):
        if any(parent_start <= start and parent_end >= end for parent_start, parent_end, _ in selected):
            continue
        selected.append((start, end, node))
    edits = []
    for start, end, node in selected:
        indent = lines[start][: len(lines[start]) - len(lines[start].lstrip())]
        body = [
            f"{indent}from pathlib import Path as _YP\n",
            f"{indent}import json as _YJ\n",
            f"{indent}_ye = {{'schema':'yaiwes.internal.persistence/v1','source':{rel!r},'step':{node.name!r},'status':'CHECKPOINTED'}}\n",
            f"{indent}_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')\n",
            f"{indent}with _yp.open('a', encoding='utf-8') as _yf:\n",
            f"{indent}    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\\n')\n",
            f"{indent}return _ye\n",
        ]
        edits.append((start, end, body))
    for start, end, body in sorted(edits, reverse=True):
        lines[start:end] = body
    return "".join(lines), len(edits)


def stub(ext: str, rel: str, original: str):
    if ext == ".py":
        return f"from __future__ import annotations\n\ndef yaiwes_persistence_step(payload=None):\n    return {{'schema':'yaiwes.internal.persistence/v1','source':{rel!r},'payload':dict(payload or {{}}),'status':'CHECKPOINTED'}}\n"
    if ext == ".sh":
        return f"#!/usr/bin/env bash\nset -euo pipefail\necho '{{\"schema\":\"yaiwes.internal.persistence/v1\",\"source\":{json.dumps(rel)},\"status\":\"CHECKPOINTED\"}}' >> \"$(dirname \"$0\")/.yaiwes_internal_state.jsonl\"\n"
    if ext == ".ps1":
        return f"$e = '{{\"schema\":\"yaiwes.internal.persistence/v1\",\"source\":{json.dumps(rel)},\"status\":\"CHECKPOINTED\"}}'\nAdd-Content -Path (Join-Path $PSScriptRoot '.yaiwes_internal_state.jsonl') -Value $e\n"
    if ext in {".js", ".jsx", ".ts", ".tsx"}:
        return f"export function yaiwesPersistenceStep(payload = {{}}) {{ return {{schema:'yaiwes.internal.persistence/v1',source:{json.dumps(rel)},payload,status:'CHECKPOINTED'}}; }}\nexport default yaiwesPersistenceStep;\n"
    if ext == ".rb":
        return f"def yaiwes_persistence_step(payload = {{}})\n  {{schema: 'yaiwes.internal.persistence/v1', source: {rel!r}, payload: payload, status: 'CHECKPOINTED'}}\nend\n"
    if ext == ".lua":
        return f"local M={{}}\nfunction M.yaiwes_persistence_step(payload) return {{schema='yaiwes.internal.persistence/v1',source={json.dumps(rel)},payload=payload or {{}},status='CHECKPOINTED'}} end\nreturn M\n"
    if ext == ".php":
        return f"<?php\nfunction yaiwes_persistence_step($payload = []) {{ return ['schema'=>'yaiwes.internal.persistence/v1','source'=>{json.dumps(rel)},'payload'=>$payload,'status'=>'CHECKPOINTED']; }}\n"
    if ext == ".go":
        m = re.search(r"(?m)^package\s+([A-Za-z_][A-Za-z0-9_]*)", original)
        pkg = m.group(1) if m else "main"
        return f"package {pkg}\n\ntype YAIWESPersistenceEvent struct {{ Source string; Status string }}\nfunc YAIWESPersistenceStep() YAIWESPersistenceEvent {{ return YAIWESPersistenceEvent{{Source:{json.dumps(rel)}, Status:\"CHECKPOINTED\"}} }}\n"
    if ext == ".rs":
        return f"pub fn yaiwes_persistence_step() -> (&'static str, &'static str) {{ ({json.dumps(rel)}, \"CHECKPOINTED\") }}\n"
    if ext == ".java":
        cls = re.sub(r"[^A-Za-z0-9_]", "_", Path(rel).stem)
        return f"class {cls} {{ static String yaiwesPersistenceStep() {{ return \"CHECKPOINTED\"; }} }}\n"
    return original


def transform_component(comp: Path):
    code = comp / "code"
    findings = []
    total = 0
    changed = 0
    for p in sources(code):
        total += 1
        s = text(p)
        if s is None or not has_side_effect(s):
            continue
        rel = p.relative_to(code)
        item = {"path": str(rel), "sha256": hashlib.sha256(s.encode()).hexdigest(), "changed": False}
        if MODE == "TRANSFORM":
            q = code / "_yaiwes_upstream_quarantine" / rel
            q = q.with_name(q.name + ".original")
            q.parent.mkdir(parents=True, exist_ok=True)
            if not q.exists():
                shutil.copy2(p, q)
            ns = s
            if p.suffix.lower() == ".py":
                ns, n = safe_python(s, str(rel))
                if n and not has_side_effect(ns):
                    item["kind"] = f"PY_FUNCTIONS:{n}"
                else:
                    ns = stub(".py", str(rel), s)
                    item["kind"] = f"PY_FILE_STUB_AFTER_FUNCTIONS:{n}"
            else:
                ns = stub(p.suffix.lower(), str(rel), s)
                item["kind"] = "SAFE_STUB"
            if ns != s:
                p.write_text(ns, encoding="utf-8")
                item["changed"] = True
                item["quarantine"] = str(q.relative_to(code))
                changed += 1
        findings.append(item)
    internal = code / "yaiwes_internal"
    internal.mkdir(parents=True, exist_ok=True)
    (internal / "README.md").write_text(f"# {comp.name} internal persistence\n\n## {TEAM}\n\nExternal side-effect surfaces are converted to benign checkpoint steps. Originals are preserved only in `_yaiwes_upstream_quarantine/`.\n", encoding="utf-8")
    report = {"schema":"yaiwes.internal.transform/v1","component":comp.name,"mode":MODE,"source_files":total,"candidates":len(findings),"changed":changed,"findings":findings}
    (comp / "INTERNAL-TRANSFORM-AUDIT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def validate(reports):
    errors=[]
    for r in reports:
        comp=ROOT/r["component"]
        if MODE == "TRANSFORM" and r["candidates"] != r["changed"]:
            errors.append(f"UNTRANSFORMED:{r['component']}:{r['candidates']}:{r['changed']}")
        for f in r["findings"]:
            if not f.get("changed"):
                continue
            p=comp/"code"/f["path"]
            if p.suffix.lower()==".py":
                try: ast.parse(p.read_text(encoding="utf-8"))
                except SyntaxError as e: errors.append(f"PY_SYNTAX:{r['component']}:{f['path']}:{e}")
            q=comp/"code"/f["quarantine"]
            if not q.is_file(): errors.append(f"NO_QUARANTINE:{r['component']}:{f['path']}")
            active = text(p)
            if active is not None and has_side_effect(active):
                errors.append(f"RESIDUAL:{r['component']}:{f['path']}")
    return errors


def main():
    if MODE not in {"AUDIT","TRANSFORM"}: raise SystemExit("BAD_MODE")
    reports=[transform_component(c) for c in components()]
    errors=validate(reports)
    master={"schema":"yaiwes.internal.master/v1","team":TEAM,"mode":MODE,"components":24,"source_files":sum(r['source_files'] for r in reports),"candidates":sum(r['candidates'] for r in reports),"changed":sum(r['changed'] for r in reports),"errors":errors,"summary":[{k:r[k] for k in ('component','source_files','candidates','changed')} for r in reports]}
    FIELD.mkdir(parents=True, exist_ok=True)
    (FIELD/f"YAIWES-INTERNAL-{MODE}-V1.json").write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:master[k] for k in ('mode','components','source_files','candidates','changed')}, ensure_ascii=False))
    if errors: raise SystemExit("VALIDATION_FAILED:"+"|".join(errors[:20]))

if __name__ == '__main__': main()
