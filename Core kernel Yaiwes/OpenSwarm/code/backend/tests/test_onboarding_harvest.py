"""Usage-harvest tests: chatgpt/claude summaries + the browser-cookie read path (all fail-open)."""

import base64
import json

import pytest

def test_summarize_chatgpt_usage_leads_with_memory_and_caps():
    from backend.apps.onboarding.usage.chatgpt_usage import TOTAL_CONVO_CHARS, summarize_chatgpt_usage

    s = summarize_chatgpt_usage(
        812,
        ["Has an Akita", "Squats 495"],
        ["Swift concurrency", "Deadlift form"],
        ["User: fix my squat form?\nAssistant: brace harder."],
    )
    assert "812 past AI conversations" in s
    assert "Has an Akita; Squats 495" in s
    assert "Swift concurrency; Deadlift form" in s
    assert "fix my squat form?" in s
    big = summarize_chatgpt_usage(
        1000,
        [],
        [f"t{i}x" for i in range(1000)],
        ["c" * 60000 for _ in range(10)],
    )
    assert "t149x" in big and "t150x" not in big
    convo_block = big.split("real asks + the exchange")[1]
    assert len(convo_block) <= TOTAL_CONVO_CHARS + 10000


@pytest.mark.asyncio
async def test_harvest_chatgpt_usage_fails_open_without_codex(monkeypatch):
    from backend.apps.onboarding.usage import chatgpt_usage

    monkeypatch.setattr(chatgpt_usage, "read_persisted_connections", lambda: [])
    assert await chatgpt_usage.harvest_chatgpt_usage() == ""


def test_read_provider_cookies_fails_open_without_a_store(monkeypatch):
    from backend.apps.onboarding.usage import browser_cookies

    # No browser store has the domain -> empty jar/records, and the keychain is never touched.
    monkeypatch.setattr(browser_cookies, "p_best_store", lambda domain: None)
    assert browser_cookies.read_provider_cookies("claude.ai") == {}
    assert browser_cookies.read_provider_cookie_records("claude.ai") == []


def test_win_storage_key_parses_local_state_and_unwraps(monkeypatch, tmp_path):
    from backend.apps.onboarding.usage import browser_cookies

    # Local State carries a base64 "DPAPI"-prefixed key; the Windows path strips the prefix and
    # hands the rest to CryptUnprotectData. Prove the parse + prefix-strip without needing Windows.
    raw_key = b"DPAPI" + b"wrapped-key-bytes"
    local_state_dir = tmp_path / "UserData"
    local_state_dir.mkdir()
    (local_state_dir / "Local State").write_text(
        json.dumps({"os_crypt": {"encrypted_key": base64.b64encode(raw_key).decode()}})
    )
    monkeypatch.setattr(browser_cookies, "CHROMIUM_ROOTS", {"Chrome": str(local_state_dir)})
    seen = {}

    def fake_unprotect(data: bytes):
        seen["passed"] = data
        return b"unwrapped-aes-key"

    monkeypatch.setattr(browser_cookies, "win_dpapi_unprotect", fake_unprotect)
    key = browser_cookies.win_storage_key("Chrome")
    assert key == b"unwrapped-aes-key"
    assert seen["passed"] == b"wrapped-key-bytes"  # the 5-byte "DPAPI" prefix was stripped


def test_win_storage_key_fails_open(monkeypatch, tmp_path):
    from backend.apps.onboarding.usage import browser_cookies

    # Missing Local State, malformed JSON, and DPAPI failure all fail open to None (-> scan fallback).
    monkeypatch.setattr(browser_cookies, "CHROMIUM_ROOTS", {"Chrome": str(tmp_path)})
    assert browser_cookies.win_storage_key("Chrome") is None  # no Local State file
    assert browser_cookies.win_storage_key("Nonexistent") is None


def test_decrypt_rejects_app_bound_v20():
    from backend.apps.onboarding.usage import browser_cookies

    # v20 = app-bound encryption (modern Chrome), out of reach on both OSes -> None, never a crash.
    assert browser_cookies.decrypt_cookie_value(b"v20" + b"anything", b"\x00" * 32) is None
    assert browser_cookies.decrypt_cookie_value(b"", b"\x00" * 32) is None


def test_dump_cookies_only_serves_allowlisted_domains(monkeypatch, capsys):
    from backend.apps.onboarding.usage import dump_cookies

    # Patch the names in dump_cookies' own namespace, so a real read (+ keychain) never fires.
    monkeypatch.setattr(dump_cookies, "read_provider_cookie_records", lambda domain: [{"name": "x", "value": "y"}])
    monkeypatch.setattr(dump_cookies, "read_google_session_records", lambda: [{"name": "SID", "value": "g"}])
    # An off-list domain must never trigger a read, prints [].
    monkeypatch.setattr("sys.argv", ["dump_cookies", "evil.example.com"])
    dump_cookies.main()
    assert capsys.readouterr().out == "[]"
    # An allowlisted domain passes through to the reader.
    monkeypatch.setattr("sys.argv", ["dump_cookies", "claude.ai"])
    dump_cookies.main()
    assert '"name": "x"' in capsys.readouterr().out
    # Gemini routes to the SCOPED google reader, not a raw gemini.google.com read.
    monkeypatch.setattr("sys.argv", ["dump_cookies", "gemini.google.com"])
    dump_cookies.main()
    assert '"name": "SID"' in capsys.readouterr().out


def test_read_google_session_records_scopes_to_named_auth_cookies(monkeypatch):
    from backend.apps.onboarding.usage import browser_cookies

    seen_domain = {}

    def fake_records(domain: str):
        seen_domain["d"] = domain
        return [
            {"name": "SID", "value": "a"},
            {"name": "__Secure-1PSID", "value": "b"},
            {"name": "SEARCH_SAMESITE", "value": "c"},  # non-auth google cookie
            {"name": "OTZ", "value": "d"},  # non-auth google cookie
        ]

    monkeypatch.setattr(browser_cookies, "read_provider_cookie_records", fake_records)
    recs = browser_cookies.read_google_session_records()
    # Reads the parent SSO domain, then keeps ONLY the named auth cookies (never a full sweep).
    assert seen_domain["d"] == ".google.com"
    assert {r["name"] for r in recs} == {"SID", "__Secure-1PSID"}


def test_summarize_claude_usage_counts_and_caps():
    from backend.apps.onboarding.usage.claude_usage import TOTAL_CONVO_CHARS, summarize_claude_usage

    s = summarize_claude_usage(
        490,
        ["Yuji Itadori and Buddhism", "B2B SaaS Startup Ideas"],
        ["User: pitch me a startup\nAssistant: sure."],
    )
    assert "490 past Claude conversations" in s
    assert "Yuji Itadori and Buddhism; B2B SaaS Startup Ideas" in s
    assert "pitch me a startup" in s
    big = summarize_claude_usage(1000, [f"t{i}x" for i in range(1000)], ["c" * 60000 for _ in range(10)])
    assert "t149x" in big and "t150x" not in big
    convo_block = big.split("real asks + the exchange")[1]
    assert len(convo_block) <= TOTAL_CONVO_CHARS + 10000


@pytest.mark.asyncio
async def test_harvest_claude_usage_fails_open_without_cookies(monkeypatch):
    from backend.apps.onboarding.usage import claude_usage

    monkeypatch.setattr(claude_usage, "read_provider_cookies", lambda domain: {})
    assert await claude_usage.harvest_claude_usage() == ""
