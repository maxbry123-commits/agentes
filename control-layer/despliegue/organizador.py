"""Organizador v2 — dry-run · config externa · SIN_REGLA/BLOQUEADOS · 0% LLM
SOURCE: DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2
"""
from __future__ import annotations
import argparse
import fnmatch
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Plan:
    mapped: list[dict[str, str]] = field(default_factory=list)
    repos: dict[str, list[str]] = field(default_factory=dict)
    sin_regla: list[str] = field(default_factory=list)
    bloqueados: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mapped": self.mapped,
            "repos": self.repos,
            "SIN_REGLA": self.sin_regla,
            "BLOQUEADOS": self.bloqueados,
        }


def _load_yaml(path: Path) -> dict:
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _protected(rel: str, name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(name, p) for p in patterns)


def organizar(project_root: str | Path, deploy_config_path: str | Path) -> Plan:
    root = Path(project_root)
    cfg = _load_yaml(Path(deploy_config_path))
    protected = list(cfg.get("protected_patterns") or [])
    strict = bool(cfg.get("strict_unmatched", True))
    default_repo = str(cfg.get("default_repo") or "default")
    plan = Plan()

    # Formato v2: repos: {name: [patterns]}
    repos_map = cfg.get("repos")
    # Formato v1: rules: [{pattern, dest}]
    rules = cfg.get("rules") or []

    code_root = root / "code" if (root / "code").exists() else root

    for path in code_root.rglob("*"):
        if not path.is_file():
            continue
        if any(x in path.parts for x in (".git", "repos_listos", "loop_data", "__pycache__")):
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if _protected(rel, path.name, protected):
            plan.bloqueados.append(rel)
            continue

        matched = False
        if repos_map:
            for repo, patterns in repos_map.items():
                for pat in patterns:
                    if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(path.name, pat):
                        plan.mapped.append({"src": rel, "dest": repo})
                        plan.repos.setdefault(repo, []).append(rel)
                        matched = True
                        break
                if matched:
                    break
        else:
            for rule in rules:
                pat = rule.get("pattern", "")
                if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(str(path.relative_to(code_root)), pat):
                    dest = rule.get("dest", default_repo)
                    plan.mapped.append({"src": rel, "dest": dest})
                    plan.repos.setdefault(dest, []).append(rel)
                    matched = True
                    break

        if not matched:
            if strict:
                plan.sin_regla.append(rel)
            else:
                plan.mapped.append({"src": rel, "dest": default_repo})
                plan.repos.setdefault(default_repo, []).append(rel)

    return plan


def write_plan(plan: Plan, out: str | Path = "plan.json") -> None:
    Path(out).write_text(json.dumps(plan.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".", type=Path)
    ap.add_argument("--config", type=Path, default=Path("config/deploy_config.yaml"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("plan.json"))
    args = ap.parse_args()
    cfg = args.config
    if not cfg.is_file():
        alt = Path(__file__).resolve().parent.parent / "templates/despliegue/deploy_config.yaml"
        cfg = alt if alt.is_file() else cfg
    plan = organizar(args.root.resolve(), cfg)
    write_plan(plan, args.out)
    print(f"wrote {args.out} mapped={len(plan.mapped)} sin_regla={len(plan.sin_regla)} bloqueados={len(plan.bloqueados)}")
    if plan.bloqueados:
        return 2
    if plan.sin_regla:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
