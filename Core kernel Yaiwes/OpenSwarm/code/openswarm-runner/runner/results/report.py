"""Tell the control plane what happened, and hand it whatever the run made.

The terminal report is the run's only receipt. Files go up BEFORE it, on purpose:
the per-run callback token stops working the instant the run reaches a terminal
state, so "upload, then close" is the only order in which both can succeed, and it
means the window for writing files to a run closes exactly when the run does.
"""

import logging
import os
import time
from typing import List, Literal, Optional
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict, Field
from typeguard import typechecked

from runner.results.deliverables import Harvest, human_bytes
from runner.run_spec import CallbackTarget

logger = logging.getLogger(__name__)

TERMINAL_ATTEMPTS = 5
TERMINAL_BACKOFF_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 15.0
# One file, one shot, generous: 20MB over a cold uplink is slower than any report.
UPLOAD_TIMEOUT_SECONDS = 120.0
FILE_PATH_HEADER = "X-Openswarm-File-Path"
FILE_SHA256_HEADER = "X-Openswarm-File-Sha256"


class ReportedFile(BaseModel):
    """One file the run produced, delivered or not, always named."""

    model_config = ConfigDict(validate_assignment=True)

    path: str
    size_bytes: int
    delivered: bool
    # Present only when delivered is False. Written for a human, because it is shown to one.
    reason: Optional[str] = None


class RunReport(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    run_id: str
    phase: Literal["started", "heartbeat", "finished"]
    status: str
    exit_code: Optional[int] = None
    error: Optional[str] = None
    cost_usd: float = 0.0
    active_step_idx: Optional[int] = None
    last_tool_label: Optional[str] = None
    answer: str = ""
    transcript: str = ""
    # The backend calls a run "success" even when the provider rejected the token; these are how the control plane sees that.
    system_notices: List[str] = Field(default_factory=list)
    # Every file the run made, including the ones that were too big to send. A deliverable that
    # silently vanished is the failure this list exists to make impossible.
    files: List[ReportedFile] = Field(default_factory=list)


@typechecked
def p_post_once(callback: CallbackTarget, report: RunReport) -> bool:
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = client.post(
                callback.url,
                headers={"Authorization": f"Bearer {callback.token}"},
                json=report.model_dump(mode="json"),
            )
        if response.status_code < 300:
            return True
        logger.warning("report %s rejected with HTTP %s", report.phase, response.status_code)
        return False
    except httpx.HTTPError as exc:
        logger.warning("report %s failed to send: %s", report.phase, exc)
        return False


@typechecked
def send_report(callback: Optional[CallbackTarget], report: RunReport) -> bool:
    """Post a report. Terminal reports retry; heartbeats get one shot and are never retried."""
    if callback is None:
        logger.info("no callback configured; %s report kept local: %s", report.phase, report.status)
        return True
    if report.phase != "finished":
        return p_post_once(callback, report)
    for attempt in range(TERMINAL_ATTEMPTS):
        if p_post_once(callback, report):
            return True
        if attempt + 1 < TERMINAL_ATTEMPTS:
            time.sleep(TERMINAL_BACKOFF_SECONDS * (attempt + 1))
    logger.error("terminal report for run %s never landed after %d attempts", report.run_id, TERMINAL_ATTEMPTS)
    return False


@typechecked
def p_upload_one(client: httpx.Client, callback: CallbackTarget, workspace: str, relative: str, sha256: str) -> Optional[str]:
    """Push one file. Returns None on success, or the sentence explaining the failure."""
    try:
        with open(os.path.join(workspace, relative), "rb") as handle:
            response = client.post(
                str(callback.artifacts_url),
                headers={
                    "Authorization": f"Bearer {callback.token}",
                    "Content-Type": "application/octet-stream",
                    FILE_PATH_HEADER: quote(relative, safe="/"),
                    FILE_SHA256_HEADER: sha256,
                },
                content=handle.read(),
            )
    except OSError as exc:
        return f"it could not be read back off disk ({exc.strerror or exc})"
    except httpx.HTTPError as exc:
        return f"the upload did not complete ({type(exc).__name__})"
    if response.status_code < 300:
        return None
    # The control plane refuses with prose it wrote for the user; keep its words rather than ours.
    detail = (response.text or "").strip()
    try:
        body = response.json()
        if isinstance(body, dict) and isinstance(body.get("error"), str):
            detail = body["error"]
    except ValueError:
        pass
    return detail[:300] if detail else f"the storage service answered HTTP {response.status_code}"


@typechecked
def deliver_files(callback: Optional[CallbackTarget], workspace: str, harvest: Harvest) -> List[ReportedFile]:
    """Hand every deliverable to the control plane and report honestly on each one.

    Never raises and never fails the run: a workflow whose answer is good and whose
    attachment did not make it should still deliver the answer, with the miss stated.
    """
    reported = [
        ReportedFile(path=item.path, size_bytes=item.size_bytes, delivered=False, reason=item.reason)
        for item in harvest.refused
    ]
    if not harvest.files:
        return reported
    if callback is None or not callback.artifacts_url:
        for item in harvest.files:
            reported.append(ReportedFile(
                path=item.path,
                size_bytes=item.size_bytes,
                delivered=False,
                reason="this run had nowhere to send files, so it kept them on the machine",
            ))
        return reported

    with httpx.Client(timeout=UPLOAD_TIMEOUT_SECONDS) as client:
        for item in harvest.files:
            failure = p_upload_one(client, callback, workspace, item.path, item.sha256)
            if failure is None:
                logger.info("delivered %s (%s)", item.path, human_bytes(item.size_bytes))
            else:
                logger.warning("could not deliver %s: %s", item.path, failure)
            reported.append(ReportedFile(
                path=item.path,
                size_bytes=item.size_bytes,
                delivered=failure is None,
                reason=failure,
            ))
    return reported
