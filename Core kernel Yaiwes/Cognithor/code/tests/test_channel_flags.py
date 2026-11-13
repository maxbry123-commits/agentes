"""Tests for channel-specific behavioral flags.

Tests:
  - All defined channel profiles
  - Default flags for unknown channels
  - Specific flag values per channel
"""

from __future__ import annotations

from cognithor.core.channel_flags import (
    CHANNEL_PROFILES,
    ChannelFlags,
    get_channel_flags,
)


class TestChannelProfiles:
    """All defined channel profiles return correct flags."""

    def test_telegram_profile(self) -> None:
        flags = get_channel_flags("telegram")
        assert flags.token_efficient is True
        assert flags.compact_output is True
        assert flags.max_response_length == 4000

    def test_discord_profile(self) -> None:
        flags = get_channel_flags("discord")
        assert flags.compact_output is True
        assert flags.max_response_length == 2000
        assert flags.allow_markdown is True

    def test_slack_profile(self) -> None:
        flags = get_channel_flags("slack")
        assert flags.max_response_length == 3000
        assert flags.allow_markdown is True
        assert flags.token_efficient is False

    def test_webui_profile(self) -> None:
        flags = get_channel_flags("webui")
        assert flags.typing_indicator is True
        assert flags.compact_output is False
        assert flags.max_response_length is None

    def test_cli_profile(self) -> None:
        flags = get_channel_flags("cli")
        assert flags.token_efficient is False
        assert flags.compact_output is False
        assert flags.max_response_length is None
        assert flags.allow_markdown is True
        assert flags.allow_code_blocks is True

    def test_voice_profile(self) -> None:
        flags = get_channel_flags("voice")
        assert flags.token_efficient is True
        assert flags.compact_output is True
        assert flags.max_response_length == 500
        assert flags.allow_markdown is False
        assert flags.allow_code_blocks is False

    def test_whatsapp_profile(self) -> None:
        flags = get_channel_flags("whatsapp")
        assert flags.token_efficient is True
        assert flags.compact_output is True
        assert flags.max_response_length == 4000
        assert flags.allow_markdown is False

    def test_signal_profile(self) -> None:
        flags = get_channel_flags("signal")
        assert flags.token_efficient is True
        assert flags.compact_output is True
        assert flags.max_response_length == 4000

    def test_matrix_profile(self) -> None:
        flags = get_channel_flags("matrix")
        assert flags.max_response_length == 4000
        assert flags.allow_markdown is True

    def test_irc_profile(self) -> None:
        flags = get_channel_flags("irc")
        assert flags.token_efficient is True
        assert flags.compact_output is True
        assert flags.max_response_length == 500
        assert flags.allow_markdown is False

    def test_teams_profile(self) -> None:
        flags = get_channel_flags("teams")
        assert flags.max_response_length == 3000
        assert flags.allow_markdown is True

    def test_twitch_profile(self) -> None:
        flags = get_channel_flags("twitch")
        assert flags.token_efficient is True
        assert flags.compact_output is True
        assert flags.max_response_length == 500
        assert flags.allow_code_blocks is False


class TestDefaultFlags:
    """Unknown channels return default ChannelFlags."""

    def test_unknown_channel_returns_default(self) -> None:
        flags = get_channel_flags("unknown_channel_xyz")
        assert flags.token_efficient is False
        assert flags.compact_output is False
        assert flags.safe_mode is False
        assert flags.max_response_length is None
        assert flags.allow_markdown is True
        assert flags.allow_code_blocks is True
        assert flags.typing_indicator is True

    def test_empty_string_returns_default(self) -> None:
        flags = get_channel_flags("")
        default = ChannelFlags()
        assert flags == default

    def test_case_sensitive(self) -> None:
        """Channel names are case-sensitive (all lowercase)."""
        flags_lower = get_channel_flags("telegram")
        flags_upper = get_channel_flags("Telegram")
        assert flags_lower.token_efficient is True
        assert flags_upper.token_efficient is False  # Falls through to default


class TestChannelFlagsDataclass:
    """ChannelFlags dataclass defaults."""

    def test_default_values(self) -> None:
        cf = ChannelFlags()
        assert cf.token_efficient is False
        assert cf.compact_output is False
        assert cf.safe_mode is False
        assert cf.max_response_length is None
        assert cf.allow_markdown is True
        assert cf.allow_code_blocks is True
        assert cf.typing_indicator is True

    def test_custom_values(self) -> None:
        cf = ChannelFlags(
            token_efficient=True,
            safe_mode=True,
            max_response_length=1000,
        )
        assert cf.token_efficient is True
        assert cf.safe_mode is True
        assert cf.max_response_length == 1000


class TestAllProfilesComplete:
    """Ensure all profiles in CHANNEL_PROFILES are valid ChannelFlags."""

    def test_all_profiles_are_channel_flags(self) -> None:
        for channel, flags in CHANNEL_PROFILES.items():
            assert isinstance(flags, ChannelFlags), f"Profile {channel} is not ChannelFlags"

    def test_minimum_profiles_exist(self) -> None:
        """At least the core channels should have profiles."""
        required = {"telegram", "discord", "slack", "webui", "cli", "voice", "whatsapp"}
        assert required.issubset(set(CHANNEL_PROFILES.keys()))
