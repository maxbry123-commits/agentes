"""Pyright runner: catches references to methods/attributes/names that don't exist.

The other checks can't do this. ruff is per-file and never builds a cross-symbol
type graph; vulture finds dead (unused) definitions, not invalid references; the
naming checks only inspect where names are *defined*, not where they're *read*.
So a missed rename like ``self._per_session`` (when the attribute is actually
``p_per_session``) sails through everything and only blows up at runtime.

Pyright resolves types/inheritance/imports, so its ``reportAttributeAccessIssue``
flags exactly that. We run it in the lowest-noise mode possible
(config/pyright_check.json sets typeCheckingMode "off" and re-enables only the
existence-checking rules as errors), so this section stays high-signal without a
full strict-mode cleanup.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import CheckError, is_excepted, is_lintignored

# Cold first run downloads the pinned node binary (pip wrapper) and warms the
# import graph; keep this generous so a slow first pass doesn't time out and
# silently report zero.
_TIMEOUT = 240

_CONFIG_REL = Path("linter") / "config" / "pyright_check.json"


def run_pyright(
    root: Path,
    exceptions: dict[str, list[str]],
    ignores: dict[Path, set[str]] | None = None,
) -> list[str]:
    """Run pyright on the Python backend and return existence errors."""
    pyright_bin = root / "backend" / ".venv" / "bin" / "pyright"
    if not pyright_bin.exists():
        found = shutil.which("pyright")
        if not found:
            raise CheckError("pyright executable not found in backend/.venv/bin or PATH")
        pyright_bin = Path(found)

    config = root / _CONFIG_REL
    if not config.exists():
        raise CheckError(f"pyright config not found at {_CONFIG_REL}")

    cmd = [str(pyright_bin), "--project", str(config), "--outputjson"]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(root), timeout=_TIMEOUT,
        )
    except subprocess.TimeoutExpired as e:
        raise CheckError(f"timed out after {_TIMEOUT}s (machine under load or cold cache)") from e
    except OSError as e:
        raise CheckError(f"failed to launch pyright ({e})") from e

    # pyright exits 0 (no errors) or 1 (errors found) on a successful run. Any
    # other code with no parseable JSON means pyright itself failed (e.g. node
    # missing, bad config) — surface it rather than treating empty as clean.
    out = result.stdout.strip()
    if not out:
        detail = (result.stderr or "no output").strip()[:300]
        raise CheckError(f"pyright produced no JSON (exit {result.returncode}): {detail}")
    try:
        data = json.loads(out)
    except json.JSONDecodeError as e:
        raise CheckError(f"pyright JSON parse failed (exit {result.returncode}): {e}") from e

    errors: list[str] = []
    for diag in data.get("generalDiagnostics", []):
        if diag.get("severity") != "error":
            continue
        file_abs = diag.get("file", "")
        try:
            relpath = str(Path(file_abs).resolve().relative_to(root))
        except ValueError:
            # Diagnostic outside the repo root (stub/site-packages); ignore.
            continue
        if is_excepted(relpath, "pyright", exceptions):
            continue
        if ignores and is_lintignored(root / relpath, root, "pyright", ignores):
            continue
        # pyright ranges are 0-based; the linter/IDE want 1-based line+col.
        start = diag.get("range", {}).get("start", {})
        line = int(start.get("line", 0)) + 1
        col = int(start.get("character", 0)) + 1
        rule = diag.get("rule", "")
        msg = " ".join((diag.get("message", "") or "").splitlines()).strip()
        rule_part = f"{rule} " if rule else ""
        errors.append(f"{relpath}:{line}:{col}: error: [pyright] {rule_part}{msg}")
    return errors
