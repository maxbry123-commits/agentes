"""Tests for jarvis.mcp.email_tools module.

Tests cover:
  - Email address validation
  - Rate limiting for sends
  - Attachment path validation
  - IMAP email fetching (mocked)
  - SMTP email sending (mocked)
  - Email summarization
  - Tool registration
  - Header decoding
  - HTML stripping
  - Body preview extraction
"""

from __future__ import annotations

import email
import os
import time
from email.mime.text import MIMEText
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from cognithor.config import CognithorConfig

if TYPE_CHECKING:
    from pathlib import Path

# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def email_config(tmp_path: Path) -> CognithorConfig:
    """CognithorConfig with email enabled and temporary paths."""
    return CognithorConfig(
        cognithor_home=tmp_path / ".cognithor",
        email={
            "enabled": True,
            "imap_host": "imap.example.com",
            "imap_port": 993,
            "smtp_host": "smtp.example.com",
            "smtp_port": 465,
            "username": "test@example.com",
            "password_env": "TEST_EMAIL_PASSWORD",
        },
        security={"allowed_paths": [str(tmp_path)]},
    )


@pytest.fixture
def email_config_disabled(tmp_path: Path) -> CognithorConfig:
    """CognithorConfig with email disabled."""
    return CognithorConfig(
        cognithor_home=tmp_path / ".cognithor",
    )


@pytest.fixture
def mock_env_password():
    """Set TEST_EMAIL_PASSWORD env var."""
    with patch.dict(os.environ, {"TEST_EMAIL_PASSWORD": "secret123"}):
        yield


@pytest.fixture
def email_tools(email_config: CognithorConfig, mock_env_password: Any):
    """EmailTools instance with mocked environment."""
    from cognithor.mcp.email_tools import EmailTools

    return EmailTools(email_config)


def _make_raw_email(
    from_addr: str = "sender@example.com",
    to_addr: str = "test@example.com",
    subject: str = "Test Subject",
    body: str = "Hello, this is a test email.",
    date: str = "Mon, 15 Jan 2024 10:30:00 +0000",
    html: bool = False,
) -> bytes:
    """Create a raw email bytes for mocking IMAP fetch."""
    content_type = "html" if html else "plain"
    msg = MIMEText(body, content_type, "utf-8")
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Date"] = date
    return msg.as_bytes()


# ── Address Validation ─────────────────────────────────────────────────────


class TestEmailValidation:
    """Tests for email address validation."""

    def test_valid_email(self, email_tools: Any) -> None:
        assert email_tools._validate_email("user@example.com") is True

    def test_valid_email_with_dots(self, email_tools: Any) -> None:
        assert email_tools._validate_email("first.last@example.co.uk") is True

    def test_valid_email_with_plus(self, email_tools: Any) -> None:
        assert email_tools._validate_email("user+tag@example.com") is True

    def test_invalid_email_no_at(self, email_tools: Any) -> None:
        assert email_tools._validate_email("userexample.com") is False

    def test_invalid_email_no_domain(self, email_tools: Any) -> None:
        assert email_tools._validate_email("user@") is False

    def test_invalid_email_no_tld(self, email_tools: Any) -> None:
        assert email_tools._validate_email("user@example") is False

    def test_invalid_email_spaces(self, email_tools: Any) -> None:
        assert email_tools._validate_email("user @example.com") is False

    def test_empty_email(self, email_tools: Any) -> None:
        assert email_tools._validate_email("") is False


# ── Rate Limiting ──────────────────────────────────────────────────────────


class TestRateLimiting:
    """Tests for send rate limiting."""

    def test_under_limit(self, email_tools: Any) -> None:
        """No error when under rate limit."""
        email_tools._send_timestamps = [time.monotonic() for _ in range(5)]
        email_tools._check_send_rate_limit()  # Should not raise

    def test_at_limit(self, email_tools: Any) -> None:
        """Error when at rate limit."""
        from cognithor.mcp.email_tools import EmailError

        email_tools._send_timestamps = [time.monotonic() for _ in range(10)]
        with pytest.raises(EmailError, match="Rate-Limit"):
            email_tools._check_send_rate_limit()

    def test_old_timestamps_expire(self, email_tools: Any) -> None:
        """Timestamps older than 1 hour are cleaned up."""
        old_time = time.monotonic() - 4000  # Over 1 hour ago
        email_tools._send_timestamps = [old_time for _ in range(10)]
        email_tools._check_send_rate_limit()  # Should not raise

    def test_mixed_timestamps(self, email_tools: Any) -> None:
        """Mix of old and recent timestamps."""
        from cognithor.mcp.email_tools import EmailError

        old = time.monotonic() - 4000
        recent = time.monotonic()
        email_tools._send_timestamps = [old] * 5 + [recent] * 10
        with pytest.raises(EmailError, match="Rate-Limit"):
            email_tools._check_send_rate_limit()


# ── Attachment Path Validation ─────────────────────────────────────────────


class TestAttachmentValidation:
    """Tests for attachment path validation."""

    def test_valid_attachment(self, email_tools: Any, tmp_path: Path) -> None:
        """Attachment within workspace is accepted."""
        test_file = tmp_path / "doc.pdf"
        test_file.write_text("fake pdf content")
        result = email_tools._validate_attachment_path(str(test_file))
        assert result == test_file.resolve()

    def test_attachment_outside_workspace(self, email_tools: Any) -> None:
        """Attachment outside workspace is rejected."""
        from cognithor.mcp.email_tools import EmailError

        with pytest.raises(EmailError, match="nicht erlaubt"):
            email_tools._validate_attachment_path("/etc/passwd")

    def test_attachment_not_found(self, email_tools: Any, tmp_path: Path) -> None:
        """Nonexistent attachment is rejected."""
        from cognithor.mcp.email_tools import EmailError

        with pytest.raises(EmailError, match="nicht gefunden"):
            email_tools._validate_attachment_path(str(tmp_path / "nonexistent.pdf"))

    def test_attachment_is_directory(self, email_tools: Any, tmp_path: Path) -> None:
        """Directory path as attachment is rejected."""
        from cognithor.mcp.email_tools import EmailError

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        with pytest.raises(EmailError, match="keine Datei|no.*file|attachment"):
            email_tools._validate_attachment_path(str(subdir))


# ── Password Retrieval ─────────────────────────────────────────────────────


class TestPasswordRetrieval:
    """Tests for password environment variable handling."""

    def test_password_found(self, email_tools: Any, mock_env_password: Any) -> None:
        assert email_tools._get_password() == "secret123"

    def test_password_missing(self, email_config: CognithorConfig) -> None:
        """Missing password env var raises error."""
        from cognithor.mcp.email_tools import EmailError, EmailTools

        with patch.dict(os.environ, {}, clear=True):
            # Remove TEST_EMAIL_PASSWORD if present
            os.environ.pop("TEST_EMAIL_PASSWORD", None)
            tools = EmailTools(email_config)
            with pytest.raises(EmailError, match="nicht gefunden"):
                tools._get_password()


# ── HTML Stripping ─────────────────────────────────────────────────────────


class TestHtmlStripping:
    """Tests for HTML tag removal."""

    def test_strip_basic_html(self) -> None:
        from cognithor.mcp.email_tools import _strip_html

        assert _strip_html("<p>Hello</p>") == "Hello"

    def test_strip_nested_html(self) -> None:
        from cognithor.mcp.email_tools import _strip_html

        result = _strip_html("<div><p>Hello <b>World</b></p></div>")
        assert result == "Hello World"

    def test_strip_empty(self) -> None:
        from cognithor.mcp.email_tools import _strip_html

        assert _strip_html("") == ""

    def test_strip_preserves_text(self) -> None:
        from cognithor.mcp.email_tools import _strip_html

        assert _strip_html("No HTML here") == "No HTML here"


# ── Header Decoding ────────────────────────────────────────────────────────


class TestHeaderDecoding:
    """Tests for MIME header decoding."""

    def test_plain_header(self) -> None:
        from cognithor.mcp.email_tools import _decode_header

        assert _decode_header("Simple Subject") == "Simple Subject"

    def test_none_header(self) -> None:
        from cognithor.mcp.email_tools import _decode_header

        assert _decode_header(None) == ""

    def test_empty_header(self) -> None:
        from cognithor.mcp.email_tools import _decode_header

        assert _decode_header("") == ""


# ── Body Preview Extraction ───────────────────────────────────────────────


class TestBodyPreview:
    """Tests for email body preview extraction."""

    def test_plain_text_preview(self) -> None:
        from cognithor.mcp.email_tools import _extract_body_preview

        raw = _make_raw_email(body="Hello World")
        msg = email.message_from_bytes(raw)
        preview, has_att = _extract_body_preview(msg)
        assert "Hello World" in preview
        assert has_att is False

    def test_html_body_stripped(self) -> None:
        from cognithor.mcp.email_tools import _extract_body_preview

        raw = _make_raw_email(body="<p>Hello <b>World</b></p>", html=True)
        msg = email.message_from_bytes(raw)
        preview, has_att = _extract_body_preview(msg)
        assert "Hello" in preview
        assert "<p>" not in preview

    def test_long_preview_truncated(self) -> None:
        from cognithor.mcp.email_tools import _extract_body_preview

        long_body = "A" * 1000
        raw = _make_raw_email(body=long_body)
        msg = email.message_from_bytes(raw)
        preview, _ = _extract_body_preview(msg)
        assert len(preview) <= 510  # 500 + "..."


# ── IMAP Read (Mocked) ────────────────────────────────────────────────────


class TestEmailReadInbox:
    """Tests for email_read_inbox with mocked IMAP."""

    async def test_read_inbox_empty(self, email_tools: Any) -> None:
        """Empty inbox returns appropriate message."""
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"0"])
        mock_conn.search.return_value = ("OK", [b""])

        with patch.object(email_tools, "_get_imap_connection", return_value=mock_conn):
            result = await email_tools.email_read_inbox()
        assert "Keine E-Mails" in result or "no_emails" in result

    async def test_read_inbox_with_emails(self, email_tools: Any) -> None:
        """Inbox with emails returns formatted list."""
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"1"])
        mock_conn.search.return_value = ("OK", [b"1 2"])

        raw1 = _make_raw_email(subject="First Email")
        raw2 = _make_raw_email(subject="Second Email")
        mock_conn.fetch.side_effect = [
            ("OK", [(b"1 (RFC822 {100}", raw1)]),
            ("OK", [(b"2 (RFC822 {100}", raw2)]),
        ]

        with patch.object(email_tools, "_get_imap_connection", return_value=mock_conn):
            result = await email_tools.email_read_inbox(count=5)
        assert "Second Email" in result
        assert "First Email" in result

    async def test_read_inbox_count_clamped(self, email_tools: Any) -> None:
        """Count is clamped to 1-50 range."""
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"0"])
        mock_conn.search.return_value = ("OK", [b""])

        with patch.object(email_tools, "_get_imap_connection", return_value=mock_conn):
            result = await email_tools.email_read_inbox(count=100)
        assert "Keine" in result

    async def test_read_inbox_unread_only(self, email_tools: Any) -> None:
        """Unread-only filter uses UNSEEN criteria."""
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"0"])
        mock_conn.search.return_value = ("OK", [b""])

        with patch.object(email_tools, "_get_imap_connection", return_value=mock_conn):
            await email_tools.email_read_inbox(unread_only=True)
        mock_conn.search.assert_called_with(None, "UNSEEN")


# ── Email Search (Mocked) ─────────────────────────────────────────────────


class TestEmailSearch:
    """Tests for email_search with mocked IMAP."""

    async def test_search_by_from(self, email_tools: Any) -> None:
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"0"])
        mock_conn.search.return_value = ("OK", [b""])

        with patch.object(email_tools, "_get_imap_connection", return_value=mock_conn):
            result = await email_tools.email_search(from_addr="boss@example.com")
        assert "Keine E-Mails" in result or "no_emails" in result
        call_args = mock_conn.search.call_args[0]
        assert 'FROM "boss@example.com"' in call_args[1]

    async def test_search_by_subject(self, email_tools: Any) -> None:
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"0"])
        mock_conn.search.return_value = ("OK", [b""])

        with patch.object(email_tools, "_get_imap_connection", return_value=mock_conn):
            await email_tools.email_search(subject="Meeting")
        call_args = mock_conn.search.call_args[0]
        assert 'SUBJECT "Meeting"' in call_args[1]

    async def test_search_invalid_date(self, email_tools: Any) -> None:
        from cognithor.mcp.email_tools import EmailError

        mock_conn = MagicMock()
        with (
            patch.object(email_tools, "_get_imap_connection", return_value=mock_conn),
            pytest.raises(EmailError, match="Ungültiges Datum"),
        ):
            await email_tools.email_search(since="not-a-date")

    async def test_search_all_criteria(self, email_tools: Any) -> None:
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"0"])
        mock_conn.search.return_value = ("OK", [b""])

        with patch.object(email_tools, "_get_imap_connection", return_value=mock_conn):
            await email_tools.email_search(
                query="project",
                from_addr="boss@example.com",
                subject="Update",
                since="2024-01-15",
            )
        call_args = mock_conn.search.call_args[0][1]
        assert "BODY" in call_args
        assert "FROM" in call_args
        assert "SUBJECT" in call_args
        assert "SINCE" in call_args


# ── Email Send (Mocked) ───────────────────────────────────────────────────


class TestEmailSend:
    """Tests for email_send with mocked SMTP."""

    async def test_send_basic(self, email_tools: Any) -> None:
        """Basic email send succeeds."""
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("cognithor.mcp.email_tools.smtplib.SMTP_SSL", return_value=mock_smtp):
            result = await email_tools.email_send(
                to="recipient@example.com",
                subject="Test",
                body="Hello",
            )
        assert "erfolgreich" in result

    async def test_send_missing_to(self, email_tools: Any) -> None:
        from cognithor.mcp.email_tools import EmailError

        with pytest.raises(EmailError, match="mpf.nger|Empfaenger|missing_recipient"):
            await email_tools.email_send(to="", subject="Test", body="Hello")

    async def test_send_missing_subject(self, email_tools: Any) -> None:
        from cognithor.mcp.email_tools import EmailError

        with pytest.raises(EmailError, match="etreff|Betreff|missing_subject"):
            await email_tools.email_send(to="recipient@example.com", subject="", body="Hello")

    async def test_send_missing_body(self, email_tools: Any) -> None:
        from cognithor.mcp.email_tools import EmailError

        with pytest.raises(EmailError, match="achrichtentext|Nachrichtentext|missing_body"):
            await email_tools.email_send(to="recipient@example.com", subject="Test", body="")

    async def test_send_invalid_address(self, email_tools: Any) -> None:
        from cognithor.mcp.email_tools import EmailError

        with pytest.raises(EmailError, match="Ungültige E-Mail"):
            await email_tools.email_send(
                to="not-an-email",
                subject="Test",
                body="Hello",
            )

    async def test_send_rate_limited(self, email_tools: Any) -> None:
        from cognithor.mcp.email_tools import EmailError

        email_tools._send_timestamps = [time.monotonic() for _ in range(10)]
        with pytest.raises(EmailError, match="Rate-Limit"):
            await email_tools.email_send(
                to="recipient@example.com",
                subject="Test",
                body="Hello",
            )

    async def test_send_with_attachment(self, email_tools: Any, tmp_path: Path) -> None:
        """Send with valid attachment succeeds."""
        att_file = tmp_path / "report.pdf"
        att_file.write_text("fake pdf")

        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("cognithor.mcp.email_tools.smtplib.SMTP_SSL", return_value=mock_smtp):
            result = await email_tools.email_send(
                to="recipient@example.com",
                subject="Report",
                body="See attached.",
                attachments=[str(att_file)],
            )
        assert "1" in result  # 1 attachment

    async def test_send_starttls(
        self, email_config: CognithorConfig, mock_env_password: Any
    ) -> None:
        """STARTTLS port (587) uses SMTP instead of SMTP_SSL."""
        from cognithor.mcp.email_tools import EmailTools

        email_config.email.smtp_port = 587
        tools = EmailTools(email_config)

        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("cognithor.mcp.email_tools.smtplib.SMTP", return_value=mock_smtp):
            result = await tools.email_send(
                to="recipient@example.com",
                subject="Test",
                body="Hello",
            )
        assert "erfolgreich" in result

    async def test_send_multiple_recipients(self, email_tools: Any) -> None:
        """Sending to multiple recipients succeeds."""
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("cognithor.mcp.email_tools.smtplib.SMTP_SSL", return_value=mock_smtp):
            result = await email_tools.email_send(
                to="a@example.com, b@example.com",
                subject="Test",
                body="Hello all",
            )
        assert "erfolgreich" in result


# ── Email Summarize ────────────────────────────────────────────────────────


class TestEmailSummarize:
    """Tests for email_summarize."""

    async def test_summarize_empty(self, email_tools: Any) -> None:
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"0"])
        mock_conn.search.return_value = ("OK", [b""])

        with patch.object(email_tools, "_get_imap_connection", return_value=mock_conn):
            result = await email_tools.email_summarize()
        assert "Keine E-Mails" in result or "no_emails" in result

    async def test_summarize_with_emails(self, email_tools: Any) -> None:
        mock_conn = MagicMock()
        mock_conn.select.return_value = ("OK", [b"3"])
        mock_conn.search.return_value = ("OK", [b"1 2 3"])

        raw1 = _make_raw_email(from_addr="alice@example.com", subject="Project Update")
        raw2 = _make_raw_email(from_addr="alice@example.com", subject="Re: Project Update")
        raw3 = _make_raw_email(from_addr="bob@example.com", subject="Meeting Notes")

        mock_conn.fetch.side_effect = [
            ("OK", [(b"1 (RFC822 {100}", raw1)]),
            ("OK", [(b"2 (RFC822 {100}", raw2)]),
            ("OK", [(b"3 (RFC822 {100}", raw3)]),
        ]

        with patch.object(email_tools, "_get_imap_connection", return_value=mock_conn):
            result = await email_tools.email_summarize(count=10)

        assert "Zusammenfassung" in result
        assert "alice@example.com" in result or "alice" in result
        assert "Absender" in result


# ── Tool Registration ──────────────────────────────────────────────────────


class TestRegistration:
    """Tests for register_email_tools."""

    def test_register_when_enabled(
        self, email_config: CognithorConfig, mock_env_password: Any
    ) -> None:
        from cognithor.mcp.email_tools import register_email_tools

        mcp = MagicMock()
        result = register_email_tools(mcp, email_config)
        assert result is not None
        assert mcp.register_builtin_handler.call_count == 4

    def test_register_when_disabled(self, email_config_disabled: CognithorConfig) -> None:
        from cognithor.mcp.email_tools import register_email_tools

        mcp = MagicMock()
        result = register_email_tools(mcp, email_config_disabled)
        assert result is None
        assert mcp.register_builtin_handler.call_count == 0

    def test_register_without_password(self, email_config: CognithorConfig) -> None:
        from cognithor.mcp.email_tools import register_email_tools

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("TEST_EMAIL_PASSWORD", None)
            mcp = MagicMock()
            result = register_email_tools(mcp, email_config)
            assert result is None

    def test_register_without_host(self, tmp_path: Path, mock_env_password: Any) -> None:
        from cognithor.mcp.email_tools import register_email_tools

        config = CognithorConfig(
            cognithor_home=tmp_path / ".cognithor",
            email={
                "enabled": True,
                "imap_host": "",
                "smtp_host": "",
                "username": "test@example.com",
                "password_env": "TEST_EMAIL_PASSWORD",
            },
        )
        mcp = MagicMock()
        result = register_email_tools(mcp, config)
        assert result is None

    def test_registered_tool_names(
        self, email_config: CognithorConfig, mock_env_password: Any
    ) -> None:
        from cognithor.mcp.email_tools import register_email_tools

        mcp = MagicMock()
        register_email_tools(mcp, email_config)

        registered_names = [call[0][0] for call in mcp.register_builtin_handler.call_args_list]
        assert "email_read_inbox" in registered_names
        assert "email_search" in registered_names
        assert "email_send" in registered_names
        assert "email_summarize" in registered_names
