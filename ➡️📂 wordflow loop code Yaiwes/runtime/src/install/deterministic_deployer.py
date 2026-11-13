"""Deterministic filesystem deployer with verified hash, health/smoke checks and rollback.

G-017 runtime primitive. It never trusts caller PASS flags: the candidate tree is
hashed locally, copied into a content-addressed release, promoted atomically via
`current`, and executable health/smoke commands are run with shell=False. Any
post-promotion failure rolls back to the previous verified release when present.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
from typing import Sequence


@dataclass(frozen=True)
class DeployResult:
    status: str
    candidate_sha256: str
    previous_release: str | None
    current_release: str | None
    health_ok: bool
    smoke_ok: bool
    rollback_performed: bool
    rollback_health_ok: bool
    evidence: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def tree_sha256(root: Path) -> str:
    if not root.is_dir():
        raise ValueError("CANDIDATE_DIR_REQUIRED")
    digest = hashlib.sha256()
    files = 0
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(rel + b"\0" + hashlib.sha256(payload).hexdigest().encode("ascii") + b"\0" + str(len(payload)).encode("ascii") + b"\n")
        files += 1
    if files == 0:
        raise ValueError("EMPTY_CANDIDATE")
    return digest.hexdigest()


class DeterministicDeployer:
    def __init__(self, deploy_root: Path, timeout_seconds: float = 10.0) -> None:
        if not 0 < timeout_seconds <= 120:
            raise ValueError("INVALID_TIMEOUT")
        self.root = deploy_root.resolve()
        self.releases = self.root / "releases"
        self.current = self.root / "current"
        self.timeout_seconds = timeout_seconds
        self.releases.mkdir(parents=True, exist_ok=True)

    def _current_target(self) -> Path | None:
        if not self.current.is_symlink():
            return None
        target = (self.current.parent / os.readlink(self.current)).resolve()
        try:
            target.relative_to(self.releases.resolve())
        except ValueError as exc:
            raise RuntimeError("CURRENT_TARGET_OUTSIDE_RELEASES") from exc
        return target

    def _atomic_point_current(self, release: Path) -> None:
        relative = release.relative_to(self.root)
        tmp = self.root / ".current.next"
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        os.symlink(relative.as_posix(), tmp)
        os.replace(tmp, self.current)

    def _run(self, release: Path, argv: Sequence[str]) -> bool:
        if not argv or any(not isinstance(x, str) or "\x00" in x for x in argv):
            raise ValueError("VALID_ARGV_REQUIRED")
        completed = subprocess.run(
            list(argv),
            cwd=release,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.timeout_seconds,
            shell=False,
            check=False,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
        )
        return completed.returncode == 0

    def deploy(
        self,
        candidate_dir: Path,
        *,
        expected_sha256: str,
        health_argv: Sequence[str],
        smoke_argv: Sequence[str],
        rollback_health_argv: Sequence[str] | None = None,
    ) -> DeployResult:
        candidate = candidate_dir.resolve()
        actual = tree_sha256(candidate)
        if actual != expected_sha256:
            return DeployResult(
                status="BLOCKED_HASH_MISMATCH",
                candidate_sha256=actual,
                previous_release=str(self._current_target()) if self._current_target() else None,
                current_release=str(self._current_target()) if self._current_target() else None,
                health_ok=False,
                smoke_ok=False,
                rollback_performed=False,
                rollback_health_ok=False,
                evidence=("candidate_hash_mismatch",),
            )

        previous = self._current_target()
        release = self.releases / actual
        if not release.exists():
            staging = self.releases / (actual + ".staging")
            shutil.rmtree(staging, ignore_errors=True)
            shutil.copytree(candidate, staging)
            copied_hash = tree_sha256(staging)
            if copied_hash != actual:
                shutil.rmtree(staging, ignore_errors=True)
                raise RuntimeError("STAGED_TREE_HASH_MISMATCH")
            os.replace(staging, release)

        self._atomic_point_current(release)
        readback = self._current_target()
        if readback != release.resolve() or tree_sha256(readback) != actual:
            raise RuntimeError("PROMOTION_READBACK_MISMATCH")

        health_ok = self._run(readback, health_argv)
        smoke_ok = self._run(readback, smoke_argv) if health_ok else False
        if health_ok and smoke_ok:
            return DeployResult(
                status="DEPLOYED_VERIFIED",
                candidate_sha256=actual,
                previous_release=str(previous) if previous else None,
                current_release=str(readback),
                health_ok=True,
                smoke_ok=True,
                rollback_performed=False,
                rollback_health_ok=False,
                evidence=("hash_verified", "atomic_promote", "health_pass", "smoke_pass", "readback_pass"),
            )

        rollback_performed = False
        rollback_health_ok = False
        if previous is not None and previous.exists():
            self._atomic_point_current(previous)
            rollback_performed = self._current_target() == previous.resolve()
            probe = rollback_health_argv if rollback_health_argv is not None else health_argv
            rollback_health_ok = rollback_performed and self._run(previous, probe)

        return DeployResult(
            status="ROLLBACK_VERIFIED" if rollback_performed and rollback_health_ok else "DEPLOYMENT_FAILED",
            candidate_sha256=actual,
            previous_release=str(previous) if previous else None,
            current_release=str(self._current_target()) if self._current_target() else None,
            health_ok=health_ok,
            smoke_ok=smoke_ok,
            rollback_performed=rollback_performed,
            rollback_health_ok=rollback_health_ok,
            evidence=("hash_verified", "atomic_promote", "post_promote_failure", "rollback_attempted"),
        )
