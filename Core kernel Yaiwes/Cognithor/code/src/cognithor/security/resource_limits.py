"""Tool Sandbox Hardening — Per-tool resource limits, watchdog, and escape detection.

Provides:
  - ToolSandboxProfile:   Per-tool sandbox configuration (CPU, RAM, network, disk)
  - ResourceWatchdog:     Monitors running tools and kills on limit violation
  - NetworkGuard:         Per-tool network isolation policy
  - EscapeDetector:       Detects sandbox escape attempts via heuristics
  - ToolResourceMetrics:  Collects and exposes per-tool resource usage
  - ToolSandboxManager:   Orchestrates profiles, watchdog, guard, and metrics

Architecture: §4.3 (Sandbox), §9.3 (Security Hardening)
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class NetworkPermission(StrEnum):
    """Network access level for a tool."""

    ALLOW = "allow"  # Full network access
    BLOCK = "block"  # No network at all
    RESTRICTED = "restricted"  # Only whitelisted hosts


class DiskPermission(StrEnum):
    """Disk access level for a tool."""

    READ_WRITE = "read_write"
    READ_ONLY = "read_only"
    NONE = "none"


class WatchdogAction(StrEnum):
    """Action to take when a resource limit is exceeded."""

    KILL = "kill"
    WARN = "warn"
    THROTTLE = "throttle"


class EscapeType(StrEnum):
    """Types of sandbox escape attempts."""

    PATH_TRAVERSAL = "path_traversal"
    SYMLINK_ATTACK = "symlink_attack"
    PROC_MOUNT = "proc_mount"
    CAPABILITY_ESCALATION = "capability_escalation"
    KERNEL_EXPLOIT = "kernel_exploit"
    NETWORK_BYPASS = "network_bypass"
    ENV_INJECTION = "env_injection"
    COMMAND_INJECTION = "command_injection"


# ---------------------------------------------------------------------------
# Tool Sandbox Profile
# ---------------------------------------------------------------------------


@dataclass
class ToolSandboxProfile:
    """Per-tool sandbox configuration.

    Defines resource limits, network policy, disk access, and allowed
    operations for a specific tool.
    """

    tool_name: str

    # Resource limits
    max_cpu_seconds: int = 10
    max_memory_mb: int = 512
    max_disk_write_mb: int = 100
    max_output_bytes: int = 50_000
    timeout_seconds: int = 30

    # Network
    network: NetworkPermission = NetworkPermission.BLOCK
    allowed_hosts: list[str] = field(default_factory=list)

    # Disk
    disk: DiskPermission = DiskPermission.READ_WRITE
    allowed_paths: list[str] = field(default_factory=list)
    denied_paths: list[str] = field(default_factory=list)

    # Process
    max_processes: int = 16
    can_spawn_children: bool = False

    # Watchdog
    watchdog_action: WatchdogAction = WatchdogAction.KILL

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "max_cpu_seconds": self.max_cpu_seconds,
            "max_memory_mb": self.max_memory_mb,
            "max_disk_write_mb": self.max_disk_write_mb,
            "timeout_seconds": self.timeout_seconds,
            "network": self.network.value,
            "allowed_hosts": self.allowed_hosts,
            "disk": self.disk.value,
            "max_processes": self.max_processes,
            "watchdog_action": self.watchdog_action.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolSandboxProfile:
        return cls(
            tool_name=data["tool_name"],
            max_cpu_seconds=data.get("max_cpu_seconds", 10),
            max_memory_mb=data.get("max_memory_mb", 512),
            max_disk_write_mb=data.get("max_disk_write_mb", 100),
            max_output_bytes=data.get("max_output_bytes", 50_000),
            timeout_seconds=data.get("timeout_seconds", 30),
            network=NetworkPermission(data.get("network", "block")),
            allowed_hosts=data.get("allowed_hosts", []),
            disk=DiskPermission(data.get("disk", "read_write")),
            allowed_paths=data.get("allowed_paths", []),
            denied_paths=data.get("denied_paths", []),
            max_processes=data.get("max_processes", 16),
            can_spawn_children=data.get("can_spawn_children", False),
            watchdog_action=WatchdogAction(data.get("watchdog_action", "kill")),
        )


# ---------------------------------------------------------------------------
# Built-in Profiles
# ---------------------------------------------------------------------------


BUILTIN_PROFILES: dict[str, ToolSandboxProfile] = {
    "exec_command": ToolSandboxProfile(
        tool_name="exec_command",
        max_cpu_seconds=30,
        max_memory_mb=512,
        timeout_seconds=60,
        network=NetworkPermission.BLOCK,
        disk=DiskPermission.READ_WRITE,
        max_processes=16,
        can_spawn_children=True,
    ),
    "web_search": ToolSandboxProfile(
        tool_name="web_search",
        max_cpu_seconds=10,
        max_memory_mb=256,
        timeout_seconds=30,
        network=NetworkPermission.ALLOW,
        disk=DiskPermission.READ_ONLY,
        max_processes=4,
    ),
    "web_fetch": ToolSandboxProfile(
        tool_name="web_fetch",
        max_cpu_seconds=15,
        max_memory_mb=256,
        timeout_seconds=30,
        network=NetworkPermission.ALLOW,
        disk=DiskPermission.READ_ONLY,
        max_processes=4,
    ),
    "search_and_read": ToolSandboxProfile(
        tool_name="search_and_read",
        max_cpu_seconds=15,
        max_memory_mb=256,
        timeout_seconds=30,
        network=NetworkPermission.ALLOW,
        disk=DiskPermission.READ_ONLY,
        max_processes=4,
    ),
    "read_file": ToolSandboxProfile(
        tool_name="read_file",
        max_cpu_seconds=5,
        max_memory_mb=128,
        timeout_seconds=10,
        network=NetworkPermission.BLOCK,
        disk=DiskPermission.READ_ONLY,
        max_processes=1,
    ),
    "write_file": ToolSandboxProfile(
        tool_name="write_file",
        max_cpu_seconds=5,
        max_memory_mb=128,
        max_disk_write_mb=50,
        timeout_seconds=10,
        network=NetworkPermission.BLOCK,
        disk=DiskPermission.READ_WRITE,
        max_processes=1,
    ),
    "memory_store": ToolSandboxProfile(
        tool_name="memory_store",
        max_cpu_seconds=5,
        max_memory_mb=128,
        timeout_seconds=10,
        network=NetworkPermission.BLOCK,
        disk=DiskPermission.READ_WRITE,
        max_processes=1,
    ),
    "memory_search": ToolSandboxProfile(
        tool_name="memory_search",
        max_cpu_seconds=10,
        max_memory_mb=256,
        timeout_seconds=15,
        network=NetworkPermission.BLOCK,
        disk=DiskPermission.READ_ONLY,
        max_processes=1,
    ),
    "vault_get": ToolSandboxProfile(
        tool_name="vault_get",
        max_cpu_seconds=2,
        max_memory_mb=64,
        timeout_seconds=5,
        network=NetworkPermission.BLOCK,
        disk=DiskPermission.READ_ONLY,
        max_processes=1,
    ),
    "document_export": ToolSandboxProfile(
        tool_name="document_export",
        max_cpu_seconds=30,
        max_memory_mb=512,
        max_disk_write_mb=200,
        timeout_seconds=60,
        network=NetworkPermission.BLOCK,
        disk=DiskPermission.READ_WRITE,
        max_processes=4,
    ),
}

# Default profile for unknown tools (restrictive)
DEFAULT_PROFILE = ToolSandboxProfile(
    tool_name="__default__",
    max_cpu_seconds=10,
    max_memory_mb=256,
    timeout_seconds=30,
    network=NetworkPermission.BLOCK,
    disk=DiskPermission.READ_ONLY,
    max_processes=4,
    watchdog_action=WatchdogAction.KILL,
)


# ---------------------------------------------------------------------------
# Resource Watchdog
# ---------------------------------------------------------------------------


@dataclass
class WatchdogEvent:
    """A resource limit violation event."""

    tool_name: str
    resource: str  # "cpu", "memory", "disk", "timeout", "output"
    limit: float
    actual: float
    action: WatchdogAction
    timestamp: float = field(default_factory=time.monotonic)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "resource": self.resource,
            "limit": self.limit,
            "actual": round(self.actual, 2),
            "action": self.action.value,
            "exceeded_by": round(self.actual - self.limit, 2),
        }


class ResourceWatchdog:
    """Monitors tool execution and enforces resource limits.

    Tracks resource consumption and triggers actions (kill/warn/throttle)
    when limits are exceeded.
    """

    def __init__(self, max_events: int = 1000) -> None:
        self._events: list[WatchdogEvent] = []
        self._max_events = max_events
        self._active_tools: dict[str, dict[str, Any]] = {}  # execution_id → state

    def start_monitoring(self, execution_id: str, profile: ToolSandboxProfile) -> None:
        """Begin monitoring a tool execution."""
        self._active_tools[execution_id] = {
            "profile": profile,
            "started_at": time.monotonic(),
            "cpu_used": 0.0,
            "memory_peak_mb": 0.0,
            "disk_written_mb": 0.0,
            "output_bytes": 0,
        }
        log.debug("watchdog_start", execution_id=execution_id, tool=profile.tool_name)

    def stop_monitoring(self, execution_id: str) -> None:
        """Stop monitoring a tool execution."""
        self._active_tools.pop(execution_id, None)

    def check_cpu(self, execution_id: str, cpu_seconds: float) -> WatchdogEvent | None:
        """Check CPU usage against limits."""
        state = self._active_tools.get(execution_id)
        if not state:
            return None

        profile: ToolSandboxProfile = state["profile"]
        state["cpu_used"] = cpu_seconds

        if cpu_seconds > profile.max_cpu_seconds:
            event = WatchdogEvent(
                tool_name=profile.tool_name,
                resource="cpu",
                limit=profile.max_cpu_seconds,
                actual=cpu_seconds,
                action=profile.watchdog_action,
            )
            self._record_event(event)
            return event
        return None

    def check_memory(self, execution_id: str, memory_mb: float) -> WatchdogEvent | None:
        """Check memory usage against limits."""
        state = self._active_tools.get(execution_id)
        if not state:
            return None

        profile: ToolSandboxProfile = state["profile"]
        state["memory_peak_mb"] = max(state["memory_peak_mb"], memory_mb)

        if memory_mb > profile.max_memory_mb:
            event = WatchdogEvent(
                tool_name=profile.tool_name,
                resource="memory",
                limit=profile.max_memory_mb,
                actual=memory_mb,
                action=profile.watchdog_action,
            )
            self._record_event(event)
            return event
        return None

    def check_disk(self, execution_id: str, disk_written_mb: float) -> WatchdogEvent | None:
        """Check disk write usage against limits."""
        state = self._active_tools.get(execution_id)
        if not state:
            return None

        profile: ToolSandboxProfile = state["profile"]
        state["disk_written_mb"] = disk_written_mb

        if disk_written_mb > profile.max_disk_write_mb:
            event = WatchdogEvent(
                tool_name=profile.tool_name,
                resource="disk",
                limit=profile.max_disk_write_mb,
                actual=disk_written_mb,
                action=profile.watchdog_action,
            )
            self._record_event(event)
            return event
        return None

    def check_timeout(self, execution_id: str) -> WatchdogEvent | None:
        """Check if tool execution has exceeded timeout."""
        state = self._active_tools.get(execution_id)
        if not state:
            return None

        profile: ToolSandboxProfile = state["profile"]
        elapsed = time.monotonic() - state["started_at"]

        if elapsed > profile.timeout_seconds:
            event = WatchdogEvent(
                tool_name=profile.tool_name,
                resource="timeout",
                limit=profile.timeout_seconds,
                actual=elapsed,
                action=WatchdogAction.KILL,  # Timeout always kills
            )
            self._record_event(event)
            return event
        return None

    def check_output(self, execution_id: str, output_bytes: int) -> WatchdogEvent | None:
        """Check output size against limits."""
        state = self._active_tools.get(execution_id)
        if not state:
            return None

        profile: ToolSandboxProfile = state["profile"]
        state["output_bytes"] = output_bytes

        if output_bytes > profile.max_output_bytes:
            event = WatchdogEvent(
                tool_name=profile.tool_name,
                resource="output",
                limit=profile.max_output_bytes,
                actual=output_bytes,
                action=WatchdogAction.WARN,  # Output overflow is a warning
            )
            self._record_event(event)
            return event
        return None

    def get_state(self, execution_id: str) -> dict[str, Any] | None:
        """Get current monitoring state for an execution."""
        return self._active_tools.get(execution_id)

    @property
    def active_count(self) -> int:
        return len(self._active_tools)

    @property
    def events(self) -> list[WatchdogEvent]:
        return list(self._events)

    def events_for_tool(self, tool_name: str) -> list[WatchdogEvent]:
        return [e for e in self._events if e.tool_name == tool_name]

    def clear_events(self) -> int:
        count = len(self._events)
        self._events.clear()
        return count

    def stats(self) -> dict[str, Any]:
        by_resource: dict[str, int] = {}
        by_tool: dict[str, int] = {}
        by_action: dict[str, int] = {}
        for e in self._events:
            by_resource[e.resource] = by_resource.get(e.resource, 0) + 1
            by_tool[e.tool_name] = by_tool.get(e.tool_name, 0) + 1
            by_action[e.action.value] = by_action.get(e.action.value, 0) + 1
        return {
            "total_violations": len(self._events),
            "active_monitors": self.active_count,
            "by_resource": by_resource,
            "by_tool": by_tool,
            "by_action": by_action,
        }

    def _record_event(self, event: WatchdogEvent) -> None:
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]
        log.warning(
            "watchdog_violation",
            tool=event.tool_name,
            resource=event.resource,
            limit=event.limit,
            actual=round(event.actual, 2),
            action=event.action.value,
        )


# ---------------------------------------------------------------------------
# Network Guard
# ---------------------------------------------------------------------------


class NetworkGuard:
    """Enforces per-tool network isolation policies.

    Validates network access based on tool profiles, tracking
    allowed/blocked requests per tool.
    """

    def __init__(self) -> None:
        self._allowed_log: list[dict[str, Any]] = []
        self._blocked_log: list[dict[str, Any]] = []

    def check_access(
        self,
        tool_name: str,
        profile: ToolSandboxProfile,
        host: str = "",
    ) -> bool:
        """Check if a tool is allowed network access.

        Args:
            tool_name: The tool requesting access.
            profile: The tool's sandbox profile.
            host: Target host (for restricted mode).

        Returns:
            True if access is allowed.
        """
        entry = {
            "tool_name": tool_name,
            "host": host,
            "policy": profile.network.value,
            "timestamp": time.time(),
        }

        if profile.network == NetworkPermission.BLOCK:
            self._blocked_log.append(entry)
            log.info("network_blocked", tool=tool_name, host=host)
            return False

        if profile.network == NetworkPermission.RESTRICTED and (
            not host or not self._host_matches(host, profile.allowed_hosts)
        ):
            self._blocked_log.append(entry)
            log.info("network_restricted_blocked", tool=tool_name, host=host)
            return False

        self._allowed_log.append(entry)
        return True

    @staticmethod
    def _host_matches(host: str, allowed_hosts: list[str]) -> bool:
        """Check if host matches any pattern in allowed list.

        Supports exact match and wildcard prefix (*.example.com).
        """
        host_lower = host.lower()
        for pattern in allowed_hosts:
            pattern_lower = pattern.lower()
            if pattern_lower.startswith("*."):
                suffix = pattern_lower[1:]  # ".example.com"
                if host_lower.endswith(suffix) or host_lower == pattern_lower[2:]:
                    return True
            elif host_lower == pattern_lower:
                return True
        return False

    @property
    def blocked_count(self) -> int:
        return len(self._blocked_log)

    @property
    def allowed_count(self) -> int:
        return len(self._allowed_log)

    def blocked_for_tool(self, tool_name: str) -> list[dict[str, Any]]:
        return [e for e in self._blocked_log if e["tool_name"] == tool_name]

    def stats(self) -> dict[str, Any]:
        return {
            "total_allowed": self.allowed_count,
            "total_blocked": self.blocked_count,
            "blocked_tools": list({e["tool_name"] for e in self._blocked_log}),
        }


# ---------------------------------------------------------------------------
# Escape Detector
# ---------------------------------------------------------------------------

# Patterns indicating sandbox escape attempts
_ESCAPE_PATTERNS: dict[EscapeType, list[re.Pattern[str]]] = {
    EscapeType.PATH_TRAVERSAL: [
        re.compile(r"(?:\.\.[/\\]){3,}"),  # Deep traversal
        re.compile(r"/proc/\d+/root"),  # procfs root escape
        re.compile(r"/proc/self/cwd"),  # Follow CWD via procfs
    ],
    EscapeType.SYMLINK_ATTACK: [
        re.compile(r"ln\s+-s.*(?:/etc|/proc|/sys)"),  # Symlink to sensitive dirs
        re.compile(r"readlink\s+.*(?:/proc|/sys)"),  # Read sensitive symlinks
    ],
    EscapeType.PROC_MOUNT: [
        re.compile(r"mount\s+-t\s+proc"),  # Mount procfs
        re.compile(r"nsenter\s+"),  # Enter namespaces
        re.compile(r"unshare\s+"),  # Create new namespaces
    ],
    EscapeType.CAPABILITY_ESCALATION: [
        re.compile(r"capsh\s+"),  # Capability shell
        re.compile(r"setcap\s+"),  # Set capabilities
        re.compile(r"chmod\s+[0-7]*[4-7][0-7]*\s+/"),  # setuid/setgid on system paths
        re.compile(r"sudo\s+"),  # Privilege escalation
    ],
    EscapeType.KERNEL_EXPLOIT: [
        re.compile(r"/dev/(?:mem|kmem|port)"),  # Direct kernel memory
        re.compile(r"insmod\s+"),  # Load kernel module
        re.compile(r"modprobe\s+"),  # Module loading
        re.compile(r"kexec\s+"),  # Kernel execution
    ],
    EscapeType.NETWORK_BYPASS: [
        re.compile(r"iptables\s+"),  # Firewall manipulation
        re.compile(r"ip\s+(?:route|rule|link)\s+"),  # Network config changes
        re.compile(r"socat\s+.*EXEC"),  # Reverse shell via socat
        re.compile(r"nc\s+-[el]"),  # Netcat listener
    ],
    EscapeType.ENV_INJECTION: [
        re.compile(r"LD_PRELOAD="),  # Library injection
        re.compile(r"LD_LIBRARY_PATH=.*(?:/tmp|/dev)"),  # Library path hijack
        re.compile(r"PYTHONPATH=.*(?:/tmp|/dev)"),  # Python path hijack
    ],
    EscapeType.COMMAND_INJECTION: [
        re.compile(r"\$\(.*(?:curl|wget|nc)\s+"),  # Command subst with network
        re.compile(r"`.*(?:curl|wget|nc)\s+"),  # Backtick subst with network
        re.compile(r"\|\s*(?:bash|sh|zsh|dash)\s"),  # Pipe to shell
        re.compile(r";\s*(?:rm|dd)\s+-"),  # Chained destructive commands
    ],
}


@dataclass
class EscapeAttempt:
    """A detected sandbox escape attempt."""

    escape_type: EscapeType
    tool_name: str
    command: str
    matched_pattern: str
    severity: str = "high"  # "critical", "high", "medium"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.escape_type.value,
            "tool_name": self.tool_name,
            "command_preview": self.command[:200],
            "severity": self.severity,
            "matched_pattern": self.matched_pattern,
        }


class EscapeDetector:
    """Detects sandbox escape attempts via command analysis.

    Scans commands against known escape patterns and maintains
    an audit log of all attempts.
    """

    # Critical escape types that should always block
    CRITICAL_TYPES: frozenset[EscapeType] = frozenset(
        {
            EscapeType.KERNEL_EXPLOIT,
            EscapeType.CAPABILITY_ESCALATION,
            EscapeType.PROC_MOUNT,
        }
    )

    def __init__(self, max_history: int = 500) -> None:
        self._history: list[EscapeAttempt] = []
        self._max_history = max_history

    def scan(self, command: str, tool_name: str = "") -> list[EscapeAttempt]:
        """Scan a command for escape patterns.

        Returns list of detected escape attempts (empty if clean).
        """
        attempts: list[EscapeAttempt] = []

        for escape_type, patterns in _ESCAPE_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(command):
                    severity = "critical" if escape_type in self.CRITICAL_TYPES else "high"
                    attempt = EscapeAttempt(
                        escape_type=escape_type,
                        tool_name=tool_name,
                        command=command,
                        matched_pattern=pattern.pattern,
                        severity=severity,
                    )
                    attempts.append(attempt)
                    break  # One match per type is enough

        if attempts:
            self._history.extend(attempts)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history :]
            log.warning(
                "escape_attempt_detected",
                tool=tool_name,
                types=[a.escape_type.value for a in attempts],
                severity=max(a.severity for a in attempts),
            )

        return attempts

    def is_safe(self, command: str, tool_name: str = "") -> bool:
        """Quick check: returns True if no escape patterns detected."""
        return len(self.scan(command, tool_name)) == 0

    @property
    def history(self) -> list[EscapeAttempt]:
        return list(self._history)

    def history_for_tool(self, tool_name: str) -> list[EscapeAttempt]:
        return [a for a in self._history if a.tool_name == tool_name]

    def critical_attempts(self) -> list[EscapeAttempt]:
        return [a for a in self._history if a.severity == "critical"]

    def clear_history(self) -> int:
        count = len(self._history)
        self._history.clear()
        return count

    def stats(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_tool: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for a in self._history:
            by_type[a.escape_type.value] = by_type.get(a.escape_type.value, 0) + 1
            if a.tool_name:
                by_tool[a.tool_name] = by_tool.get(a.tool_name, 0) + 1
            by_severity[a.severity] = by_severity.get(a.severity, 0) + 1
        return {
            "total_attempts": len(self._history),
            "critical_attempts": len(self.critical_attempts()),
            "by_type": by_type,
            "by_tool": by_tool,
            "by_severity": by_severity,
        }


# ---------------------------------------------------------------------------
# Tool Resource Metrics
# ---------------------------------------------------------------------------


@dataclass
class ToolExecution:
    """Record of a single tool execution with resource usage."""

    tool_name: str
    execution_id: str
    started_at: float
    finished_at: float = 0.0
    cpu_seconds: float = 0.0
    memory_peak_mb: float = 0.0
    disk_written_mb: float = 0.0
    output_bytes: int = 0
    exit_code: int = 0
    timed_out: bool = False
    killed_by_watchdog: bool = False
    sandbox_level: str = "bare"
    network_requests: int = 0

    @property
    def duration_ms(self) -> float:
        if self.finished_at <= 0:
            return 0.0
        return (self.finished_at - self.started_at) * 1000

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.killed_by_watchdog

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "execution_id": self.execution_id,
            "duration_ms": round(self.duration_ms, 1),
            "cpu_seconds": round(self.cpu_seconds, 2),
            "memory_peak_mb": round(self.memory_peak_mb, 1),
            "disk_written_mb": round(self.disk_written_mb, 2),
            "output_bytes": self.output_bytes,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "killed_by_watchdog": self.killed_by_watchdog,
            "sandbox_level": self.sandbox_level,
            "success": self.success,
        }


class ToolResourceMetrics:
    """Collects per-tool resource usage metrics.

    Tracks execution history and provides aggregate statistics
    per tool for monitoring and UI display.
    """

    def __init__(self, max_history: int = 500) -> None:
        self._executions: list[ToolExecution] = []
        self._max_history = max_history

    def record(self, execution: ToolExecution) -> None:
        """Record a completed tool execution."""
        self._executions.append(execution)
        if len(self._executions) > self._max_history:
            self._executions = self._executions[-self._max_history :]

    def for_tool(self, tool_name: str) -> list[ToolExecution]:
        return [e for e in self._executions if e.tool_name == tool_name]

    def aggregate(self, tool_name: str) -> dict[str, Any]:
        """Compute aggregate metrics for a tool."""
        execs = self.for_tool(tool_name)
        if not execs:
            return {"tool_name": tool_name, "executions": 0}

        durations = [e.duration_ms for e in execs if e.duration_ms > 0]
        cpu_values = [e.cpu_seconds for e in execs]
        mem_values = [e.memory_peak_mb for e in execs]
        successes = sum(1 for e in execs if e.success)

        return {
            "tool_name": tool_name,
            "executions": len(execs),
            "success_rate": round(successes / len(execs) * 100, 1) if execs else 0.0,
            "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else 0.0,
            "max_duration_ms": round(max(durations), 1) if durations else 0.0,
            "avg_cpu_seconds": round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0.0,
            "max_memory_mb": round(max(mem_values), 1) if mem_values else 0.0,
            "total_timeouts": sum(1 for e in execs if e.timed_out),
            "total_watchdog_kills": sum(1 for e in execs if e.killed_by_watchdog),
        }

    def all_tools(self) -> list[str]:
        """Get all tool names with recorded executions."""
        return sorted({e.tool_name for e in self._executions})

    @property
    def total_executions(self) -> int:
        return len(self._executions)

    def recent(self, limit: int = 20) -> list[ToolExecution]:
        return list(reversed(self._executions[-limit:]))

    def stats(self) -> dict[str, Any]:
        tools = self.all_tools()
        return {
            "total_executions": self.total_executions,
            "unique_tools": len(tools),
            "tools": {t: self.aggregate(t) for t in tools},
        }


# ---------------------------------------------------------------------------
# Tool Sandbox Manager
# ---------------------------------------------------------------------------


class ToolSandboxManager:
    """Orchestrates per-tool sandboxing with profiles, watchdog, and metrics.

    Central entry point for:
    - Looking up / registering tool profiles
    - Pre-execution validation (escape detection, network check)
    - Runtime monitoring (watchdog)
    - Post-execution metrics recording
    """

    def __init__(self) -> None:
        self._profiles: dict[str, ToolSandboxProfile] = dict(BUILTIN_PROFILES)
        self._watchdog = ResourceWatchdog()
        self._network_guard = NetworkGuard()
        self._escape_detector = EscapeDetector()
        self._metrics = ToolResourceMetrics()

    @property
    def watchdog(self) -> ResourceWatchdog:
        return self._watchdog

    @property
    def network_guard(self) -> NetworkGuard:
        return self._network_guard

    @property
    def escape_detector(self) -> EscapeDetector:
        return self._escape_detector

    @property
    def metrics(self) -> ToolResourceMetrics:
        return self._metrics

    # -- Profile management --

    def get_profile(self, tool_name: str) -> ToolSandboxProfile:
        """Get sandbox profile for a tool (falls back to default)."""
        return self._profiles.get(tool_name, DEFAULT_PROFILE)

    def register_profile(self, profile: ToolSandboxProfile) -> None:
        """Register a custom sandbox profile for a tool."""
        self._profiles[profile.tool_name] = profile
        log.info("profile_registered", tool=profile.tool_name)

    def list_profiles(self) -> list[ToolSandboxProfile]:
        return list(self._profiles.values())

    def has_profile(self, tool_name: str) -> bool:
        return tool_name in self._profiles

    # -- Pre-execution checks --

    def pre_execute_check(
        self,
        tool_name: str,
        command: str = "",
        target_host: str = "",
    ) -> dict[str, Any]:
        """Run all pre-execution safety checks.

        Returns a dict with:
        - allowed: bool
        - profile: the resolved profile
        - escape_attempts: list of detected escape attempts
        - network_allowed: bool (if network relevant)
        - warnings: list of warning strings
        """
        profile = self.get_profile(tool_name)
        warnings: list[str] = []
        escape_attempts: list[EscapeAttempt] = []

        # 1. Escape detection
        if command:
            escape_attempts = self._escape_detector.scan(command, tool_name)
            if any(a.severity == "critical" for a in escape_attempts):
                return {
                    "allowed": False,
                    "profile": profile,
                    "escape_attempts": escape_attempts,
                    "network_allowed": False,
                    "reason": "Critical escape attempt detected",
                    "warnings": warnings,
                }
            if escape_attempts:
                warnings.append(f"Escape patterns detected: {len(escape_attempts)}")

        # 2. Network check
        network_allowed = True
        if target_host or profile.network != NetworkPermission.BLOCK:
            network_allowed = self._network_guard.check_access(tool_name, profile, target_host)
            if not network_allowed and target_host:
                warnings.append(f"Network access blocked for host: {target_host}")

        # 3. Profile warnings
        if not self.has_profile(tool_name):
            warnings.append("Using default restrictive profile (unknown tool)")

        return {
            "allowed": True,
            "profile": profile,
            "escape_attempts": escape_attempts,
            "network_allowed": network_allowed,
            "warnings": warnings,
        }

    # -- Execution lifecycle --

    def begin_execution(self, execution_id: str, tool_name: str) -> ToolSandboxProfile:
        """Start monitoring a tool execution. Returns the profile to use."""
        profile = self.get_profile(tool_name)
        self._watchdog.start_monitoring(execution_id, profile)
        return profile

    def end_execution(self, execution: ToolExecution) -> None:
        """Record a completed tool execution."""
        self._watchdog.stop_monitoring(execution.execution_id)
        self._metrics.record(execution)

    # -- Stats --

    def stats(self) -> dict[str, Any]:
        return {
            "profiles": len(self._profiles),
            "builtin_profiles": len(BUILTIN_PROFILES),
            "watchdog": self._watchdog.stats(),
            "network_guard": self._network_guard.stats(),
            "escape_detector": self._escape_detector.stats(),
            "metrics": self._metrics.stats(),
        }
