"""W09-W11 tests."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sheriff.domain import Domain, run_domain
from skills.registry import SkillMissingError, SkillRegistry
from source_mirror.manifest import SourceMirror


def test_skill_block_missing():
    r = SkillRegistry()
    r.register({"id": "auth", "name": "auth", "validated": True})
    try:
        r.resolve_required(["auth", "payments"])
        raise AssertionError("expected missing")
    except SkillMissingError as e:
        assert "payments" in e.missing


def test_source_mirror_sha():
    with tempfile.TemporaryDirectory() as td:
        sm = SourceMirror(Path(td) / "idx.jsonl")
        e = sm.register(
            source_id="tencent-mem",
            repo_url="https://github.com/TencentCloud/TencentDB-Agent-Memory.git",
            ref="v2.0.0",
            commit_sha="0aff21a2d9f2b8a0354aaa80a2e586aab4054562",
            category="memory",
        )
        assert e.content_hash.startswith("sha256:")
        assert sm.require_source("tencent-mem").commit_sha.startswith("0aff21a")


def test_domain_github_no_token():
    v = run_domain(Domain.GITHUB, {"agent_has_token": True, "repo_bound": True})
    assert v.allow is False
    assert "agent_must_not_hold_token" in v.reasons


def test_domain_code_from_scratch():
    v = run_domain(Domain.CODE, {"from_scratch": True})
    assert v.allow is False


if __name__ == "__main__":
    test_skill_block_missing()
    test_source_mirror_sha()
    test_domain_github_no_token()
    test_domain_code_from_scratch()
    print("W09-W11 OK")
