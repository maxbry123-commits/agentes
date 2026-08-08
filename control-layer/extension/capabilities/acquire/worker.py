"""Worker · executes one DAG node · minimal install path.
"""
from __future__ import annotations

import json
import tarfile
from pathlib import Path
from typing import Any

from .dag import DAG, DagNode, DagStore, build_acquire_dag
from .download import download_url
from .investigate import investigate
from .rate_governor import RateGovernor
from .rollback import RollbackService
from .schema import stable_hash


def execute_node(
    node: DagNode,
    *,
    root: Path,
    mission_id: str,
    repo: str = "",
    tag: str | None = None,
    commit: str | None = None,
    token: str | None = None,
    dest_root: str | None = None,
    dry_run: bool = False,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return {ok, data, error}. Mutates state dict for pipeline."""
    state = state if state is not None else {}
    gov = RateGovernor()
    missions = root / "missions" / mission_id.replace("/", "_")
    missions.mkdir(parents=True, exist_ok=True)
    artifacts = missions / "artifacts"
    artifacts.mkdir(exist_ok=True)

    op = node.op

    if op == "WAIT_DEPS":
        # parent queue must have marked deps DONE — checked externally
        return {"ok": True, "data": {"deps": node.params.get("missions")}}

    if op == "INVESTIGATE":
        r = investigate(repo, tag=tag, commit=commit, token=token, dry_run=dry_run, governor=gov)
        state["investigate"] = r.to_dict()
        if not r.ok:
            return {"ok": False, "error": r.error, "data": r.to_dict()}
        state["commit"] = r.commit
        state["archive_url"] = r.archive_url
        state["strategy"] = r.strategy
        (missions / "investigate.json").write_text(
            json.dumps(r.to_dict(), indent=2) + "\n", encoding="utf-8"
        )
        return {"ok": True, "data": r.to_dict()}

    if op == "PLAN":
        dag = build_acquire_dag(mission_id, dry_run=dry_run)
        # keep already-done investigate/plan if re-entry — store full plan once
        DagStore(root).save(dag)
        state["plan"] = dag.to_dict()
        return {"ok": True, "data": {"nodes": len(dag.nodes)}}

    if op == "BUDGET_ESTIMATE":
        inv = state.get("investigate") or {}
        est = {"strategy": inv.get("strategy"), "size_hint": inv.get("size_hint")}
        return {"ok": True, "data": est}

    if op == "DOWNLOAD":
        url = state.get("archive_url")
        if not url:
            return {"ok": False, "error": "no_archive_url"}
        dest = artifacts / "source.tar.gz"
        r = download_url(url, dest, token=token, governor=gov)
        state["download"] = r.to_dict()
        if not r.ok:
            return {"ok": False, "error": r.error, "data": r.to_dict()}
        return {"ok": True, "data": r.to_dict()}

    if op == "VERIFY_SHA256":
        dl = state.get("download") or {}
        path = dl.get("path")
        if not path or not Path(path).is_file():
            return {"ok": False, "error": "missing_artifact"}
        if not dl.get("sha256"):
            return {"ok": False, "error": "missing_sha"}
        state["verified_sha256"] = dl["sha256"]
        prov = {
            "repo": repo,
            "commit": state.get("commit"),
            "url": state.get("archive_url"),
            "sha256": dl["sha256"],
            "size": dl.get("size"),
            "method": dl.get("method"),
            "mission_id": mission_id,
        }
        (missions / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "data": prov}

    if op == "TAR_INDEX":
        dl = state.get("download") or {}
        path = Path(dl.get("path") or "")
        if not path.is_file():
            return {"ok": False, "error": "missing_tar"}
        names: list[str] = []
        with tarfile.open(path, "r:*") as tf:
            for m in tf.getmembers():
                if m.isfile():
                    names.append(m.name)
        index = {"files": names, "count": len(names)}
        (missions / "tar_index.json").write_text(json.dumps(index) + "\n", encoding="utf-8")
        state["tar_index"] = index
        return {"ok": True, "data": {"count": len(names)}}

    if op == "EXTRACT":
        dl = state.get("download") or {}
        path = Path(dl.get("path") or "")
        rb = RollbackService(root)
        staging = rb.prepare_staging(mission_id)
        # clear prior extract
        for p in staging.iterdir():
            if p.is_file():
                p.unlink()
            else:
                import shutil
                shutil.rmtree(p)
        with tarfile.open(path, "r:*") as tf:
            tf.extractall(staging)
        state["staging"] = str(staging)
        return {"ok": True, "data": {"staging": str(staging)}}

    if op == "INSTALL":
        rb = RollbackService(root)
        dest = Path(dest_root or str(root / "install" / mission_id))
        r = rb.atomic_promote(mission_id, dest, allow_overwrite=bool(state.get("allow_overwrite")))
        if not r.ok:
            return {"ok": False, "error": r.action, "data": r.to_dict()}
        state["dest"] = str(dest)
        return {"ok": True, "data": r.to_dict()}

    if op == "TEST":
        dest = Path(state.get("dest") or dest_root or "")
        ok = dest.exists() and any(dest.iterdir()) if dest.exists() else False
        return {"ok": ok, "error": None if ok else "dest_empty", "data": {"dest": str(dest)}}

    if op == "VERIFY_FINAL":
        ok = bool(state.get("verified_sha256") and state.get("dest"))
        return {"ok": ok, "data": {"sha256": state.get("verified_sha256"), "dest": state.get("dest")}, "error": None if ok else "incomplete"}

    return {"ok": False, "error": f"unknown_op:{op}"}
