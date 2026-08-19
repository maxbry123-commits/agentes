"""Deterministic apply → commit → push. 0% LLM.

The agent only supplies dest + account_id + token_ref + files.
Wordflow decides nothing: rules in this module + deploy_config.yaml.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from extensions.github_deploy.accounts_load import load_accounts, register_ephemeral
from extensions.github_deploy.credential_env import CredentialUnresolved, EnvCredentialStore, redact, resolve_token
from extensions.github_deploy.git_data_port import FileChange, build_git_data_port
from extensions.github_deploy.hf_port import build_hf_port
from extensions.github_deploy.plan_push import ForcePushDenied, plan_push
from extensions.github_deploy.protected import check_protected
from extensions.github_deploy.token_ref import DeployConfig
from extensions.wordflow.accounts.resolver import AccountResolver, WorkspaceRepo


def _parse_dest(dest: dict[str, Any] | str | None) -> dict[str, str]:
    if dest is None:
        raise ValueError("DEST_MISSING")
    if isinstance(dest, str):
        left, _, path = dest.partition(":")
        repo_part, _, branch = left.partition("@")
        owner, _, repo = repo_part.partition("/")
        if not owner or not repo:
            raise ValueError("DEST_BAD")
        return {
            "provider": "github",
            "owner": owner,
            "repo": repo,
            "branch": branch or "main",
            "path_prefix": path,
        }
    provider = str(dest.get("provider") or "github").strip().lower()
    owner = str(dest.get("owner") or "").strip()
    repo = str(dest.get("repo") or "").strip()
    if not owner or not repo:
        raise ValueError("DEST_BAD")
    return {
        "provider": provider,
        "owner": owner,
        "repo": repo,
        "branch": str(dest.get("branch") or "main"),
        "path_prefix": str(dest.get("path_prefix") or dest.get("path") or ""),
    }


def _rel_path(path_prefix: str, file_path: str) -> str:
    p = str(file_path).lstrip("/")
    prefix = str(path_prefix or "").strip("/")
    if prefix and not p.startswith(prefix + "/") and p != prefix:
        return f"{prefix}/{p}"
    return p


def _write_evidence(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(payload), indent=2) + "\n", encoding="utf-8")


def apply_and_push(
    *,
    dest: dict[str, Any] | str | None,
    files: list[dict[str, Any]] | None,
    account_id: str | None,
    token_ref: str | None = None,
    commit_message: str = "wordflow apply",
    expected_head: str | None = None,
    force: bool = False,
    dry_run: bool | None = None,
    registry: Any = None,
    credentials: Any = None,
    port: Any = None,
    evidence_path: str | Path | None = None,
) -> dict[str, Any]:
    """Apply file changes and update git ref. Never force. Never log tokens."""
    out: dict[str, Any] = {
        "ok": False,
        "llm_control": "DENY",
        "published": False,
        "git_apply": False,
        "contract": "APPLY_PUSH",
    }
    try:
        parsed = _parse_dest(dest)
    except ValueError as exc:
        out["reason"] = str(exc)
        return out

    if force:
        try:
            plan_push(force=True)
        except ForcePushDenied:
            out["reason"] = "FORCE_PUSH_DENIED"
            return out

    file_rows = list(files or [])
    if not file_rows:
        out["reason"] = "FILES_MISSING"
        return out

    rels = [_rel_path(parsed["path_prefix"], str(f.get("path") or f.get("destination") or "")) for f in file_rows]
    if any(not r for r in rels):
        out["reason"] = "FILE_PATH_MISSING"
        return out
    hold = check_protected(rels)
    if not hold.get("ok"):
        out.update(hold)
        out["reason"] = "PROTECTED_PATH"
        return out

    if not account_id:
        out["reason"] = "ACCOUNT_REQUIRED"
        return out

    if registry is None:
        registry = load_accounts()
    if token_ref:
        register_ephemeral(
            registry,
            account_id=account_id,
            provider=parsed["provider"],
            credential_ref=token_ref,
            allowed_repositories=(),
            can_deploy=True,
        )

    resolved = AccountResolver(registry).resolve(
        WorkspaceRepo(
            workspace_id="apply_push",
            provider=parsed["provider"],
            owner=parsed["owner"],
            repo=parsed["repo"],
            account_id=account_id,
            branch=parsed["branch"],
        ),
        need_write=True,
        need_deploy=not bool(token_ref),
    )
    if resolved.decision != "ALLOW":
        out["reason"] = resolved.reason
        out["detail"] = resolved.detail
        return out

    ref = token_ref or resolved.credential_ref
    try:
        DeployConfig(token_ref=str(ref), repository=f"{parsed['owner']}/{parsed['repo']}", branch=parsed["branch"])
    except ValueError:
        out["reason"] = "RAW_TOKEN_FORBIDDEN"
        return out

    store = credentials or EnvCredentialStore()
    try:
        token = store.resolve(str(ref)) if hasattr(store, "resolve") else None
        if not token:
            token = resolve_token(str(ref))
    except CredentialUnresolved as exc:
        out["reason"] = "TOKEN_REF_UNRESOLVED"
        out["token_ref"] = str(ref)
        out["detail"] = str(exc)
        return out

    plan = plan_push(
        owner=parsed["owner"],
        repo=parsed["repo"],
        branch=parsed["branch"],
        files=rels,
        force=False,
        message=commit_message,
    )

    if parsed["provider"] == "huggingface":
        hf = port or build_hf_port(dry_run)
        result = hf.deploy(
            parsed["owner"],
            parsed["repo"],
            parsed["branch"],
            [{"path": p, "content": file_rows[i].get("content") or ""} for i, p in enumerate(rels)],
            commit_message,
            token,
        )
    else:
        git_port = port or build_git_data_port(dry_run)
        changes = []
        for i, rel in enumerate(rels):
            raw = file_rows[i].get("content")
            if raw is None:
                src = file_rows[i].get("source")
                if src and Path(str(src)).is_file():
                    data = Path(str(src)).read_bytes()
                else:
                    out["reason"] = "FILE_CONTENT_MISSING"
                    out["path"] = rel
                    return out
            elif isinstance(raw, bytes):
                data = raw
            else:
                data = str(raw).encode("utf-8")
            changes.append(FileChange(path=rel, content=data))
        deployed = git_port.deploy(
            parsed["owner"],
            parsed["repo"],
            parsed["branch"],
            changes,
            commit_message,
            expected_head=expected_head,
        )
        status = getattr(deployed, "status", None) or (deployed.get("status") if isinstance(deployed, dict) else None)
        commit_sha = getattr(deployed, "commit_sha", None) if not isinstance(deployed, dict) else deployed.get("commit_sha")
        if status == "CONFLICT":
            result = {
                "ok": False,
                "status": "CONFLICT",
                "reason": "HEAD_CONFLICT",
                "detail": getattr(deployed, "detail", {}),
            }
        elif status in ("OK", "DRY_RUN"):
            result = {
                "ok": True,
                "status": status,
                "published": status == "OK",
                "commit_sha": commit_sha,
                "repository": f"{parsed['owner']}/{parsed['repo']}",
                "branch": parsed["branch"],
                "files": rels,
                "provider": "github",
            }
        else:
            result = {
                "ok": False,
                "status": status or "ERROR",
                "reason": getattr(deployed, "message", None) or "DEPLOY_FAILED",
            }

    out.update(result)
    out["llm_control"] = "DENY"
    out["plan"] = {k: plan[k] for k in ("owner", "repo", "branch", "files", "force", "message") if k in plan}
    out["account_id"] = account_id
    out["token_ref"] = str(ref)
    out["git_apply"] = bool(out.get("ok"))
    evidence = {
        "ok": out.get("ok"),
        "status": out.get("status"),
        "published": out.get("published"),
        "repository": f"{parsed['owner']}/{parsed['repo']}",
        "branch": parsed["branch"],
        "provider": parsed["provider"],
        "account_id": account_id,
        "files": rels,
        "commit_sha": out.get("commit_sha"),
        "git_apply": out.get("git_apply"),
        "llm_control": "DENY",
    }
    dest_ev = Path(evidence_path) if evidence_path else Path.cwd() / "evidence.json"
    _write_evidence(dest_ev, evidence)
    out["evidence_path"] = str(dest_ev)
    out["evidence"] = evidence
    return redact(out)


def apply_from_payload(payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return apply_and_push(
        dest=payload.get("dest") or payload.get("destination"),
        files=payload.get("files"),
        account_id=payload.get("account_id"),
        token_ref=payload.get("token_ref") or payload.get("credential_ref"),
        commit_message=str(payload.get("commit_message") or "wordflow apply"),
        expected_head=payload.get("expected_head"),
        force=bool(payload.get("force")),
        **kwargs,
    )


if __name__ == "__main__":
    import sys

    raw = sys.stdin.read() if not sys.argv[1:] else Path(sys.argv[1]).read_text(encoding="utf-8")
    payload = json.loads(raw or "{}")
    print(json.dumps(apply_from_payload(payload), indent=2))
