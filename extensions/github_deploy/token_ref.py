"""T39 — DeployConfig.token_ref only. Never log raw PAT."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DeployConfig:
    token_ref: str
    repository: str = ""
    branch: str = "main"

    def __post_init__(self) -> None:
        ref = str(self.token_ref or "")
        if ref.startswith("ghp_") or ref.startswith("github_pat_"):
            raise ValueError("raw token forbidden; use token_ref")


def redact_logs(text: str) -> str:
    out = str(text)
    for prefix in ("ghp_", "github_pat_"):
        i = 0
        while True:
            j = out.find(prefix, i)
            if j < 0:
                break
            k = j
            while k < len(out) and (out[k].isalnum() or out[k] in "_-"):
                k += 1
            out = out[:j] + "[REDACTED]" + out[k:]
            i = j + len("[REDACTED]")
    return out


if __name__ == "__main__":
    cfg = DeployConfig(token_ref="secret://github/work")
    assert cfg.token_ref == "secret://github/work"
    try:
        DeployConfig(token_ref="ghp_ABC123secret")
        raise SystemExit("expected reject")
    except ValueError:
        pass
    logs = redact_logs("token=ghp_ABC123secret done")
    assert "ghp_" not in logs
    print("ok", cfg.token_ref, logs)
