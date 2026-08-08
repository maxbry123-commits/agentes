"""Register acquire.* capabilities on WordflowExtension ABI · Phase 0.

Handlers are infrastructure-only (no network downloads).
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Mapping

from extension.abi import EvidenceOutput, WordflowExtension

from .checkpoint import CheckpointStore
from .journal import Journal
from .memory_ops import MemoryOpsStore
from .queue import TaskQueue
from .recover import RecoverService
from .registry import MissionRegistry
from .rollback import RollbackService
from .run_loop import RunLoop
from .schema import SCHEMA_VERSION, StopPolicy, stable_hash


def _root_from_ctx(ctx: Mapping[str, Any] | None, params: Mapping[str, Any]) -> Path:
    if params.get("root"):
        return Path(str(params["root"]))
    if ctx and ctx.get("acquire_root"):
        return Path(str(ctx["acquire_root"]))
    if ctx and ctx.get("state_dir"):
        return Path(str(ctx["state_dir"])) / "acquire"
    return Path("./acquire_state")


def register_acquire(ext: WordflowExtension, *,
                     default_root: Path | str | None = None) -> None:
    """Attach acquire.start|status|run_loop|recover|rollback to extension."""

    def _root(params: dict[str, Any]) -> Path:
        if default_root is not None and not params.get("root"):
            return Path(default_root)
        return _root_from_ctx(ext._ctx, params)

    def start_handler(params: dict[str, Any], nivel: str) -> EvidenceOutput:
        root = _root(params)
        queue = TaskQueue(root)
        reg = MissionRegistry(root)
        journal = Journal(root)
        memory = MemoryOpsStore(root)
        cps = CheckpointStore(root)

        mission_id = str(params.get("mission_id") or f"m-{uuid.uuid4().hex[:12]}")
        repo = str(params.get("repo") or "")
        tag = params.get("tag")
        commit = params.get("commit")
        priority = int(params.get("priority") or 100)
        dry_run = bool(params.get("dry_run", False))
        dest_root = params.get("dest") or params.get("dest_root")

        if reg.exists(mission_id):
            return EvidenceOutput(
                ok=False,
                capability="acquire.start",
                evidence_hash="",
                error=f"mission_exists:{mission_id}",
            )

        sp = StopPolicy.from_dict(params.get("stop_policy"))
        # phase 0 defaults: allow a few noop nodes, no downloads
        if "max_nodes" not in (params.get("stop_policy") or {}):
            sp.max_nodes = int(params.get("max_nodes") or 8)

        rec = reg.create(
            mission_id,
            repo=repo,
            tag=tag,
            commit=commit,
            dest_root=str(dest_root) if dest_root else None,
            priority=priority,
            dry_run=dry_run,
            stop_policy=sp,
            meta={"nivel": nivel, "schema_version": SCHEMA_VERSION},
        )
        queue.enqueue(
            mission_id,
            repo=repo,
            tag=tag,
            commit=commit,
            priority=priority,
            dry_run=dry_run,
            status="RUNNABLE",
        )
        cps.init(mission_id, nodes_total=3)
        memory.init(mission_id, next_action="execute" if not dry_run else "investigate")
        journal.append(
            mission_id,
            "start",
            ok=True,
            detail={"repo": repo, "dry_run": dry_run, "priority": priority},
        )
        body = {"mission_id": mission_id, "status": "RUNNABLE", "repo": repo}
        return EvidenceOutput(
            ok=True,
            capability="acquire.start",
            evidence_hash=stable_hash(body),
            data=body,
        )

    def status_handler(params: dict[str, Any], nivel: str) -> EvidenceOutput:
        root = _root(params)
        mission_id = params.get("mission_id")
        queue = TaskQueue(root)
        reg = MissionRegistry(root)
        memory = MemoryOpsStore(root)
        cps = CheckpointStore(root)
        journal = Journal(root)

        if mission_id:
            mid = str(mission_id)
            data = {
                "queue": queue.get(mid).to_dict() if queue.get(mid) else None,
                "task": reg.get(mid).to_dict() if reg.get(mid) else None,
                "memory": memory.get(mid).to_dict() if memory.get(mid) else None,
                "checkpoint": (
                    cps.load_unchecked(mid).to_dict() if cps.load_unchecked(mid) else None
                ),
                "journal_tail": [e.to_dict() for e in journal.tail(mid, 10)],
            }
        else:
            data = {
                "queue": [e.to_dict() for e in queue.list_all()],
            }
        return EvidenceOutput(
            ok=True,
            capability="acquire.status",
            evidence_hash=stable_hash({"n": len(data.get("queue") or [])}),
            data=data,
        )

    def run_loop_handler(params: dict[str, Any], nivel: str) -> EvidenceOutput:
        root = _root(params)
        mission_id = str(params.get("mission_id") or "")
        if not mission_id:
            return EvidenceOutput(
                ok=False,
                capability="acquire.run_loop",
                evidence_hash="",
                error="mission_id_required",
            )
        loop = RunLoop(root)
        result = loop.run(
            mission_id,
            force_lock=bool(params.get("force_lock", False)),
            blocked=bool(params.get("blocked", False)),
            fail_on_node=params.get("fail_on_node"),
        )
        return EvidenceOutput(
            ok=result.status == "DONE",
            capability="acquire.run_loop",
            evidence_hash=stable_hash(result.to_dict()),
            data=result.to_dict(),
            error=None if result.status == "DONE" else result.reason,
        )

    def recover_handler(params: dict[str, Any], nivel: str) -> EvidenceOutput:
        root = _root(params)
        svc = RecoverService(root)
        if params.get("all"):
            results = [r.to_dict() for r in svc.recover_all()]
            body = {"results": results}
        else:
            mission_id = str(params.get("mission_id") or "")
            if not mission_id:
                return EvidenceOutput(
                    ok=False,
                    capability="acquire.recover",
                    evidence_hash="",
                    error="mission_id_required",
                )
            body = svc.recover(
                mission_id, force_clear_lock=bool(params.get("force_clear_lock", False))
            ).to_dict()
        return EvidenceOutput(
            ok=True,
            capability="acquire.recover",
            evidence_hash=stable_hash(body),
            data=body,
        )

    def rollback_handler(params: dict[str, Any], nivel: str) -> EvidenceOutput:
        root = _root(params)
        mission_id = str(params.get("mission_id") or "")
        if not mission_id:
            return EvidenceOutput(
                ok=False,
                capability="acquire.rollback",
                evidence_hash="",
                error="mission_id_required",
            )
        svc = RollbackService(root)
        result = svc.rollback(
            mission_id,
            allow_destructive=bool(params.get("allow_destructive", False)),
            dest_root=params.get("dest_root"),
        )
        return EvidenceOutput(
            ok=result.ok,
            capability="acquire.rollback",
            evidence_hash=stable_hash(result.to_dict()),
            data=result.to_dict(),
            error=None if result.ok else result.action,
        )

    ext.register("acquire.start", start_handler)
    ext.register("acquire.status", status_handler)
    ext.register("acquire.run_loop", run_loop_handler)
    ext.register("acquire.recover", recover_handler)
    ext.register("acquire.rollback", rollback_handler)
