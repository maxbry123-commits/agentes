"""Validadores deterministas D1/D3/D4/D6/D8 — 0% LLM
SOURCE: schemas/*.yaml rules condensed
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any

PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
SECRET_RE = re.compile(r"(ghp_|github_pat_|sk-|AKIA)[A-Za-z0-9_\-]{8,}")


def _load(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        import json
        return json.loads(text)
    try:
        import yaml
        data = yaml.safe_load(text) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def validate_manifest(path: Path) -> list[str]:
    errs: list[str] = []
    raw = path.read_text(encoding="utf-8")
    if SECRET_RE.search(raw):
        errs.append("secret pattern in manifest")
    # extract yaml block if md
    data = _load(path) if path.suffix in (".yaml", ".yml") else {}
    if not data and "project_id:" in raw:
        m = re.search(r"project_id:\s*[\"']?([a-z0-9_-]+)", raw)
        if m and not PROJECT_ID_RE.match(m.group(1)):
            errs.append("project_id pattern")
    pid = str(data.get("project_id") or "")
    if pid and not PROJECT_ID_RE.match(pid):
        errs.append("project_id pattern")
    if data and data.get("kind") not in (None, "PROJECT_MANIFEST"):
        errs.append("kind must be PROJECT_MANIFEST")
    return errs


def validate_agent_node(path: Path) -> list[str]:
    data = _load(path)
    errs: list[str] = []
    node = data.get("node") or data.get("agent") or data
    aid = str(node.get("id") or node.get("agent_id") or path.stem)
    if not PROJECT_ID_RE.match(aid) and not re.match(r"^[a-z0-9][a-z0-9_-]*$", aid):
        errs.append(f"bad id {aid}")
    caps = node.get("capabilities") or node.get("caps") or []
    if not caps:
        errs.append("capabilities empty")
    return errs


def validate_dag(path: Path) -> list[str]:
    data = _load(path)
    errs: list[str] = []
    dag = data.get("dag") or data
    nodes = dag.get("nodes") or []
    ids = {n.get("id") for n in nodes if isinstance(n, dict)}
    for n in nodes:
        if not isinstance(n, dict):
            continue
        for dep in n.get("depends_on") or []:
            if dep not in ids:
                errs.append(f"depends_on missing {dep}")
        if not (n.get("required_capabilities") or n.get("capabilities")):
            errs.append(f"node {n.get('id')} without capabilities")
    return errs


def validate_project_dir(root: Path) -> dict[str, Any]:
    report: dict[str, Any] = {"ok": True, "errors": []}
    man = root / "PROJECT_MANIFEST.md"
    if man.is_file():
        e = validate_manifest(man)
        report["errors"].extend([f"manifest:{x}" for x in e])
    nodes = root / "nodes"
    if nodes.is_dir():
        for p in list(nodes.glob("*.yaml")) + list(nodes.glob("*.yml")):
            e = validate_agent_node(p)
            report["errors"].extend([f"{p.name}:{x}" for x in e])
    dag = root / "dag"
    if dag.is_dir():
        for p in list(dag.glob("*.yaml")) + list(dag.glob("*.yml")):
            e = validate_dag(p)
            report["errors"].extend([f"{p.name}:{x}" for x in e])
    report["ok"] = len(report["errors"]) == 0
    return report


if __name__ == "__main__":
    import json
    import sys
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(validate_project_dir(root), indent=2))
    raise SystemExit(0 if validate_project_dir(root)["ok"] else 1)
