"""Organizador de despliegue — dry-run y plan.
SOURCE: CAPA DE CONTROL 1 · deploy_config.yaml
No sube nada. Solo clasifica archivos según reglas del proyecto.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import fnmatch
import json


@dataclass
class Plan:
    mapped: list[dict[str, str]] = field(default_factory=list)
    sin_regla: list[str] = field(default_factory=list)
    bloqueados: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mapped": self.mapped,
            "SIN_REGLA": self.sin_regla,
            "BLOQUEADOS": self.bloqueados,
        }


def _load_yaml(path: Path) -> dict:
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def organizar(project_root: str | Path, deploy_config_path: str | Path) -> Plan:
    root = Path(project_root)
    cfg = _load_yaml(Path(deploy_config_path))
    rules = cfg.get("rules", [])
    protected = cfg.get("protected_patterns", [])

    plan = Plan()
    code_root = root / "code"
    if not code_root.exists():
        code_root = root

    for path in code_root.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))

        if any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(path.name, p) for p in protected):
            plan.bloqueados.append(rel)
            continue

        matched = False
        for rule in rules:
            if fnmatch.fnmatch(rel, rule["pattern"]) or fnmatch.fnmatch(str(path.relative_to(code_root)), rule["pattern"]):
                plan.mapped.append({"src": rel, "dest": rule["dest"]})
                matched = True
                break
        if not matched:
            plan.sin_regla.append(rel)

    return plan


def write_plan(plan: Plan, out: str | Path = "plan.json") -> None:
    Path(out).write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
