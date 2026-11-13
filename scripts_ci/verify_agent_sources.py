import hashlib
import json
import os
import py_compile
import sys
import tempfile

BASE = sys.argv[1]

TARGETS = [
    "agent_zero", "aider", "claude_code", "cline", "codex", "goose",
    "hermes", "meta_agent_cookbook", "meta_muse_code_sdk", "metacua",
    "mirothinker", "muse_glimmer", "openclaw", "opencode", "opendev",
    "openhands", "orca", "qwen_code", "research_agent_lab", "smolagents",
]
EDGE_CASES = ["cua_mcp", "mimo_code", "kimi_k"]

report = {}

debug = {
    "base_dir_arg": BASE,
    "base_dir_exists": os.path.isdir(BASE),
    "base_dir_listing": sorted(os.listdir(BASE)) if os.path.isdir(BASE) else None,
    "cwd": os.getcwd(),
}
report["_debug"] = debug


def sha256_of_tree(path):
    h = hashlib.sha256()
    count = 0
    size = 0
    py_ok = 0
    py_bad = 0
    exts = {}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in sorted(files):
            fp = os.path.join(root, f)
            try:
                st = os.stat(fp)
            except OSError:
                continue
            size += st.st_size
            count += 1
            ext = os.path.splitext(f)[1]
            exts[ext] = exts.get(ext, 0) + 1
            with open(fp, "rb") as fh:
                h.update(fh.read())
            if ext == ".py":
                try:
                    with tempfile.TemporaryDirectory() as td:
                        py_compile.compile(
                            fp, cfile=os.path.join(td, "x.pyc"), doraise=True
                        )
                    py_ok += 1
                except Exception:
                    py_bad += 1
    return {
        "file_count": count,
        "total_bytes": size,
        "sha256_of_all_content": h.hexdigest(),
        "ext_histogram": exts,
        "python_files_compiled_ok": py_ok,
        "python_files_compile_failed": py_bad,
    }


for name in TARGETS + EDGE_CASES:
    category = "target" if name in TARGETS else "edge_case"
    p = os.path.join(BASE, name)
    if not os.path.isdir(p):
        report[name] = {"status": "MISSING_FOLDER", "category": category}
        continue
    stats = sha256_of_tree(p)
    is_real = stats["file_count"] >= 5 and stats["total_bytes"] >= 5000
    stats["status"] = "REAL" if is_real else "SUSPICIOUS_EMPTY_OR_STUB"
    stats["category"] = category
    report[name] = stats

with open("verification_report.json", "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(json.dumps(report, indent=2, ensure_ascii=False))

failures = [
    n
    for n, r in report.items()
    if isinstance(r, dict)
    and r.get("category") == "target"
    and r.get("status") != "REAL"
]
if failures:
    print(f"::error::Targets NOT real: {failures}")
    sys.exit(1)
