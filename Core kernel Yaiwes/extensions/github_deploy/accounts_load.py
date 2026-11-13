"""Load AccountRegistry from YAML. 0% LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from extensions.wordflow.accounts.registry import AccountRecord, AccountRegistry

DEFAULT_YAML = Path(__file__).resolve().parents[1] / "wordflow" / "connectors" / "external_accounts.yaml"


def _policy(raw: dict[str, Any] | None) -> dict[str, Any]:
    base = {"can_read": True, "can_write": True, "can_deploy": False}
    if isinstance(raw, dict):
        base.update({k: bool(raw[k]) for k in ("can_read", "can_write", "can_deploy") if k in raw})
    return base


def load_accounts(path: str | Path | None = None) -> AccountRegistry:
    registry = AccountRegistry()
    p = Path(path) if path else DEFAULT_YAML
    if not p.is_file():
        return registry
    try:
        import yaml  # type: ignore
    except ImportError:
        return registry
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    rows = data.get("accounts") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return registry
    for row in rows:
        if not isinstance(row, dict):
            continue
        allowed = tuple(str(x) for x in (row.get("allowed_repositories") or []))
        registry.register(
            AccountRecord(
                account_id=str(row["account_id"]),
                provider=str(row.get("provider") or "github"),
                credential_ref=str(row["credential_ref"]),
                allowed_repositories=allowed,
                default_branch=str(row.get("branch") or "main"),
                policy=_policy(row.get("policy")),
                metadata={
                    "owner": row.get("owner"),
                    "repo": row.get("repo"),
                    "role": row.get("role"),
                },
            )
        )
    return registry


def register_ephemeral(
    registry: AccountRegistry,
    *,
    account_id: str,
    provider: str,
    credential_ref: str,
    allowed_repositories: tuple[str, ...] = (),
    can_deploy: bool = True,
) -> None:
    if registry.get(account_id) is not None:
        return
    registry.register(
        AccountRecord(
            account_id=account_id,
            provider=provider,
            credential_ref=credential_ref,
            allowed_repositories=allowed_repositories,
            policy={"can_read": True, "can_write": True, "can_deploy": can_deploy},
        )
    )
