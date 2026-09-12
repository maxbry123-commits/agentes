"""Fail-closed UEK sandbox backed by a real Bubblewrap process.

Caller-supplied dictionaries are never isolation evidence. The only path that
can authorize execution is a successful process started with the required
kernel namespaces and resource limits by :meth:`execute_isolated`.
"""
from __future__ import annotations

import hashlib
import json
import os
import resource
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence


class SandboxManager:
    """Execute argv without a shell in an enforceable Bubblewrap sandbox."""

    BACKEND = "bubblewrap"

    def __init__(
        self,
        network_policy: str = "DENY",
        memory_limit_mb: int = 512,
        timeout_seconds: float = 30.0,
        backend_path: str | None = None,
    ) -> None:
        if network_policy not in {"DENY", "ALLOWLIST"}:
            raise ValueError("INVALID_NETWORK_POLICY")
        if memory_limit_mb < 64:
            raise ValueError("MEMORY_LIMIT_TOO_LOW")
        if not 0 < timeout_seconds <= 300:
            raise ValueError("INVALID_TIMEOUT")
        self.network_policy = network_policy
        self.memory_limit_mb = memory_limit_mb
        self.timeout_seconds = timeout_seconds
        self.backend_path = backend_path if backend_path is not None else shutil.which("bwrap")

    def acquire_sandbox(
        self,
        sandbox_type: str,
        attestation: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Reject descriptors and untrusted external attestations."""
        if not sandbox_type.strip():
            raise ValueError("SANDBOX_TYPE_REQUIRED")
        status = "BLOCKED_UNTRUSTED_ATTESTATION" if attestation is not None else "BLOCKED_EXECUTION_REQUIRED"
        return {
            "sandbox_id": None,
            "type": sandbox_type,
            "backend": self.BACKEND,
            "network_policy": self.network_policy,
            "memory_limit_mb": self.memory_limit_mb,
            "timeout_seconds": self.timeout_seconds,
            "status": status,
            "execution_authorized": False,
        }

    def execute_isolated(self, sandbox_type: str, argv: Sequence[str]) -> Dict[str, Any]:
        """Run an argv only when all requested isolation can be enforced."""
        if not sandbox_type.strip():
            raise ValueError("SANDBOX_TYPE_REQUIRED")
        if not argv or any(not isinstance(arg, str) or "\x00" in arg for arg in argv):
            raise ValueError("VALID_ARGV_REQUIRED")
        if not Path(argv[0]).is_absolute():
            raise ValueError("ABSOLUTE_EXECUTABLE_REQUIRED")
        if self.network_policy != "DENY":
            return self._blocked(sandbox_type, "BLOCKED_ALLOWLIST_BACKEND_UNAVAILABLE")
        if not self.backend_path or not os.path.isfile(self.backend_path):
            return self._blocked(sandbox_type, "BLOCKED_BACKEND_UNAVAILABLE")
        backend = Path(self.backend_path).resolve()
        backend_stat = backend.stat()
        if (
            backend.name != "bwrap"
            or backend_stat.st_uid != 0
            or backend_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        ):
            return self._blocked(sandbox_type, "BLOCKED_UNTRUSTED_BACKEND")

        command = self._bubblewrap_command(tuple(argv))
        memory_bytes = self.memory_limit_mb * 1024 * 1024

        def apply_limits() -> None:
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
                preexec_fn=apply_limits,
            )
        except subprocess.TimeoutExpired as exc:
            return self._blocked(
                sandbox_type,
                "BLOCKED_TIME_LIMIT_EXCEEDED",
                stdout=self._text(exc.stdout),
                stderr=self._text(exc.stderr),
            )
        except OSError as exc:
            return self._blocked(sandbox_type, "BLOCKED_BACKEND_START_FAILED", stderr=str(exc))

        if completed.returncode != 0:
            return self._blocked(
                sandbox_type,
                "BLOCKED_ISOLATION_OR_EXECUTION_FAILED",
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )

        checks = {
            "backend_executed": True,
            "process_namespace": True,
            "filesystem_namespace": True,
            "network_namespace_deny": True,
            "memory_rlimit": True,
            "wall_time_limit": True,
            "shell_disabled": True,
        }
        material = json.dumps(
            {
                "backend": self.BACKEND,
                "argv": list(argv),
                "checks": checks,
                "memory_limit_mb": self.memory_limit_mb,
                "network_policy": self.network_policy,
                "returncode": completed.returncode,
                "stderr": completed.stderr,
                "stdout": completed.stdout,
                "timeout_seconds": self.timeout_seconds,
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
        return {
            "sandbox_id": "sbx_" + digest[:16],
            "type": sandbox_type,
            "backend": self.BACKEND,
            "checks": checks,
            "status": "EXECUTION_VERIFIED",
            "execution_authorized": True,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "evidence_ref": "sha256:" + digest,
        }

    def _bubblewrap_command(self, argv: tuple[str, ...]) -> list[str]:
        command = [
            str(self.backend_path),
            "--die-with-parent", "--new-session", "--unshare-user", "--unshare-pid",
            "--unshare-net", "--unshare-uts", "--unshare-ipc", "--clearenv",
            "--setenv", "PATH", "/usr/bin:/bin",
        ]
        for source in ("/usr", "/bin", "/lib", "/lib64"):
            if os.path.exists(source):
                command.extend(("--ro-bind", source, source))
        command.extend(("--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp"))
        command.extend(("--tmpfs", "/work", "--chdir", "/work", "--"))
        command.extend(argv)
        return command

    def _blocked(self, sandbox_type: str, status: str, **details: Any) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "sandbox_id": None,
            "type": sandbox_type,
            "backend": self.BACKEND,
            "status": status,
            "execution_authorized": False,
        }
        result.update(details)
        return result

    @staticmethod
    def _text(value: str | bytes | None) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value or ""

    def release_sandbox(self, sandbox_id: str, release_evidence_ref: str = "") -> Dict[str, Any]:
        if not sandbox_id.strip() or not release_evidence_ref.strip():
            return {"released": False, "status": "BLOCKED_RELEASE_EVIDENCE_REQUIRED"}
        return {
            "released": True,
            "sandbox_id": sandbox_id,
            "status": "RELEASE_RECORDED",
            "evidence_ref": release_evidence_ref,
        }
