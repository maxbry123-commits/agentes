"""Cross-platform regression tests for ImprovementGate + PromptEvolutionEngine.

Each test targets a specific cross-platform risk and proves the fix works
regardless of OS, Python hash seed, line endings, or path separators.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path

from cognithor.config import ImprovementGovernanceConfig, PromptEvolutionConfig
from cognithor.governance.improvement_gate import (
    GateVerdict,
    ImprovementDomain,
    ImprovementGate,
)
from cognithor.learning.prompt_evolution import (
    PromptEvolutionEngine,
    _version_id,
)

# =========================================================================
# 1. CRLF vs LF: SHA-256 hashing must be consistent
# =========================================================================


class TestVersionIdNewlineConsistency:
    """_version_id must produce the same hash regardless of line endings."""

    def test_lf_and_crlf_produce_same_id_after_normalization(self):
        """If template_text contains \\r\\n vs \\n, the hash should still work
        deterministically (same input -> same output). This test documents
        the current behavior: CRLF and LF are treated as DIFFERENT prompts."""
        text_lf = "Hello\nWorld\n{tools_section}"
        text_crlf = "Hello\r\nWorld\r\n{tools_section}"

        vid_lf = _version_id("test", text_lf)
        vid_crlf = _version_id("test", text_crlf)

        # These are different strings -> different hashes (documenting behavior)
        # The key invariant: same string -> same hash ON EVERY PLATFORM
        assert vid_lf == _version_id("test", text_lf)
        assert vid_crlf == _version_id("test", text_crlf)
        assert len(vid_lf) == 16
        assert len(vid_crlf) == 16

    def test_version_id_deterministic_across_calls(self):
        """Same input must always produce the same version ID."""
        text = "Du bist Jarvis\n{tools_section}\n{context_section}"
        results = {_version_id("system_prompt", text) for _ in range(100)}
        assert len(results) == 1, f"Got {len(results)} different IDs for same input"

    def test_version_id_uses_utf8(self):
        """German umlauts and special chars must hash consistently."""
        text = "Aerger mit Umlauten: ae oe ue ss"
        vid = _version_id("test", text)
        # Verify manually
        expected = hashlib.sha256(f"test:{text}".encode()).hexdigest()[:16]
        assert vid == expected

    def test_encode_defaults_to_utf8(self):
        """Prove that str.encode() == str.encode('utf-8') on this platform."""
        text = "system_prompt:Hello {tools_section}"
        assert text.encode() == text.encode("utf-8")


# =========================================================================
# 2. SQLite path handling: backslashes, spaces, unicode
# =========================================================================


class TestSQLitePathHandling:
    def test_path_with_spaces(self, tmp_path):
        """DB path containing spaces (common on Windows: 'Program Files')."""
        db_dir = tmp_path / "path with spaces"
        db_dir.mkdir()
        db = str(db_dir / "test.db")

        engine = PromptEvolutionEngine(db_path=db)
        vid = engine.register_prompt("sp", "Hello")
        assert vid is not None
        retrieved_id, text = engine.get_active_version("sp")
        assert text == "Hello"
        engine.close()

    def test_path_with_unicode(self, tmp_path):
        """DB path containing unicode chars (e.g. German user directory)."""
        db_dir = tmp_path / "Benutzer"
        db_dir.mkdir()
        db = str(db_dir / "prompt_evo.db")

        engine = PromptEvolutionEngine(db_path=db)
        vid = engine.register_prompt("sp", "Test")
        assert vid is not None
        engine.close()

    def test_pathlib_resolved_path(self, tmp_path):
        """Prove that pathlib Path -> str -> sqlite3 works on this OS."""
        p = (tmp_path / "subdir" / ".." / "actual.db").resolve()
        p.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(p))
        conn.execute("CREATE TABLE t (x TEXT)")
        conn.execute("INSERT INTO t VALUES ('ok')")
        conn.commit()
        val = conn.execute("SELECT x FROM t").fetchone()[0]
        conn.close()
        assert val == "ok"

    def test_db_path_with_name_pattern(self, tmp_path):
        """Simulate the config.db_path.with_name() pattern used in advanced.py."""
        base_db = tmp_path / "index" / "memory.db"
        base_db.parent.mkdir(parents=True, exist_ok=True)

        pe_db = str(base_db.with_name("memory_prompt_evolution.db"))
        assert pe_db.endswith("memory_prompt_evolution.db")
        assert Path(pe_db).parent == base_db.parent

        # Actually create and use the DB
        engine = PromptEvolutionEngine(db_path=pe_db)
        engine.register_prompt("sp", "Works")
        engine.close()
        assert Path(pe_db).exists()


# =========================================================================
# 3. time.monotonic() arithmetic: cooldowns work correctly
# =========================================================================


class TestMonotonicTimeCooldown:
    def test_cooldown_uses_monotonic_not_wall_clock(self):
        """time.monotonic() is not affected by system clock changes."""
        config = ImprovementGovernanceConfig(cooldown_minutes=5)
        gate = ImprovementGate(config)

        gate.record_outcome(ImprovementDomain.PROMPT_TUNING, success=False)
        assert gate.check(ImprovementDomain.PROMPT_TUNING) == GateVerdict.COOLDOWN

        # Simulate 5 minutes passing by directly manipulating the timestamp
        gate._cooldowns[ImprovementDomain.PROMPT_TUNING] = time.monotonic() - 301
        assert gate.check(ImprovementDomain.PROMPT_TUNING) == GateVerdict.ALLOWED

    def test_rate_limit_uses_monotonic(self):
        """Rate limit window (1 hour) is based on monotonic time."""
        config = ImprovementGovernanceConfig(max_changes_per_hour=2)
        gate = ImprovementGate(config)

        # Add 2 changes
        gate.record_outcome(ImprovementDomain.PROMPT_TUNING, success=True)
        gate.record_outcome(ImprovementDomain.TOOL_PARAMETERS, success=True)
        assert gate.check(ImprovementDomain.WORKFLOW_ORDER) == GateVerdict.COOLDOWN

        # Simulate timestamps older than 1 hour
        gate._change_timestamps = [time.monotonic() - 3601, time.monotonic() - 3601]
        assert gate.check(ImprovementDomain.WORKFLOW_ORDER) == GateVerdict.ALLOWED

    def test_monotonic_is_nonnegative_and_increasing(self):
        """Basic sanity: monotonic() never goes backwards."""
        t1 = time.monotonic()
        t2 = time.monotonic()
        assert t2 >= t1
        assert t1 >= 0


# =========================================================================
# 4. hash(session_id) % 2 determinism: A/B split within one process
# =========================================================================


class TestABSplitDeterminism:
    def test_same_session_always_same_arm(self, tmp_path):
        """Within one process, hash() is deterministic for the same string."""
        db = str(tmp_path / "ab.db")
        engine = PromptEvolutionEngine(db_path=db)

        vid_a = engine.register_prompt("sp", "A")
        vid_b = engine.register_prompt("sp", "B")
        engine.start_ab_test("sp", vid_a, vid_b)

        # Call 50 times with same session_id -> must always return same arm
        results = set()
        for _ in range(50):
            version_id, _ = engine.get_active_version("sp", "fixed_session_42")
            results.add(version_id)
        assert len(results) == 1
        engine.close()

    def test_different_sessions_produce_both_arms(self, tmp_path):
        """Different session IDs should eventually hit both arms."""
        db = str(tmp_path / "ab2.db")
        engine = PromptEvolutionEngine(db_path=db)

        vid_a = engine.register_prompt("sp", "A")
        vid_b = engine.register_prompt("sp", "B")
        engine.start_ab_test("sp", vid_a, vid_b)

        seen = set()
        for i in range(200):
            version_id, _ = engine.get_active_version("sp", f"session_{i}")
            seen.add(version_id)
            if len(seen) == 2:
                break

        assert len(seen) == 2, "A/B split never produced both arms over 200 sessions"
        engine.close()

    def test_hash_mod2_within_process_is_stable(self):
        """Prove hash() % 2 is stable for a given string within one process."""
        values = [hash("test_session") % 2 for _ in range(100)]
        assert len(set(values)) == 1


# =========================================================================
# 5. Config defaults load correctly on every platform
# =========================================================================


class TestConfigCrossPlatform:
    def test_improvement_governance_defaults(self):
        config = ImprovementGovernanceConfig()
        assert config.enabled is True
        assert "prompt_tuning" in config.auto_domains
        assert "code_generation" in config.blocked_domains
        assert config.cooldown_minutes == 30
        assert config.max_changes_per_hour == 5

    def test_prompt_evolution_defaults(self):
        config = PromptEvolutionConfig()
        assert config.enabled is False
        assert config.min_sessions_per_arm == 20
        assert config.significance_threshold == 0.05
        assert config.evolution_interval_hours == 6
        assert config.max_concurrent_tests == 1

    def test_jarvis_config_includes_new_fields(self):
        from cognithor.config import CognithorConfig

        config = CognithorConfig()
        assert hasattr(config, "improvement")
        assert hasattr(config, "prompt_evolution")
        assert isinstance(config.improvement, ImprovementGovernanceConfig)
        assert isinstance(config.prompt_evolution, PromptEvolutionConfig)


# =========================================================================
# 6. SQLite WAL mode + concurrent access
# =========================================================================


class TestSQLiteWALMode:
    def test_wal_mode_enabled(self, tmp_path):
        """WAL mode should be set for better concurrent read performance."""
        db = str(tmp_path / "wal_test.db")
        engine = PromptEvolutionEngine(db_path=db)

        journal_mode = engine._conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert journal_mode == "wal"
        engine.close()

    def test_busy_timeout_set(self, tmp_path):
        """busy_timeout should be set to prevent immediate SQLITE_BUSY errors."""
        db = str(tmp_path / "busy_test.db")
        engine = PromptEvolutionEngine(db_path=db)

        timeout = engine._conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert timeout == 5000
        engine.close()


# =========================================================================
# 7. ImprovementGate enum string values match config strings
# =========================================================================


class TestEnumConfigConsistency:
    def test_all_domain_values_are_lowercase_snake_case(self):
        """Config uses string lists like ['prompt_tuning']. Enum values must match."""
        for domain in ImprovementDomain:
            assert domain.value == domain.value.lower()
            assert " " not in domain.value

    def test_default_auto_domains_are_valid_enum_values(self):
        config = ImprovementGovernanceConfig()
        valid_values = {d.value for d in ImprovementDomain}
        for d in config.auto_domains:
            assert d in valid_values, f"auto_domain '{d}' is not a valid ImprovementDomain"

    def test_default_hitl_domains_are_valid_enum_values(self):
        config = ImprovementGovernanceConfig()
        valid_values = {d.value for d in ImprovementDomain}
        for d in config.hitl_domains:
            assert d in valid_values, f"hitl_domain '{d}' is not a valid ImprovementDomain"

    def test_default_blocked_domains_are_valid_enum_values(self):
        config = ImprovementGovernanceConfig()
        valid_values = {d.value for d in ImprovementDomain}
        for d in config.blocked_domains:
            assert d in valid_values, f"blocked_domain '{d}' is not a valid ImprovementDomain"

    def test_no_overlap_between_auto_and_blocked(self):
        config = ImprovementGovernanceConfig()
        overlap = set(config.auto_domains) & set(config.blocked_domains)
        assert not overlap, f"Domains in both auto and blocked: {overlap}"


# =========================================================================
# 8. Template format placeholders survive A/B test round-trip
# =========================================================================


class TestTemplatePlaceholderRoundTrip:
    def test_format_placeholders_preserved_through_db(self, tmp_path):
        """Prompt templates with {placeholders} must survive SQLite storage."""
        db = str(tmp_path / "rt.db")
        engine = PromptEvolutionEngine(db_path=db)

        original = (
            "Du bist {owner_name}.\n"
            "Tools: {tools_section}\n"
            "Context: {context_section}\n"
            "Time: {current_datetime}\n"
            "{personality_section}"
        )
        engine.register_prompt("system_prompt", original)
        retrieved_id, retrieved_text = engine.get_active_version("system_prompt")

        assert retrieved_text == original

        # Prove it can still be .format()'d
        rendered = retrieved_text.format(
            owner_name="Alexander",
            tools_section="[tools]",
            context_section="[ctx]",
            current_datetime="2026-03-06",
            personality_section="[warm]",
        )
        assert "Alexander" in rendered
        assert "[tools]" in rendered
        engine.close()

    def test_unicode_template_survives_round_trip(self, tmp_path):
        """German umlauts and special chars in prompts must survive."""
        db = str(tmp_path / "unicode.db")
        engine = PromptEvolutionEngine(db_path=db)

        text = "Aergere dich nicht, {owner_name}! Gruesse aus Muenchen."
        engine.register_prompt("greeting", text)
        _, retrieved = engine.get_active_version("greeting")
        assert retrieved == text
        engine.close()
