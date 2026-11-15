# -*- coding: utf-8 -*-
"""
Updater — actualización incremental de documentos/proyecto
Fuente: PIPELINE 12 FULL §14
A5 — Implementación ejecutable (no stub)

Algoritmo:
  1. Hash documento anterior vs nuevo
  2. Si igual → ignorar
  3. Si diferente:
       a. Identificar dependientes
       b. Pausar solo esos micro-flujos
       c. Re-ejecutar únicamente afectados
       d. Nueva evidencia (hash + timestamp)
       e. Continuar resto sin reinicio
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set


def content_hash(content: Any) -> str:
    raw = json.dumps(content, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


DEPENDENCY_GRAPH: Dict[str, List[str]] = {
    "goal_struct": ["task_list", "PROJECT_PROFILE", "execution_plan"],
    "task_list": ["execution_plan", "TASKS"],
    "PROJECT_PROFILE": ["ARCHITECTURE", "WORKFLOW", "TRACEABILITY"],
    "ARCHITECTURE": ["WORKFLOW", "PIPELINE", "CAPABILITIES"],
    "WORKFLOW": ["PIPELINE"],
    "PIPELINE": ["TRACEABILITY"],
    "CAPABILITIES": ["TRACEABILITY"],
    "TRACEABILITY": ["CHANGELOG"],
    "CHANGELOG": [],
    "execution_plan": ["next_step"],
    "next_step": [],
}


@dataclass
class ArtifactState:
    name: str
    content_hash: str
    content: Any
    updated_at: float
    version: int = 1

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "content_hash": self.content_hash,
            "updated_at": self.updated_at,
            "version": self.version,
        }


@dataclass
class UpdateResult:
    changed: bool
    artifact: str
    old_hash: Optional[str]
    new_hash: str
    impacted: List[str]
    paused: List[str]
    reexecuted: List[str]
    evidence_hash: str
    timestamp: float
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


class IncrementalUpdater:
    def __init__(self, dependency_graph: Optional[Dict[str, List[str]]] = None):
        self.graph = dependency_graph or DEPENDENCY_GRAPH
        self.artifacts: Dict[str, ArtifactState] = {}
        self.history: List[UpdateResult] = []

    def register(self, name: str, content: Any) -> ArtifactState:
        h = content_hash(content)
        art = ArtifactState(
            name=name,
            content_hash=h,
            content=content,
            updated_at=time.time(),
            version=1,
        )
        self.artifacts[name] = art
        return art

    def get_hash(self, name: str) -> Optional[str]:
        art = self.artifacts.get(name)
        return art.content_hash if art else None

    def _collect_dependents(self, name: str) -> List[str]:
        impacted: List[str] = []
        seen: Set[str] = set()
        queue = list(self.graph.get(name, []))
        while queue:
            node = queue.pop(0)
            if node in seen:
                continue
            seen.add(node)
            impacted.append(node)
            queue.extend(self.graph.get(node, []))
        return impacted

    def apply_update(
        self,
        name: str,
        new_content: Any,
        reexecute_fn: Optional[Any] = None,
    ) -> UpdateResult:
        old = self.artifacts.get(name)
        old_hash = old.content_hash if old else None
        new_hash = content_hash(new_content)

        if old_hash is not None and old_hash == new_hash:
            result = UpdateResult(
                changed=False,
                artifact=name,
                old_hash=old_hash,
                new_hash=new_hash,
                impacted=[],
                paused=[],
                reexecuted=[],
                evidence_hash=new_hash,
                timestamp=time.time(),
                notes="hash igual — ignorado",
            )
            self.history.append(result)
            return result

        impacted = self._collect_dependents(name)
        paused = list(impacted)
        reexecuted: List[str] = []

        version = (old.version + 1) if old else 1
        self.artifacts[name] = ArtifactState(
            name=name,
            content_hash=new_hash,
            content=new_content,
            updated_at=time.time(),
            version=version,
        )

        if reexecute_fn is not None:
            for dep in impacted:
                try:
                    dep_content = reexecute_fn(dep, source=name, new_content=new_content)
                    if dep_content is not None:
                        dep_hash = content_hash(dep_content)
                        prev = self.artifacts.get(dep)
                        self.artifacts[dep] = ArtifactState(
                            name=dep,
                            content_hash=dep_hash,
                            content=dep_content,
                            updated_at=time.time(),
                            version=(prev.version + 1) if prev else 1,
                        )
                        reexecuted.append(dep)
                except Exception as e:
                    reexecuted.append(f"{dep}:ERROR:{e}")

        evidence = {
            "artifact": name,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "impacted": impacted,
            "reexecuted": reexecuted,
            "ts": time.time(),
        }
        evidence_hash = content_hash(evidence)

        result = UpdateResult(
            changed=True,
            artifact=name,
            old_hash=old_hash,
            new_hash=new_hash,
            impacted=impacted,
            paused=paused,
            reexecuted=reexecuted,
            evidence_hash=evidence_hash,
            timestamp=time.time(),
            notes=f"v{version} — {len(impacted)} impactados, {len(reexecuted)} re-ejecutados",
        )
        self.history.append(result)
        return result

    def snapshot(self) -> Dict[str, Any]:
        return {
            "artifacts": {k: v.to_dict() for k, v in self.artifacts.items()},
            "history_len": len(self.history),
            "last": self.history[-1].to_dict() if self.history else None,
        }


if __name__ == "__main__":
    up = IncrementalUpdater()
    up.register("goal_struct", {"objective": "Crear login"})
    up.register("task_list", [{"id": "T001", "title": "paso 1"}])
    up.register("PROJECT_PROFILE", {"proposito": "login"})
    print("Initial hashes:")
    for name in ["goal_struct", "task_list", "PROJECT_PROFILE"]:
        print(f"  {name}: {up.get_hash(name)[:20]}...")
    r0 = up.apply_update("goal_struct", {"objective": "Crear login"})
    print("\nSame content → changed:", r0.changed, r0.notes)
    def fake_reexec(dep, source=None, new_content=None):
        return {"regenerated_from": source, "dep": dep}
    r1 = up.apply_update(
        "goal_struct",
        {"objective": "Crear login OAuth2 con Google"},
        reexecute_fn=fake_reexec,
    )
    print("\nChanged content →", r1.to_dict())
    print("\nSnapshot artifacts:", list(up.snapshot()["artifacts"].keys()))
