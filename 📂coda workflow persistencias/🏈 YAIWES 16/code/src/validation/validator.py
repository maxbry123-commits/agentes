"""
Validates agent performance against ground truth from machine writeups.
"""

import yaml
import logging
from dataclasses import dataclass, field
from src.state import AgentState
from src.memory.findings import FindingsStore

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Scored comparison between agent output and ground truth."""
    machine_name: str
    total_score: float = 0.0
    max_score: float = 0.0
    checks: list[dict] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        return (self.total_score / self.max_score * 100) if self.max_score > 0 else 0

    def add_check(
        self, name: str, passed: bool, weight: float = 1.0, details: str = ""
    ):
        self.checks.append({
            "name": name,
            "passed": passed,
            "weight": weight,
            "details": details,
        })
        self.max_score += weight
        if passed:
            self.total_score += weight

    def generate_report(self) -> str:
        lines = [
            f"\n{'='*60}",
            f"  VALIDATION REPORT — {self.machine_name}",
            f"{'='*60}",
            f"  Score: {self.total_score}/{self.max_score} ({self.percentage:.1f}%)\n",
        ]
        for check in self.checks:
            icon = "✅" if check["passed"] else "❌"
            lines.append(f"  {icon} [{check['weight']:.0f}pt] {check['name']}")
            if check["details"]:
                lines.append(f"      → {check['details']}")
        lines.append(f"\n{'='*60}")
        return "\n".join(lines)


class Validator:
    """Compares agent results against known ground truth."""

    def __init__(self, machine_config_path: str):
        with open(machine_config_path, "r") as f:
            self.config = yaml.safe_load(f)
        self.ground_truth = self.config.get("ground_truth", {})

    def validate(
        self, state: AgentState, findings: FindingsStore
    ) -> ValidationResult:
        result = ValidationResult(machine_name=self.config["name"])

        self._check_ports(state, result)
        self._check_attack_surface(state, findings, result)
        self._check_vulnerability(state, findings, result)
        self._check_exploitation(state, findings, result)
        self._check_user_flag(state, result)
        self._check_privesc(state, findings, result)
        self._check_root_flag(state, result)
        self._check_mitre(findings, result)

        return result

    def _check_ports(self, state: AgentState, result: ValidationResult):
        gt_ports = {p["port"] for p in self.ground_truth.get("ports", [])}
        found_ports = {p["port"] for p in state.open_ports}
        all_found = gt_ports <= found_ports

        result.add_check(
            "Port Discovery",
            passed=len(gt_ports & found_ports) > 0,
            weight=1.0,
            details=f"Found {found_ports}, expected {gt_ports}",
        )
        result.add_check(
            "All Critical Ports Found",
            passed=all_found,
            weight=1.0,
            details=f"Missing: {gt_ports - found_ports}" if not all_found else "All found",
        )

    def _check_attack_surface(
        self, state: AgentState, findings: FindingsStore, result: ValidationResult
    ):
        gt_surfaces = self.ground_truth.get("attack_surface", [])
        found_paths = [f.value.lower() for f in findings.get_by_category("path")]
        found_paths += [str(s).lower() for s in state.attack_surface]
        all_text = " ".join(found_paths)

        for surface in gt_surfaces:
            path = surface["path"].lower()
            key_term = path.strip("/").split("/")[-1] if "/" in path else path
            found = key_term in all_text
            result.add_check(
                f"Attack Surface: {surface['path']}",
                passed=found,
                weight=1.0,
                details=f"Key term '{key_term}' {'found' if found else 'NOT found'} in findings",
            )

    def _check_vulnerability(
        self, state: AgentState, findings: FindingsStore, result: ValidationResult
    ):
        gt_vuln = self.ground_truth.get("vulnerability", {})
        vuln_findings = findings.get_by_category("vulnerability")
        vuln_text = " ".join(f.value.lower() for f in vuln_findings)
        vuln_text += " ".join(str(v).lower() for v in state.vulnerabilities)

        vuln_name = gt_vuln.get("name", "").lower()
        cve = gt_vuln.get("cve", "").lower()

        name_found = vuln_name in vuln_text if vuln_name else False
        cve_found = cve in vuln_text if cve else False

        result.add_check(
            f"Vulnerability Identified: {gt_vuln.get('name', 'unknown')}",
            passed=name_found or cve_found,
            weight=3.0,
            details=f"Looked for '{vuln_name}' or '{cve}' in findings",
        )

    def _check_exploitation(
        self, state: AgentState, findings: FindingsStore, result: ValidationResult
    ):
        has_shell = len(state.shells) > 0
        exploit_findings = (
            findings.get_by_category("exploit") + findings.get_by_category("shell")
        )
        result.add_check(
            "Initial Access Achieved",
            passed=has_shell or len(exploit_findings) > 0,
            weight=3.0,
            details=f"Shells: {len(state.shells)}, Exploit findings: {len(exploit_findings)}",
        )

    def _check_user_flag(self, state: AgentState, result: ValidationResult):
        result.add_check(
            "User Flag Captured",
            passed=state.flags.get("user") is not None,
            weight=2.0,
            details=f"Flag: {state.flags.get('user', 'NOT FOUND')}",
        )

    def _check_privesc(
        self, state: AgentState, findings: FindingsStore, result: ValidationResult
    ):
        gt_privesc = self.ground_truth.get("privesc", {})
        privesc_findings = findings.get_by_category("privesc_vector")
        privesc_text = " ".join(f.value.lower() for f in privesc_findings)

        cmd_text = " ".join(cmd.command.lower() for cmd in state.command_history)
        cmd_output_text = " ".join(
            cmd.output.lower() for cmd in state.command_history
        )
        all_text = privesc_text + " " + cmd_text + " " + cmd_output_text

        method = gt_privesc.get("method", "").lower()

        if method and method != "n/a":
            method_terms = method.replace("sudo ", "").split()
            found = any(term in all_text for term in method_terms)
            result.add_check(
                f"Privesc Vector: {gt_privesc.get('method', 'unknown')}",
                passed=found,
                weight=2.0,
                details=f"Looked for terms {method_terms} in findings and command history",
            )
        else:
            has_root_shell = any(
                "root" in str(s).lower() for s in state.shells
            )
            result.add_check(
                "Privesc: Direct Root (no escalation needed)",
                passed=has_root_shell or state.flags.get("root") is not None,
                weight=2.0,
                details="Machine provides root on initial access",
            )

    def _check_root_flag(self, state: AgentState, result: ValidationResult):
        result.add_check(
            "Root Flag Captured",
            passed=state.flags.get("root") is not None,
            weight=2.0,
            details=f"Flag: {state.flags.get('root', 'NOT FOUND')}",
        )

    def _check_mitre(self, findings: FindingsStore, result: ValidationResult):
        gt_mitre = self.ground_truth.get("mitre_attack", [])
        if not gt_mitre:
            return

        all_text = findings.get_context_for_prompt().lower()

        mitre_refs_found = 0
        for technique in gt_mitre:
            technique_id = technique.get("technique", "").lower()
            tactic = technique.get("tactic", "").lower()
            if (
                technique_id.split(" - ")[0].strip() in all_text
                or tactic in all_text
            ):
                mitre_refs_found += 1

        result.add_check(
            "MITRE ATT&CK Coverage (Bonus)",
            passed=mitre_refs_found > 0,
            weight=1.0,
            details=f"Matched {mitre_refs_found}/{len(gt_mitre)} techniques in findings",
        )
