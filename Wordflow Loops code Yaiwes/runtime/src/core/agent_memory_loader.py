"""Deterministic loader for the 18 agent memory contracts."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

EXPECTED_AGENT_IDS: Tuple[str, ...] = (
    "opencode", "openhands", "claude_code", "mimo_code", "codex",
    "smolagents", "hermes", "openclaw", "aider", "muse_glimmer",
    "kimi_k", "qwen_code", "cline", "goose", "agent_zero", "opendev",
    "research_agent_lab", "mirothinker",
)


class AgentMemoryError(ValueError):
    pass


@dataclass(frozen=True)
class AgentMemory:
    agent_id: str
    path: str
    sha256: str
    content: str


def load_agent_memory(memory_root: Path, agent_id: str) -> AgentMemory:
    if agent_id not in EXPECTED_AGENT_IDS:
        raise AgentMemoryError("UNKNOWN_AGENT_ID")
    path = memory_root / agent_id / "agente-readme-memoria.md"
    if not path.is_file():
        raise AgentMemoryError("MEMORY_FILE_MISSING")
    content = path.read_text(encoding="utf-8")
    required = (f"agent_id: `{agent_id}`", "tel.workflow/v4", "➡️📂 Wordflow LOOP Yaiwes/")
    if any(marker not in content for marker in required):
        raise AgentMemoryError("MEMORY_CONTRACT_INVALID")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return AgentMemory(agent_id, str(path), digest, content)


def verify_all_memories(memory_root: Path) -> Dict[str, AgentMemory]:
    return {agent_id: load_agent_memory(memory_root, agent_id) for agent_id in EXPECTED_AGENT_IDS}


def build_pre_execution_context(memory: AgentMemory, task_contract: str) -> str:
    if not task_contract.strip():
        raise AgentMemoryError("TASK_CONTRACT_REQUIRED")
    return memory.content.rstrip() + "\n\n# TASK CONTRACT\n" + task_contract.strip() + "\n"
