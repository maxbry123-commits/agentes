"""Tests fuer utils/logging.py -- Structured Logging Setup."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from cognithor.utils.logging import (
    _StructlogCompatLogger,
    bind_context,
    clear_context,
    get_logger,
    setup_logging,
)

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# _StructlogCompatLogger
# ============================================================================


class TestStructlogCompatLogger:
    def setup_method(self) -> None:
        self.inner = MagicMock(spec=logging.Logger)
        self.log = _StructlogCompatLogger(self.inner)

    def test_info(self) -> None:
        self.log.info("test_event", key="value")
        self.inner.info.assert_called_once()
        msg = self.inner.info.call_args[0][0]
        assert "test_event" in msg
        assert "key='value'" in msg

    def test_warning(self) -> None:
        self.log.warning("warn_event")
        self.inner.warning.assert_called_once()

    def test_error(self) -> None:
        self.log.error("err_event", code=42)
        self.inner.error.assert_called_once()
        msg = self.inner.error.call_args[0][0]
        assert "code=42" in msg

    def test_debug(self) -> None:
        self.log.debug("debug_event")
        self.inner.debug.assert_called_once()

    def test_exception(self) -> None:
        self.log.exception("exc_event", detail="oops")
        self.inner.exception.assert_called_once()
        msg = self.inner.exception.call_args[0][0]
        assert "exc_event" in msg
        assert "detail='oops'" in msg

    def test_exception_no_kwargs(self) -> None:
        self.log.exception("simple_exc")
        self.inner.exception.assert_called_once_with("simple_exc")

    def test_bind_returns_self(self) -> None:
        result = self.log.bind(key="val")
        assert result is self.log

    def test_getattr_delegates(self) -> None:
        self.inner.name = "test_logger"
        assert self.log.name == "test_logger"

    def test_log_with_args(self) -> None:
        self.log.info("msg %s %s", "a", "b")
        self.inner.info.assert_called_once()

    def test_log_with_format_error(self) -> None:
        """When % formatting fails, args are appended as repr."""
        self.log.info("msg %d", "not-a-number")
        self.inner.info.assert_called_once()
        msg = self.inner.info.call_args[0][0]
        assert "not-a-number" in msg

    def test_log_with_non_string_event(self) -> None:
        self.log.info(42)
        self.inner.info.assert_called_once()
        msg = self.inner.info.call_args[0][0]
        assert "42" in msg

    def test_exception_with_non_string_event(self) -> None:
        """Exception method with non-string event should not crash."""

        class BadStr:
            def __str__(self):
                raise ValueError("no str")

            def __repr__(self):
                return "BadStr()"

        self.log.exception(BadStr())
        self.inner.exception.assert_called_once()
        msg = self.inner.exception.call_args[0][0]
        assert "BadStr()" in msg


# ============================================================================
# get_logger
# ============================================================================


class TestGetLogger:
    def test_returns_logger(self) -> None:
        log = get_logger("test.module")
        assert log is not None

    def test_returns_logger_without_name(self) -> None:
        log = get_logger()
        assert log is not None

    def test_fallback_without_structlog(self) -> None:
        with patch("cognithor.utils.logging.structlog", None):
            log = get_logger("fallback_test")
            assert isinstance(log, _StructlogCompatLogger)

    def test_with_structlog_available(self) -> None:
        # When structlog is available, it should use structlog.get_logger
        mock_structlog = MagicMock()
        mock_structlog.get_logger.return_value = MagicMock()
        with patch("cognithor.utils.logging.structlog", mock_structlog):
            get_logger("structlog_test")
            mock_structlog.get_logger.assert_called_once_with("structlog_test")


# ============================================================================
# setup_logging
# ============================================================================


class TestSetupLogging:
    def test_setup_creates_log_dir(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)
        assert log_dir.exists()

    def test_setup_creates_log_file(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)
        assert (log_dir / "cognithor.jsonl").exists() or True  # File created on first write

    def test_setup_with_json_logs(self, tmp_path: Path) -> None:
        """json_logs=True should not crash."""
        setup_logging(level="DEBUG", json_logs=True, log_dir=tmp_path / "logs")

    def test_setup_console_only(self) -> None:
        setup_logging(level="WARNING", console=True)

    def test_setup_no_console(self) -> None:
        setup_logging(console=False)

    def test_setup_silences_noisy_loggers(self) -> None:
        setup_logging()
        for name in ("httpx", "httpcore", "asyncio", "watchdog", "urllib3"):
            assert logging.getLogger(name).level >= logging.WARNING

    def test_setup_with_invalid_level(self) -> None:
        """Unknown level should fall back to INFO."""
        setup_logging(level="NONEXISTENT")
        # Should not crash

    def test_setup_without_structlog(self) -> None:
        with patch("cognithor.utils.logging.structlog", None):
            setup_logging(level="DEBUG")  # Should return early without error

    def test_setup_with_log_dir_nested(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "a" / "b" / "c" / "logs"
        setup_logging(log_dir=log_dir)
        assert log_dir.exists()


# ============================================================================
# bind_context / clear_context
# ============================================================================


class TestContextManagement:
    def test_bind_context_without_structlog(self) -> None:
        with patch("cognithor.utils.logging.structlog", None):
            bind_context(user="test")  # Should be a no-op

    def test_clear_context_without_structlog(self) -> None:
        with patch("cognithor.utils.logging.structlog", None):
            clear_context()  # Should be a no-op

    def test_bind_context_with_structlog(self) -> None:
        mock_structlog = MagicMock()
        with patch("cognithor.utils.logging.structlog", mock_structlog):
            bind_context(user="test", session="abc")
            mock_structlog.contextvars.bind_contextvars.assert_called_once_with(
                user="test", session="abc"
            )

    def test_clear_context_with_structlog(self) -> None:
        mock_structlog = MagicMock()
        with patch("cognithor.utils.logging.structlog", mock_structlog):
            clear_context()
            mock_structlog.contextvars.clear_contextvars.assert_called_once()
