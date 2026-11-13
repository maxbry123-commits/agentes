"""
Recon Phase Agent — Port scanning and service discovery.
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

RECON_SYSTEM_PROMPT = """You are an expert penetration tester performing the RECONNAISSANCE phase against a target.

Your goal: Discover all open ports and identify running services on the target.

RULES:
1. You MUST respond with valid JSON only — no markdown, no explanation outside JSON.
2. Start with a fast scan, then follow up based on results.
3. You have a maximum of {max_commands} commands for this phase.
4. When you have sufficient port/service information, set "phase_complete" to true.
5. Make sure to run a service version scan (-sV) on ALL discovered open ports.

AVAILABLE TOOLS: nmap, ping, curl, netcat (nc)

RESPONSE FORMAT (strictly JSON):
{{
    "reasoning": "Why I'm choosing this action",
    "command": "the exact shell command to run",
    "phase_complete": false,
    "findings": [
        {{
            "category": "port|service|os",
            "value": "description of finding",
            "confidence": "high|medium|low"
        }}
    ],
    "hypotheses": ["potential attack vectors to investigate"]
}}

When phase_complete is true, include a comprehensive summary in findings."""

RECON_USER_TEMPLATE = """TARGET: {target_ip}

CURRENT STATE:
{state_context}

ACCUMULATED FINDINGS:
{findings_context}

Commands remaining this phase: {commands_remaining}

What is your next action?"""


class ReconAgent:
    """Drives the reconnaissance phase using Claude for decision-making."""

    def __init__(
        self,
        client: Anthropic,
        executor: ToolExecutor,
        findings: FindingsStore,
        model: str = "claude-sonnet-4-20250514",
        max_commands: int = 8,
    ):
        self.client = client
        self.executor = executor
        self.findings = findings
        self.model = model
        self.max_commands = max_commands

    def run(self, state: AgentState) -> PhaseResult:
        """Execute the recon phase in an agentic loop."""
        logger.info(f"{'='*60}")
        logger.info(f"RECON PHASE — Target: {state.target_ip}")
        logger.info(f"{'='*60}")

        commands_run = []
        reasoning_trace = []
        commands_used = 0

        while commands_used < self.max_commands:
            # Build prompt with current context
            user_prompt = RECON_USER_TEMPLATE.format(
                target_ip=state.target_ip,
                state_context=state.get_context_summary(),
                findings_context=self.findings.get_context_for_prompt(),
                commands_remaining=self.max_commands - commands_used,
            )

            # Ask Claude what to do
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=RECON_SYSTEM_PROMPT.format(max_commands=self.max_commands),
                messages=[{"role": "user", "content": user_prompt}],
            )

            response_text = response.content[0].text.strip()

            # Parse Claude's response using robust parser
            try:
                decision = parse_agent_response(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Claude response: {response_text[:200]}")
                reasoning_trace.append(f"[PARSE ERROR] {response_text[:200]}")
                commands_used += 1
                continue

            reasoning = decision.get("reasoning", "")
            command = decision.get("command", "")
            phase_complete = decision.get("phase_complete", False)
            new_findings = decision.get("findings", [])
            hypotheses = decision.get("hypotheses", [])

            reasoning_trace.append(reasoning)
            logger.info(f"[RECON] Reasoning: {reasoning}")
            logger.info(f"[RECON] Command: {command}")

            # Process findings and check for flags
            for f in new_findings:
                self.findings.add_finding(Finding(
                    category=f["category"],
                    value=f["value"],
                    source_command=command or "analysis",
                    confidence=f.get("confidence", "medium"),
                    phase="recon",
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
                logger.info("[RECON] Phase marked complete by agent.")
                break

            if not command:
                logger.warning("[RECON] No command provided, skipping.")
                commands_used += 1
                continue

            # Execute the command
            record = self.executor.execute(command, reasoning=reasoning)
            state.add_command(record)
            commands_run.append(record)
            commands_used += 1

            # Update state with port info if we can detect it
            self._extract_ports_from_output(record.output, state)

            # Check for flags in command output
            self._check_for_flags(record.output, state)

            logger.info(f"[RECON] Output preview: {record.output[:300]}")

        return PhaseResult(
            phase=Phase.RECON,
            success=len(state.open_ports) > 0,
            findings=[f.value for f in self.findings.get_by_category("port")]
                     + [f.value for f in self.findings.get_by_category("service")],
            commands_run=commands_run,
            reasoning_trace=reasoning_trace,
        )

    def _extract_ports_from_output(self, output: str, state: AgentState) -> None:
        """Extract open ports from nmap output and update state."""
        for match in re.finditer(r"(\d+)/tcp\s+open\s+(\S+)(.*)", output):
            port_info = {
                "port": int(match.group(1)),
                "service": match.group(2),
                "details": match.group(3).strip(),
            }
            if not any(p["port"] == port_info["port"] for p in state.open_ports):
                state.open_ports.append(port_info)
                logger.info(
                    f"[RECON] Port discovered: {port_info['port']}/{port_info['service']}"
                )

        for match in re.finditer(r"(\d+)/udp\s+open\s+(\S+)(.*)", output):
            port_info = {
                "port": int(match.group(1)),
                "service": match.group(2) + " (UDP)",
                "details": match.group(3).strip(),
            }
            if not any(p["port"] == port_info["port"] for p in state.open_ports):
                state.open_ports.append(port_info)
                logger.info(
                    f"[RECON] UDP Port discovered: {port_info['port']}/{port_info['service']}"
                )

    def _check_for_flags(self, output: str, state: AgentState) -> None:
        """Check command output for HTB flag patterns."""
        flags = re.findall(r"\b[a-f0-9]{32}\b", output)
        for flag in flags:
            if not state.flags["user"]:
                state.flags["user"] = flag
                logger.info(f"[FLAG] Possible user flag found: {flag}")
            elif not state.flags["root"] and flag != state.flags["user"]:
                state.flags["root"] = flag
                logger.info(f"[FLAG] Possible root flag found: {flag}")
