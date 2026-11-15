"""Skill → DAG JSON 90% D."""
from __future__ import annotations
import json, re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class DagNode:
    id: str
    title: str
    deterministic: bool = True
    sheriff: list = field(default_factory=lambda: ["budget", "idempotency", "no_secrets"])
    llm: bool = False
    def to_dict(self): return asdict(self)

@dataclass
class SkillCompileResult:
    ok: bool
    skill_id: str
    dag_path: str
    nodes: list = field(default_factory=list)
    error: str = ""
    def to_dict(self): return asdict(self)

class SkillCompiler:
    def compile(self, *, skill_id, steps=None, skill_text="", out_dir="extensions/skills"):
        nodes = []
        if steps:
            for i, step in enumerate(steps):
                if isinstance(step, str):
                    nodes.append(DagNode(f"s{i}", step))
                else:
                    nid = str(step.get("id") or f"s{i}")
                    title = str(step.get("title") or step.get("name") or nid)
                    llm = bool(step.get("llm", False))
                    nodes.append(DagNode(nid, title, not llm, llm=llm))
        elif skill_text:
            for i, ln in enumerate(skill_text.splitlines()):
                ln2 = re.sub(r"^[\-\*\d\.\)\s]+", "", ln.strip())
                if len(ln2) < 2: continue
                llm = any(k in ln2.lower() for k in ("generate", "write code", "llm", "reason"))
                nodes.append(DagNode(f"s{i}", ln2[:120], not llm, llm=llm))
        else:
            return SkillCompileResult(False, skill_id, "", error="no_steps_or_text")
        out = Path(out_dir) / skill_id
        out.mkdir(parents=True, exist_ok=True)
        dag = {"skill_id": skill_id, "ratio_target": "90D_10LLM", "nodes": [n.to_dict() for n in nodes], "edges": [{"from": nodes[i].id, "to": nodes[i+1].id} for i in range(len(nodes)-1)]}
        dag_path = out / "dag.json"
        dag_path.write_text(json.dumps(dag, indent=2), encoding="utf-8")
        (out / "manifest.json").write_text(json.dumps({"id": skill_id, "kind": "skill", "capabilities": [f"skill.{skill_id}.run"]}, indent=2), encoding="utf-8")
        return SkillCompileResult(True, skill_id, str(dag_path), [n.to_dict() for n in nodes])
