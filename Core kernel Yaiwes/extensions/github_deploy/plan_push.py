"""T32 — dry-run push plan. force_push prohibited. No real push."""
from __future__ import annotations


class ForcePushDenied(ValueError):
    pass


def plan_push(
    *,
    owner: str = "owner",
    repo: str = "repo",
    branch: str = "main",
    files: list[str] | None = None,
    force: bool = False,
    message: str = "plan",
) -> dict:
    if force is True:
        raise ForcePushDenied("force_push prohibited")
    return {
        "ok": True,
        "mode": "dry_run",
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "files": list(files or []),
        "force": False,
        "message": message,
        "published": False,
    }


if __name__ == "__main__":
    ok = plan_push(files=["a.py"])
    assert ok["ok"] is True and ok["force"] is False
    try:
        plan_push(force=True)
        raise SystemExit("expected ForcePushDenied")
    except ForcePushDenied:
        pass
    print("ok", ok["mode"], "force_rejected")
