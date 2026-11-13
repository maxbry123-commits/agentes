"""Coverage-Tests fuer errors.py -- alle Error-Klassen abdecken."""

from __future__ import annotations

import pytest

from cognithor.core.errors import (
    AuthenticationError,
    ChannelError,
    ConfigError,
    GatekeeperDenied,
    JarvisError,
    JarvisMemoryError,
    JarvisSecurityError,
    LLMError,
    PolicyViolation,
    RateLimitExceeded,
    SandboxError,
    ToolExecutionError,
)


class TestJarvisError:
    def test_base_error(self) -> None:
        err = JarvisError("base error")
        assert str(err) == "base error"
        assert err.error_code == "COGNITHOR_ERROR"
        assert err.details == {}

    def test_base_error_with_code_and_details(self) -> None:
        err = JarvisError("oops", error_code="CUSTOM", details={"key": "val"})
        assert err.error_code == "CUSTOM"
        assert err.details == {"key": "val"}

    def test_is_exception(self) -> None:
        with pytest.raises(JarvisError):
            raise JarvisError("test")


class TestConfigError:
    def test_default_code(self) -> None:
        err = ConfigError("bad config")
        assert err.error_code == "CONFIG_ERROR"
        assert isinstance(err, JarvisError)

    def test_custom_code(self) -> None:
        err = ConfigError("missing key", error_code="CONFIG_INVALID_MODEL", details={"model": "x"})
        assert err.error_code == "CONFIG_INVALID_MODEL"
        assert err.details["model"] == "x"


class TestLLMError:
    def test_default_code(self) -> None:
        err = LLMError("timeout")
        assert err.error_code == "LLM_ERROR"

    def test_with_details(self) -> None:
        err = LLMError("rate limit", details={"provider": "openai", "timeout_s": 30})
        assert err.details["provider"] == "openai"


class TestToolExecutionError:
    def test_default_code(self) -> None:
        err = ToolExecutionError("tool crash")
        assert err.error_code == "TOOL_EXECUTION_ERROR"


class TestSandboxError:
    def test_default_code(self) -> None:
        err = SandboxError("sandbox fail")
        assert err.error_code == "SANDBOX_ERROR"


class TestChannelError:
    def test_default_code(self) -> None:
        err = ChannelError("connection lost")
        assert err.error_code == "CHANNEL_ERROR"


class TestJarvisMemoryError:
    def test_default_code(self) -> None:
        err = JarvisMemoryError("corrupted")
        assert err.error_code == "MEMORY_ERROR"


class TestJarvisSecurityError:
    def test_default_code(self) -> None:
        err = JarvisSecurityError("access denied")
        assert err.error_code == "SECURITY_ERROR"


class TestPolicyViolation:
    def test_default_code(self) -> None:
        err = PolicyViolation("policy breach")
        assert err.error_code == "POLICY_VIOLATION"
        assert isinstance(err, JarvisError)


class TestGatekeeperDenied:
    def test_default_code(self) -> None:
        err = GatekeeperDenied("denied")
        assert err.error_code == "GATEKEEPER_DENIED"
        assert isinstance(err, PolicyViolation)
        assert isinstance(err, JarvisError)


class TestAuthenticationError:
    def test_default_code(self) -> None:
        err = AuthenticationError("invalid token")
        assert err.error_code == "AUTHENTICATION_ERROR"


class TestRateLimitExceeded:
    def test_default_code(self) -> None:
        err = RateLimitExceeded("too many requests")
        assert err.error_code == "RATE_LIMIT_EXCEEDED"

    def test_with_details(self) -> None:
        err = RateLimitExceeded("limit", details={"limit": 100, "window_s": 60})
        assert err.details["limit"] == 100
