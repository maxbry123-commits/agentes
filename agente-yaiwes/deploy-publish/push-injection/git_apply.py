"""Hook: dest + account + files → apply_and_push. 0% LLM."""
from __future__ import annotations

from typing import Any


def push_if_dest(input_block: dict[str, Any] | None, kwargs: dict[str, Any], phase: dict[str, Any]) -> dict[str, Any]:
    block = input_block if isinstance(input_block, dict) else {}
    dest = kwargs.get("dest") or block.get("dest") or block.get("destination")
    files = kwargs.get("files") or block.get("files")
    account_id = kwargs.get("account_id") or block.get("account_id")
    token_ref = kwargs.get("token_ref") or block.get("token_ref") or block.get("credential_ref")
    if not dest or not files or not account_id:
        return {"ok": False, "skipped": True, "reason": "locate_only", "git_apply": False}
    try:
        from extensions.github_deploy.apply_push import apply_and_push
    except ImportError:
        return {"ok": False, "skipped": False, "reason": "APPLY_PUSH_MISSING", "git_apply": False}
    prefix = kwargs.get("path_prefix") or (dest.get("path_prefix") if isinstance(dest, dict) else None) or phase.get("path")
    if isinstance(dest, dict) and prefix and not dest.get("path_prefix"):
        dest = {**dest, "path_prefix": prefix}
    return apply_and_push(
        dest=dest,
        files=files,
        account_id=str(account_id),
        token_ref=token_ref,
        commit_message=str(kwargs.get("commit_message") or block.get("commit_message") or "wordflow apply"),
        expected_head=kwargs.get("expected_head") or block.get("expected_head"),
        force=bool(kwargs.get("force") or block.get("force")),
        dry_run=kwargs.get("dry_run"),
        evidence_path=kwargs.get("evidence_path"),
        credentials=kwargs.get("credentials"),
        port=kwargs.get("port"),
        registry=kwargs.get("registry"),
    )
