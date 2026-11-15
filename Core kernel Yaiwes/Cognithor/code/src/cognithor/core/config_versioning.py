"""Cognithor · Config Versioning with Rollback.

Saves configuration revisions before changes and allows rollback
to any previous revision.

Revisions are stored as JSON files in ``~/.cognithor/config_revisions/``
with the naming scheme ``rev_<timestamp_ms>.json``.

Architecture Bible: §12
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

_MAX_REVISIONS = 50

# Default directory — can be overridden for testing
_revisions_dir: Path | None = None


def _get_revisions_dir() -> Path:
    """Return the revisions directory, creating it if needed."""
    if _revisions_dir is not None:
        d = _revisions_dir
    else:
        d = Path.home() / ".cognithor" / "config_revisions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def set_revisions_dir(path: Path | None) -> None:
    """Override the revisions directory (useful for testing)."""
    global _revisions_dir
    _revisions_dir = path


def save_config_revision(config_dict: dict[str, Any], reason: str = "") -> str:
    """Save a configuration revision before a change.

    Args:
        config_dict: The current configuration as a dictionary.
        reason: Human-readable reason for the change.

    Returns:
        The revision ID (e.g. ``rev_1712500000000``).
    """
    revisions_dir = _get_revisions_dir()
    timestamp_ms = int(time.time() * 1000)
    revision_id = f"rev_{timestamp_ms}"
    filepath = revisions_dir / f"{revision_id}.json"

    payload = {
        "revision_id": revision_id,
        "timestamp": timestamp_ms / 1000.0,
        "reason": reason,
        "config": config_dict,
    }

    filepath.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    log.info("config_revision_saved", revision_id=revision_id, reason=reason)

    _cleanup_old_revisions()

    return revision_id


def list_revisions() -> list[dict[str, Any]]:
    """List all saved config revisions (newest first).

    Returns:
        List of dicts with keys: ``revision_id``, ``timestamp``, ``reason``.
    """
    revisions_dir = _get_revisions_dir()
    results: list[dict[str, Any]] = []

    for filepath in sorted(revisions_dir.glob("rev_*.json"), reverse=True):
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            results.append(
                {
                    "revision_id": data["revision_id"],
                    "timestamp": data["timestamp"],
                    "reason": data.get("reason", ""),
                }
            )
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            log.warning("config_revision_read_error", file=str(filepath), error=str(exc))

    return results


def rollback_to(revision_id: str) -> dict[str, Any]:
    """Retrieve the config dict for a given revision.

    Args:
        revision_id: The revision ID to roll back to.

    Returns:
        The config dictionary from that revision.

    Raises:
        FileNotFoundError: If the revision does not exist.
        ValueError: If the revision file is corrupt.
    """
    revisions_dir = _get_revisions_dir()
    filepath = revisions_dir / f"{revision_id}.json"

    if not filepath.exists():
        msg = f"Revision '{revision_id}' not found"
        raise FileNotFoundError(msg)

    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"Revision '{revision_id}' is corrupt"
        raise ValueError(msg) from exc

    config = data.get("config")
    if not isinstance(config, dict):
        msg = f"Revision '{revision_id}' has no valid config"
        raise ValueError(msg)

    log.info("config_rollback", revision_id=revision_id)
    return config


def _cleanup_old_revisions() -> None:
    """Remove old revisions, keeping at most ``_MAX_REVISIONS``."""
    revisions_dir = _get_revisions_dir()
    files = sorted(revisions_dir.glob("rev_*.json"))

    if len(files) <= _MAX_REVISIONS:
        return

    to_remove = files[: len(files) - _MAX_REVISIONS]
    for filepath in to_remove:
        try:
            filepath.unlink()
            log.debug("config_revision_removed", file=str(filepath))
        except OSError as exc:
            log.warning("config_revision_remove_error", file=str(filepath), error=str(exc))
