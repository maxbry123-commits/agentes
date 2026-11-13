"""Verifier identity — honest digests of the verifier that actually ran.

This module RECORDS; it does not prove. A digest states what this process
observed about a command it was handed and is about to execute. A worker that
lies about *who* verified, or that rewrites the record afterwards, is not caught
here — see reference/safety-and-approvals.md §5 and reference/repo-os-contract.md §17.
"""

from __future__ import annotations

import hashlib
import os
import shlex
import stat
from pathlib import Path
from typing import Any, Mapping

from .chain import canonical_json

CODE_DIGEST_BASES = (
    "workspace_file", "path_lookup", "outside_workspace", "not_a_file",
    "unresolvable", "unreadable", "unparseable_command", "empty_command",
    "injected_verifier",
)
POLICY_FIELDS = ("criterion_ref", "depends_on", "id", "verify")

_CHUNK = 64 * 1024


def _digest_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            while chunk := handle.read(_CHUNK):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def verifier_code_digest(command: str | None, workspace: str | Path) -> tuple[str | None, str]:
    """Digest argv[0] only when it is a readable regular file inside the workspace.

    Returns ``(digest_or_None, basis)``. ``basis`` is always one of
    ``CODE_DIGEST_BASES`` and always explains a null digest truthfully — a null is
    the right answer for ``python3 -m pytest``, and ``unresolvable`` (not
    ``not_a_file``) is the right answer when resolution itself failed.
    Never raises.
    """
    if not isinstance(command, str) or not command.strip():
        return None, "empty_command"
    try:
        argv = shlex.split(command, posix=True)
    except ValueError:
        return None, "unparseable_command"
    if not argv:
        return None, "empty_command"
    argv0 = argv[0]
    if "/" not in argv0 and os.sep not in argv0:
        # No separator: the OS resolves this through PATH. A same-named file in
        # the workspace is NOT what ran, so hashing it would be a fabrication.
        return None, "path_lookup"
    try:
        root = Path(workspace).resolve()
        candidate = Path(argv0)
        resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
        # stat(), not Path.is_file(): pathlib ignores ENOENT/ENOTDIR/EBADF/ELOOP
        # alike, so on 3.13 — where resolve() returns a symlink loop unresolved
        # rather than raising — is_file() would report that undeterminable case as
        # the confident "not_a_file". The errno keeps the two apart.
        is_file = stat.S_ISREG(os.stat(resolved).st_mode)
    except (FileNotFoundError, NotADirectoryError, ValueError):
        # ValueError is an embedded NUL in argv0, raised by resolve() itself on
        # every supported version: no such path can exist, so this is definite.
        return None, "not_a_file"
    except (OSError, RuntimeError):
        # RuntimeError is pathlib's symlink-loop signal, raised by resolve() on
        # <=3.12; 3.13 surfaces the same ELOOP as an OSError from stat(). Both are
        # "this process could not complete the resolution".
        return None, "unresolvable"
    if not is_file:
        return None, "not_a_file"
    try:
        resolved.relative_to(root)
    except ValueError:
        return None, "outside_workspace"
    digest = _digest_file(resolved)
    return (digest, "workspace_file") if digest is not None else (None, "unreadable")


def executed_verifier_identity(command: str | None, workspace: str | Path) -> dict[str, Any]:
    """Identity of a DECLARED command this process is about to execute.

    Call this BEFORE running the verifier: the digest must describe the bytes that
    ran, and a verify script that rewrites itself would otherwise be recorded by
    its post-run bytes.
    """
    digest, basis = verifier_code_digest(command, workspace)
    return {"command": command, "code_digest": digest,
            "code_digest_basis": basis, "source": "declared_command"}


def injected_verifier_identity() -> dict[str, Any]:
    """Identity when the caller injected a verifier callable.

    The task's declared ``verify`` command did NOT run, so recording it — or a
    digest of it — would be a fabrication. Everything the process does not know
    is null, and the basis says why.
    """
    return {"command": None, "code_digest": None,
            "code_digest_basis": "injected_verifier", "source": "injected_callable"}


def verification_policy(task: Mapping[str, Any]) -> dict[str, Any]:
    """The declared goalpost subset of a TASKS.json entry (run state excluded)."""
    return {field: task.get(field) for field in POLICY_FIELDS}


def verification_policy_digest(task: Mapping[str, Any]) -> str:
    """sha256 over the canonical JSON of the declared goalpost.

    Reuses loop.chain.canonical_json — one canonicalizer for writer and verifier
    (repo-os-contract.md §16). Raises ChainHashError for a task entry that is not
    canonicalizable (e.g. a NaN that survived json.loads); callers convert that to
    their own typed error rather than letting it escape.
    """
    return hashlib.sha256(canonical_json(verification_policy(task)).encode("utf-8")).hexdigest()


def criterion_partition(task: Mapping[str, Any]) -> dict[str, Any]:
    """Record the DECLARED visible/held-out split — never invent one.

    ``holdout_executed`` is always False: the runner executes exactly the task's
    declared ``verify`` command. Running a holdout set is scripts/holdout_gate.py's
    job, and its verdict artifact is a different, canonical shape.
    """
    declared_visible = task.get("visible_criteria")
    declared_holdout = task.get("holdout_criteria")
    declared = isinstance(declared_visible, list) or isinstance(declared_holdout, list)
    if isinstance(declared_visible, list):
        visible = [item for item in declared_visible if isinstance(item, str)]
    else:
        ref = task.get("criterion_ref")
        visible = [ref] if isinstance(ref, str) and ref else []
    holdout = ([item for item in declared_holdout if isinstance(item, str)]
               if isinstance(declared_holdout, list) else [])
    return {"visible": visible, "holdout": holdout,
            "declared": declared, "holdout_executed": False}
