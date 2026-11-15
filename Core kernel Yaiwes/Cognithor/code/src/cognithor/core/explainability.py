"""Cognithor - Explainability Layer.

Transparent decision path for business-critical tasks:

  - DecisionTrail:       Step-by-step protocol of the decision path
  - SourceAttribution:   Source attribution for each claim
  - TrustScoreCalculator: Calculates trustworthiness of a response
  - ExplainabilityEngine: Orchestrates tracking and reporting

Architecture reference: §16 (Explainability), §13 (Transparency)

Explainability promotes:
  - Trust in business-critical decisions
  - Error analysis and debugging
  - Compliance with EU AI Act Art. 13 (Transparency)
  - Quality control of agent outputs
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ============================================================================
# Enums
# ============================================================================


class StepType(Enum):
    """Type of a decision step."""

    INPUT_RECEIVED = "input_received"
    AGENT_SELECTED = "agent_selected"
    TOOL_CALLED = "tool_called"
    MEMORY_RETRIEVED = "memory_retrieved"
    REASONING = "reasoning"
    PLANNING = "planning"
    SKILL_EXECUTED = "skill_executed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    OUTPUT_GENERATED = "output_generated"
    DELEGATION = "delegation"
    ERROR = "error"


class SourceType(Enum):
    """Type of an information source."""

    MEMORY_SEMANTIC = "memory_semantic"
    MEMORY_EPISODIC = "memory_episodic"
    MEMORY_PROCEDURAL = "memory_procedural"
    TOOL_OUTPUT = "tool_output"
    WEB_SEARCH = "web_search"
    FILE_CONTENT = "file_content"
    USER_INPUT = "user_input"
    MODEL_KNOWLEDGE = "model_knowledge"
    SKILL_RESULT = "skill_result"


class TrustLevel(Enum):
    """Trust level of a response."""

    VERY_HIGH = "very_high"  # 90-100%: Verified, multi-source
    HIGH = "high"  # 70-89%: Reliable sources
    MODERATE = "moderate"  # 50-69%: Single source or unverified
    LOW = "low"  # 30-49%: Model knowledge only
    VERY_LOW = "very_low"  # 0-29%: Speculative


# ============================================================================
# Decision-Trail
# ============================================================================


@dataclass
class TrailStep:
    """A single step in the decision path."""

    step_id: str
    step_type: StepType
    timestamp: str
    description: str
    agent_id: str = ""
    duration_ms: int = 0
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "timestamp": self.timestamp,
            "description": self.description,
            "agent_id": self.agent_id,
            "duration_ms": self.duration_ms,
            "confidence": self.confidence,
        }


@dataclass
class DecisionTrail:
    """Complete decision path of an agent interaction.

    Records every step from input to output
    with timestamps, involved agents and duration.
    """

    trail_id: str
    request_id: str = ""
    agent_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    steps: list[TrailStep] = field(default_factory=list)
    total_duration_ms: int = 0
    final_confidence: float = 0.0

    def add_step(
        self,
        step_type: StepType,
        description: str,
        *,
        agent_id: str = "",
        duration_ms: int = 0,
        confidence: float = 0.0,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TrailStep:
        """Add a step to the trail."""
        step = TrailStep(
            step_id=f"{self.trail_id}-{len(self.steps):03d}",
            step_type=step_type,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            description=description,
            agent_id=agent_id or self.agent_id,
            duration_ms=duration_ms,
            confidence=confidence,
            inputs=inputs or {},
            outputs=outputs or {},
            metadata=metadata or {},
        )
        self.steps.append(step)
        return step

    def complete(self) -> None:
        """Mark the trail as completed."""
        self.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.total_duration_ms = sum(s.duration_ms for s in self.steps)
        if self.steps:
            self.final_confidence = self.steps[-1].confidence

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def tools_used(self) -> list[str]:
        return [s.description for s in self.steps if s.step_type == StepType.TOOL_CALLED]

    @property
    def agents_involved(self) -> list[str]:
        return list(set(s.agent_id for s in self.steps if s.agent_id))

    @property
    def had_approval(self) -> bool:
        return any(
            s.step_type in (StepType.APPROVAL_REQUESTED, StepType.APPROVAL_GRANTED)
            for s in self.steps
        )

    @property
    def had_errors(self) -> bool:
        return any(s.step_type == StepType.ERROR for s in self.steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trail_id": self.trail_id,
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "step_count": self.step_count,
            "total_duration_ms": self.total_duration_ms,
            "final_confidence": self.final_confidence,
            "tools_used": self.tools_used,
            "agents_involved": self.agents_involved,
            "had_approval": self.had_approval,
            "had_errors": self.had_errors,
            "steps": [s.to_dict() for s in self.steps],
        }

    def to_human_readable(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"Entscheidungsweg {self.trail_id}",
            f"Agent: {self.agent_id}",
            f"Schritte: {self.step_count}, Dauer: {self.total_duration_ms}ms",
            f"Vertrauen: {self.final_confidence:.0%}",
            "",
        ]
        for i, step in enumerate(self.steps, 1):
            icon = _STEP_ICONS.get(step.step_type, "•")
            lines.append(f"  {i}. {icon} {step.description} ({step.duration_ms}ms)")
        return "\n".join(lines)


# ============================================================================
# Source-Attribution
# ============================================================================


@dataclass
class SourceReference:
    """Reference to an information source."""

    source_id: str
    source_type: SourceType
    title: str
    content_preview: str = ""
    relevance_score: float = 0.0
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "title": self.title,
            "content_preview": self.content_preview[:100],
            "relevance_score": self.relevance_score,
        }


class SourceAttribution:
    """Source attribution for agent outputs.

    Links each claim in the output with the
    sources that support it. Fulfills EU AI Act Art. 13.
    """

    def __init__(self) -> None:
        self._sources: dict[str, list[SourceReference]] = {}

    def add_source(
        self,
        claim_id: str,
        source: SourceReference,
    ) -> None:
        """Link a source with a claim."""
        if claim_id not in self._sources:
            self._sources[claim_id] = []
        self._sources[claim_id].append(source)

    def get_sources(self, claim_id: str) -> list[SourceReference]:
        return self._sources.get(claim_id, [])

    def all_sources(self) -> dict[str, list[SourceReference]]:
        return dict(self._sources)

    @property
    def claim_count(self) -> int:
        return len(self._sources)

    @property
    def total_sources(self) -> int:
        return sum(len(v) for v in self._sources.values())

    def source_diversity(self) -> dict[str, int]:
        """Count how many sources were used per type."""
        counts: dict[str, int] = {}
        for sources in self._sources.values():
            for s in sources:
                key = s.source_type.value
                counts[key] = counts.get(key, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_count": self.claim_count,
            "total_sources": self.total_sources,
            "diversity": self.source_diversity(),
            "claims": {k: [s.to_dict() for s in v] for k, v in self._sources.items()},
        }


# ============================================================================
# Trust-Score-Calculator
# ============================================================================


class TrustScoreCalculator:
    """Calculate trustworthiness of a response.

    Factors:
    - Source diversity (multi-source confirmation)
    - Source type reliability
    - Recency of sources
    - Human approval
    - Consistency (no contradictions)
    """

    # Reliability weights per source type
    SOURCE_WEIGHTS: dict[SourceType, float] = {
        SourceType.USER_INPUT: 0.95,
        SourceType.MEMORY_PROCEDURAL: 0.85,
        SourceType.FILE_CONTENT: 0.80,
        SourceType.TOOL_OUTPUT: 0.75,
        SourceType.WEB_SEARCH: 0.70,
        SourceType.MEMORY_SEMANTIC: 0.65,
        SourceType.MEMORY_EPISODIC: 0.60,
        SourceType.SKILL_RESULT: 0.70,
        SourceType.MODEL_KNOWLEDGE: 0.50,
    }

    def __init__(self) -> None:
        self._weights = dict(self.SOURCE_WEIGHTS)

    def calculate(
        self,
        *,
        sources: list[SourceReference] | None = None,
        human_approved: bool = False,
        contradictions_found: int = 0,
        trail: DecisionTrail | None = None,
    ) -> tuple[float, TrustLevel, dict[str, Any]]:
        """Calculate the trust score.

        Returns:
            Tupel aus (score 0.0-1.0, TrustLevel, Breakdown-Dict)
        """
        components: dict[str, float] = {}

        # 1. Quellen-Score (0-0.4)
        if sources:
            source_scores = [
                self._weights.get(s.source_type, 0.5) * s.relevance_score for s in sources
            ]
            avg_source = sum(source_scores) / len(source_scores) if source_scores else 0
            diversity_bonus = min(len(set(s.source_type for s in sources)) * 0.05, 0.15)
            components["sources"] = min(avg_source + diversity_bonus, 0.4)
        else:
            components["sources"] = 0.1

        # 2. Multi-source confirmation (0-0.2)
        source_count = len(sources) if sources else 0
        components["multi_source"] = min(source_count * 0.05, 0.2)

        # 3. Human approval (0-0.2)
        components["human_approval"] = 0.2 if human_approved else 0.0

        # 4. Consistency (0-0.1)
        if contradictions_found == 0:
            components["consistency"] = 0.1
        else:
            components["consistency"] = max(0, 0.1 - contradictions_found * 0.03)

        # 5. Trail quality (0-0.1)
        if trail:
            has_tools = bool(trail.tools_used)
            has_memory = any(s.step_type == StepType.MEMORY_RETRIEVED for s in trail.steps)
            no_errors = not trail.had_errors
            trail_score = sum(
                [
                    0.03 if has_tools else 0,
                    0.03 if has_memory else 0,
                    0.04 if no_errors else 0,
                ]
            )
            components["trail_quality"] = trail_score
        else:
            components["trail_quality"] = 0.0

        total = sum(components.values())
        total = min(max(total, 0.0), 1.0)

        # Determine trust level
        if total >= 0.9:
            level = TrustLevel.VERY_HIGH
        elif total >= 0.7:
            level = TrustLevel.HIGH
        elif total >= 0.5:
            level = TrustLevel.MODERATE
        elif total >= 0.3:
            level = TrustLevel.LOW
        else:
            level = TrustLevel.VERY_LOW

        breakdown = {
            "total_score": round(total, 3),
            "trust_level": level.value,
            "components": {k: round(v, 3) for k, v in components.items()},
        }
        return total, level, breakdown


# ============================================================================
# Explainability Engine: Orchestrates everything
# ============================================================================


class ExplainabilityEngine:
    """Central engine for transparency and traceability.

    Creates and manages decision trails, source attributions
    and trust scores for all agent interactions.
    """

    def __init__(self, max_trails: int = 1_000) -> None:
        self._trails: dict[str, DecisionTrail] = {}
        self._max_trails = max_trails
        self._trust_calculator = TrustScoreCalculator()
        self._total_requests = 0

    def start_trail(
        self,
        request_id: str,
        agent_id: str = "",
    ) -> DecisionTrail:
        """Start a new decision trail."""
        trail_id = hashlib.sha256(f"{request_id}-{time.time()}".encode()).hexdigest()[:16]

        trail = DecisionTrail(
            trail_id=trail_id,
            request_id=request_id,
            agent_id=agent_id,
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        self._trails[trail_id] = trail
        self._total_requests += 1

        # Cleanup on overflow
        if len(self._trails) > self._max_trails:
            oldest_key = next(iter(self._trails))
            del self._trails[oldest_key]

        return trail

    def get_trail(self, trail_id: str) -> DecisionTrail | None:
        return self._trails.get(trail_id)

    def complete_trail(
        self,
        trail_id: str,
        *,
        sources: list[SourceReference] | None = None,
        human_approved: bool = False,
        contradictions: int = 0,
    ) -> tuple[DecisionTrail | None, dict[str, Any]]:
        """Complete a trail and calculate trust score."""
        trail = self._trails.get(trail_id)
        if not trail:
            return None, {}

        trail.complete()

        score, level, breakdown = self._trust_calculator.calculate(
            sources=sources,
            human_approved=human_approved,
            contradictions_found=contradictions,
            trail=trail,
        )

        trail.final_confidence = score

        return trail, breakdown

    def record_decision(
        self,
        trail_id: str,
        *,
        tool_name: str,
        gate_status: str,
        risk_level: str,
        reason: str,
        outcome: str,
        duration_ms: int = 0,
        success: bool = True,
    ) -> None:
        """Record a gatekeeper decision + execution outcome into a trail.

        Called from the PGE loop after each tool execution. Creates a
        :class:`TrailStep` that captures both the gatekeeper verdict and
        the runtime result, making every decision auditable and explainable.
        """
        trail = self._trails.get(trail_id)
        if trail is None:
            return

        if gate_status == "block":
            step_type = StepType.APPROVAL_DENIED
        elif not success:
            step_type = StepType.ERROR
        else:
            step_type = StepType.TOOL_CALLED

        trail.add_step(
            step_type,
            description=tool_name,
            duration_ms=duration_ms,
            confidence=1.0 if success else 0.0,
            inputs={"gate_status": gate_status, "risk_level": risk_level},
            outputs={"outcome": outcome[:500]},
            metadata={"reason": reason[:200]},
        )

    def recent_trails(self, limit: int = 20) -> list[DecisionTrail]:
        trails = list(self._trails.values())
        return trails[-limit:]

    def trails_by_agent(self, agent_id: str) -> list[DecisionTrail]:
        return [t for t in self._trails.values() if t.agent_id == agent_id]

    def low_trust_trails(self, threshold: float = 0.5) -> list[DecisionTrail]:
        return [
            t for t in self._trails.values() if t.final_confidence < threshold and t.completed_at
        ]

    def stats(self) -> dict[str, Any]:
        completed = [t for t in self._trails.values() if t.completed_at]
        avg_confidence = (
            round(sum(t.final_confidence for t in completed) / len(completed), 3)
            if completed
            else 0.0
        )
        avg_steps = (
            round(sum(t.step_count for t in completed) / len(completed), 1) if completed else 0.0
        )

        return {
            "total_requests": self._total_requests,
            "active_trails": len(self._trails),
            "completed_trails": len(completed),
            "avg_confidence": avg_confidence,
            "avg_steps": avg_steps,
            "low_trust_count": len(self.low_trust_trails()),
            "unique_agents": len(set(t.agent_id for t in self._trails.values())),
        }


# ============================================================================
# Icon-Mapping
# ============================================================================

_STEP_ICONS: dict[StepType, str] = {
    StepType.INPUT_RECEIVED: "📥",
    StepType.AGENT_SELECTED: "🤖",
    StepType.TOOL_CALLED: "🔧",
    StepType.MEMORY_RETRIEVED: "🧠",
    StepType.REASONING: "💭",
    StepType.PLANNING: "📋",
    StepType.SKILL_EXECUTED: "⚡",
    StepType.APPROVAL_REQUESTED: "❓",
    StepType.APPROVAL_GRANTED: "✅",
    StepType.APPROVAL_DENIED: "❌",
    StepType.OUTPUT_GENERATED: "📤",
    StepType.DELEGATION: "🔄",
    StepType.ERROR: "⚠️",
}
