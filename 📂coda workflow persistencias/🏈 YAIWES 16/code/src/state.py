"""
Kill chain state machine for the autonomous pentest agent.
Tracks current phase, findings, and transition logic.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class Phase(Enum):
    """Kill chain phases modeled as a state machine."""
    INIT = "init"
    RECON = "recon"
    ENUMERATION = "enumeration"
    EXPLOIT = "exploit"
    PRIVESC = "privesc"
    LOOT = "loot"
    COMPLETE = "complete"
    FAILED = "failed"

    @property
    def next_phase(self) -> Optional["Phase"]:
        transitions = {
            Phase.INIT: Phase.RECON,
            Phase.RECON: Phase.ENUMERATION,
            Phase.ENUMERATION: Phase.EXPLOIT,
            Phase.EXPLOIT: Phase.PRIVESC,
            Phase.PRIVESC: Phase.LOOT,
            Phase.LOOT: Phase.COMPLETE,
        }
        return transitions.get(self)


@dataclass
class CommandRecord:
    """Record of a single command execution."""
    command: str
    output: str
    exit_code: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    phase: str = ""
    reasoning: str = ""


@dataclass
class PhaseResult:
    """Result of a completed phase."""
    phase: Phase
    success: bool
    findings: list[str] = field(default_factory=list)
    commands_run: list[CommandRecord] = field(default_factory=list)
    reasoning_trace: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class AgentState:
    """
    Full agent state — passed between phases and used for
    context management and reporting.
    """
    target_ip: str
    machine_name: str
    current_phase: Phase = Phase.INIT
    phases_completed: list[PhaseResult] = field(default_factory=list)
    command_history: list[CommandRecord] = field(default_factory=list)
    open_ports: list[dict] = field(default_factory=list)
    attack_surface: list[dict] = field(default_factory=list)
    vulnerabilities: list[dict] = field(default_factory=list)
    credentials: list[dict] = field(default_factory=list)
    shells: list[dict] = field(default_factory=list)
    flags: dict = field(default_factory=lambda: {"user": None, "root": None})
    hypothesis_stack: list[str] = field(default_factory=list)
    dead_ends: list[str] = field(default_factory=list)
    total_commands: int = 0
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())

    def advance_phase(self, result: PhaseResult) -> None:
        """Advance to next phase after completing current one."""
        self.phases_completed.append(result)
        next_phase = self.current_phase.next_phase
        if next_phase:
            self.current_phase = next_phase
        else:
            self.current_phase = Phase.COMPLETE

    def add_command(self, record: CommandRecord) -> None:
        """Record a command execution."""
        record.phase = self.current_phase.value
        self.command_history.append(record)
        self.total_commands += 1

    def get_context_summary(self) -> str:
        """Generate a summary of current state for Claude's context window."""
        summary = f"""
=== CURRENT AGENT STATE ===
Target: {self.target_ip} ({self.machine_name})
Current Phase: {self.current_phase.value}
Commands Run: {self.total_commands}

--- Open Ports ---
{self._format_list(self.open_ports)}

--- Attack Surface ---
{self._format_list(self.attack_surface)}

--- Vulnerabilities Identified ---
{self._format_list(self.vulnerabilities)}

--- Active Shells ---
{self._format_list(self.shells)}

--- Credentials Found ---
{self._format_list(self.credentials)}

--- Flags ---
User: {self.flags.get('user', 'NOT FOUND')}
Root: {self.flags.get('root', 'NOT FOUND')}

--- Current Hypotheses ---
{chr(10).join(f'  * {h}' for h in self.hypothesis_stack) if self.hypothesis_stack else '  (none)'}

--- Dead Ends (do NOT retry) ---
{chr(10).join(f'  x {d}' for d in self.dead_ends) if self.dead_ends else '  (none)'}

--- Last 5 Commands ---
{self._format_recent_commands()}
"""
        return summary.strip()

    def _format_list(self, items: list) -> str:
        if not items:
            return "  (none discovered yet)"
        return "\n".join(f"  * {item}" for item in items)

    def _format_recent_commands(self) -> str:
        recent = self.command_history[-5:]
        if not recent:
            return "  (no commands run yet)"
        lines = []
        for cmd in recent:
            # Increased from 200 to 1000 to prevent critical output truncation
            output_preview = (
                cmd.output[:1000] + "..." if len(cmd.output) > 1000 else cmd.output
            )
            lines.append(
                f"  $ {cmd.command}\n    -> exit={cmd.exit_code} | {output_preview}"
            )
        return "\n".join(lines)    
