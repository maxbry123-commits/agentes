from __future__ import annotations

import io
import json
import subprocess
import tarfile
import tomllib

from data.nemotron_gym.verifiers import HYBRID_IFEVAL_JUDGE_VERIFIER_PY
from data.tasktrove.rewardkit_migration import (
    REWARDKIT_PACKAGE,
    migrate_task_binary,
    patch_task_toml,
)


GENERIC_VERIFIER = (
    """from litellm import completion\nscore = completion(model='judge')\n"""
)


def _archive(verifier: str, verifier_data: dict) -> bytes:
    files = {
        "instruction.md": b"Answer the question.",
        "environment/Dockerfile": b"FROM ubuntu:24.04\nRUN apt-get update && apt-get install -y python3 python3-pip\n",
        "tests/test.sh": b"echo 0 > /logs/verifier/reward.txt\npython3 /tests/verifier.py || true\n",
        "tests/verifier.py": verifier.encode(),
        "tests/verifier_data.json": json.dumps(verifier_data).encode(),
        "task.toml": b'version = "1.0"\n[verifier]\nenv = { OPENAI_API_KEY = "${OPENAI_API_KEY}" }\n',
    }
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, content in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    return output.getvalue()


def _files(task_binary: bytes) -> dict[str, bytes]:
    with tarfile.open(fileobj=io.BytesIO(task_binary), mode="r:gz") as archive:
        return {
            member.name: archive.extractfile(member).read()
            for member in archive.getmembers()
            if member.isfile()
        }


def test_generic_judge_migrates_to_rewardkit() -> None:
    task_binary = _archive(
        GENERIC_VERIFIER,
        {
            "instruction": "Explain the result.",
            "rubric": [{"id": "correct", "criteria": "The result is correct."}],
        },
    )

    migrated, migration = migrate_task_binary(task_binary)
    files = _files(migrated)

    assert migration is not None
    assert migration.family == "generic"
    assert "tests/verifier.py" not in files
    assert "tests/judge.toml" in files
    judge = tomllib.loads(files["tests/judge.toml"].decode())
    assert judge["criterion"][0]["name"] == "reward"
    assert judge["criterion"][0]["type"] == "numeric"
    assert REWARDKIT_PACKAGE in files["environment/Dockerfile"].decode()
    assert "|| true" not in files["tests/test.sh"].decode()
    assert "> /logs/verifier/reward.txt" not in files["tests/test.sh"].decode()
    assert "LITELLM_DROP_PARAMS=1" in files["tests/test.sh"].decode()
    tomllib.loads(files["task.toml"].decode())


def test_hybrid_judge_retains_deterministic_gate() -> None:
    task_binary = _archive(
        HYBRID_IFEVAL_JUDGE_VERIFIER_PY,
        {
            "instruction": "Reply in JSON and be polite.",
            "det_constraints": [{"instruction_id": "json_format"}],
            "judge_questions": ["Is the response polite?"],
        },
    )

    migrated, migration = migrate_task_binary(task_binary)
    files = _files(migrated)

    assert migration is not None
    assert migration.family == "hybrid"
    assert migration.has_deterministic_gate
    gate = files["tests/deterministic_gate"].decode()
    compile(gate, "deterministic_gate", "exec")
    judge = tomllib.loads(files["tests/judge.toml"].decode())
    assert judge["scoring"]["aggregation"] == "all_pass"


def test_legacy_litellm_layer_is_removed() -> None:
    archive = _archive(GENERIC_VERIFIER, {"instruction": "x"})
    files = _files(archive)
    files["environment/Dockerfile"] = (
        b"FROM python:3.11-slim-bookworm\n"
        b"RUN pip install --no-cache-dir litellm==1.51.3\n"
    )
    rebuilt = io.BytesIO()
    with tarfile.open(fileobj=rebuilt, mode="w:gz") as task:
        for name, content in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            task.addfile(member, io.BytesIO(content))

    migrated, _ = migrate_task_binary(rebuilt.getvalue())
    dockerfile = _files(migrated)["environment/Dockerfile"].decode()
    assert "litellm==1.51.3" not in dockerfile
    assert "FROM python:3.12-slim-bookworm" in dockerfile
    assert REWARDKIT_PACKAGE in dockerfile


def test_task_toml_section_remains_valid() -> None:
    source = 'version = "1.0"\n[verifier]\ntimeout_sec = 300\n[verifier.env]\nOPENAI_API_KEY = "${OPENAI_API_KEY}"\n[agent]\ntimeout_sec = 900\n'
    patched = patch_task_toml(source)

    config = tomllib.loads(patched)
    assert config["verifier"]["env"]["REWARDKIT_JUDGE"].endswith("gpt-4o-mini}")
    assert config["agent"]["timeout_sec"] == 900


def test_test_script_has_scoreable_empty_answer_branch() -> None:
    migrated, _ = migrate_task_binary(_archive(GENERIC_VERIFIER, {"instruction": "x"}))
    script = _files(migrated)["tests/test.sh"].decode()

    subprocess.run(["bash", "-n"], input=script, text=True, check=True)
    empty_branch = script.index("if [[ ! -s /app/response.txt")
    rewardkit_call = script.index("rewardkit /tests")
    assert empty_branch < rewardkit_call
