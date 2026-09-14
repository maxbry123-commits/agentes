"""
Sandboxed command executor with safety controls.
"""

import subprocess
import re
import logging
from typing import Optional
from src.state import CommandRecord

logger = logging.getLogger(__name__)

# Commands that should NEVER be run automatically
BLOCKED_COMMANDS = [
    r"rm\s+-rf\s+/",
    r"mkfs\.",
    r"dd\s+if=.*of=/dev/",
    r":\(\)\{.*\}",
    r"chmod\s+-R\s+777\s+/",
]

# Commands requiring explicit user confirmation
CONFIRM_COMMANDS = [
    r"rm\s+",
    r"reboot",
    r"shutdown",
    r"systemctl\s+stop",
]


class ToolExecutor:
    """Executes system commands with safety guardrails."""

    def __init__(
        self,
        timeout: int = 120,
        max_output_bytes: int = 50000,
        require_confirmation: bool = False,
        dry_run: bool = False,
    ):
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes
        self.require_confirmation = require_confirmation
        self.dry_run = dry_run
        self.execution_log: list[CommandRecord] = []

    def execute(
        self,
        command: str,
        reasoning: str = "",
        timeout_override: Optional[int] = None,
    ) -> CommandRecord:
        """Execute a command and return a structured record."""
        timeout = timeout_override or self.timeout

        # Safety check: blocked commands
        if self._is_blocked(command):
            logger.warning(f"BLOCKED dangerous command: {command}")
            record = CommandRecord(
                command=command,
                output="[BLOCKED] This command is not allowed for safety reasons.",
                exit_code=-1,
                reasoning=reasoning,
            )
            self.execution_log.append(record)
            return record

        # Safety check: commands requiring confirmation
        if self.require_confirmation and self._needs_confirmation(command):
            print(f"\n⚠️  Agent wants to run: {command}")
            print(f"   Reasoning: {reasoning}")
            approval = input("   Approve? [y/N]: ").strip().lower()
            if approval != "y":
                record = CommandRecord(
                    command=command,
                    output="[DENIED] User declined to approve this command.",
                    exit_code=-1,
                    reasoning=reasoning,
                )
                self.execution_log.append(record)
                return record

        # Dry run mode
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {command}")
            record = CommandRecord(
                command=command,
                output="[DRY RUN] Command not executed.",
                exit_code=0,
                reasoning=reasoning,
            )
            self.execution_log.append(record)
            return record

        # Execute the command
        logger.info(f"Executing: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            stdout = result.stdout
            stderr = result.stderr
            output = stdout
            if stderr:
                output += f"\n[STDERR]\n{stderr}" if stdout else stderr

            # Truncate if too large (preserve head + tail)
            if len(output) > self.max_output_bytes:
                half = self.max_output_bytes // 2
                output = (
                    output[:half]
                    + f"\n\n[... TRUNCATED {len(output) - self.max_output_bytes} bytes ...]\n\n"
                    + output[-half:]
                )

            record = CommandRecord(
                command=command,
                output=output,
                exit_code=result.returncode,
                reasoning=reasoning,
            )

        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out after {timeout}s: {command}")
            record = CommandRecord(
                command=command,
                output=f"[TIMEOUT] Command exceeded {timeout}s timeout.",
                exit_code=-2,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Command execution error: {e}")
            record = CommandRecord(
                command=command,
                output=f"[ERROR] {str(e)}",
                exit_code=-3,
                reasoning=reasoning,
            )

        self.execution_log.append(record)
        return record

    def _is_blocked(self, command: str) -> bool:
        return any(re.search(pattern, command) for pattern in BLOCKED_COMMANDS)

    def _needs_confirmation(self, command: str) -> bool:
        return any(re.search(pattern, command) for pattern in CONFIRM_COMMANDS)
