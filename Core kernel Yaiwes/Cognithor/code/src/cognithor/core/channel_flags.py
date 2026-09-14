"""Channel-specific behavioral flags for response formatting.

Each channel has different constraints (message length, markdown support,
typing indicators, etc.). This module provides a centralized registry
of per-channel flags that the gateway and planner can use to adapt
output behavior.
"""

from __future__ import annotations

from dataclasses import dataclass

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class ChannelFlags:
    """Behavioral flags for a specific channel."""

    token_efficient: bool = False
    compact_output: bool = False
    safe_mode: bool = False
    max_response_length: int | None = None
    allow_markdown: bool = True
    allow_code_blocks: bool = True
    typing_indicator: bool = True


CHANNEL_PROFILES: dict[str, ChannelFlags] = {
    "telegram": ChannelFlags(
        token_efficient=True,
        compact_output=True,
        max_response_length=4000,
    ),
    "discord": ChannelFlags(
        compact_output=True,
        max_response_length=2000,
        allow_markdown=True,
    ),
    "slack": ChannelFlags(
        max_response_length=3000,
        allow_markdown=True,
    ),
    "webui": ChannelFlags(
        typing_indicator=True,
    ),
    "cli": ChannelFlags(),
    "voice": ChannelFlags(
        token_efficient=True,
        compact_output=True,
        max_response_length=500,
        allow_markdown=False,
        allow_code_blocks=False,
    ),
    "whatsapp": ChannelFlags(
        token_efficient=True,
        compact_output=True,
        max_response_length=4000,
        allow_markdown=False,
    ),
    "signal": ChannelFlags(
        token_efficient=True,
        compact_output=True,
        max_response_length=4000,
        allow_markdown=False,
    ),
    "matrix": ChannelFlags(
        max_response_length=4000,
        allow_markdown=True,
    ),
    "irc": ChannelFlags(
        token_efficient=True,
        compact_output=True,
        max_response_length=500,
        allow_markdown=False,
        allow_code_blocks=False,
    ),
    "teams": ChannelFlags(
        max_response_length=3000,
        allow_markdown=True,
    ),
    "twitch": ChannelFlags(
        token_efficient=True,
        compact_output=True,
        max_response_length=500,
        allow_markdown=False,
        allow_code_blocks=False,
    ),
}


def get_channel_flags(channel: str) -> ChannelFlags:
    """Get behavioral flags for the given channel.

    Returns default ChannelFlags for unknown channels.
    """
    return CHANNEL_PROFILES.get(channel, ChannelFlags())
