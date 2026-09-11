from pathlib import Path

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
