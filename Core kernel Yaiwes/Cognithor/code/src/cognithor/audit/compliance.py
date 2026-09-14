"""Cognithor · Compliance & Audit-Report Framework.

EU AI Act compliant audit reports with:

  - ComplianceFramework:  Regulatory checks (GDPR, EU AI Act)
  - DecisionLog:          Traceable decision logs
  - ComplianceReport:     Structured reports with risk scores
  - ReportExporter:       Export as JSON, CSV, Markdown
  - RemediationTracker:   Tracking open measures with deadlines

Architecture Bible: §14.6 (Compliance), §15 (Regulation)

EU AI Act requirements:
  - Art. 9: Risk management system
  - Art. 12: Record-keeping obligations
  - Art. 13: Transparency requirements
  - Art. 14: Human oversight
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


class RiskLevel(Enum):
    """EU AI Act risk classification."""

    MINIMAL = "minimal"  # Art. 6: Minimal risk
    LIMITED = "limited"  # Art. 6: Limited risk
    HIGH = "high"  # Art. 6: High risk
    UNACCEPTABLE = "unacceptable"  # Art. 5: Prohibited practices


class ComplianceStatus(Enum):
    """Status of a compliance check."""

    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"


class RemediationStatus(Enum):
    """Status of a remediation measure."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    OVERDUE = "overdue"
    WAIVED = "waived"


# ============================================================================
# Decision Log: Decision records
# ============================================================================


@dataclass
class DecisionRecord:
    """Recorded agent decision."""

    decision_id: str
    agent_id: str
    timestamp: str
    action: str
    reasoning: str
    inputs_summary: str = ""
    tools_used: list[str] = field(default_factory=list)
    sources_cited: list[str] = field(default_factory=list)
    confidence: float = 0.0
    human_approved: bool = False
    risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "reasoning": self.reasoning,
            "inputs_summary": self.inputs_summary,
            "tools_used": self.tools_used,
            "sources_cited": self.sources_cited,
            "confidence": self.confidence,
            "human_approved": self.human_approved,
            "risk_flags": self.risk_flags,
        }


class DecisionLog:
    """Traceable decision logs for all agents.

    Fulfils EU AI Act Art. 12 (record-keeping obligations):
    Every agent decision is logged with context, reasoning,
    and sources.
    """

    def __init__(self, max_entries: int = 10_000) -> None:
        self._entries: list[DecisionRecord] = []
        self._max = max_entries

    @property
    def count(self) -> int:
        return len(self._entries)

    def log(self, record: DecisionRecord) -> None:
        """Records a decision."""
        self._entries.append(record)
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max :]

    def query(
        self,
        *,
        agent_id: str = "",
        action: str = "",
        since: str = "",
        has_risk_flags: bool = False,
        limit: int = 100,
    ) -> list[DecisionRecord]:
        """Searches the decision log."""
        results = self._entries

        if agent_id:
            results = [r for r in results if r.agent_id == agent_id]
        if action:
            results = [r for r in results if action in r.action]
        if since:
            results = [r for r in results if r.timestamp >= since]
        if has_risk_flags:
            results = [r for r in results if r.risk_flags]

        return results[-limit:]

    def flagged_decisions(self) -> list[DecisionRecord]:
        """Returns all decisions with risk flags."""
        return [r for r in self._entries if r.risk_flags]

    def approval_rate(self) -> float:
        """Proportion of human-approved decisions."""
        if not self._entries:
            return 0.0
        approved = sum(1 for r in self._entries if r.human_approved)
        return round((approved / len(self._entries)) * 100, 1)

    def stats(self) -> dict[str, Any]:
        return {
            "total_decisions": len(self._entries),
            "flagged_count": len(self.flagged_decisions()),
            "approval_rate": self.approval_rate(),
            "unique_agents": len(set(r.agent_id for r in self._entries)),
            "avg_confidence": (
                round(sum(r.confidence for r in self._entries) / len(self._entries), 2)
                if self._entries
                else 0.0
            ),
        }


# ============================================================================
# Compliance Check: Regulatory checks
# ============================================================================


@dataclass
class ComplianceCheck:
    """A single compliance check."""

    check_id: str
    regulation: str  # e.g. "EU-AI-Act Art. 12"
    requirement: str
    description: str
    status: ComplianceStatus = ComplianceStatus.NOT_ASSESSED
    evidence: str = ""
    risk_level: RiskLevel = RiskLevel.LIMITED
    remediation: str = ""
    assessed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "regulation": self.regulation,
            "requirement": self.requirement,
            "status": self.status.value,
            "risk_level": self.risk_level.value,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "assessed_at": self.assessed_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


# Standard EU AI Act compliance checks
_EU_AI_ACT_CHECKS: list[ComplianceCheck] = [
    ComplianceCheck(
        check_id="EUAIA-9.1",
        regulation="EU-AI-Act Art. 9",
        requirement="Risikomanagement-System",
        description="Ein Risikomanagement-System muss eingerichtet und dokumentiert sein.",
        risk_level=RiskLevel.HIGH,
    ),
    ComplianceCheck(
        check_id="EUAIA-9.2",
        regulation="EU-AI-Act Art. 9",
        requirement="Risikobewertung",
        description="Bekannte und vorhersehbare Risiken müssen identifiziert und bewertet werden.",
        risk_level=RiskLevel.HIGH,
    ),
    ComplianceCheck(
        check_id="EUAIA-12.1",
        regulation="EU-AI-Act Art. 12",
        requirement="Automatische Aufzeichnung",
        description="Das System muss Ereignisse automatisch protokollieren (Logs).",
        risk_level=RiskLevel.HIGH,
    ),
    ComplianceCheck(
        check_id="EUAIA-12.2",
        regulation="EU-AI-Act Art. 12",
        requirement="Rückverfolgbarkeit",
        description="Entscheidungen müssen rückverfolgbar und nachvollziehbar sein.",
        risk_level=RiskLevel.HIGH,
    ),
    ComplianceCheck(
        check_id="EUAIA-13.1",
        regulation="EU-AI-Act Art. 13",
        requirement="Transparenz",
        description="Das System muss transparent und verständlich dokumentiert sein.",
        risk_level=RiskLevel.HIGH,
    ),
    ComplianceCheck(
        check_id="EUAIA-14.1",
        regulation="EU-AI-Act Art. 14",
        requirement="Menschliche Aufsicht",
        description="Menschliche Überwachung und Eingriffsmöglichkeit müssen gewährleistet sein.",
        risk_level=RiskLevel.HIGH,
    ),
    ComplianceCheck(
        check_id="EUAIA-14.2",
        regulation="EU-AI-Act Art. 14",
        requirement="Notfallabschaltung",
        description="Ein Kill-Switch oder Notfallabschaltung muss verfügbar sein.",
        risk_level=RiskLevel.HIGH,
    ),
    ComplianceCheck(
        check_id="DSGVO-25.1",
        regulation="DSGVO Art. 25",
        requirement="Datenschutz durch Technikgestaltung",
        description="Privacy-by-Design: Nur notwendige Daten werden verarbeitet.",
        risk_level=RiskLevel.HIGH,
    ),
    ComplianceCheck(
        check_id="DSGVO-32.1",
        regulation="DSGVO Art. 32",
        requirement="Sicherheit der Verarbeitung",
        description="Technische und organisatorische Maßnahmen zum Datenschutz.",
        risk_level=RiskLevel.HIGH,
    ),
    ComplianceCheck(
        check_id="DSGVO-35.1",
        regulation="DSGVO Art. 35",
        requirement="Datenschutz-Folgenabschätzung",
        description="Bei hohem Risiko ist eine DSFA durchzuführen.",
        risk_level=RiskLevel.HIGH,
    ),
]


class ComplianceFramework:
    """Regulatory compliance checks.

    Checks the system against regulatory requirements
    (EU AI Act, GDPR) and creates compliance reports.
    """

    def __init__(
        self,
        *,
        checks: list[ComplianceCheck] | None = None,
    ) -> None:
        self._checks = checks or [_clone_check(c) for c in _EU_AI_ACT_CHECKS]
        self._assessments: dict[str, ComplianceCheck] = {c.check_id: c for c in self._checks}

    @property
    def check_count(self) -> int:
        return len(self._checks)

    def assess(
        self,
        check_id: str,
        status: ComplianceStatus,
        evidence: str = "",
        remediation: str = "",
    ) -> ComplianceCheck | None:
        """Evaluates a compliance check."""
        check = self._assessments.get(check_id)
        if not check:
            return None
        check.status = status
        check.evidence = evidence
        check.remediation = remediation
        check.assessed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return check

    def auto_assess(
        self,
        *,
        has_audit_log: bool = False,
        has_decision_log: bool = False,
        has_kill_switch: bool = False,
        has_encryption: bool = False,
        has_rbac: bool = False,
        has_sandbox: bool = False,
        has_approval_workflow: bool = False,
        has_redteam: bool = False,
    ) -> None:
        """Automatic assessment based on system capabilities."""
        assessments = {
            "EUAIA-9.1": (
                ComplianceStatus.COMPLIANT if has_redteam else ComplianceStatus.PARTIAL,
                "Red-Team-Framework vorhanden" if has_redteam else "Kein Red-Team-Framework",
            ),
            "EUAIA-9.2": (
                ComplianceStatus.COMPLIANT if has_redteam else ComplianceStatus.PARTIAL,
                "Risikobewertung via SecurityScanner" if has_redteam else "",
            ),
            "EUAIA-12.1": (
                ComplianceStatus.COMPLIANT if has_audit_log else ComplianceStatus.NON_COMPLIANT,
                "AuditLogger aktiv" if has_audit_log else "Kein Audit-Log",
            ),
            "EUAIA-12.2": (
                ComplianceStatus.COMPLIANT if has_decision_log else ComplianceStatus.PARTIAL,
                "DecisionLog aktiv" if has_decision_log else "Kein Decision-Log",
            ),
            "EUAIA-13.1": (
                ComplianceStatus.PARTIAL,
                "Dokumentation in Architektur-Bibel vorhanden",
            ),
            "EUAIA-14.1": (
                ComplianceStatus.COMPLIANT if has_approval_workflow else ComplianceStatus.PARTIAL,
                "Approval-Workflow implementiert" if has_approval_workflow else "",
            ),
            "EUAIA-14.2": (
                ComplianceStatus.COMPLIANT if has_kill_switch else ComplianceStatus.NON_COMPLIANT,
                "Kill-Switch vorhanden" if has_kill_switch else "Kein Kill-Switch",
            ),
            "DSGVO-25.1": (
                ComplianceStatus.COMPLIANT if has_sandbox else ComplianceStatus.PARTIAL,
                "Sandbox + Workspace-Isolation" if has_sandbox else "",
            ),
            "DSGVO-32.1": (
                ComplianceStatus.COMPLIANT
                if has_encryption and has_rbac
                else ComplianceStatus.PARTIAL,
                "Verschlüsselung + RBAC" if has_encryption else "",
            ),
            "DSGVO-35.1": (
                ComplianceStatus.NOT_ASSESSED,
                "DSFA muss manuell durchgeführt werden",
            ),
        }

        for check_id, (status, evidence) in assessments.items():
            self.assess(check_id, status, evidence)

    def compliance_score(self) -> float:
        """Calculates the compliance score (0-100)."""
        if not self._checks:
            return 0.0

        weights = {
            ComplianceStatus.COMPLIANT: 1.0,
            ComplianceStatus.PARTIAL: 0.5,
            ComplianceStatus.NON_COMPLIANT: 0.0,
            ComplianceStatus.NOT_ASSESSED: 0.0,
        }

        total = sum(weights.get(c.status, 0) for c in self._checks)
        return round((total / len(self._checks)) * 100, 1)

    def non_compliant_checks(self) -> list[ComplianceCheck]:
        return [c for c in self._checks if c.status == ComplianceStatus.NON_COMPLIANT]

    def generate_report(self) -> ComplianceReport:
        """Creates a complete compliance report."""
        return ComplianceReport(
            report_id=hashlib.sha256(str(time.time()).encode()).hexdigest()[:16],
            framework_name="EU-AI-Act + DSGVO",
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            compliance_score=self.compliance_score(),
            total_checks=len(self._checks),
            compliant=sum(1 for c in self._checks if c.status == ComplianceStatus.COMPLIANT),
            partial=sum(1 for c in self._checks if c.status == ComplianceStatus.PARTIAL),
            non_compliant=sum(
                1 for c in self._checks if c.status == ComplianceStatus.NON_COMPLIANT
            ),
            not_assessed=sum(1 for c in self._checks if c.status == ComplianceStatus.NOT_ASSESSED),
            checks=list(self._checks),
        )

    def stats(self) -> dict[str, Any]:
        return {
            "total_checks": len(self._checks),
            "compliance_score": self.compliance_score(),
            "compliant": sum(1 for c in self._checks if c.status == ComplianceStatus.COMPLIANT),
            "partial": sum(1 for c in self._checks if c.status == ComplianceStatus.PARTIAL),
            "non_compliant": sum(
                1 for c in self._checks if c.status == ComplianceStatus.NON_COMPLIANT
            ),
        }


# ============================================================================
# Compliance-Report
# ============================================================================


@dataclass
class ComplianceReport:
    """Structured compliance report."""

    report_id: str
    framework_name: str
    generated_at: str
    compliance_score: float
    total_checks: int
    compliant: int
    partial: int
    non_compliant: int
    not_assessed: int
    checks: list[ComplianceCheck] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "framework_name": self.framework_name,
            "generated_at": self.generated_at,
            "compliance_score": self.compliance_score,
            "total_checks": self.total_checks,
            "compliant": self.compliant,
            "partial": self.partial,
            "non_compliant": self.non_compliant,
            "not_assessed": self.not_assessed,
            "checks": [c.to_dict() for c in self.checks],
        }


# ============================================================================
# Report-Exporter
# ============================================================================


class ReportExporter:
    """Export functions for compliance reports.

    Exports as JSON, CSV, or Markdown for auditors
    and regulatory documentation.
    """

    @staticmethod
    def to_json(report: ComplianceReport) -> str:
        """Exports as JSON string."""
        import json

        return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)

    @staticmethod
    def to_csv(report: ComplianceReport) -> str:
        """Exports as CSV string."""
        lines = ["Check-ID;Regulierung;Anforderung;Status;Risiko;Evidenz;Bewertungsdatum"]
        for c in report.checks:
            lines.append(
                f"{c.check_id};{c.regulation};{c.requirement};"
                f"{c.status.value};{c.risk_level.value};"
                f"{c.evidence};{c.assessed_at}"
            )
        return "\n".join(lines)

    @staticmethod
    def to_markdown(report: ComplianceReport) -> str:
        """Exports as Markdown report."""
        status_emoji = {
            "compliant": "✅",
            "partial": "⚠️",
            "non_compliant": "❌",
            "not_assessed": "❓",
        }

        lines = [
            f"# Compliance-Bericht: {report.framework_name}",
            "",
            f"**Bericht-ID:** {report.report_id}",
            f"**Erstellt:** {report.generated_at}",
            f"**Compliance-Score:** {report.compliance_score}%",
            "",
            "## Zusammenfassung",
            "",
            "| Status | Anzahl |",
            "|--------|--------|",
            f"| ✅ Konform | {report.compliant} |",
            f"| ⚠️ Teilweise | {report.partial} |",
            f"| ❌ Nicht konform | {report.non_compliant} |",
            f"| ❓ Nicht bewertet | {report.not_assessed} |",
            "",
            "## Einzelprüfungen",
            "",
        ]

        for c in report.checks:
            emoji = status_emoji.get(c.status.value, "❓")
            lines.append(f"### {emoji} {c.check_id}: {c.requirement}")
            lines.append("")
            lines.append(f"**Regulierung:** {c.regulation}")
            lines.append(f"**Beschreibung:** {c.description}")
            if c.evidence:
                lines.append(f"**Evidenz:** {c.evidence}")
            if c.remediation:
                lines.append(f"**Maßnahme:** {c.remediation}")
            lines.append("")

        return "\n".join(lines)


# ============================================================================
# Remediation-Tracker
# ============================================================================


@dataclass
class RemediationItem:
    """An open remediation item."""

    item_id: str
    check_id: str
    title: str
    description: str
    severity: str = "medium"
    status: RemediationStatus = RemediationStatus.OPEN
    assigned_to: str = ""
    due_date: str = ""
    created_at: str = ""
    resolved_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "check_id": self.check_id,
            "title": self.title,
            "status": self.status.value,
            "severity": self.severity,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date,
            "resolved_at": self.resolved_at,
        }


class RemediationTracker:
    """Tracking open remediation items.

    Tracks remediation items, checks for overdue items,
    and calculates MTTR (Mean Time to Remediate).
    """

    def __init__(self) -> None:
        self._items: dict[str, RemediationItem] = {}

    @property
    def count(self) -> int:
        return len(self._items)

    def add(self, item: RemediationItem) -> None:
        item.created_at = item.created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._items[item.item_id] = item

    def resolve(self, item_id: str) -> RemediationItem | None:
        item = self._items.get(item_id)
        if item:
            item.status = RemediationStatus.RESOLVED
            item.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return item

    def get(self, item_id: str) -> RemediationItem | None:
        return self._items.get(item_id)

    def open_items(self) -> list[RemediationItem]:
        return [
            i
            for i in self._items.values()
            if i.status in (RemediationStatus.OPEN, RemediationStatus.IN_PROGRESS)
        ]

    def overdue_items(self, reference_date: str = "") -> list[RemediationItem]:
        ref = reference_date or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return [
            i
            for i in self._items.values()
            if i.due_date
            and i.due_date < ref
            and i.status in (RemediationStatus.OPEN, RemediationStatus.IN_PROGRESS)
        ]

    def stats(self) -> dict[str, Any]:
        items = list(self._items.values())
        return {
            "total": len(items),
            "open": sum(1 for i in items if i.status == RemediationStatus.OPEN),
            "in_progress": sum(1 for i in items if i.status == RemediationStatus.IN_PROGRESS),
            "resolved": sum(1 for i in items if i.status == RemediationStatus.RESOLVED),
            "overdue": len(self.overdue_items()),
        }


# ============================================================================
# Helpers
# ============================================================================


def _clone_check(c: ComplianceCheck) -> ComplianceCheck:
    """Creates a copy of a ComplianceCheck."""
    return ComplianceCheck(
        check_id=c.check_id,
        regulation=c.regulation,
        requirement=c.requirement,
        description=c.description,
        status=c.status,
        evidence=c.evidence,
        risk_level=c.risk_level,
        remediation=c.remediation,
    )
