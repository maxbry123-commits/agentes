"""Lay down the backend's data dir before it boots, so the run is ready on the first tick.

Everything here is written pre-boot on purpose: the workflow store and the settings
store both load from disk once at startup, so seeding files is cheaper and more
deterministic than replaying create/PATCH calls over HTTP (no aux LLM naming call,
no schedule normalization, no chance of the container inventing a second workflow).
"""

import json
import os
import tempfile
from typing import Any, Dict

from typeguard import typechecked

from backend.apps.dashboards.models import Dashboard
from backend.apps.settings.models import AppSettings
from runner.run_spec import CLOUD_RUN_DASHBOARD_ID, RunSpec

# 9Router provider id -> the AppSettings field the backend reads a raw key from.
API_KEY_SETTINGS_FIELD: Dict[str, str] = {
    "anthropic": "anthropic_api_key",
    "openai": "openai_api_key",
    "gemini": "google_api_key",
    "google": "google_api_key",
    "openrouter": "openrouter_api_key",
}

# One synthetic id for every cloud run. Without it each ephemeral container mints a fresh uuid and analytics sees a brand-new "install" per run.
CLOUD_RUNNER_INSTALLATION_ID = "openswarm-cloud-runner"

# Told to the agent in as many words, because it cannot find this out any other way and the
# consequence of not knowing is a report written to a folder that is deleted minutes later.
DELIVERY_NOTE = (
    "You are running in the OpenSwarm cloud on a throwaway machine. Your working directory is "
    "the ONLY place that survives: every file you save there is delivered back to the user, and "
    "everything else on this machine is destroyed the moment this run ends. So when a task asks "
    "for a document, spreadsheet, image or archive, write it to a plainly named file in your "
    "working directory rather than only pasting it into your reply. Do not write deliverables to "
    "/tmp or to your home directory; they will not come back."
)


@typechecked
def p_write_json(path: str, payload: Any) -> None:
    """Atomic, owner-only write; these files hold API keys."""
    directory = os.path.dirname(path)
    os.makedirs(directory, mode=0o700, exist_ok=True)
    handle, temp_path = tempfile.mkstemp(dir=directory, prefix=".seed-", suffix=".json")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2)
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)
    except BaseException:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


@typechecked
def unavailable_apps_note(spec: RunSpec) -> str:
    """Name the user's connected apps this run cannot reach, so silence is not mistaken for absence.

    Their MCP credentials never leave the laptop, so the servers are not here and never will be
    mid-run. Without this sentence the agent has no way to know the app exists, and "update my
    Notion" comes back as a confident paragraph about Notion rather than an admission.
    """
    names = [server.name for server in spec.unavailable_mcp_servers]
    if not names:
        return ""
    return (
        "These apps are connected on the user's own computer but NOT reachable from this cloud "
        f"run, because their sign-in details stay on that computer: {', '.join(sorted(names))}. "
        "If a task needs one of them, say plainly that it cannot be done from a cloud run and "
        "that it has to run on their machine. Never guess at, invent, or describe from memory "
        "what one of those apps contains."
    )


@typechecked
def settings_for_run(spec: RunSpec, workspace: str) -> AppSettings:
    """The AppSettings a cloud run needs: this workflow's model, this run's keys, no telemetry.

    `default_folder` is what makes the run's files findable afterwards. Left unset, the agent
    falls back to $HOME and the launcher reroutes it into a per-session scratch directory whose
    name nothing outside the backend can predict, so the harvest would have nowhere to look.
    """
    settings = AppSettings()
    settings.default_model = spec.workflow.model
    settings.connection_mode = "own_key"
    settings.analytics_opt_in = False
    settings.installation_id = CLOUD_RUNNER_INSTALLATION_ID
    settings.default_folder = workspace
    additions = [DELIVERY_NOTE, unavailable_apps_note(spec)]
    settings.default_system_prompt = "\n\n".join(
        part for part in [settings.default_system_prompt or "", *additions] if part
    ).strip()
    for credential in spec.credentials:
        if credential.auth_type != "api_key":
            continue
        field = API_KEY_SETTINGS_FIELD.get(credential.provider)
        if field is None:
            raise ValueError(
                f"no settings field for api_key provider {credential.provider!r}; "
                f"supported: {', '.join(sorted(set(API_KEY_SETTINGS_FIELD)))}"
            )
        setattr(settings, field, credential.api_key)
    return settings


@typechecked
def seed_data_root(data_root: str, workspace: str, spec: RunSpec) -> None:
    """Write the workflow, settings and dashboard records the backend will read at boot.

    The dashboard exists so the Electron window has somewhere to land and browser cards have
    somewhere to render. Writing it here rather than letting the backend's first-boot migration
    invent one keeps its id knowable before anything has started.

    The workspace sits OUTSIDE the data root deliberately: it is the agent's own folder, and a
    Glob or Grep run inside it should not sweep up the settings file its API keys live in.
    """
    os.makedirs(workspace, mode=0o700, exist_ok=True)
    workflow = spec.workflow_for_disk()
    p_write_json(
        os.path.join(data_root, "workflows", f"{workflow.id}.json"),
        workflow.model_dump(mode="json"),
    )
    p_write_json(
        os.path.join(data_root, "settings", "settings.json"),
        settings_for_run(spec, workspace).model_dump(mode="json"),
    )
    dashboard = Dashboard(id=CLOUD_RUN_DASHBOARD_ID, name=spec.workflow.title or "Cloud run")
    p_write_json(
        os.path.join(data_root, "dashboards", f"{dashboard.id}.json"),
        dashboard.model_dump(mode="json"),
    )
