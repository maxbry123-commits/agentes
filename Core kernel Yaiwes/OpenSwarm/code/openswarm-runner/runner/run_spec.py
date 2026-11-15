"""Typed description of the single workflow run this container exists to execute.

The control plane hands the container exactly one of these (JSON in
OPENSWARM_RUN_SPEC, or a path in OPENSWARM_RUN_SPEC_FILE) and nothing else. Every
field is validated before the backend boots, so a malformed job dies in under a
second instead of burning a machine-minute discovering it.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typeguard import typechecked

from backend.apps.workflows.models import Workflow

SPEC_ENV = "OPENSWARM_RUN_SPEC"
SPEC_FILE_ENV = "OPENSWARM_RUN_SPEC_FILE"

# The one dashboard a cloud run has. Fixed rather than generated so the Electron window can be
# deep-linked at it before the backend has even booted, and so a workflow arriving with the
# laptop dashboard id it was authored against gets repointed at a dashboard that exists here.
CLOUD_RUN_DASHBOARD_ID = "cloud-run"

# Headroom the access token must still have on arrival. The control plane refreshes right before dispatch; anything thinner than this means its clock or its queue is broken, and we must not paper over that by refreshing ourselves.
MIN_TOKEN_LIFETIME = timedelta(minutes=2)

# A skill is prose plus the odd small script. These bounds keep a run spec from becoming a file
# transfer, and are enforced here so an oversized one dies before a machine is billed for it.
MAX_SKILLS = 60
MAX_SKILL_FILE_CHARS = 200_000


class InvalidRunSpec(ValueError):
    """The control plane handed us something we refuse to run."""


class ProviderCredential(BaseModel):
    """One already-refreshed provider credential, spendable but not rotatable.

    `extra="forbid"` is the first of two walls keeping a refresh token out of this
    container: a payload carrying `refreshToken` fails validation here and the run
    dies loudly. See runner.router_credentials for the second wall and the why.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    provider: str = Field(min_length=1)
    auth_type: Literal["oauth", "api_key"]
    label: str = "OpenSwarm cloud run"
    access_token: Optional[str] = None
    api_key: Optional[str] = None
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None

    @model_validator(mode="after")
    def p_require_matching_secret(self) -> "ProviderCredential":
        if self.auth_type == "oauth":
            if not self.access_token:
                raise ValueError(f"credential for {self.provider!r} is oauth but carries no access_token")
            if self.expires_at is None:
                raise ValueError(f"credential for {self.provider!r} is oauth but carries no expires_at")
            if self.api_key:
                raise ValueError(f"credential for {self.provider!r} carries both an access_token and an api_key")
        else:
            if not self.api_key:
                raise ValueError(f"credential for {self.provider!r} is api_key but carries no api_key")
            if self.access_token:
                raise ValueError(f"credential for {self.provider!r} carries both an access_token and an api_key")
        return self

    @typechecked
    def remaining_lifetime(self, now: datetime) -> Optional[timedelta]:
        """How long this credential is still good for; None when it cannot expire."""
        if self.expires_at is None:
            return None
        return self.expires_at.astimezone(timezone.utc) - now.astimezone(timezone.utc)


class CallbackTarget(BaseModel):
    """Where the run reports back. The token is a dedicated two-party secret, never a user credential."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    url: str = Field(min_length=1)
    token: str = Field(min_length=1)
    heartbeat_seconds: int = Field(default=30, ge=5, le=300)
    # Where the run's files go. Named outright rather than derived from `url`, so a control plane
    # that cannot accept files says so by leaving it out instead of being guessed at.
    artifacts_url: Optional[str] = None


class SkillFile(BaseModel):
    """One file inside a skill folder. Text only: a skill is prose plus small scripts."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    path: str = Field(min_length=1, max_length=180)
    text: str = Field(max_length=MAX_SKILL_FILE_CHARS)

    @model_validator(mode="after")
    def p_reject_escaping_path(self) -> "SkillFile":
        parts = self.path.split("/")
        if self.path.startswith("/") or "\\" in self.path or any(p in ("", ".", "..") for p in parts):
            raise ValueError(f"skill file path {self.path!r} is not a plain relative path")
        return self


class SkillPayload(BaseModel):
    """One of the user's skills, carried up so the agent has the same know-how it has at home.

    Skills are the user's own writing, not credentials. Nothing in here is a token, and the
    control plane never learns anything from it that it could spend.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    # Also the folder name under ~/.claude/skills, so it has to survive being a directory.
    id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    files: List[SkillFile] = Field(min_length=1)

    @model_validator(mode="after")
    def p_require_skill_md(self) -> "SkillPayload":
        if not any(file.path == "SKILL.md" for file in self.files):
            raise ValueError(f"skill {self.id!r} has no SKILL.md, so nothing would ever load it")
        return self


class McpServerNote(BaseModel):
    """A server the user has connected at home, named so the agent can say it cannot reach it.

    Deliberately carries NO transport and NO secret. The user's MCP credentials (Slack session
    cookies, Notion and GitHub access tokens, Google refresh tokens) stay on their laptop, so this
    is a list of names and nothing else. Its whole job is to stop the agent quietly answering
    "update my Notion" from general knowledge because it never knew Notion existed.
    """

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    name: str = Field(min_length=1, max_length=120)


class RunSpec(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    run_id: str = Field(min_length=1)
    workflow: Workflow
    credentials: List[ProviderCredential] = Field(min_length=1)
    callback: Optional[CallbackTarget] = None
    # The user's skills, shipped so a cloud run is as capable as the same workflow at home.
    skills: List[SkillPayload] = Field(default_factory=list, max_length=MAX_SKILLS)
    # Names only. See McpServerNote for why there is no config here.
    unavailable_mcp_servers: List[McpServerNote] = Field(default_factory=list, max_length=100)
    # Hard wall-clock ceiling. Fly bills by machine-second, so an agent that wedges must cost a bounded amount.
    max_run_seconds: int = Field(default=1800, ge=60, le=7200)
    # Boot Electron under a virtual display so browser steps work. On by default: parity is the
    # point of running in a container at all, and a workflow that never touches a browser is the
    # exception that should have to say so. Costs a few seconds and a few hundred MB when on.
    needs_browser: bool = True

    @typechecked
    def expired_credentials(self, now: datetime) -> List[ProviderCredential]:
        """Credentials too close to expiry to spend. The runner cannot refresh, so this is fatal, not a retry."""
        stale: List[ProviderCredential] = []
        for credential in self.credentials:
            remaining = credential.remaining_lifetime(now)
            if remaining is not None and remaining < MIN_TOKEN_LIFETIME:
                stale.append(credential)
        return stale

    @typechecked
    def workflow_for_disk(self) -> Workflow:
        """The workflow as this container should see it: one run, never a schedule.

        A cloud-executed workflow arrives with its schedule still configured. Left
        enabled, the container's own scheduler would fire it a second time inside
        the box, so the timer is stripped here rather than trusted to stay off.

        It also arrives pointing at whatever dashboard it was authored on, which does not
        exist in this container; left alone, the first browser card would 404 looking for
        it. Repointed at the one dashboard this run has.
        """
        copy = self.workflow.model_copy(deep=True)
        copy.dashboard_id = CLOUD_RUN_DASHBOARD_ID
        copy.schedule.enabled = False
        copy.deleted_at = None
        copy.draft_steps = None
        copy.next_run_at = None
        return copy


@typechecked
def load_run_spec() -> RunSpec:
    """Parse the run spec from the environment, or raise InvalidRunSpec with a legible reason."""
    raw = os.environ.get(SPEC_ENV, "").strip()
    source = SPEC_ENV
    if not raw:
        path = os.environ.get(SPEC_FILE_ENV, "").strip()
        if not path:
            raise InvalidRunSpec(f"no run spec: set {SPEC_ENV} to JSON or {SPEC_FILE_ENV} to a file path")
        source = f"{SPEC_FILE_ENV}={path}"
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw = handle.read()
        except OSError as exc:
            raise InvalidRunSpec(f"cannot read run spec from {source}: {exc}") from exc

    try:
        return RunSpec.model_validate_json(raw)
    except json.JSONDecodeError as exc:
        raise InvalidRunSpec(f"run spec from {source} is not valid JSON: {exc}") from exc
    except ValueError as exc:
        raise InvalidRunSpec(f"run spec from {source} is not a valid RunSpec: {exc}") from exc
