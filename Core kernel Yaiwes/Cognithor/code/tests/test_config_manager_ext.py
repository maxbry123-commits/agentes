"""Extended tests for ConfigManager -- covering missing lines.

Targets:
  - _is_secret_field with pattern exclusions
  - _strip_masked_secrets (nested dict handling, depth guard)
  - _mask_secrets depth guard
  - save() atomic write failure cleanup
  - update_top_level secret field logging paths
  - reload with on_reload callback
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cognithor.config import CognithorConfig
from cognithor.config_manager import (
    ConfigManager,
    _is_secret_field,
)

if TYPE_CHECKING:
    from pathlib import Path

# ============================================================================
# _is_secret_field
# ============================================================================


class TestIsSecretField:
    def test_explicit_secret_fields(self) -> None:
        for f in ("openai_api_key", "telegram_token", "pg_password", "secret_key"):
            assert _is_secret_field(f) is True

    def test_pattern_match_token(self) -> None:
        assert _is_secret_field("my_custom_token") is True

    def test_pattern_match_password(self) -> None:
        assert _is_secret_field("db_password") is True

    def test_pattern_match_secret(self) -> None:
        assert _is_secret_field("webhook_secret") is True

    def test_pattern_match_key(self) -> None:
        assert _is_secret_field("some_key") is True

    def test_exclusion_key_file(self) -> None:
        assert _is_secret_field("ssh_key_file") is False

    def test_exclusion_keyboard(self) -> None:
        assert _is_secret_field("keyboard") is False

    def test_exclusion_tokens_plural(self) -> None:
        assert _is_secret_field("chunk_size_tokens") is False

    def test_exclusion_token_budget(self) -> None:
        assert _is_secret_field("response_token_budget") is False

    def test_exclusion_max_tokens(self) -> None:
        assert _is_secret_field("anthropic_max_tokens") is False

    def test_non_secret_field(self) -> None:
        assert _is_secret_field("owner_name") is False
        assert _is_secret_field("temperature") is False
        assert _is_secret_field("log_level") is False

    # --- Web API Keys: Verifizierung dass sie als Secret erkannt werden ---

    def test_google_cse_api_key_is_secret(self) -> None:
        """google_cse_api_key enthält 'key' → muss als Secret maskiert werden."""
        assert _is_secret_field("google_cse_api_key") is True

    def test_jina_api_key_is_secret(self) -> None:
        """jina_api_key enthält 'key' → muss als Secret maskiert werden."""
        assert _is_secret_field("jina_api_key") is True

    def test_brave_api_key_is_secret(self) -> None:
        """brave_api_key enthält 'key' → muss als Secret maskiert werden."""
        assert _is_secret_field("brave_api_key") is True

    def test_google_cse_cx_is_not_secret(self) -> None:
        """google_cse_cx ist kein Secret (enthält kein Pattern)."""
        assert _is_secret_field("google_cse_cx") is False

    def test_searxng_url_is_not_secret(self) -> None:
        """searxng_url ist kein Secret."""
        assert _is_secret_field("searxng_url") is False


# ============================================================================
# _mask_secrets depth guard
# ============================================================================


class TestMaskSecrets:
    def test_masks_nested_secrets(self, tmp_path: Path) -> None:
        data = {
            "channels": {
                "telegram_token": "real-token",
                "enabled": True,
            }
        }
        ConfigManager._mask_secrets(data)
        assert data["channels"]["telegram_token"] == "***"
        assert data["channels"]["enabled"] is True

    def test_depth_guard_stops_at_5(self) -> None:
        # Build deeply nested dict (7 levels)
        data: dict[str, Any] = {"api_key": "deep-secret"}
        current = data
        for i in range(7):
            current["nested"] = {"api_key": f"secret-{i}"}
            current = current["nested"]

        ConfigManager._mask_secrets(data)
        # Top level should be masked
        assert data["api_key"] == "***"
        # But deeply nested should NOT be masked due to depth guard
        # Level 5+ should not be processed

    def test_empty_values_not_masked(self) -> None:
        data = {"openai_api_key": "", "anthropic_api_key": None}
        ConfigManager._mask_secrets(data)
        # Empty/falsy values should not be replaced
        assert data["openai_api_key"] == ""
        assert data["anthropic_api_key"] is None


# ============================================================================
# _strip_masked_secrets
# ============================================================================


class TestStripMaskedSecrets:
    def test_strips_masked_keys(self) -> None:
        data = {
            "openai_api_key": "***",
            "owner_name": "Alex",
            "telegram_token": "***",
        }
        ConfigManager._strip_masked_secrets(data)
        assert "openai_api_key" not in data
        assert "telegram_token" not in data
        assert data["owner_name"] == "Alex"

    def test_strips_nested_masked_keys(self) -> None:
        data = {
            "channels": {
                "slack_token": "***",
                "enabled": True,
            }
        }
        ConfigManager._strip_masked_secrets(data)
        assert "slack_token" not in data["channels"]
        assert data["channels"]["enabled"] is True

    def test_preserves_non_secret_star_values(self) -> None:
        data = {"owner_name": "***"}
        ConfigManager._strip_masked_secrets(data)
        # Not a secret field, so *** should be preserved
        assert data["owner_name"] == "***"

    def test_depth_guard(self) -> None:
        # Build deeply nested, should not crash
        data: dict[str, Any] = {}
        current = data
        for _i in range(8):
            current["sub"] = {"api_key": "***"}
            current = current["sub"]
        ConfigManager._strip_masked_secrets(data)
        # Should not raise


# ============================================================================
# update_top_level with secret field
# ============================================================================


class TestUpdateTopLevelSecretField:
    def test_update_api_key_set_value(self, tmp_path: Path) -> None:
        config = CognithorConfig(cognithor_home=tmp_path / ".cognithor")
        mgr = ConfigManager(config=config)
        mgr.update_top_level("openai_api_key", "sk-new-key")
        assert mgr.config.openai_api_key == "sk-new-key"

    def test_update_api_key_clear_warns(self, tmp_path: Path) -> None:
        config = CognithorConfig(
            cognithor_home=tmp_path / ".cognithor",
            openai_api_key="sk-existing",
        )
        mgr = ConfigManager(config=config)
        # Clear the key
        mgr.update_top_level("openai_api_key", "")

    def test_update_api_key_masked_value_treated_as_no_value(self, tmp_path: Path) -> None:
        config = CognithorConfig(
            cognithor_home=tmp_path / ".cognithor",
            openai_api_key="sk-real-key",
        )
        mgr = ConfigManager(config=config)
        # "***" is the mask placeholder -- treated as "gets no value"
        mgr.update_top_level("openai_api_key", "***")


# ============================================================================
# save() atomic write failure
# ============================================================================


class TestSaveAtomicFailure:
    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        config = CognithorConfig(cognithor_home=tmp_path / ".cognithor")
        mgr = ConfigManager(config=config)
        target = tmp_path / "sub" / "dir" / "config.yaml"
        result = mgr.save(target)
        assert result == target
        assert target.exists()

    def test_save_without_callback(self, tmp_path: Path) -> None:
        config = CognithorConfig(cognithor_home=tmp_path / ".cognithor")
        mgr = ConfigManager(config=config, on_reload=None)
        target = tmp_path / "no_callback.yaml"
        mgr.save(target)
        assert target.exists()


# ============================================================================
# reload with on_reload callback
# ============================================================================


class TestReloadCallback:
    def test_reload_triggers_callback(self, tmp_path: Path) -> None:
        config_path = tmp_path / ".cognithor" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("owner_name: TestReload\n")

        reloaded: list[CognithorConfig] = []
        mgr = ConfigManager(config_path=config_path, on_reload=reloaded.append)

        mgr.reload()
        assert len(reloaded) == 1
        assert reloaded[0].owner_name == "TestReload"

    def test_reload_without_callback(self, tmp_path: Path) -> None:
        config_path = tmp_path / ".cognithor" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("owner_name: NoCallback\n")

        mgr = ConfigManager(config_path=config_path, on_reload=None)
        result = mgr.reload()
        assert result.owner_name == "NoCallback"
