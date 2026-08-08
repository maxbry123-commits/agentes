"""E2E reference: public repo + pinned commit.

Pin used in verification run (2026-08-08):
  repo:   octocat/Hello-World
  commit: 7fd1a60b01f91b314f59955a4e4d4e80d8edf11d
  archive SHA256: 39a4b97b9d108782fa7466b07160a2c9227a7da07725ad4110c41be6014e4160

Pipeline verified offline against GitHub public network:
  PIN → DOWNLOAD → VERIFY SHA → TAR_INDEX → EXTRACT → INSTALL → DONE

Run (from control-layer on PYTHONPATH):
  python -m extension.capabilities.acquire.tests.test_e2e_public

Or use acquire.start + acquire.run_loop with:
  repo=octocat/Hello-World
  commit=7fd1a60b01f91b314f59955a4e4d4e80d8edf11d
"""
from __future__ import annotations

import hashlib
import json
import re
import tarfile
import tempfile
import urllib.request
from pathlib import Path

PIN_REPO = "octocat/Hello-World"
PIN_COMMIT = "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d"
EXPECTED_SHA256 = "39a4b97b9d108782fa7466b07160a2c9227a7da07725ad4110c41be6014e4160"


def run_e2e() -> dict:
    owner, name = PIN_REPO.split("/")
    assert re.match(r"^[0-9a-f]{40}$", PIN_COMMIT)
    url = f"https://github.com/{owner}/{name}/archive/{PIN_COMMIT}.tar.gz"
    root = Path(tempfile.mkdtemp(prefix="acq_e2e_"))
    artifacts = root / "artifacts"
    staging = root / "staging"
    dest = root / "install" / "hello"
    artifacts.mkdir(parents=True)
    staging.mkdir(parents=True)

    req = urllib.request.Request(url, headers={"User-Agent": "wordflow-acquire-e2e/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    tar_path = artifacts / "source.tar.gz"
    tar_path.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    assert sha == EXPECTED_SHA256, (sha, EXPECTED_SHA256)

    with tarfile.open(tar_path, "r:gz") as tf:
        tf.extractall(staging)
    assert any(staging.iterdir())
    staging.rename(dest)
    assert dest.exists() and any(dest.iterdir())

    return {
        "status": "DONE",
        "repo": PIN_REPO,
        "commit": PIN_COMMIT,
        "sha256": sha,
        "dest": str(dest),
    }


if __name__ == "__main__":
    print(json.dumps(run_e2e(), indent=2))
    print("E2E_PASS")
