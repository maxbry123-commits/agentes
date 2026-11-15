"""Bring a cloud run's files down to the machine the user actually sits at.

A cloud run finishes while the laptop is shut, so the files live in the cloud until
something fetches them. That something is this module, and it puts them in Downloads
rather than anywhere clever: the whole point of a deliverable is that the user can
find it without being told where to look, and "it is in Downloads" is the one answer
nobody needs explained.

Every file is fetched at most once. The local path is derived, never stored, so a
user who moves or deletes a file just gets it back on the next look rather than
staring at a broken link.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from typeguard import typechecked

from backend.apps.workflows.cloud import client as cloud
from backend.apps.workflows.models import Workflow

logger = logging.getLogger(__name__)

# Bounded so one History open cannot spend minutes pulling a whole month of runs.
MAX_CONCURRENT_DOWNLOADS = 3


class LocalRunFile(BaseModel):
    """A cloud file plus where it is (or would be) on this machine."""

    model_config = ConfigDict(validate_assignment=True)

    id: str
    path: str
    size_bytes: int
    refusal: Optional[str] = None
    # Set once the bytes are on disk. None means "not here yet", never "not coming".
    local_path: Optional[str] = None


@typechecked
def safe_component(raw: str) -> str:
    """One path segment a filesystem will take, with the user's own name still legible."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", raw).strip(" .")
    return cleaned[:60] or "untitled"


@typechecked
def downloads_root() -> str:
    home = os.path.expanduser("~")
    downloads = os.path.join(home, "Downloads")
    return os.path.join(downloads if os.path.isdir(downloads) else home, "OpenSwarm")


@typechecked
def run_folder(workflow: Workflow, run: cloud.CloudRun) -> str:
    """Where this run's files go: one folder per run, named so a list of them reads as a history."""
    stamp = run.finished_at or run.started_at
    when = "unknown-date"
    if stamp:
        from datetime import datetime, timezone

        when = datetime.fromtimestamp(stamp / 1000, tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H%M")
    return os.path.join(
        downloads_root(),
        safe_component(workflow.title or "Workflow"),
        safe_component(f"{when} {run.id[:8]}"),
    )


@typechecked
def local_path_for(folder: str, file: cloud.CloudRunFile) -> str:
    """The file's home, with every segment of the run-relative path made filesystem-safe."""
    parts = [safe_component(part) for part in file.path.split("/") if part not in ("", ".", "..")]
    return os.path.join(folder, *(parts or ["file"]))


@typechecked
def p_already_here(path: str, size_bytes: int) -> bool:
    try:
        return os.path.getsize(path) == size_bytes
    except OSError:
        return False


@typechecked
def described(workflow: Workflow, run: cloud.CloudRun) -> List[LocalRunFile]:
    """This run's files and where they are right now. Reads disk, never fetches."""
    folder = run_folder(workflow, run)
    out: List[LocalRunFile] = []
    for file in run.files:
        local = local_path_for(folder, file)
        out.append(LocalRunFile(
            id=file.id,
            path=file.path,
            size_bytes=file.size_bytes,
            refusal=file.refusal,
            local_path=local if file.refusal is None and p_already_here(local, file.size_bytes) else None,
        ))
    return out


@typechecked
async def p_fetch_one(hosted_id: str, run: cloud.CloudRun, file: cloud.CloudRunFile, target: str) -> None:
    payload = await cloud.download_run_file(hosted_id, run.id, file.id)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    temporary = f"{target}.part"
    with open(temporary, "wb") as handle:
        handle.write(payload)
    os.replace(temporary, target)
    logger.info("cloud run %s: saved %s to %s", run.id, file.path, target)


@typechecked
async def fetch_missing(hosted_id: str, workflow: Workflow, runs: List[cloud.CloudRun]) -> None:
    """Pull down anything not already here. Never raises: a run's answer must render
    even when its attachments cannot be fetched, and the next look tries again."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

    async def p_guarded(run: cloud.CloudRun, file: cloud.CloudRunFile, target: str) -> None:
        async with semaphore:
            try:
                await p_fetch_one(hosted_id, run, file, target)
            except (cloud.SignedOut, cloud.CloudRefused, cloud.CloudUnreachable, OSError) as exc:
                logger.info("cloud run %s: %s not fetched (%s)", run.id, file.path, exc)

    pending = []
    for run in runs:
        folder = run_folder(workflow, run)
        for file in run.files:
            if file.refusal is not None:
                continue
            target = local_path_for(folder, file)
            if p_already_here(target, file.size_bytes):
                continue
            pending.append(p_guarded(run, file, target))
    if pending:
        await asyncio.gather(*pending)
