"""The user's know-how travelling up, and their app credentials not travelling at all."""

import os

import pytest
from pydantic import ValidationError

from runner.run_spec import McpServerNote, RunSpec, SkillPayload
from runner.seed.data_root import settings_for_run, unavailable_apps_note
from runner.seed.skills import skills_dir, write_skills

COFFEE = {
    "id": "coffee-ratio",
    "files": [
        {"path": "SKILL.md", "text": "---\nname: coffee-ratio\ndescription: house ratio\n---\n\n1:16.5\n"},
        {"path": "scripts/brew.py", "text": "print('brew')\n"},
    ],
}


def p_spec(**overrides) -> RunSpec:
    body = {
        "run_id": "cr-1",
        "workflow": {"id": "wf-1", "title": "Test", "steps": [{"id": "s1", "text": "go"}]},
        "credentials": [{"provider": "anthropic", "auth_type": "api_key", "api_key": "sk-test"}],
    }
    body.update(overrides)
    return RunSpec.model_validate(body)


def test_a_skill_folder_lands_where_the_backend_looks_for_it(tmp_path) -> None:
    written = write_skills(str(tmp_path), [SkillPayload.model_validate(COFFEE)])

    assert written == 1
    root = skills_dir(str(tmp_path))
    assert root.endswith(os.path.join(".claude", "skills"))
    with open(os.path.join(root, "coffee-ratio", "SKILL.md"), encoding="utf-8") as handle:
        assert "house ratio" in handle.read()
    assert os.path.isfile(os.path.join(root, "coffee-ratio", "scripts", "brew.py"))


def test_no_skills_is_an_empty_directory_not_a_failure(tmp_path) -> None:
    assert write_skills(str(tmp_path), []) == 0
    assert os.path.isdir(skills_dir(str(tmp_path)))


def test_a_skill_with_no_skill_md_is_refused_before_a_machine_boots() -> None:
    with pytest.raises(ValidationError, match="no SKILL.md"):
        SkillPayload.model_validate({"id": "x", "files": [{"path": "README.md", "text": "hi"}]})


@pytest.mark.parametrize("bad", ["../escape.md", "/etc/passwd", "a/../../b.md", "a\\b.md", ""])
def test_a_skill_path_that_could_climb_out_is_refused(bad: str) -> None:
    with pytest.raises(ValidationError):
        SkillPayload.model_validate({"id": "x", "files": [{"path": bad, "text": "hi"}]})


@pytest.mark.parametrize("bad", ["../evil", "a/b", ".hidden", "has space", ""])
def test_a_skill_id_that_is_not_a_plain_folder_name_is_refused(bad: str) -> None:
    with pytest.raises(ValidationError):
        SkillPayload.model_validate({"id": bad, "files": [{"path": "SKILL.md", "text": "hi"}]})


def test_the_spec_cannot_carry_an_mcp_secret_at_all() -> None:
    # extra="forbid" is the wall: there is no field for a token, so a payload with one dies here
    # rather than landing in a container that runs the user's own prose with Bash.
    with pytest.raises(ValidationError):
        McpServerNote.model_validate({"name": "Notion", "access_token": "secret_abc"})
    with pytest.raises(ValidationError):
        McpServerNote.model_validate({"name": "Slack", "env": {"SLACK_MCP_XOXC_TOKEN": "xoxc-1"}})


def test_unreachable_apps_are_named_in_the_prompt_so_silence_is_not_mistaken_for_absence(tmp_path) -> None:
    spec = p_spec(unavailable_mcp_servers=[{"name": "Notion"}, {"name": "Google Workspace"}])
    note = unavailable_apps_note(spec)

    assert "Notion" in note and "Google Workspace" in note
    assert "cannot be done from a cloud run" in note
    assert note in (settings_for_run(spec, str(tmp_path)).default_system_prompt or "")


def test_with_no_connected_apps_nothing_is_added_to_the_prompt(tmp_path) -> None:
    assert unavailable_apps_note(p_spec()) == ""
