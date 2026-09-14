"""Execution Recorder — Capture full agent runs for deterministic replay.

Records every decision point during an agent execution:
  - LLM calls (prompt, response, model, temperature)
  - Tool calls (name, params, result, duration)
  - Planner decisions (action plans, confidence)
  - Gatekeeper decisions (risk, policy)
  - Context injections (memories, procedures)

Recordings are serializable to JSONL for export and sharing.

Architecture: §17.1 (Deterministic Replay)
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Event Types
# ---------------------------------------------------------------------------


class EventType(StrEnum):
    """Types of recorded execution events."""

    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    PLAN_GENERATED = "plan_generated"
    GATE_DECISION = "gate_decision"
    CONTEXT_INJECTION = "context_injection"
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    ITERATION_START = "iteration_start"
    ITERATION_END = "iteration_end"
    ERROR = "error"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Execution Event
# ---------------------------------------------------------------------------


@dataclass
class ExecutionEvent:
    """A single recorded event during an agent execution.

    Each event captures a decision point or side effect that is needed
    to reproduce the execution deterministically.
    """

    event_id: str
    event_type: EventType
    timestamp: float = field(default_factory=time.time)
    sequence: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    parent_event_id: str = ""
    iteration: int = 0
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "data": self.data,
            "parent_event_id": self.parent_event_id,
            "iteration": self.iteration,
            "duration_ms": round(self.duration_ms, 2),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExecutionEvent:
        return cls(
            event_id=d["event_id"],
            event_type=EventType(d["event_type"]),
            timestamp=d.get("timestamp", 0.0),
            sequence=d.get("sequence", 0),
            data=d.get("data", {}),
            parent_event_id=d.get("parent_event_id", ""),
            iteration=d.get("iteration", 0),
            duration_ms=d.get("duration_ms", 0.0),
        )


# ---------------------------------------------------------------------------
# Execution Recording
# ---------------------------------------------------------------------------


@dataclass
class ExecutionRecording:
    """A complete recording of an agent execution.

    Contains all events in sequence, plus metadata about the run.
    """

    recording_id: str
    session_id: str = ""
    agent_name: str = ""
    model: str = ""
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0
    events: list[ExecutionEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    temperature: float = 0.0
    success: bool = False
    error: str = ""

    @property
    def duration_ms(self) -> float:
        if self.finished_at <= 0:
            return 0.0
        return (self.finished_at - self.started_at) * 1000

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def iteration_count(self) -> int:
        return max((e.iteration for e in self.events), default=0)

    @property
    def tool_calls(self) -> list[ExecutionEvent]:
        return [e for e in self.events if e.event_type == EventType.TOOL_CALL]

    @property
    def llm_calls(self) -> list[ExecutionEvent]:
        return [e for e in self.events if e.event_type == EventType.LLM_REQUEST]

    @property
    def checksum(self) -> str:
        """Content hash for integrity verification."""
        content = json.dumps(
            [e.to_dict() for e in self.events],
            sort_keys=True,
            ensure_ascii=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "recording_id": self.recording_id,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "model": self.model,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": round(self.duration_ms, 1),
            "event_count": self.event_count,
            "iteration_count": self.iteration_count,
            "seed": self.seed,
            "temperature": self.temperature,
            "success": self.success,
            "error": self.error,
            "checksum": self.checksum,
            "metadata": self.metadata,
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExecutionRecording:
        rec = cls(
            recording_id=d["recording_id"],
            session_id=d.get("session_id", ""),
            agent_name=d.get("agent_name", ""),
            model=d.get("model", ""),
            started_at=d.get("started_at", 0.0),
            finished_at=d.get("finished_at", 0.0),
            seed=d.get("seed"),
            temperature=d.get("temperature", 0.0),
            success=d.get("success", False),
            error=d.get("error", ""),
            metadata=d.get("metadata", {}),
        )
        rec.events = [ExecutionEvent.from_dict(e) for e in d.get("events", [])]
        return rec


# ---------------------------------------------------------------------------
# Execution Recorder
# ---------------------------------------------------------------------------


class ExecutionRecorder:
    """Records agent execution events for later replay.

    Usage::

        recorder = ExecutionRecorder()
        rec = recorder.start("session_123", agent_name="planner")
        recorder.record_llm_request(rec.recording_id, prompt="...", model="qwen3:32b")
        recorder.record_llm_response(rec.recording_id, response="...", tokens=500)
        recorder.record_tool_call(rec.recording_id, tool="web_search", params={...})
        recorder.record_tool_result(rec.recording_id, tool="web_search", result="...")
        recorder.finish(rec.recording_id, success=True)

        # Export
        recorder.export_jsonl(rec.recording_id, Path("run.jsonl"))
    """

    def __init__(self, max_recordings: int = 100) -> None:
        self._recordings: dict[str, ExecutionRecording] = {}
        self._max_recordings = max_recordings
        self._sequence_counters: dict[str, int] = {}

    def start(
        self,
        session_id: str = "",
        *,
        agent_name: str = "",
        model: str = "",
        seed: int | None = None,
        temperature: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionRecording:
        """Start a new execution recording."""
        recording_id = hashlib.sha256(f"rec:{session_id}:{time.time()}".encode()).hexdigest()[:16]

        rec = ExecutionRecording(
            recording_id=recording_id,
            session_id=session_id,
            agent_name=agent_name,
            model=model,
            seed=seed,
            temperature=temperature,
            metadata=metadata or {},
        )
        self._recordings[recording_id] = rec
        self._sequence_counters[recording_id] = 0

        # Enforce max recordings (FIFO eviction)
        if len(self._recordings) > self._max_recordings:
            oldest_id = next(iter(self._recordings))
            del self._recordings[oldest_id]
            self._sequence_counters.pop(oldest_id, None)

        log.info("recording_started", recording_id=recording_id, session_id=session_id)
        return rec

    def finish(
        self,
        recording_id: str,
        *,
        success: bool = True,
        error: str = "",
    ) -> ExecutionRecording | None:
        """Finish a recording."""
        rec = self._recordings.get(recording_id)
        if not rec:
            return None
        rec.finished_at = time.time()
        rec.success = success
        rec.error = error
        log.info(
            "recording_finished",
            recording_id=recording_id,
            events=rec.event_count,
            duration_ms=round(rec.duration_ms, 1),
        )
        return rec

    def get(self, recording_id: str) -> ExecutionRecording | None:
        return self._recordings.get(recording_id)

    def list_recordings(self) -> list[ExecutionRecording]:
        return list(self._recordings.values())

    # -- Convenience event recorders --

    def record_event(
        self,
        recording_id: str,
        event_type: EventType,
        data: dict[str, Any] | None = None,
        *,
        iteration: int = 0,
        parent_event_id: str = "",
        duration_ms: float = 0.0,
    ) -> ExecutionEvent | None:
        """Record a generic event."""
        rec = self._recordings.get(recording_id)
        if not rec:
            return None

        seq = self._sequence_counters.get(recording_id, 0)
        self._sequence_counters[recording_id] = seq + 1

        event_id = f"{recording_id}:{seq:04d}"
        event = ExecutionEvent(
            event_id=event_id,
            event_type=event_type,
            sequence=seq,
            data=data or {},
            parent_event_id=parent_event_id,
            iteration=iteration,
            duration_ms=duration_ms,
        )
        rec.events.append(event)
        return event

    def record_llm_request(
        self,
        recording_id: str,
        *,
        prompt: str = "",
        model: str = "",
        temperature: float = 0.0,
        max_tokens: int = 0,
        iteration: int = 0,
    ) -> ExecutionEvent | None:
        return self.record_event(
            recording_id,
            EventType.LLM_REQUEST,
            {
                "prompt_preview": prompt[:500],
                "prompt_length": len(prompt),
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            iteration=iteration,
        )

    def record_llm_response(
        self,
        recording_id: str,
        *,
        response: str = "",
        tokens: int = 0,
        model: str = "",
        duration_ms: float = 0.0,
        iteration: int = 0,
    ) -> ExecutionEvent | None:
        return self.record_event(
            recording_id,
            EventType.LLM_RESPONSE,
            {
                "response_preview": response[:500],
                "response_length": len(response),
                "tokens": tokens,
                "model": model,
            },
            iteration=iteration,
            duration_ms=duration_ms,
        )

    def record_tool_call(
        self,
        recording_id: str,
        *,
        tool: str,
        params: dict[str, Any] | None = None,
        iteration: int = 0,
    ) -> ExecutionEvent | None:
        return self.record_event(
            recording_id,
            EventType.TOOL_CALL,
            {"tool": tool, "params": params or {}},
            iteration=iteration,
        )

    def record_tool_result(
        self,
        recording_id: str,
        *,
        tool: str,
        result: str = "",
        is_error: bool = False,
        duration_ms: float = 0.0,
        iteration: int = 0,
    ) -> ExecutionEvent | None:
        return self.record_event(
            recording_id,
            EventType.TOOL_RESULT,
            {
                "tool": tool,
                "result_preview": result[:500],
                "result_length": len(result),
                "is_error": is_error,
            },
            iteration=iteration,
            duration_ms=duration_ms,
        )

    def record_plan(
        self,
        recording_id: str,
        *,
        goal: str = "",
        steps: list[dict[str, Any]] | None = None,
        confidence: float = 0.0,
        iteration: int = 0,
    ) -> ExecutionEvent | None:
        return self.record_event(
            recording_id,
            EventType.PLAN_GENERATED,
            {
                "goal": goal,
                "steps": steps or [],
                "step_count": len(steps or []),
                "confidence": confidence,
            },
            iteration=iteration,
        )

    def record_gate_decision(
        self,
        recording_id: str,
        *,
        tool: str = "",
        status: str = "allow",
        risk_level: str = "green",
        policy: str = "",
        iteration: int = 0,
    ) -> ExecutionEvent | None:
        return self.record_event(
            recording_id,
            EventType.GATE_DECISION,
            {
                "tool": tool,
                "status": status,
                "risk_level": risk_level,
                "policy": policy,
            },
            iteration=iteration,
        )

    def record_user_message(
        self,
        recording_id: str,
        *,
        message: str = "",
        channel: str = "",
    ) -> ExecutionEvent | None:
        return self.record_event(
            recording_id,
            EventType.USER_MESSAGE,
            {"message_preview": message[:500], "message_length": len(message), "channel": channel},
        )

    def record_agent_response(
        self,
        recording_id: str,
        *,
        response: str = "",
        iteration: int = 0,
    ) -> ExecutionEvent | None:
        return self.record_event(
            recording_id,
            EventType.AGENT_RESPONSE,
            {"response_preview": response[:500], "response_length": len(response)},
            iteration=iteration,
        )

    # -- Export --

    def export_jsonl(self, recording_id: str, path: Path) -> bool:
        """Export a recording as JSONL (one JSON line per event)."""
        rec = self._recordings.get(recording_id)
        if not rec:
            return False

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            # Header line with metadata
            header = {
                "type": "header",
                "recording_id": rec.recording_id,
                "session_id": rec.session_id,
                "agent_name": rec.agent_name,
                "model": rec.model,
                "started_at": rec.started_at,
                "finished_at": rec.finished_at,
                "seed": rec.seed,
                "temperature": rec.temperature,
                "success": rec.success,
                "checksum": rec.checksum,
                "metadata": rec.metadata,
            }
            f.write(json.dumps(header, ensure_ascii=False) + "\n")

            # Events
            for event in rec.events:
                line = {"type": "event", **event.to_dict()}
                f.write(json.dumps(line, ensure_ascii=False) + "\n")

        log.info("recording_exported", path=str(path), events=rec.event_count)
        return True

    def import_jsonl(self, path: Path) -> ExecutionRecording | None:
        """Import a recording from JSONL file."""
        if not path.exists():
            return None

        header: dict[str, Any] = {}
        events: list[ExecutionEvent] = []

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if obj.get("type") == "header":
                    header = obj
                elif obj.get("type") == "event":
                    events.append(ExecutionEvent.from_dict(obj))

        if not header:
            return None

        rec = ExecutionRecording(
            recording_id=header.get("recording_id", ""),
            session_id=header.get("session_id", ""),
            agent_name=header.get("agent_name", ""),
            model=header.get("model", ""),
            started_at=header.get("started_at", 0.0),
            finished_at=header.get("finished_at", 0.0),
            seed=header.get("seed"),
            temperature=header.get("temperature", 0.0),
            success=header.get("success", False),
            metadata=header.get("metadata", {}),
        )
        rec.events = events
        self._recordings[rec.recording_id] = rec
        return rec

    # -- Stats --

    def stats(self) -> dict[str, Any]:
        recs = list(self._recordings.values())
        return {
            "total_recordings": len(recs),
            "total_events": sum(r.event_count for r in recs),
            "completed": sum(1 for r in recs if r.finished_at > 0),
            "successful": sum(1 for r in recs if r.success),
        }
