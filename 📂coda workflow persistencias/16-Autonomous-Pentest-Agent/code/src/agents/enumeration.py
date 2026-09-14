"""
Enumeration Phase Agent — Deep-dive into discovered services.
"""

import re
import json
import logging
from anthropic import Anthropic
from src.state import AgentState, PhaseResult, Phase
from src.tools.executor import ToolExecutor
from src.memory.findings import FindingsStore, Finding
from src.agents.parse_utils import parse_agent_response

logger = logging.getLogger(__name__)

ENUM_SYSTEM_PROMPT = """You are an expert penetration tester performing the ENUMERATION phase.

You have already completed reconnaissance and discovered open ports/services. Now you must
dig deeper into each service to find attack surfaces — directories, files, versions,
misconfigurations, and potential vulnerabilities.

YOUR FINDINGS SO FAR:
{findings_context}

RULES:
1. You MUST respond with valid JSON only — no markdown, no explanation outside JSON.
2. Focus on the most promising services first (web servers, SMB, FTP with anon access).
3. For web services: run directory/file brute-forcing, check for interesting paths, fingerprint technologies.
4. For SMB: enumerate shares, check for anonymous access, identify versions.
5. For FTP: check anonymous login, identify version.
6. You have a maximum of {max_commands} commands for this phase.
7. When you have identified concrete attack surfaces, set "phase_complete" to true.
8. IMPORTANT: When using gobuster, prefer smaller wordlists to avoid timeouts:
   - Use /usr/share/wordlists/dirb/common.txt (NOT directory-list-2.3-medium.txt)
   - Use -t 50 for faster scanning
   - If scanning /cgi-bin/, use -x sh,cgi,pl only

AVAILABLE TOOLS: gobuster, nikto, whatweb, curl, smbclient, enum4linux, ftp, nmap (scripts)

RESPONSE FORMAT (strictly JSON):
{{
    "reasoning": "Why I'm choosing this action",
    "command": "the exact shell command to run",
    "phase_complete": false,
    "findings": [
        {{
            "category": "path|technology|misconfiguration|version",
            "value": "description of finding",
            "confidence": "high|medium|low"
        }}
    ],
    "hypotheses": ["potential vulnerabilities or attack vectors"]
}}"""

ENUM_USER_TEMPLATE = """TARGET: {target_ip}

CURRENT STATE:
{state_context}

ACCUMULATED FINDINGS:
{findings_context}

Commands remaining this phase: {commands_remaining}

What is your next action for enumeration?"""


class EnumerationAgent:
    """Drives the enumeration phase using Claude."""

    def __init__(
        self,
        client: Anthropic,
        executor: ToolExecutor,
        findings: FindingsStore,
        model: str = "claude-sonnet-4-20250514",
        max_commands: int = 12,
    ):
        self.client = client
        self.executor = executor
        self.findings = findings
        self.model = model
        self.max_commands = max_commands

    def run(self, state: AgentState) -> PhaseResult:
        logger.info(f"{'='*60}")
        logger.info(f"ENUMERATION PHASE — Target: {state.target_ip}")
        logger.info(f"{'='*60}")

        commands_run = []
        reasoning_trace = []
        commands_used = 0

        while commands_used < self.max_commands:
            user_prompt = ENUM_USER_TEMPLATE.format(
                target_ip=state.target_ip,
                state_context=state.get_context_summary(),
                findings_context=self.findings.get_context_for_prompt(),
                commands_remaining=self.max_commands - commands_used,
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=ENUM_SYSTEM_PROMPT.format(
                    findings_context=self.findings.get_context_for_prompt(),
                    max_commands=self.max_commands,
                ),
                messages=[{"role": "user", "content": user_prompt}],
            )

            response_text = response.content[0].text.strip()

            try:
                decision = parse_agent_response(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse response: {response_text[:200]}")
                reasoning_trace.append(f"[PARSE ERROR] {response_text[:200]}")
                commands_used += 1
                continue

            reasoning = decision.get("reasoning", "")
            command = decision.get("command", "")
            phase_complete = decision.get("phase_complete", False)
            new_findings = decision.get("findings", [])
            hypotheses = decision.get("hypotheses", [])

            reasoning_trace.append(reasoning)
            logger.info(f"[ENUM] Reasoning: {reasoning}")
            logger.info(f"[ENUM] Command: {command}")

            for f in new_findings:
                self.findings.add_finding(Finding(
                    category=f["category"],
                    value=f["value"],
                    source_command=command or "analysis",
                    confidence=f.get("confidence", "medium"),
                    phase="enumeration",
                ))
                # Check if any finding contains a flag hash
                flag_match = re.search(r"\b[a-f0-9]{32}\b", f["value"])
                if flag_match:
                    flag_val = flag_match.group(0)
                    if not state.flags["user"]:
                        state.flags["user"] = flag_val
                        logger.info(f"[FLAG] User flag found in findings: {flag_val}")
                    elif not state.flags["root"] and flag_val != state.flags["user"]:
                        state.flags["root"] = flag_val
                        logger.info(f"[FLAG] Root flag found in findings: {flag_val}")

            for h in hypotheses:
                self.findings.add_hypothesis(h)

            if phase_complete:
                logger.info("[ENUM] Phase marked complete by agent.")
                break

            if not command:
                commands_used += 1
                continue

            # Some enumeration commands need longer timeouts
            timeout = 600 if "gobuster" in command or "nikto" in command else None
            record = self.executor.execute(
                command, reasoning=reasoning, timeout_override=timeout
            )
            state.add_command(record)
            commands_run.append(record)
            commands_used += 1

            # Update attack surface in state
            self._extract_attack_surface(record.output, command, state)

            # Check for flags in command output
            self._check_for_flags(record.output, state)

            logger.info(f"[ENUM] Output preview: {record.output[:300]}")

        return PhaseResult(
            phase=Phase.ENUMERATION,
            success=len(state.attack_surface) > 0
            or len(self.findings.get_by_category("path")) > 0,
            findings=[f.value for f in self.findings.get_by_category("path")]
                     + [f.value for f in self.findings.get_by_category("technology")],
            commands_run=commands_run,
            reasoning_trace=reasoning_trace,
        )

    def _extract_attack_surface(
        self, output: str, command: str, state: AgentState
    ) -> None:
        """Extract discovered paths and attack surfaces from tool output."""
        # Gobuster results
        for match in re.finditer(r"(/\S+)\s+\(Status:\s*(\d+)\)", output):
            path = match.group(1)
            status = match.group(2)
            if status in ("200", "301", "302", "403"):
                entry = {"path": path, "status": status, "source": command}
                if entry not in state.attack_surface:
                    state.attack_surface.append(entry)

    def _check_for_flags(self, output: str, state: AgentState) -> None:
        """Check command output for HTB flag patterns."""
        flags = re.findall(r"\b[a-f0-9]{32}\b", output)
        for flag in flags:
            if not state.flags["user"]:
                state.flags["user"] = flag
                logger.info(f"[FLAG] User flag captured: {flag}")
            elif not state.flags["root"] and flag != state.flags["user"]:
                state.flags["root"] = flag
                logger.info(f"[FLAG] Root flag captured: {flag}")
