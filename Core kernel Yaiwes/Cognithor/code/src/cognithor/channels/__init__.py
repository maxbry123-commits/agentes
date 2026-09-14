"""Cognithor channels module.

Alle Kommunikationskanaele zwischen User und Gateway.
Bibel-Referenz: §9 (Gateway & Channels)
"""

from cognithor.channels.base import Channel, MessageHandler

# v22: Canvas
from cognithor.channels.canvas import CanvasManager
from cognithor.channels.commands import (
    CommandRegistry,
    InteractionStore,
)
from cognithor.channels.connectors import (
    ConnectorRegistry,
    JiraConnector,
    ServiceNowConnector,
    TeamsConnector,
)
from cognithor.channels.discord import DiscordChannel
from cognithor.channels.feishu import FeishuChannel

# v22: Neue Channels (lazy imports um optionale Dependencies zu vermeiden)
from cognithor.channels.google_chat import GoogleChatChannel
from cognithor.channels.interactive import (
    AdaptiveCard,
    DiscordMessageBuilder,
    FallbackRenderer,
    FormField,
    InteractionStateStore,
    ModalHandler,
    ProgressTracker,
    SignatureVerifier,
    SlackMessageBuilder,
    SlashCommandRegistry,
)
from cognithor.channels.irc import IRCChannel
from cognithor.channels.mattermost import MattermostChannel
from cognithor.channels.slack import SlackChannel
from cognithor.channels.twitch import TwitchChannel

__all__ = [
    "AdaptiveCard",
    "CanvasManager",
    "Channel",
    "CommandRegistry",
    "ConnectorRegistry",
    "DiscordChannel",
    "DiscordMessageBuilder",
    "FallbackRenderer",
    "FeishuChannel",
    "FormField",
    # v22: Neue Channels
    "GoogleChatChannel",
    "IRCChannel",
    "InteractionStateStore",
    "InteractionStore",
    "JiraConnector",
    "MattermostChannel",
    "MessageHandler",
    "ModalHandler",
    "ProgressTracker",
    "ServiceNowConnector",
    "SignatureVerifier",
    "SlackChannel",
    "SlackMessageBuilder",
    "SlashCommandRegistry",
    "TeamsConnector",
    "TwitchChannel",
]
