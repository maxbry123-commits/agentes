from __future__ import annotations
import difflib
import fnmatch
import hashlib
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.code_patch import CodePatch


_COPY_IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", "results", "checkpoints", "wandb", "runs"}


def _ignore_dirs(base_dir: str, names: list[str]) -> set[str]:
    return {n for n in names if n in _COPY_IGNORE_DIRS or n.endswith((".pt", ".pth", ".ckpt", ".safetensors"))}


class CodeWriterAgent(Agent):
    name = "code_writer"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        plans = state.values.get("experiment_plans", []) or []
        if not plans:
            return AgentResult(notes=["code_writer: no experiment plans"])

        plan = plans[0] if isinstance(plans[0], dict) else {}
        experiment_id = plan.get("experiment_id", "unknown")
        enable_code_writes = bool(context.settings.get("enable_code_writes"))

        if not enable_code_writes:
            patch = CodePatch(
                experiment_id=experiment_id,
                status="skipped",
                reason="code writes disabled; set --enable-code-writes",
            )
            return self._persist(patch, state, context, experiment_id)

        codebase = state.topic.codebase
        repo_path = codebase.get("repo_path", "")
        run_dir = context.artifact_store.run_dir(state.run_id)
        attempt = int(state.values.get("orchestrator_attempt", 0))

        work_dir, mode = self._setup_work_dir(repo_path, run_dir, experiment_id, attempt, codebase)

        code_tasks = state.values.get("code_tasks", []) or []
        task = next(
            (
                t for t in code_tasks
                if isinstance(t, dict) and t.get("experiment_id") == experiment_id
            ),
            None,
        )
        if task is None:
            patch = CodePatch(
                experiment_id=experiment_id,
                attempt=attempt,
                mode=mode,
                work_dir=str(work_dir),
                status="blocked",
                reason=f"no CodeTask matched experiment_id={experiment_id}",
            )
            return self._persist(patch, state, context, experiment_id)

        task_allowed = task.get("allowed_paths", []) or []
        task_protected = task.get("protected_paths", []) or []

        pending_fixes = state.values.get("pending_fixes_by_experiment_id", {})
        if experiment_id in pending_fixes and pending_fixes[experiment_id]:
            changes = pending_fixes[experiment_id]
        else:
            changes = {}
            for file_path in plan.get("files_to_change", []):
                target = work_dir / file_path
                if target.exists():
                    changes[file_path] = target.read_text(encoding="utf-8")

        if not changes:
            patch = CodePatch(
                experiment_id=experiment_id,
                task_id=task.get("task_id", ""),
                attempt=attempt,
                mode=mode,
                work_dir=str(work_dir),
                status="pending",
                reason="no file changes provided; smoke-only run",
            )
            return self._persist(patch, state, context, experiment_id)

        # ProjectSafetyPolicy business-rule check
        from tools.project_safety import ProjectSafetyPolicy
        policy = ProjectSafetyPolicy.from_topic(state.topic)
        problems = policy.validate_planned_paths(list(changes.keys()))
        if problems:
            patch = CodePatch(
                experiment_id=experiment_id,
                task_id=task.get("task_id", ""),
                attempt=attempt,
                mode=mode,
                work_dir=str(work_dir),
                status="blocked",
                reason="; ".join(problems),
            )
            return self._persist(patch, state, context, experiment_id)

        changed_files, backups, ok, reason = self._apply_changes(changes, work_dir, task_allowed, task_protected)
        if not ok:
            patch = CodePatch(
                experiment_id=experiment_id,
                task_id=task.get("task_id", ""),
                attempt=attempt,
                mode=mode,
                work_dir=str(work_dir),
                status="blocked",
                reason=reason,
            )
            return self._persist(patch, state, context, experiment_id)

        diff_lines = difflib.unified_diff(
            [], [],
            fromfile="", tofile="",
        )
        diff_summary = "\n".join(
            f"{f['relative_path']}: {f['action']}"
            for f in changed_files
        )

        patch = CodePatch(
            experiment_id=experiment_id,
            task_id=task.get("task_id", ""),
            attempt=attempt,
            mode=mode,
            work_dir=str(work_dir),
            changed_files=changed_files,
            backup_paths=backups,
            diff_summary=diff_summary,
            status="applied",
            reason="files changed successfully",
        )
        return self._persist(patch, state, context, experiment_id)

    def _setup_work_dir(self, repo_path: str, run_dir: Path, experiment_id: str, attempt: int, codebase: dict) -> tuple[Path, str]:
        if bool(codebase.get("copy_can_modify")):
            return Path(repo_path), "sandbox"
        dst = run_dir / "code_copies" / experiment_id / f"attempt_{attempt}"
        dst.mkdir(parents=True, exist_ok=True)
        self._copy_codebase(Path(repo_path), dst)
        return dst, "copy"

    def _copy_codebase(self, src: Path, dst: Path) -> None:
        for item in src.iterdir():
            if item.name in _COPY_IGNORE_DIRS:
                continue
            if item.is_dir():
                shutil.copytree(str(item), str(dst / item.name), ignore=_ignore_dirs, dirs_exist_ok=True)
            else:
                dst.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(item), str(dst / item.name))

    def _hash_file(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]

    def _make_backup(self, file_path: Path) -> Path:
        bak = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy2(str(file_path), str(bak))
        return bak

    def _apply_changes(self, changes: dict[str, str], work_dir: Path, allowed_paths: list[str] | None = None, protected_paths: list[str] | None = None) -> tuple[list[dict], dict[str, str], bool, str]:
        changed_files: list[dict] = []
        backups: dict[str, str] = {}

        ok, reason = self._validate_paths(list(changes.keys()), work_dir, allowed_paths, protected_paths)
        if not ok:
            return [], {}, False, reason

        for rel_path, new_content in changes.items():
            target = (work_dir / rel_path).resolve()
            base_hash = ""
            if target.exists():
                base_hash = self._hash_file(target)
                bak = self._make_backup(target)
                backups[rel_path] = str(bak)

            target.parent.mkdir(parents=True, exist_ok=True)
            action = "modify" if base_hash else "create"
            old_content = target.read_text(encoding="utf-8") if target.exists() else ""
            target.write_text(new_content, encoding="utf-8")
            new_hash = self._hash_file(target)

            diff_lines = list(
                difflib.unified_diff(
                    old_content.splitlines(keepends=True) if old_content else [],
                    new_content.splitlines(keepends=True),
                    fromfile=str(rel_path), tofile=str(rel_path),
                )
            )
            changed_files.append({
                "relative_path": rel_path,
                "action": action,
                "diff": "".join(diff_lines),
                "base_file_hash": base_hash,
                "new_file_hash": new_hash,
            })

        return changed_files, backups, True, ""

    def _validate_paths(self, relative_paths: list[str], work_dir: Path, allowed_paths: list[str] | None = None, protected_paths: list[str] | None = None) -> tuple[bool, str]:
        for rel in relative_paths:
            if not rel or rel != rel.strip():
                return False, f"empty or whitespace-padded path: {rel!r}"
            if Path(rel).is_absolute() or rel.startswith("/") or (len(rel) >= 3 and rel[1] == ":"):
                return False, f"absolute or drive-letter path rejected: {rel}"
            if ".." in Path(rel).parts:
                return False, f"parent traversal rejected: {rel}"
            resolved = (work_dir / rel).resolve()
            work_resolved = work_dir.resolve()
            try:
                resolved.relative_to(work_resolved)
            except ValueError:
                return False, f"resolved path {resolved} is outside work_dir {work_resolved}"
            normalized = rel.replace("\\", "/").lstrip("/")
            if allowed_paths:
                if not any(fnmatch.fnmatch(normalized, self._fn_normalize(p)) for p in allowed_paths):
                    return False, f"path {rel} not in allowed_paths"
            if protected_paths:
                if any(fnmatch.fnmatch(normalized, self._fn_normalize(p)) for p in protected_paths):
                    return False, f"protected file: {rel}"
        return True, ""

    @staticmethod
    def _fn_normalize(path: str) -> str:
        p = path.replace("\\", "/")
        if p.endswith("/"):
            p = p.rstrip("/") + "/*"
        return p.lstrip("/")

    def _persist(self, patch: CodePatch, state: ResearchState, context: AgentContext, experiment_id: str) -> AgentResult:
        patch_dict = asdict(patch)
        patches = state.values.setdefault("code_patches_by_experiment_id", {})
        patches[experiment_id] = patch_dict
        state.values["code_patch"] = patch_dict
        context.artifact_store.save_json(state.run_id, "code_patches", patch.patch_id, patch_dict)
        return AgentResult(
            notes=[f"code_writer: status={patch.status} reason={patch.reason}"],
            artifacts={"code_patches": [patch.patch_id]},
            values={
                "code_patch": patch_dict,
                "code_patches_by_experiment_id": patches,
            },
        )
