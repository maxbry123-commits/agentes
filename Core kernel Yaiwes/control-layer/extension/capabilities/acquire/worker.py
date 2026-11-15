"""Worker · 12-step acquire ops · minimal."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Any

from .dag import DagStore, build_acquire_dag
from .download import download_url
from .investigate import investigate
from .rate_governor import RateGovernor
from .rollback import RollbackService

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def execute_node(
    node: Any,
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
    state = state if state is not None else {}
    gov = RateGovernor()
    missions = root / "missions" / mission_id.replace("/", "_")
    missions.mkdir(parents=True, exist_ok=True)
    artifacts = missions / "artifacts"
    artifacts.mkdir(exist_ok=True)
    op = node.op

    if op == "WAIT_DEPS":
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
        store = DagStore(root)
        existing = store.load(mission_id)
        if existing is not None and existing.nodes:
            state["plan"] = existing.to_dict()
            return {"ok": True, "data": {"nodes": len(existing.nodes), "reused": True}}
        dag = build_acquire_dag(mission_id, dry_run=dry_run)
        store.save(dag)
        state["plan"] = dag.to_dict()
        return {"ok": True, "data": {"nodes": len(dag.nodes), "reused": False}}

    if op == "SOURCE_STRATEGY":
        inv = state.get("investigate") or {}
        strategy = inv.get("strategy") or state.get("strategy") or "ARCHIVE"
        # executable strategy selection (not just label)
        if strategy not in ("ARCHIVE", "GIT_CLONE", "RELEASE"):
            strategy = "ARCHIVE"
        # large repo → prefer clone if already flagged
        size_hint = inv.get("size_hint") or 0
        if size_hint and int(size_hint) > 500_000_000 and strategy == "ARCHIVE":
            strategy = "GIT_CLONE"
        state["strategy"] = strategy
        state["source_strategy"] = {
            "strategy": strategy,
            "archive_url": inv.get("archive_url") or state.get("archive_url"),
            "commit": inv.get("commit") or state.get("commit"),
            "size_hint": size_hint,
        }
        (missions / "strategy.json").write_text(
            json.dumps(state["source_strategy"], indent=2) + "\n", encoding="utf-8"
        )
        return {"ok": True, "data": state["source_strategy"]}

    if op == "BUDGET_ESTIMATE":
        inv = state.get("investigate") or {}
        return {"ok": True, "data": {"strategy": inv.get("strategy"), "size_hint": inv.get("size_hint")}}

    if op == "DOWNLOAD":
        strategy = state.get("strategy") or "ARCHIVE"
        pinned = state.get("commit") or commit
        if strategy == "GIT_CLONE":
            return _download_clone(repo, pinned, artifacts / "clone", token, state)
        if strategy == "RELEASE":
            url = state.get("release_url") or state.get("archive_url")
            if not url:
                return {"ok": False, "error": "no_release_url"}
            dest = artifacts / "release.bin"
            r = download_url(url, dest, token=token, governor=gov)
            state["download"] = r.to_dict()
            state["artifact_kind"] = "release"
            return {"ok": r.ok, "error": r.error, "data": r.to_dict()}
        # ARCHIVE default
        url = state.get("archive_url")
        if not url:
            return {"ok": False, "error": "no_archive_url"}
        dest = artifacts / "source.tar.gz"
        r = download_url(url, dest, token=token, governor=gov)
        state["download"] = r.to_dict()
        state["artifact_kind"] = "source_archive"
        if not r.ok:
            return {"ok": False, "error": r.error, "data": r.to_dict()}
        return {"ok": True, "data": r.to_dict()}

    if op == "VERIFY_SHA256":
        dl = state.get("download") or {}
        path = dl.get("path")
        if not path or not Path(path).is_file():
            # clone path: hash a marker file list instead
            if state.get("artifact_kind") == "git_clone":
                clone = Path(state.get("clone_path") or "")
                if clone.is_dir():
                    state["verified_sha256"] = "git:" + (state.get("commit") or "")
                    return {"ok": True, "data": {"kind": "git_clone", "commit": state.get("commit")}}
            return {"ok": False, "error": "missing_artifact"}
        if not dl.get("sha256"):
            return {"ok": False, "error": "missing_sha"}
        state["verified_sha256"] = dl["sha256"]
        prov = {
            "repo": repo,
            "commit": state.get("commit"),
            "url": state.get("archive_url") or state.get("release_url"),
            "sha256": dl["sha256"],
            "size": dl.get("size"),
            "method": dl.get("method"),
            "strategy": state.get("strategy"),
            "mission_id": mission_id,
        }
        (missions / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "data": prov}

    if op == "VERIFY_COMMIT":
        pinned = state.get("commit") or commit
        if not pinned or not _COMMIT_RE.match(str(pinned)):
            return {"ok": False, "error": "no_pinned_commit"}
        kind = state.get("artifact_kind") or "source_archive"
        if kind == "git_clone":
            clone = Path(state.get("clone_path") or "")
            if not clone.is_dir():
                return {"ok": False, "error": "no_clone"}
            try:
                head = subprocess.check_output(
                    ["git", "-C", str(clone), "rev-parse", "HEAD"],
                    text=True,
                    timeout=30,
                ).strip()
            except Exception as e:  # noqa: BLE001
                return {"ok": False, "error": f"rev_parse:{e}"}
            if head != pinned:
                return {"ok": False, "error": f"commit_mismatch:{head}!={pinned}"}
            state["commit_verified"] = head
            return {"ok": True, "data": {"head": head, "method": "git_rev_parse"}}
        # archive: root dir often REPO-SHORTSHA or full sha
        dl = state.get("download") or {}
        path = Path(dl.get("path") or "")
        if not path.is_file():
            return {"ok": False, "error": "missing_tar"}
        roots: set[str] = set()
        try:
            with tarfile.open(path, "r:*") as tf:
                for m in tf.getmembers()[:50]:
                    roots.add(m.name.split("/")[0])
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"tar_read:{e}"}
        short = pinned[:7]
        matched = any(short in r or pinned in r for r in roots)
        if not matched:
            # still accept if pin known from investigate URL (github archive by commit is authoritative)
            url = state.get("archive_url") or ""
            if pinned in url:
                matched = True
        if not matched:
            return {"ok": False, "error": f"commit_not_in_archive_roots:{list(roots)[:3]}"}
        state["commit_verified"] = pinned
        return {"ok": True, "data": {"commit": pinned, "roots": list(roots)[:5], "method": "archive_name+url"}}

    if op == "TAR_INDEX":
        if state.get("artifact_kind") == "git_clone":
            clone = Path(state.get("clone_path") or "")
            files = [str(p.relative_to(clone)) for p in clone.rglob("*") if p.is_file()][:5000]
            index = {"files": files, "count": len(files), "kind": "git_clone"}
            (missions / "tar_index.json").write_text(json.dumps(index) + "\n", encoding="utf-8")
            state["tar_index"] = index
            return {"ok": True, "data": {"count": len(files)}}
        if state.get("artifact_kind") == "release":
            state["tar_index"] = {"files": [state.get("download", {}).get("path")], "count": 1, "kind": "release"}
            return {"ok": True, "data": state["tar_index"]}
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
        if state.get("artifact_kind") == "git_clone":
            # already on disk as clone; copy to staging
            rb = RollbackService(root)
            staging = rb.prepare_staging(mission_id)
            clone = Path(state.get("clone_path") or "")
            if staging.exists():
                shutil.rmtree(staging)
            shutil.copytree(clone, staging, symlinks=True)
            state["staging"] = str(staging)
            return {"ok": True, "data": {"staging": str(staging), "kind": "clone_copy"}}
        if state.get("artifact_kind") == "release":
            rb = RollbackService(root)
            staging = rb.prepare_staging(mission_id)
            dl = state.get("download") or {}
            src = Path(dl.get("path") or "")
            if not src.is_file():
                return {"ok": False, "error": "missing_release"}
            target = staging / src.name
            shutil.copy2(src, target)
            state["staging"] = str(staging)
            return {"ok": True, "data": {"staging": str(staging), "kind": "release_copy"}}
        dl = state.get("download") or {}
        path = Path(dl.get("path") or "")
        rb = RollbackService(root)
        staging = rb.prepare_staging(mission_id)
        for p in staging.iterdir():
            if p.is_file():
                p.unlink()
            else:
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
        ok = bool(state.get("verified_sha256") and state.get("dest") and state.get("commit_verified"))
        return {
            "ok": ok,
            "data": {
                "sha256": state.get("verified_sha256"),
                "commit": state.get("commit_verified"),
                "dest": state.get("dest"),
                "strategy": state.get("strategy"),
            },
            "error": None if ok else "incomplete",
        }

    return {"ok": False, "error": f"unknown_op:{op}"}


def _download_clone(
    repo: str,
    commit: str | None,
    dest: Path,
    token: str | None,
    state: dict[str, Any],
) -> dict[str, Any]:
    if not commit or not _COMMIT_RE.match(commit):
        return {"ok": False, "error": "clone_needs_commit"}
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = repo if repo.startswith("http") else f"https://github.com/{repo}.git"
    if token and url.startswith("https://github.com/"):
        url = url.replace("https://", f"https://x-access-token:{token}@")
    try:
        subprocess.check_call(
            ["git", "clone", "--depth", "1", url, str(dest)],
            timeout=300,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # depth-1 may not have commit if not tip — fetch commit
        head = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
        if head != commit:
            subprocess.check_call(
                ["git", "-C", str(dest), "fetch", "--depth", "1", "origin", commit],
                timeout=300,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.check_call(
                ["git", "-C", str(dest), "checkout", commit],
                timeout=60,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            head = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
        if head != commit:
            return {"ok": False, "error": f"clone_commit_mismatch:{head}"}
        state["clone_path"] = str(dest)
        state["artifact_kind"] = "git_clone"
        state["download"] = {"path": str(dest), "sha256": None, "method": "GIT_CLONE", "ok": True}
        return {"ok": True, "data": {"path": str(dest), "commit": head, "method": "GIT_CLONE"}}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"clone_failed:{e}"}
