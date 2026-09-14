"""Tests for the local PII redactor."""

from __future__ import annotations

import pytest

from cognithor.security.pii_redactor import PIIRedactor, _luhn_valid


class TestLuhnChecksum:
    def test_valid_visa_passes(self):
        assert _luhn_valid("4111111111111111")

    def test_valid_mastercard_passes(self):
        assert _luhn_valid("5500 0000 0000 0004")

    def test_invalid_fails(self):
        assert not _luhn_valid("4111111111111112")

    def test_too_short_fails(self):
        assert not _luhn_valid("1234567")

    def test_too_long_fails(self):
        assert not _luhn_valid("12345678901234567890")


class TestEmail:
    def test_redacts_standard(self):
        r = PIIRedactor(categories=["email"])
        out, matches = r.redact("Contact: alex.s@example.com for help")
        assert out == "Contact: [REDACTED:email] for help"
        assert len(matches) == 1
        assert matches[0].category == "email"

    def test_redacts_multiple(self):
        r = PIIRedactor(categories=["email"])
        out, matches = r.redact("alice@foo.com or bob@bar.co.uk")
        assert out == "[REDACTED:email] or [REDACTED:email]"
        assert len(matches) == 2

    def test_preserves_surrounding_punctuation(self):
        r = PIIRedactor(categories=["email"])
        out, _ = r.redact("Send to foo@bar.com, then reply.")
        assert out == "Send to [REDACTED:email], then reply."

    def test_no_false_positive_on_url(self):
        r = PIIRedactor(categories=["email"])
        out, matches = r.redact("Visit https://example.com")
        assert matches == []
        assert out == "Visit https://example.com"


class TestPhone:
    def test_redacts_e164(self):
        r = PIIRedactor(categories=["phone"])
        out, matches = r.redact("Call +49 30 12345678 tomorrow")
        assert "[REDACTED:phone]" in out
        assert len(matches) == 1

    def test_redacts_us_format(self):
        r = PIIRedactor(categories=["phone"])
        out, matches = r.redact("My number is (555) 123-4567")
        assert "[REDACTED:phone]" in out
        assert len(matches) == 1

    def test_no_false_positive_on_year(self):
        # Years and small numeric IDs should not trip the phone pattern.
        r = PIIRedactor(categories=["phone"])
        _, matches = r.redact("The year 2024 was good")
        assert matches == []


class TestApiKey:
    def test_redacts_openai(self):
        r = PIIRedactor(categories=["api_key"])
        text = "key=sk-proj-abc123def456ghi789jkl012mno345"
        out, matches = r.redact(text)
        assert "[REDACTED:api_key]" in out
        assert len(matches) == 1

    def test_redacts_github_pat(self):
        r = PIIRedactor(categories=["api_key"])
        text = "token: gho_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        out, matches = r.redact(text)
        assert "[REDACTED:api_key]" in out

    def test_redacts_aws_access_key(self):
        r = PIIRedactor(categories=["api_key"])
        text = "AKIAIOSFODNN7EXAMPLE"
        out, matches = r.redact(text)
        assert out == "[REDACTED:api_key]"
        assert len(matches) == 1

    def test_redacts_google_api_key(self):
        r = PIIRedactor(categories=["api_key"])
        text = "AIzaSyABCDEF1234567890abcdef1234567890ABCD"
        out, matches = r.redact(text)
        assert out == "[REDACTED:api_key]"

    def test_no_false_positive_on_random_base64(self):
        r = PIIRedactor(categories=["api_key"])
        text = "hash: YWJjZGVmZ2hpamtsbW5vcHFy=="
        _, matches = r.redact(text)
        assert matches == []


class TestCreditCard:
    def test_redacts_valid_visa(self):
        r = PIIRedactor(categories=["credit_card"])
        out, matches = r.redact("Card: 4111 1111 1111 1111")
        assert "[REDACTED:credit_card]" in out
        assert len(matches) == 1

    def test_rejects_invalid_luhn(self):
        r = PIIRedactor(categories=["credit_card"])
        _, matches = r.redact("Fake number 4111 1111 1111 1112")
        assert matches == []


class TestSSN:
    def test_redacts(self):
        r = PIIRedactor(categories=["ssn"])
        out, matches = r.redact("SSN: 123-45-6789 on file")
        assert out == "SSN: [REDACTED:ssn] on file"
        assert len(matches) == 1

    def test_rejects_invalid_prefix(self):
        r = PIIRedactor(categories=["ssn"])
        _, matches = r.redact("000-12-3456")
        assert matches == []


class TestIban:
    def test_redacts(self):
        r = PIIRedactor(categories=["iban"])
        out, matches = r.redact("IBAN: DE89370400440532013000 please send funds")
        assert "[REDACTED:iban]" in out
        assert len(matches) == 1


class TestPrivateKey:
    def test_redacts_pem_block(self):
        r = PIIRedactor(categories=["private_key"])
        text = (
            "here is my key:\n"
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEowIBAAKCAQEA...lots of base64...\n"
            "-----END RSA PRIVATE KEY-----\n"
            "please keep safe"
        )
        out, matches = r.redact(text)
        assert "MIIEowIBAAKCAQEA" not in out
        assert "[REDACTED:private_key]" in out
        assert len(matches) == 1


class TestMultiCategory:
    def test_multiple_categories_in_one_text(self):
        r = PIIRedactor()
        text = "Contact alice@foo.com, card 4111111111111111, SSN 123-45-6789"
        out, matches = r.redact(text)
        categories = {m.category for m in matches}
        assert categories == {"email", "credit_card", "ssn"}
        assert "alice@foo.com" not in out
        assert "4111111111111111" not in out
        assert "123-45-6789" not in out

    def test_filters_by_configured_categories(self):
        r = PIIRedactor(categories=["email"])
        text = "alice@foo.com and 123-45-6789"
        out, matches = r.redact(text)
        assert out == "[REDACTED:email] and 123-45-6789"
        assert len(matches) == 1


class TestOverlaps:
    def test_longer_match_wins_on_overlap(self):
        # A credit-card-shaped number should not be cut into smaller
        # phone-number pieces.
        r = PIIRedactor(categories=["phone", "credit_card"])
        out, matches = r.redact("My card: 4111 1111 1111 1111")
        # Credit card spans the whole number; no separate phone match
        # should appear inside it.
        cat_counts: dict[str, int] = {}
        for m in matches:
            cat_counts[m.category] = cat_counts.get(m.category, 0) + 1
        assert cat_counts.get("credit_card", 0) == 1
        # The entire card is replaced; no residual digit fragments remain.
        assert "4111" not in out


class TestReplacementTemplate:
    def test_custom_template(self):
        r = PIIRedactor(
            categories=["email"],
            replacement_template="<<redacted {category}>>",
        )
        out, _ = r.redact("mail alice@foo.com now")
        assert out == "mail <<redacted email>> now"


class TestMessageLevel:
    def test_redacts_content_fields(self):
        r = PIIRedactor(categories=["email"])
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "email me at alice@foo.com"},
            {"role": "assistant", "content": "sure"},
        ]
        out, matches = r.redact_messages(messages)
        assert out[0]["content"] == "You are helpful."
        assert out[1]["content"] == "email me at [REDACTED:email]"
        assert out[2]["content"] == "sure"
        assert len(matches) == 1

    def test_does_not_mutate_input(self):
        r = PIIRedactor(categories=["email"])
        original = [{"role": "user", "content": "alice@foo.com"}]
        _, _ = r.redact_messages(original)
        # Input dict + list must be untouched.
        assert original[0]["content"] == "alice@foo.com"

    def test_handles_empty_messages(self):
        r = PIIRedactor(categories=["email"])
        out, matches = r.redact_messages([])
        assert out == []
        assert matches == []

    def test_handles_missing_content(self):
        r = PIIRedactor(categories=["email"])
        out, matches = r.redact_messages([{"role": "system"}])  # no content
        assert out == [{"role": "system"}]
        assert matches == []


class TestDisabledCategories:
    def test_empty_categories_noop(self):
        r = PIIRedactor(categories=[])
        text = "alice@foo.com"
        out, matches = r.redact(text)
        assert out == text
        assert matches == []


class TestConfigIntegration:
    def test_config_default_disabled(self):
        """Default config must leave PII redactor disabled (backward compat)."""
        from cognithor.config import CognithorConfig

        cfg = CognithorConfig()
        assert cfg.security.pii_redactor.enabled is False

    def test_config_accepts_enabled(self):
        from cognithor.config import CognithorConfig, PIIRedactorConfig

        cfg = CognithorConfig()
        cfg.security.pii_redactor = PIIRedactorConfig(enabled=True)
        assert cfg.security.pii_redactor.enabled is True

    def test_config_rejects_unknown_category(self):
        from pydantic import ValidationError

        from cognithor.config import PIIRedactorConfig

        with pytest.raises(ValidationError):
            PIIRedactorConfig(categories=["not_a_real_category"])  # type: ignore[list-item]
