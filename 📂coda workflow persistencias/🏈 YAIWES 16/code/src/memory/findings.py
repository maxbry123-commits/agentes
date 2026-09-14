"""
Structured memory for the agent — accumulates findings,
tracks hypotheses, and provides context for Claude.
"""

from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class Finding:
    """A single discovered fact about the target."""
    category: str        # port, service, path, vulnerability, credential, flag
    value: str           # the actual finding
    source_command: str   # what command produced this
    confidence: str      # high, medium, low
    phase: str           # which phase discovered it
    notes: str = ""


class FindingsStore:
    """
    Accumulates and retrieves findings across phases.
    Provides structured context injection for Claude prompts.
    """

    def __init__(self):
        self.findings: list[Finding] = []
        self.hypotheses: list[dict] = []  # {hypothesis, status, evidence}
        self.dead_ends: list[dict] = []   # {approach, reason, phase}

    def add_finding(self, finding: Finding) -> None:
        """Add a new finding, avoiding exact duplicates."""
        for existing in self.findings:
            if existing.category == finding.category and existing.value == finding.value:
                return  # Skip duplicate
        self.findings.append(finding)

    def add_hypothesis(self, hypothesis: str, evidence: str = "") -> None:
        """Add a new attack hypothesis to explore."""
        self.hypotheses.append({
            "hypothesis": hypothesis,
            "status": "untested",
            "evidence": evidence,
        })

    def update_hypothesis(self, hypothesis: str, status: str, result: str = "") -> None:
        """Update status of a hypothesis (confirmed, rejected, partial)."""
        for h in self.hypotheses:
            if h["hypothesis"] == hypothesis:
                h["status"] = status
                h["evidence"] += f" | {result}" if result else ""
                if status == "rejected":
                    self.dead_ends.append({
                        "approach": hypothesis,
                        "reason": result,
                    })
                return

    def get_by_category(self, category: str) -> list[Finding]:
        return [f for f in self.findings if f.category == category]

    def get_context_for_prompt(self) -> str:
        """Format all findings for injection into Claude's context."""
        sections = []

        # Group findings by category
        categories = {}
        for f in self.findings:
            categories.setdefault(f.category, []).append(f)

        for cat, items in categories.items():
            section = f"[{cat.upper()}]\n"
            for item in items:
                section += f"  • {item.value} (confidence: {item.confidence}, from: {item.source_command})\n"
                if item.notes:
                    section += f"    Note: {item.notes}\n"
            sections.append(section)

        # Active hypotheses
        active = [h for h in self.hypotheses if h["status"] == "untested"]
        if active:
            section = "[UNTESTED HYPOTHESES]\n"
            for h in active:
                section += f"  ? {h['hypothesis']}"
                if h["evidence"]:
                    section += f" (evidence: {h['evidence']})"
                section += "\n"
            sections.append(section)

        # Dead ends
        if self.dead_ends:
            section = "[DEAD ENDS — DO NOT RETRY]\n"
            for d in self.dead_ends:
                section += f"  ✗ {d['approach']}: {d['reason']}\n"
            sections.append(section)

        return "\n".join(sections) if sections else "(No findings yet)"

    def to_dict(self) -> dict:
        """Serialize for reporting."""
        return {
            "findings": [
                {
                    "category": f.category,
                    "value": f.value,
                    "source_command": f.source_command,
                    "confidence": f.confidence,
                    "phase": f.phase,
                    "notes": f.notes,
                }
                for f in self.findings
            ],
            "hypotheses": self.hypotheses,
            "dead_ends": self.dead_ends,
        }