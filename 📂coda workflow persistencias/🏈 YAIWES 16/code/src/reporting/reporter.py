"""
Generates the final pentest report with full attack narrative,
command log, reasoning trace, and MITRE ATT&CK mapping.
"""

import json
import logging
from datetime import datetime
from typing import Optional
from src.state import AgentState, PhaseResult
from src.memory.findings import FindingsStore
from src.validation.validator import ValidationResult

logger = logging.getLogger(__name__)


class Reporter:
    """Generates structured pentest reports from agent run data."""

    def __init__(self, state: AgentState, findings: FindingsStore):
        self.state = state
        self.findings = findings

    def generate_full_report(
        self,
        validation: Optional[ValidationResult] = None,
    ) -> str:
        """Generate a complete pentest report."""
        report = []
        report.append(self._header())
        report.append(self._executive_summary())
        report.append(self._attack_narrative())
        report.append(self._findings_section())
        report.append(self._command_log())
        report.append(self._reasoning_trace())
        if validation:
            report.append(validation.generate_report())
        report.append(self._recommendations())
        return "\n\n".join(report)

    def _header(self) -> str:
        return f"""
{'#'*60}
#  AUTONOMOUS PENTEST AGENT — ENGAGEMENT REPORT
#  Target: {self.state.target_ip} ({self.state.machine_name})
#  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#  Total Commands Executed: {self.state.total_commands}
#  Flags Captured: User={'✅' if self.state.flags.get('user') else '❌'} | Root={'✅' if self.state.flags.get('root') else '❌'}
{'#'*60}"""

    def _executive_summary(self) -> str:
        phases_completed = [p.phase.value for p in self.state.phases_completed]
        successful_phases = [p.phase.value for p in self.state.phases_completed if p.success]

        return f"""
## EXECUTIVE SUMMARY

Phases Attempted: {', '.join(phases_completed) if phases_completed else 'None'}
Phases Successful: {', '.join(successful_phases) if successful_phases else 'None'}
Open Ports Discovered: {len(self.state.open_ports)}
Vulnerabilities Found: {len(self.state.vulnerabilities)}
Shells Obtained: {len(self.state.shells)}
User Flag: {self.state.flags.get('user', 'NOT CAPTURED')}
Root Flag: {self.state.flags.get('root', 'NOT CAPTURED')}"""

    def _attack_narrative(self) -> str:
        narrative = "\n## ATTACK NARRATIVE\n"
        for phase_result in self.state.phases_completed:
            narrative += f"\n### {phase_result.phase.value.upper()}\n"
            narrative += f"Success: {'Yes' if phase_result.success else 'No'}\n"
            narrative += f"Commands Run: {len(phase_result.commands_run)}\n"
            if phase_result.reasoning_trace:
                narrative += "Key Reasoning:\n"
                for i, reason in enumerate(phase_result.reasoning_trace, 1):
                    narrative += f"  {i}. {reason}\n"
            if phase_result.findings:
                narrative += "Findings:\n"
                for finding in phase_result.findings:
                    narrative += f"  • {finding}\n"
        return narrative

    def _findings_section(self) -> str:
        return f"""
## ALL FINDINGS

{self.findings.get_context_for_prompt()}"""

    def _command_log(self) -> str:
        log = "\n## FULL COMMAND LOG\n"
        for i, cmd in enumerate(self.state.command_history, 1):
            log += f"\n--- Command #{i} [{cmd.phase}] ---\n"
            log += f"Reasoning: {cmd.reasoning}\n"
            log += f"$ {cmd.command}\n"
            log += f"Exit Code: {cmd.exit_code}\n"
            # Truncate very long outputs for the report
            output = cmd.output
            if len(output) > 1000:
                output = output[:500] + f"\n[... {len(output)-1000} chars truncated ...]\n" + output[-500:]
            log += f"Output:\n{output}\n"
        return log

    def _reasoning_trace(self) -> str:
        trace = "\n## REASONING TRACE (All Phases)\n"
        for phase_result in self.state.phases_completed:
            trace += f"\n### {phase_result.phase.value.upper()}\n"
            for i, reason in enumerate(phase_result.reasoning_trace, 1):
                trace += f"  [{i}] {reason}\n"
        return trace

    def _recommendations(self) -> str:
        return """
## AGENT RECOMMENDATIONS FOR IMPROVEMENT

Based on this engagement:
• Dead ends encountered should be added to the knowledge base
• Successful attack paths should be templated for similar targets
• Tool timeout values may need adjustment based on network conditions
"""

    def save_report(self, filepath: str, validation: Optional[ValidationResult] = None) -> None:
        """Save report to file."""
        report = self.generate_full_report(validation)
        with open(filepath, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {filepath}")

    def save_json(self, filepath: str) -> None:
        """Save structured data as JSON for programmatic analysis."""
        data = {
            "target": self.state.target_ip,
            "machine": self.state.machine_name,
            "start_time": self.state.start_time,
            "total_commands": self.state.total_commands,
            "flags": self.state.flags,
            "open_ports": self.state.open_ports,
            "vulnerabilities": self.state.vulnerabilities,
            "shells": self.state.shells,
            "findings": self.findings.to_dict(),
            "phases": [
                {
                    "name": p.phase.value,
                    "success": p.success,
                    "findings": p.findings,
                    "commands": [
                        {
                            "command": c.command,
                            "exit_code": c.exit_code,
                            "reasoning": c.reasoning,
                            "output_length": len(c.output),
                        }
                        for c in p.commands_run
                    ],
                    "reasoning_trace": p.reasoning_trace,
                }
                for p in self.state.phases_completed
            ],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"JSON data saved to {filepath}")