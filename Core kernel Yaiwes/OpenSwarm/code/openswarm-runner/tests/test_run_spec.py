"""The run spec is the only thing the control plane can say to this container."""

import json
import os
import stat

import pytest

from runner.run_spec import InvalidRunSpec, RunSpec, load_run_spec
from runner.seed.data_root import seed_data_root, settings_for_run

VALID_CREDENTIAL = {"provider": "anthropic", "auth_type": "api_key", "api_key": "sk-test-not-real"}


def spec_body(**overrides) -> dict:
    body = {
        "run_id": "run-1",
        "workflow": {
            "id": "wf-1",
            "title": "Daily digest",
            "model": "opus-5",
            "steps": [{"text": "summarize the inbox"}],
            "schedule": {"enabled": True, "repeat_unit": "day", "hour": 9},
        },
        "credentials": [VALID_CREDENTIAL],
    }
    body.update(overrides)
    return body


def test_a_missing_spec_names_both_env_vars(monkeypatch) -> None:
    monkeypatch.delenv("OPENSWARM_RUN_SPEC", raising=False)
    monkeypatch.delenv("OPENSWARM_RUN_SPEC_FILE", raising=False)
    with pytest.raises(InvalidRunSpec, match="OPENSWARM_RUN_SPEC_FILE"):
        load_run_spec()


def test_a_spec_file_is_accepted(tmp_path, monkeypatch) -> None:
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec_body()), encoding="utf-8")
    monkeypatch.delenv("OPENSWARM_RUN_SPEC", raising=False)
    monkeypatch.setenv("OPENSWARM_RUN_SPEC_FILE", str(path))
    assert load_run_spec().workflow.title == "Daily digest"


def test_unknown_top_level_fields_are_rejected(monkeypatch) -> None:
    monkeypatch.setenv("OPENSWARM_RUN_SPEC", json.dumps(spec_body(surprise="hello")))
    with pytest.raises(InvalidRunSpec, match="surprise"):
        load_run_spec()


def test_a_run_needs_at_least_one_credential(monkeypatch) -> None:
    monkeypatch.setenv("OPENSWARM_RUN_SPEC", json.dumps(spec_body(credentials=[])))
    with pytest.raises(InvalidRunSpec):
        load_run_spec()


def test_the_container_never_inherits_the_schedule() -> None:
    spec = RunSpec.model_validate(spec_body())
    assert spec.workflow.schedule.enabled is True
    assert spec.workflow_for_disk().schedule.enabled is False


def test_seeding_writes_the_workflow_and_owner_only_settings(tmp_path) -> None:
    spec = RunSpec.model_validate(spec_body())
    workspace = str(tmp_path / "workspace")
    seed_data_root(str(tmp_path / "data"), workspace, spec)

    workflow_path = tmp_path / "data" / "workflows" / "wf-1.json"
    settings_path = tmp_path / "data" / "settings" / "settings.json"
    assert json.loads(workflow_path.read_text())["schedule"]["enabled"] is False
    assert stat.S_IMODE(os.stat(settings_path).st_mode) == 0o600

    settings = json.loads(settings_path.read_text())
    assert settings["anthropic_api_key"] == "sk-test-not-real"
    assert settings["default_model"] == "opus-5"
    assert settings["analytics_opt_in"] is False
    # The agent's folder is the deliverable folder, and it exists before the backend boots.
    assert settings["default_folder"] == workspace
    assert os.path.isdir(workspace)


def test_the_agent_is_told_its_files_only_survive_from_the_workspace(tmp_path) -> None:
    spec = RunSpec.model_validate(spec_body())
    prompt = settings_for_run(spec, str(tmp_path)).default_system_prompt or ""
    assert "delivered back to the user" in prompt


def test_an_unmappable_api_key_provider_fails_loudly(tmp_path) -> None:
    spec = RunSpec.model_validate(spec_body(
        credentials=[{"provider": "wat", "auth_type": "api_key", "api_key": "x"}]
    ))
    with pytest.raises(ValueError, match="no settings field"):
        settings_for_run(spec, str(tmp_path))
