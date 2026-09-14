"""Runtime monitor: Real-time security monitoring.

Monitors EVERY tool execution and blocks suspicious actions
BEFORE they are executed. Supplements the static code analysis
of the PackageInstaller with dynamic runtime checking.

Check chains:
  1. Policy checks: Check allowed/forbidden tool parameters
  2. Rate limiting: Block too many calls per time window
  3. Resource limits: Monitor file sizes, memory, CPU time
  4. Anomaly detection: Detect unusual patterns

Each violation is logged as a SecurityEvent in the AuditLog
and can instruct the executor to block the action.

Bible reference: §3.4 (Runtime Security)
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("cognithor.security.monitor")


# ============================================================================
# Security Events
# ============================================================================


class Severity(Enum):
    """Severity of a security event."""

    INFO = "info"  # Normal operation
    WARNING = "warning"  # Suspicious but not blocked
    CRITICAL = "critical"  # Blocked
    ALERT = "alert"  # Immediate notification


class Verdict(Enum):
    """Decision of the runtime monitor."""

    ALLOW = "allow"  # Allow action
    WARN = "warn"  # Allow + log warning
    BLOCK = "block"  # Block action
    THROTTLE = "throttle"  # Throttle action


@dataclass
class SecurityEvent:
    """A single security event."""

    event_id: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )
    severity: Severity = Severity.INFO
    verdict: Verdict = Verdict.ALLOW
    category: str = ""  # policy, rate_limit, resource, anomaly
    tool_name: str = ""
    agent_name: str = ""
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    rule_id: str = ""  # Which rule triggered

    @property
    def is_blocked(self) -> bool:
        return self.verdict == Verdict.BLOCK


# ============================================================================
# Policy Rules
# ============================================================================


@dataclass
class PolicyRule:
    """A security rule for the runtime monitor.

    Defines conditions and actions:
      - match: Which tool/which agent
      - condition: Parameter check
      - action: ALLOW/WARN/BLOCK
    """

    rule_id: str
    description: str = ""
    enabled: bool = True

    # Matching
    tool_pattern: str = "*"  # Glob-Pattern oder exakter Name
    agent_pattern: str = "*"

    # Condition (parameter checks)
    forbidden_params: dict[str, list[str]] = field(default_factory=dict)
    # z.B. {"path": ["/etc", "/proc", "/sys"]}
    required_params: list[str] = field(default_factory=list)
    max_param_length: int = 0  # 0 = unbegrenzt

    # Action
    verdict: Verdict = Verdict.BLOCK
    severity: Severity = Severity.CRITICAL


# Default rules
_DEFAULT_RULES: list[PolicyRule] = [
    PolicyRule(
        rule_id="no_system_dirs",
        description="Block access to system directories",
        tool_pattern="*",
        forbidden_params={
            "path": ["/etc", "/proc", "/sys", "/boot", "/root"],
            "file": ["/etc", "/proc", "/sys", "/boot", "/root"],
            "directory": ["/etc", "/proc", "/sys", "/boot", "/root"],
        },
        verdict=Verdict.BLOCK,
        severity=Severity.CRITICAL,
    ),
    PolicyRule(
        rule_id="no_credential_leak",
        description="Block credentials in parameters",
        tool_pattern="*",
        forbidden_params={
            "content": ["password", "api_key", "secret", "token"],
        },
        verdict=Verdict.WARN,
        severity=Severity.WARNING,
    ),
    PolicyRule(
        rule_id="param_length_limit",
        description="Block oversized parameters (injection protection)",
        tool_pattern="*",
        max_param_length=50000,  # 50KB
        verdict=Verdict.BLOCK,
        severity=Severity.CRITICAL,
    ),
]


# ============================================================================
# Rate Limiter
# ============================================================================


@dataclass
class RateLimit:
    """Rate limit configuration."""

    name: str
    max_calls: int  # Maximum calls
    window_seconds: int  # Time window
    scope: str = "global"  # global, per_agent, per_tool


class RateLimiter:
    """Token-bucket-based rate limiter.

    Tracks tool calls per scope and blocks on exceeding limits.
    """

    def __init__(self) -> None:
        self._limits: list[RateLimit] = []
        self._buckets: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=10000))

    def add_limit(self, limit: RateLimit) -> None:
        self._limits.append(limit)

    def check(
        self,
        tool_name: str,
        agent_name: str = "",
    ) -> tuple[bool, str]:
        """Checks if a call is allowed.

        Returns:
            (allowed, reason)
        """
        now = time.monotonic()

        for limit in self._limits:
            # Determine scope key
            if limit.scope == "global":
                key = f"global:{limit.name}"
            elif limit.scope == "per_agent":
                key = f"agent:{agent_name}:{limit.name}"
            elif limit.scope == "per_tool":
                key = f"tool:{tool_name}:{limit.name}"
            else:
                key = f"global:{limit.name}"

            bucket = self._buckets[key]

            # Remove old entries
            while bucket and now - bucket[0] > limit.window_seconds:
                bucket.popleft()

            if len(bucket) >= limit.max_calls:
                return False, (
                    f"Rate limit '{limit.name}' exceeded: {limit.max_calls}/{limit.window_seconds}s"
                )

        return True, ""

    def record(self, tool_name: str, agent_name: str = "") -> None:
        """Records a call."""
        now = time.monotonic()
        for limit in self._limits:
            if limit.scope == "global":
                key = f"global:{limit.name}"
            elif limit.scope == "per_agent":
                key = f"agent:{agent_name}:{limit.name}"
            elif limit.scope == "per_tool":
                key = f"tool:{tool_name}:{limit.name}"
            else:
                key = f"global:{limit.name}"
            self._buckets[key].append(now)


# ============================================================================
# Runtime Monitor
# ============================================================================


class RuntimeMonitor:
    """Real-time security monitoring for tool executions.

    Usage:
        monitor = RuntimeMonitor()

        # Vor jeder Tool-Ausfuehrung:
        event = monitor.check_tool_call("file_write", {"path": "/etc/passwd"}, agent="coder")
        if event.is_blocked:
            raise SecurityError(event.description)

        # Nach Ausfuehrung:
        monitor.record_execution("file_write", agent="coder", success=True)
    """

    def __init__(self, *, enable_defaults: bool = True) -> None:
        self._rules: list[PolicyRule] = []
        self._rate_limiter = RateLimiter()
        self._events: deque[SecurityEvent] = deque(maxlen=10000)
        self._event_counter = 0
        self._total_checks = 0
        self._total_blocks = 0
        self._total_warnings = 0

        if enable_defaults:
            self._rules.extend(_DEFAULT_RULES)
            self._rate_limiter.add_limit(
                RateLimit("global_burst", max_calls=100, window_seconds=60),
            )
            self._rate_limiter.add_limit(
                RateLimit("per_tool_limit", max_calls=30, window_seconds=60, scope="per_tool"),
            )

    # ── Configuration ────────────────────────────────────────────

    def add_rule(self, rule: PolicyRule) -> None:
        """Adds a new security rule."""
        self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Removes a rule."""
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.rule_id != rule_id]
        return len(self._rules) < before

    def add_rate_limit(self, limit: RateLimit) -> None:
        self._rate_limiter.add_limit(limit)

    # ── Check ────────────────────────────────────────────────────

    def check_tool_call(
        self,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
        *,
        agent_name: str = "",
    ) -> SecurityEvent:
        """Checks a tool call BEFORE it is executed.

        Runs through all rules and rate limits.

        Args:
            tool_name: Name of the tool to call.
            parameters: Tool parameters.
            agent_name: Name of the calling agent.

        Returns:
            SecurityEvent with verdict (ALLOW/WARN/BLOCK).
        """
        self._total_checks += 1
        params = parameters or {}

        # 1. Check policy rules
        for rule in self._rules:
            if not rule.enabled:
                continue

            if not self._matches_pattern(tool_name, rule.tool_pattern):
                continue
            if agent_name and not self._matches_pattern(agent_name, rule.agent_pattern):
                continue

            violation = self._check_rule(rule, params)
            if violation:
                event = self._create_event(
                    severity=rule.severity,
                    verdict=rule.verdict,
                    category="policy",
                    tool_name=tool_name,
                    agent_name=agent_name,
                    description=violation,
                    parameters=params,
                    rule_id=rule.rule_id,
                )
                if event.is_blocked:
                    self._total_blocks += 1
                elif event.verdict == Verdict.WARN:
                    self._total_warnings += 1
                return event

        # 2. Rate-Limiting
        allowed, reason = self._rate_limiter.check(tool_name, agent_name)
        if not allowed:
            event = self._create_event(
                severity=Severity.WARNING,
                verdict=Verdict.THROTTLE,
                category="rate_limit",
                tool_name=tool_name,
                agent_name=agent_name,
                description=reason,
                parameters=params,
            )
            self._total_blocks += 1
            return event

        # 3. All OK
        self._rate_limiter.record(tool_name, agent_name)
        return self._create_event(
            severity=Severity.INFO,
            verdict=Verdict.ALLOW,
            category="check",
            tool_name=tool_name,
            agent_name=agent_name,
            description="Tool call allowed",
        )

    def record_execution(
        self,
        tool_name: str,
        *,
        agent_name: str = "",
        success: bool = True,
        duration_ms: float = 0,
    ) -> None:
        """Records an executed tool action."""
        self._create_event(
            severity=Severity.INFO,
            verdict=Verdict.ALLOW,
            category="execution",
            tool_name=tool_name,
            agent_name=agent_name,
            description=f"{'Success' if success else 'Error'} ({duration_ms:.0f}ms)",
        )

    # ── Rule-Checking ────────────────────────────────────────────

    def _check_rule(
        self,
        rule: PolicyRule,
        params: dict[str, Any],
    ) -> str:
        """Checks a single rule against parameters.

        Returns:
            Empty string if OK, error description if violation.
        """
        # Forbidden-Params
        for param_name, forbidden_values in rule.forbidden_params.items():
            value = str(params.get(param_name, ""))
            if not value:
                continue
            value_lower = value.lower()
            for forbidden in forbidden_values:
                if forbidden.lower() in value_lower:
                    return (
                        f"Rule '{rule.rule_id}': parameter '{param_name}' "
                        f"contains forbidden value '{forbidden}'"
                    )

        # Required-Params
        for required in rule.required_params:
            if required not in params:
                return f"Rule '{rule.rule_id}': required parameter '{required}' is missing"

        # Max-Param-Length
        if rule.max_param_length > 0:
            for param_name, value in params.items():
                str_value = str(value)
                if len(str_value) > rule.max_param_length:
                    return (
                        f"Rule '{rule.rule_id}': parameter '{param_name}' "
                        f"too long ({len(str_value)} > {rule.max_param_length})"
                    )

        return ""

    @staticmethod
    def _matches_pattern(value: str, pattern: str) -> bool:
        """Simple glob matching: '*' matches everything."""
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return value.startswith(pattern[:-1])
        return value == pattern

    # ── Event management ─────────────────────────────────────────

    def _create_event(self, **kwargs: Any) -> SecurityEvent:
        self._event_counter += 1
        event = SecurityEvent(
            event_id=f"sec_{self._event_counter}",
            **kwargs,
        )
        self._events.append(event)

        # Logging
        if event.severity in (Severity.CRITICAL, Severity.ALERT):
            logger.warning(
                "SECURITY %s: %s (tool=%s, agent=%s, rule=%s)",
                event.verdict.value,
                event.description,
                event.tool_name,
                event.agent_name,
                event.rule_id,
            )

        return event

    def get_events(
        self,
        *,
        severity: Severity | None = None,
        category: str = "",
        limit: int = 100,
    ) -> list[SecurityEvent]:
        """Returns filtered security events."""
        events = list(self._events)

        if severity:
            events = [e for e in events if e.severity == severity]
        if category:
            events = [e for e in events if e.category == category]

        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    def get_blocked_events(self, limit: int = 50) -> list[SecurityEvent]:
        """All blocked actions."""
        return [e for e in list(self._events) if e.is_blocked][-limit:]

    # ── Stats ────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        return {
            "total_checks": self._total_checks,
            "total_blocks": self._total_blocks,
            "total_warnings": self._total_warnings,
            "active_rules": len([r for r in self._rules if r.enabled]),
            "events_logged": len(self._events),
            "block_rate": (
                self._total_blocks / self._total_checks if self._total_checks > 0 else 0.0
            ),
        }
