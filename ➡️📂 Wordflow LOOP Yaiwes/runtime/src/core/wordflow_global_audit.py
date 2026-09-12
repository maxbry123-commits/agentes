from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Sequence

SCHEMA = "yaiwes.wordflow_global_audit/v1"


class WordflowAuditError(ValueError):
    pass


def _resolved_root(root: Path) -> Path:
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise WordflowAuditError("authorized root must be an existing directory")
    return root


def _safe_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise WordflowAuditError(f"path escapes authorized root: {relative}") from exc
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> list[dict[str, object]]:
    root = _resolved_root(root)
    rows: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if path.is_symlink():
            target = path.resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise WordflowAuditError(f"symlink escapes authorized root: {path}") from exc
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        rows.append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "suffix": path.suffix.lower(),
            }
        )
    return rows


def exact_duplicate_groups(rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    by_hash: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if int(row["bytes"]) == 0:
            continue
        by_hash[str(row["sha256"])].append(str(row["path"]))
    groups = []
    for digest, paths in sorted(by_hash.items()):
        if len(paths) > 1:
            groups.append({"sha256": digest, "paths": sorted(paths), "count": len(paths)})
    return groups


def _module_name(source_root: Path, path: Path) -> str:
    rel = path.relative_to(source_root).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def python_orphan_candidates(root: Path) -> list[str]:
    root = _resolved_root(root)
    source_root = root / "runtime" / "src"
    if not source_root.is_dir():
        return []
    py_files = sorted(source_root.rglob("*.py"), key=lambda p: p.as_posix())
    modules = {_module_name(source_root, path): path for path in py_files}
    inbound: Counter[str] = Counter()
    for path in py_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            candidates: list[str] = []
            if isinstance(node, ast.Import):
                candidates.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                candidates.append(node.module)
            for imported in candidates:
                for module in modules:
                    if imported == module or imported.startswith(module + "."):
                        inbound[module] += 1
    entry_names = {"core.kernel", "agent.agent_router"}
    candidates = []
    for module, path in sorted(modules.items()):
        if not module or path.name == "__init__.py" or module in entry_names:
            continue
        if inbound[module] == 0:
            candidates.append(path.relative_to(root).as_posix())
    return candidates


def required_path_status(root: Path, required_paths: Iterable[str]) -> list[dict[str, object]]:
    root = _resolved_root(root)
    statuses = []
    for relative in sorted(set(required_paths)):
        path = _safe_path(root, relative)
        statuses.append({"path": relative, "exists": path.is_file() or path.is_dir()})
    return statuses


def audit_wordflow(root: Path, *, required_paths: Iterable[str] = ()) -> dict[str, object]:
    root = _resolved_root(root)
    rows = inventory(root)
    required = required_path_status(root, required_paths)
    broken = [item["path"] for item in required if not item["exists"]]
    suffix_counts = Counter(str(row["suffix"]) or "<none>" for row in rows)
    top_level_counts = Counter(str(row["path"]).split("/", 1)[0] for row in rows)
    report: dict[str, object] = {
        "schema": SCHEMA,
        "root": root.name,
        "file_count": len(rows),
        "byte_count": sum(int(row["bytes"]) for row in rows),
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "top_level_file_counts": dict(sorted(top_level_counts.items())),
        "required_paths": required,
        "broken_required_paths": broken,
        "exact_duplicate_groups": exact_duplicate_groups(rows),
        "python_orphan_candidates": python_orphan_candidates(root),
        "policy": {
            "duplicates_are_candidates_not_auto_delete": True,
            "orphans_are_candidates_not_auto_delete": True,
            "broken_required_paths_are_fail_closed": True,
            "mutation_authorized": False,
        },
    }
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    report["report_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report
