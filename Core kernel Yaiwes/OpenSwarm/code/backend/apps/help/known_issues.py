"""The curated known-issues list that ships with this build.

Deliberately NOT the live GitHub issue queue: that queue is engineering-facing (path guards, token
budgets) and phrased in nothing like the words a user would use for their symptom, so matching a
user's complaint against it produces false confidence. It is also network-dependent and publicly
writable, which is a prompt-injection surface for no gain.

So: a short list of real, user-visible symptoms, each verified. The help chat is told this list is
complete and that it has no live view of the tracker, so it can never invent a bug status.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class HelpKnownIssue(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: str
    title: str
    status: Literal["known", "mitigated", "fixed"]
    detail: str
    workaround: Optional[str] = None


KNOWN_ISSUES: List[HelpKnownIssue] = [
    HelpKnownIssue(
        id="free-trial-capacity",
        title="Free-trial runs fail with a capacity or busy message",
        status="mitigated",
        detail=(
            "The free trial runs on one shared pool of capacity, so under load a run can come back "
            "saying it is out of capacity. The app now waits and retries automatically instead of "
            "erroring straight away, but a sustained busy period still ends in that message."
        ),
        workaround="Connecting your own subscription or API key under Settings, then Models, avoids the shared pool entirely.",
    ),
    HelpKnownIssue(
        id="windows-cli-quarantine",
        title="Windows: 'Claude Code not found' after installing",
        status="mitigated",
        detail=(
            "Some Windows antivirus products quarantine the command-line binary that ships inside the "
            "app, which makes every run fail with a not-found error. Newer builds ship that binary "
            "code-signed, and the app now detects the case and shows repair steps instead of a raw error."
        ),
        workaround="Restore the file from your antivirus quarantine, or reinstall OpenSwarm. Your chats are kept either way.",
    ),
    HelpKnownIssue(
        id="dashboard-switch-logout",
        title="Switching dashboards can sign you out of a site in a browser card",
        status="known",
        detail=(
            "Some sites keep their login in per-tab storage that only lives as long as the page is "
            "mounted. Panning away from a card and back preserves it, because that state is captured "
            "and restored, but switching to another dashboard and back can still lose it."
        ),
        workaround="Keep browser cards you are signed into on the dashboard you are working in, or sign in again after switching.",
    ),
]
