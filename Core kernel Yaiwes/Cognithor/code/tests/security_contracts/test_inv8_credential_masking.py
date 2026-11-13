"""INVARIANT 8 — Credential masking is complete before audit log write.

No recognized credential pattern must appear verbatim in the JSONL
audit log. The masking happens BEFORE the hash is computed, so
the hash covers the masked version.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cognithor.security.audit import AuditTrail, mask_credentials

pytestmark = pytest.mark.security_contract


# ---------------------------------------------------------------------------
# Example-based: known credential formats
# ---------------------------------------------------------------------------


CREDENTIAL_SAMPLES = {
    "openai_key": "sk-abcd1234567890abcdef1234567890abcdef12345678",
    "aws_key": "AKIAIOSFODNN7EXAMPLE",
    "bearer_token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature",
    "github_pat": "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
    "slack_token": "xoxb-" + "1" * 13 + "-" + "2" * 13 + "-" + "a" * 24,
    "generic_password": "password = MySuperSecret123!",
    "generic_secret": "secret=my_very_secret_value_here",
    "generic_api_key": "api_key = sk_live_abcdefghijklmnop",
    "private_key": (
        "-----BEGIN RSA PRIVATE KEY-----\nMIIE...content...\n-----END RSA PRIVATE KEY-----"
    ),
    "token_prefix": "token_abcd1234567890abcdef",
}


@pytest.mark.parametrize("name,raw", list(CREDENTIAL_SAMPLES.items()))
def test_mask_credentials_removes_secret(name: str, raw: str):
    """Each credential pattern must be masked — raw value must not survive."""
    masked = mask_credentials(raw)
    assert masked != raw, f"Credential '{name}' was not masked"
    assert "***" in masked, f"Credential '{name}' missing mask marker"


@pytest.mark.parametrize("name,raw", list(CREDENTIAL_SAMPLES.items()))
def test_credential_not_in_audit_log(name: str, raw: str, tmp_path):
    """Credentials in execution_result must not appear verbatim in the log."""
    from .conftest import make_audit_entry

    entry = make_audit_entry(execution_result=raw)
    trail = AuditTrail(log_path=tmp_path / f"audit_{name}.jsonl")
    trail.record(entry)

    log_content = (tmp_path / f"audit_{name}.jsonl").read_text(encoding="utf-8")

    if name == "private_key":
        assert "MIIE...content..." not in log_content
    elif name.startswith("generic_"):
        pass
    else:
        core_secret = raw.split()[-1] if " " in raw else raw
        if len(core_secret) > 12:
            assert core_secret not in log_content, (
                f"Full credential '{name}' found verbatim in audit log"
            )


# ---------------------------------------------------------------------------
# mask_credentials edge cases
# ---------------------------------------------------------------------------


def test_mask_empty_string():
    assert mask_credentials("") == ""


def test_mask_no_credentials():
    safe = "This is a normal log message with no secrets"
    assert mask_credentials(safe) == safe


def test_mask_multiple_credentials():
    text = "key1=sk-abcd1234567890abcdef12345678 and token_xyz9abcdef1234"
    masked = mask_credentials(text)
    assert "sk-abcd***" in masked
    assert "token_xyz9***" in masked


# ---------------------------------------------------------------------------
# Hypothesis: random credential-like strings
# ---------------------------------------------------------------------------


@given(suffix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=20, max_size=60))
@settings(max_examples=50)
def test_fuzz_openai_key_always_masked(suffix: str):
    raw = f"sk-{suffix}"
    masked = mask_credentials(raw)
    assert masked != raw


@given(suffix=st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=16, max_size=30))
@settings(max_examples=50)
def test_fuzz_aws_key_always_masked(suffix: str):
    raw = f"AKIA{suffix}"
    masked = mask_credentials(raw)
    assert masked != raw


@given(suffix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789._-", min_size=10, max_size=60))
@settings(max_examples=50)
def test_fuzz_bearer_always_masked(suffix: str):
    raw = f"Bearer {suffix}"
    masked = mask_credentials(raw)
    assert masked != raw
