import importlib.util
import json
from pathlib import Path
import sys

import pytest

from runtime.src.core.agent_memory_loader import (
    EXPECTED_AGENT_IDS,
    AgentMemoryError,
    build_pre_execution_context,
    load_agent_memory,
    verify_all_memories,
)


def _write_memory(root: Path, agent_id: str) -> None:
    path = root / agent_id / "agente-readme-memoria.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# memory\nagent_id: `{agent_id}`\ncontract tel.workflow/v4\n"
        "root ➡️📂 Wordflow LOOP Yaiwes/\n",
        encoding="utf-8",
    )


def test_all_18_memories_are_required(tmp_path):
    for agent_id in EXPECTED_AGENT_IDS:
        _write_memory(tmp_path, agent_id)
    loaded = verify_all_memories(tmp_path)
    assert tuple(loaded) == EXPECTED_AGENT_IDS
    assert len(loaded) == 18


def test_missing_memory_fails_closed(tmp_path):
    with pytest.raises(AgentMemoryError, match="MEMORY_FILE_MISSING"):
        load_agent_memory(tmp_path, "opencode")


def test_pre_execution_context_injects_memory_before_task(tmp_path):
    _write_memory(tmp_path, "opencode")
    memory = load_agent_memory(tmp_path, "opencode")
    context = build_pre_execution_context(memory, "TASK=T-001")
    assert context.index("agent_id") < context.index("# TASK CONTRACT")
    assert "TASK=T-001" in context


def test_real_fleet_injects_memory_before_runtime_task(tmp_path, monkeypatch):
    project_root = Path(__file__).resolve().parents[2]
    memory_root = (
        project_root
        / "wordflow_loop"
        / "wordflow_loop"
        / "agent_fleet"
        / "memory"
    )
    memories = verify_all_memories(memory_root)
    assert len(memories) == 18

    adapter_path = (
        project_root
        / "wordflow_loop"
        / "wordflow_loop"
        / "agent_fleet"
        / "agent_fleet_adapter.py"
    )
    registry_path = adapter_path.with_name("agent_fleet_registry.json")
    spec = importlib.util.spec_from_file_location("g014_agent_fleet_adapter", adapter_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    echo_script = tmp_path / "echo_stdin.py"
    echo_script.write_text("import sys\nprint(sys.stdin.read())\n", encoding="utf-8")
    monkeypatch.setenv("YAIWES_OPENCODE_COMMAND", f"{sys.executable} {echo_script}")

    fleet = module.AgentFleetAdapter(registry_path, memory_root=memory_root)
    result = fleet.invoke("opencode", {"task_id": "G-014"})
    received = json.loads(result["stdout"])
    context = received["pre_execution_context"]

    assert received["agent_id"] == "opencode"
    assert received["memory_sha256"] == memories["opencode"].sha256
    assert context.index("agent_id: `opencode`") < context.index("# TASK CONTRACT")
    assert '"task_id":"G-014"' in context
    assert received["task_payload"] == {"task_id": "G-014"}
