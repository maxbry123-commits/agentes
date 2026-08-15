# -*- coding: utf-8 -*-
"""C-26 Policy Engine seed — every node consults. 0% LLM. fail_closed."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

DEFAULT_POLICY: dict[str, Any] = {
    "version": "1.0",
    "fail_closed": True,
    "llm_control": "DENY",
    "security": {
        "can_write_kernel": False,
        "can_write_github": False,
        "token_in_logs": False,
    },
    "license": {
        "allowed": ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"],
        "require_gate": True,
    },
    "deploy": {
        "force_push": False,
        "require_expected_head": True,
        "dry_run_first": True,
        "protected_patterns": [".github/workflows/**", "**/secrets/**"],
    },
    "credentials": {
        "mode": "token_ref_only",
        "never_literal": True,
        "providers": ["env", "github", "vault"],
    },
    "limits": {"max_parallel": 4, "timeout_ms": 30000, "max_repair": 2},
}


class PolicyError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def load_policy(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).resolve().parents[1] / "policies" / "policy_seed.yaml"
    p = Path(path)
    if not p.is_file():
        return dict(DEFAULT_POLICY)
    text = p.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text) or {}
    else:
        data = dict(DEFAULT_POLICY)
    if not isinstance(data, dict):
        raise PolicyError("POLICY_NOT_OBJECT")
    merged = dict(DEFAULT_POLICY)
    for k, v in data.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v
    return merged


def check_action(policy: dict[str, Any], action: str, **ctx: Any) -> dict[str, Any]:
    """Return {allowed, reason_codes}. fail_closed on unknown action."""
    reasons: list[str] = []
    sec = policy.get("security") or {}
    lic = policy.get("license") or {}
    dep = policy.get("deploy") or {}
    cred = policy.get("credentials") or {}
    action = (action or "").lower()

    if action in ("write_kernel", "mutate_kernel"):
        if not sec.get("can_write_kernel", False):
            reasons.append("DENY_WRITE_KERNEL")
    elif action in ("write_github", "push", "deploy"):
        if not sec.get("can_write_github", False):
            reasons.append("DENY_WRITE_GITHUB_UNTIL_AUTHORIZED")
        if action == "deploy" and dep.get("force_push") is False and ctx.get("force_push"):
            reasons.append("DENY_FORCE_PUSH")
        if dep.get("require_expected_head") and not ctx.get("expected_head"):
            reasons.append("MISSING_EXPECTED_HEAD")
    elif action == "use_license":
        name = ctx.get("license")
        allowed = set(lic.get("allowed") or [])
        if name and allowed and name not in allowed:
            reasons.append(f"LICENSE_NOT_ALLOWED:{name}")
    elif action == "use_credential":
        if cred.get("never_literal") and ctx.get("literal_token"):
            reasons.append("DENY_LITERAL_TOKEN")
        providers = set(cred.get("providers") or [])
        prov = ctx.get("provider")
        if prov and providers and prov not in providers:
            reasons.append(f"PROVIDER_NOT_ALLOWED:{prov}")
    elif action == "log":
        if sec.get("token_in_logs") is False and ctx.get("contains_token"):
            reasons.append("DENY_TOKEN_IN_LOGS")
    else:
        if policy.get("fail_closed", True):
            reasons.append(f"UNKNOWN_ACTION:{action}")

    return {
        "allowed": len(reasons) == 0,
        "reason_codes": reasons,
        "action": action,
        "fail_closed": bool(policy.get("fail_closed", True)),
        "llm_control": "DENY",
    }


def require_allowed(policy: dict[str, Any], action: str, **ctx: Any) -> dict[str, Any]:
    result = check_action(policy, action, **ctx)
    if not result["allowed"] and policy.get("fail_closed", True):
        raise PolicyError("POLICY_DENIED", ",".join(result["reason_codes"]))
    return result
