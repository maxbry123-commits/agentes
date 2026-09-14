"""Replay Engine — Reproduce recorded agent runs deterministically.

Provides:
  - ReplayEngine:    Replays a recording by feeding recorded LLM/tool responses
  - ReplayDiff:      Compares original recording with a replay result
  - ReplayResult:    Structured result of a replay run

The replay engine mocks LLM calls and tool executions using the recorded
data, allowing exact reproduction and "what-if" analysis.

Architecture: §17.2 (Deterministic Replay)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from cognithor.telemetry.recorder import EventType, ExecutionEvent, ExecutionRecording
from cognithor.utils.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Diff Types
# ---------------------------------------------------------------------------


class DiffType(StrEnum):
    """Type of difference between original and replay."""

    MATCH = "match"
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    REORDERED = "reordered"


@dataclass
class DiffEntry:
    """A single difference between original and replay."""

    diff_type: DiffType
    event_type: str
    sequence: int
    original: dict[str, Any] = field(default_factory=dict)
    replay: dict[str, Any] = field(default_factory=dict)
    field_name: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "diff_type": self.diff_type.value,
            "event_type": self.event_type,
            "sequence": self.sequence,
            "field_name": self.field_name,
            "description": self.description,
            "original": self.original,
            "replay": self.replay,
        }


# ---------------------------------------------------------------------------
# Replay Result
# ---------------------------------------------------------------------------


@dataclass
class ReplayResult:
    """Result of replaying an execution recording."""

    recording_id: str
    replayed_at: float = field(default_factory=time.time)
    events: list[ExecutionEvent] = field(default_factory=list)
    duration_ms: float = 0.0
    success: bool = False
    deterministic: bool = True  # True if replay matches original exactly
    diffs: list[DiffEntry] = field(default_factory=list)
    error: str = ""

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def diff_count(self) -> int:
        return len(self.diffs)

    @property
    def match_count(self) -> int:
        return sum(1 for d in self.diffs if d.diff_type == DiffType.MATCH)

    @property
    def mismatch_count(self) -> int:
        return sum(1 for d in self.diffs if d.diff_type != DiffType.MATCH)

    @property
    def match_rate(self) -> float:
        total = len(self.diffs)
        if total == 0:
            return 100.0
        return self.match_count / total * 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "recording_id": self.recording_id,
            "replayed_at": self.replayed_at,
            "event_count": self.event_count,
            "duration_ms": round(self.duration_ms, 1),
            "success": self.success,
            "deterministic": self.deterministic,
            "match_rate": round(self.match_rate, 1),
            "diff_count": self.diff_count,
            "diffs": [d.to_dict() for d in self.diffs],
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Replay Engine
# ---------------------------------------------------------------------------


class ReplayEngine:
    """Replays a recorded execution using mocked LLM and tool responses.

    The engine walks through the recorded events and:
    1. For LLM_REQUEST: returns the recorded LLM_RESPONSE
    2. For TOOL_CALL: returns the recorded TOOL_RESULT
    3. For other events: replays them as-is

    This allows deterministic reproduction and "what-if" analysis
    by injecting modified responses.

    Usage::

        engine = ReplayEngine()
        result = engine.replay(recording)
        print(f"Deterministic: {result.deterministic}")
        print(f"Match rate: {result.match_rate}%")

        # With overrides (what-if analysis)
        result = engine.replay(recording, overrides={
            "0003": {"data": {"response": "Different LLM output"}},
        })
    """

    def __init__(self) -> None:
        self._results: list[ReplayResult] = []

    def replay(
        self,
        recording: ExecutionRecording,
        *,
        overrides: dict[str, dict[str, Any]] | None = None,
    ) -> ReplayResult:
        """Replay a recorded execution.

        Args:
            recording: The recording to replay.
            overrides: Optional dict of event_id → modified data.
                       Used for "what-if" analysis.

        Returns:
            ReplayResult with events and diffs.
        """
        start = time.monotonic()
        overrides = overrides or {}
        replayed_events: list[ExecutionEvent] = []

        # Build lookup for recorded responses
        response_map = self._build_response_map(recording)

        try:
            for event in recording.events:
                # Check for override
                short_id = (
                    event.event_id.split(":")[-1] if ":" in event.event_id else event.event_id
                )
                override = overrides.get(short_id) or overrides.get(event.event_id)

                if override:
                    # Apply override
                    replayed_event = ExecutionEvent(
                        event_id=f"replay:{event.event_id}",
                        event_type=event.event_type,
                        timestamp=time.time(),
                        sequence=event.sequence,
                        data={**event.data, **override.get("data", {})},
                        parent_event_id=event.parent_event_id,
                        iteration=event.iteration,
                        duration_ms=event.duration_ms,
                    )
                else:
                    # Replay as recorded (for LLM/tool: use recorded response)
                    replayed_event = self._replay_event(event, response_map)

                replayed_events.append(replayed_event)

            elapsed = (time.monotonic() - start) * 1000
            result = ReplayResult(
                recording_id=recording.recording_id,
                events=replayed_events,
                duration_ms=elapsed,
                success=True,
            )

            # Compute diffs
            result.diffs = self._compute_diffs(recording.events, replayed_events)
            result.deterministic = all(d.diff_type == DiffType.MATCH for d in result.diffs)

        except Exception as exc:
            result = ReplayResult(
                recording_id=recording.recording_id,
                duration_ms=(time.monotonic() - start) * 1000,
                success=False,
                error=str(exc),
            )

        self._results.append(result)
        log.info(
            "replay_completed",
            recording_id=recording.recording_id,
            events=result.event_count,
            deterministic=result.deterministic,
            match_rate=round(result.match_rate, 1),
        )
        return result

    def replay_from_iteration(
        self,
        recording: ExecutionRecording,
        start_iteration: int,
        *,
        overrides: dict[str, dict[str, Any]] | None = None,
    ) -> ReplayResult:
        """Replay only from a specific iteration onward.

        Useful for debugging: "What would happen if iteration 3 went differently?"
        """
        filtered = ExecutionRecording(
            recording_id=f"{recording.recording_id}:from_{start_iteration}",
            session_id=recording.session_id,
            agent_name=recording.agent_name,
            model=recording.model,
            started_at=recording.started_at,
            seed=recording.seed,
            temperature=recording.temperature,
            metadata=recording.metadata,
        )
        filtered.events = [e for e in recording.events if e.iteration >= start_iteration]
        return self.replay(filtered, overrides=overrides)

    def get_llm_responses(self, recording: ExecutionRecording) -> list[ExecutionEvent]:
        """Extract all LLM responses from a recording for analysis."""
        return [e for e in recording.events if e.event_type == EventType.LLM_RESPONSE]

    def get_tool_results(self, recording: ExecutionRecording) -> list[ExecutionEvent]:
        """Extract all tool results from a recording."""
        return [e for e in recording.events if e.event_type == EventType.TOOL_RESULT]

    @property
    def results(self) -> list[ReplayResult]:
        return list(self._results)

    def stats(self) -> dict[str, Any]:
        return {
            "total_replays": len(self._results),
            "deterministic": sum(1 for r in self._results if r.deterministic),
            "non_deterministic": sum(1 for r in self._results if not r.deterministic),
            "avg_match_rate": (
                round(sum(r.match_rate for r in self._results) / len(self._results), 1)
                if self._results
                else 0.0
            ),
        }

    # -- Internal --

    @staticmethod
    def _build_response_map(
        recording: ExecutionRecording,
    ) -> dict[str, ExecutionEvent]:
        """Build a map of request → response for LLM and tool events."""
        response_map: dict[str, ExecutionEvent] = {}
        pending_requests: list[ExecutionEvent] = []

        for event in recording.events:
            if event.event_type in (EventType.LLM_REQUEST, EventType.TOOL_CALL):
                pending_requests.append(event)
            elif (
                event.event_type in (EventType.LLM_RESPONSE, EventType.TOOL_RESULT)
                and pending_requests
            ):
                request = pending_requests.pop(0)
                response_map[request.event_id] = event

        return response_map

    @staticmethod
    def _replay_event(
        event: ExecutionEvent,
        response_map: dict[str, ExecutionEvent],
    ) -> ExecutionEvent:
        """Replay a single event, using recorded response if available."""
        return ExecutionEvent(
            event_id=f"replay:{event.event_id}",
            event_type=event.event_type,
            timestamp=time.time(),
            sequence=event.sequence,
            data=dict(event.data),
            parent_event_id=event.parent_event_id,
            iteration=event.iteration,
            duration_ms=event.duration_ms,
        )

    @staticmethod
    def _compute_diffs(
        original: list[ExecutionEvent],
        replayed: list[ExecutionEvent],
    ) -> list[DiffEntry]:
        """Compare original and replayed event sequences."""
        diffs: list[DiffEntry] = []

        max_len = max(len(original), len(replayed))
        for i in range(max_len):
            orig = original[i] if i < len(original) else None
            repl = replayed[i] if i < len(replayed) else None

            if orig and not repl:
                diffs.append(
                    DiffEntry(
                        diff_type=DiffType.REMOVED,
                        event_type=orig.event_type.value,
                        sequence=orig.sequence,
                        original=orig.to_dict(),
                        description=f"Event removed: {orig.event_type.value}",
                    )
                )
            elif repl and not orig:
                diffs.append(
                    DiffEntry(
                        diff_type=DiffType.ADDED,
                        event_type=repl.event_type.value,
                        sequence=repl.sequence,
                        replay=repl.to_dict(),
                        description=f"Event added: {repl.event_type.value}",
                    )
                )
            elif orig and repl:
                # Compare data (ignore timestamps and event_ids which differ)
                if orig.event_type != repl.event_type:
                    diffs.append(
                        DiffEntry(
                            diff_type=DiffType.MODIFIED,
                            event_type=orig.event_type.value,
                            sequence=orig.sequence,
                            original=orig.to_dict(),
                            replay=repl.to_dict(),
                            field_name="event_type",
                            description=f"Type changed: {orig.event_type} → {repl.event_type}",
                        )
                    )
                elif orig.data != repl.data:
                    changed_fields = _diff_dicts(orig.data, repl.data)
                    diffs.append(
                        DiffEntry(
                            diff_type=DiffType.MODIFIED,
                            event_type=orig.event_type.value,
                            sequence=orig.sequence,
                            original={"data": orig.data},
                            replay={"data": repl.data},
                            field_name=", ".join(changed_fields),
                            description=f"Data changed in fields: {', '.join(changed_fields)}",
                        )
                    )
                else:
                    diffs.append(
                        DiffEntry(
                            diff_type=DiffType.MATCH,
                            event_type=orig.event_type.value,
                            sequence=orig.sequence,
                        )
                    )

        return diffs


# ---------------------------------------------------------------------------
# Diff Helpers
# ---------------------------------------------------------------------------


class ReplayDiff:
    """Utility class for comparing execution recordings.

    Provides higher-level diff operations beyond event-by-event comparison.
    """

    @staticmethod
    def compare(
        original: ExecutionRecording,
        replay_result: ReplayResult,
    ) -> dict[str, Any]:
        """High-level comparison between original and replay."""
        orig_tools = [
            e.data.get("tool", "") for e in original.events if e.event_type == EventType.TOOL_CALL
        ]
        replay_tools = [
            e.data.get("tool", "")
            for e in replay_result.events
            if e.event_type == EventType.TOOL_CALL
        ]

        orig_plans = [e for e in original.events if e.event_type == EventType.PLAN_GENERATED]
        replay_plans = [e for e in replay_result.events if e.event_type == EventType.PLAN_GENERATED]

        return {
            "deterministic": replay_result.deterministic,
            "match_rate": round(replay_result.match_rate, 1),
            "event_count": {
                "original": original.event_count,
                "replay": replay_result.event_count,
            },
            "tool_calls": {
                "original": orig_tools,
                "replay": replay_tools,
                "same_sequence": orig_tools == replay_tools,
            },
            "plans": {
                "original_count": len(orig_plans),
                "replay_count": len(replay_plans),
            },
            "iterations": {
                "original": original.iteration_count,
                "replay": max((e.iteration for e in replay_result.events), default=0),
            },
        }

    @staticmethod
    def summary(diffs: list[DiffEntry]) -> dict[str, Any]:
        """Summarize a list of diff entries."""
        by_type: dict[str, int] = {}
        by_event: dict[str, int] = {}
        for d in diffs:
            by_type[d.diff_type.value] = by_type.get(d.diff_type.value, 0) + 1
            if d.diff_type != DiffType.MATCH:
                by_event[d.event_type] = by_event.get(d.event_type, 0) + 1
        return {
            "total_diffs": len(diffs),
            "matches": by_type.get("match", 0),
            "mismatches": sum(v for k, v in by_type.items() if k != "match"),
            "by_type": by_type,
            "changed_event_types": by_event,
        }


def _diff_dicts(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Find keys that differ between two dicts."""
    changed: list[str] = []
    all_keys = set(a.keys()) | set(b.keys())
    for key in sorted(all_keys):
        if a.get(key) != b.get(key):
            changed.append(key)
    return changed
