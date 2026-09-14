"""Tests fuer den Trust-Resolver."""

from __future__ import annotations

import os
import tempfile

from cognithor.security.trust_resolver import TrustConfig, TrustResolver


class TestTrustResolver:
    def test_default_policy(self):
        resolver = TrustResolver()
        decision, reason = resolver.evaluate("/some/random/path")
        assert decision == "require_approval"
        assert "not in allowlist" in reason

    def test_allowlisted_path(self):
        with tempfile.TemporaryDirectory() as td:
            resolver = TrustResolver(TrustConfig(allowlisted=[td]))
            subdir = os.path.join(td, "subproject")
            os.makedirs(subdir, exist_ok=True)
            decision, reason = resolver.evaluate(subdir)
            assert decision == "auto_trust"
            assert td in reason

    def test_denied_path(self):
        resolver = TrustResolver(TrustConfig(denied=["/etc", "C:\\Windows"]))
        decision, reason = resolver.evaluate("/etc/passwd")
        assert decision == "deny"

    def test_denied_takes_precedence_over_default(self):
        resolver = TrustResolver(
            TrustConfig(
                denied=["/etc"],
                default_policy="auto_trust",
            )
        )
        decision, _ = resolver.evaluate("/etc/shadow")
        assert decision == "deny"

    def test_allowlist_over_default(self):
        with tempfile.TemporaryDirectory() as td:
            resolver = TrustResolver(
                TrustConfig(
                    allowlisted=[td],
                    default_policy="deny",
                )
            )
            decision, _ = resolver.evaluate(td)
            assert decision == "auto_trust"

    def test_custom_default_policy(self):
        resolver = TrustResolver(TrustConfig(default_policy="auto_trust"))
        decision, _ = resolver.evaluate("/tmp/whatever")
        assert decision == "auto_trust"


class TestTrustPromptDetection:
    def test_detects_english_prompt(self):
        resolver = TrustResolver()
        assert resolver.detect_trust_prompt_in_output("Do you trust the files in this folder?")

    def test_detects_german_prompt(self):
        resolver = TrustResolver()
        assert resolver.detect_trust_prompt_in_output("Vertrauen Sie diesem Ordner?")

    def test_no_false_positive(self):
        resolver = TrustResolver()
        assert not resolver.detect_trust_prompt_in_output("Build completed successfully.")


class TestFromJarvisConfig:
    def test_no_trust_config(self):
        class FakeConfig:
            pass

        resolver = TrustResolver.from_jarvis_config(FakeConfig())
        assert resolver._config.default_policy == "require_approval"

    def test_with_trust_config(self):
        class TrustCfg:
            allowlisted = ["/home/user"]
            denied = ["/etc"]
            default_policy = "deny"

        class FakeConfig:
            trust = TrustCfg()

        resolver = TrustResolver.from_jarvis_config(FakeConfig())
        assert resolver._config.allowlisted == ["/home/user"]
        assert resolver._config.denied == ["/etc"]
        assert resolver._config.default_policy == "deny"
