"""What the run made, and what of it is allowed to come home.

A cloud run's machine is destroyed the moment it exits, so a file it wrote is gone
unless something carries it out. This module is the "what": it walks the one
directory a run is given as its working folder and decides, per file, deliver or
refuse. The "how" (handing bytes to the control plane) lives in runner.results.report.

Refusing loudly is the whole point of the caps. A user who asked for a video and
got a 20MB fragment of one is worse off than a user who was told the video was too
big, so nothing here ever truncates a file: it either arrives whole or it arrives
as a sentence explaining why it did not.
"""

import hashlib
import logging
import os
from typing import List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field
from typeguard import typechecked

logger = logging.getLogger(__name__)

# Per-file ceiling. Deliverables are reports, spreadsheets, charts and small archives; a run that
# produces something bigger is doing a different job than this pipe was built for.
MAX_FILE_BYTES = 20 * 1024 * 1024
# Per-run ceiling, enforced in walk order so the first files still arrive when a later one blows it.
MAX_TOTAL_BYTES = 50 * 1024 * 1024
MAX_FILES = 40
# Longest path we will accept, so a deep tree cannot produce a name no filesystem will take back.
MAX_RELATIVE_PATH_CHARS = 180

# Machinery, not deliverables. Everything here is either regenerable (dependencies, caches,
# compiled bytecode) or the run's own plumbing, and shipping it would blow the file budget on
# things nobody asked for.
EXCLUDED_DIRS = frozenset({
    ".git",
    ".claude",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".cache",
    ".npm",
})
EXCLUDED_NAMES = frozenset({".DS_Store", ".gitignore", ".gitkeep"})

READ_CHUNK_BYTES = 1024 * 1024


class Deliverable(BaseModel):
    """One file that fits, addressed by its path relative to the run's workspace."""

    model_config = ConfigDict(validate_assignment=True)

    path: str
    size_bytes: int
    sha256: str


class Refused(BaseModel):
    """One file that does not come home, and the sentence the user gets instead."""

    model_config = ConfigDict(validate_assignment=True)

    path: str
    size_bytes: int
    reason: str


class Harvest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    files: List[Deliverable] = Field(default_factory=list)
    refused: List[Refused] = Field(default_factory=list)

    @typechecked
    def total_bytes(self) -> int:
        return sum(item.size_bytes for item in self.files)


@typechecked
def human_bytes(count: int) -> str:
    if count < 1024:
        return f"{count} B"
    if count < 1024 * 1024:
        return f"{count / 1024:.0f} KB"
    if count < 1024 * 1024 * 1024:
        return f"{count / (1024 * 1024):.1f} MB"
    return f"{count / (1024 * 1024 * 1024):.1f} GB"


@typechecked
def p_digest(path: str) -> Optional[str]:
    """sha256, streamed. None when the file went away mid-walk, which is not an error."""
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(READ_CHUNK_BYTES)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        logger.warning("could not read %s while harvesting: %s", path, exc)
        return None
    return digest.hexdigest()


@typechecked
def p_walk(workspace: str) -> List[Tuple[str, int]]:
    """Every candidate file under the workspace as (relative path, size), sorted for determinism."""
    found: List[Tuple[str, int]] = []
    for directory, subdirs, filenames in os.walk(workspace):
        subdirs[:] = sorted(name for name in subdirs if name not in EXCLUDED_DIRS)
        for filename in sorted(filenames):
            if filename in EXCLUDED_NAMES:
                continue
            absolute = os.path.join(directory, filename)
            # Symlinks are not followed: a run that linked to /etc/passwd must not exfiltrate it.
            if os.path.islink(absolute) or not os.path.isfile(absolute):
                continue
            try:
                size = os.path.getsize(absolute)
            except OSError:
                continue
            found.append((os.path.relpath(absolute, workspace), size))
    return found


@typechecked
def collect(workspace: str) -> Harvest:
    """Decide, for every file in the run's workspace, whether it comes home."""
    harvest = Harvest()
    if not os.path.isdir(workspace):
        return harvest

    running_total = 0
    for relative, size in p_walk(workspace):
        if len(relative) > MAX_RELATIVE_PATH_CHARS:
            harvest.refused.append(Refused(
                path=relative[:MAX_RELATIVE_PATH_CHARS] + "...",
                size_bytes=size,
                reason="its path is too long to save anywhere",
            ))
            continue
        if size == 0:
            continue
        if size > MAX_FILE_BYTES:
            harvest.refused.append(Refused(
                path=relative,
                size_bytes=size,
                reason=(
                    f"it is {human_bytes(size)} and a single cloud-run file cannot exceed "
                    f"{human_bytes(MAX_FILE_BYTES)}"
                ),
            ))
            continue
        if len(harvest.files) >= MAX_FILES:
            harvest.refused.append(Refused(
                path=relative,
                size_bytes=size,
                reason=f"this run already produced the maximum of {MAX_FILES} files",
            ))
            continue
        if running_total + size > MAX_TOTAL_BYTES:
            harvest.refused.append(Refused(
                path=relative,
                size_bytes=size,
                reason=(
                    f"the run's files already total {human_bytes(running_total)} and the limit "
                    f"is {human_bytes(MAX_TOTAL_BYTES)}"
                ),
            ))
            continue
        digest = p_digest(os.path.join(workspace, relative))
        if digest is None:
            harvest.refused.append(Refused(path=relative, size_bytes=size, reason="it could not be read"))
            continue
        harvest.files.append(Deliverable(path=relative, size_bytes=size, sha256=digest))
        running_total += size

    logger.info(
        "harvested %d file(s) totalling %s from %s, refused %d",
        len(harvest.files),
        human_bytes(running_total),
        workspace,
        len(harvest.refused),
    )
    return harvest
