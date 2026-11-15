# Cognithor Channels Guide

> How to enable and configure communication channels.
> For implementing a custom channel, see [DEVELOPER.md](DEVELOPER.md#adding-a-channel).

## Available Channels

| Channel | Package Extra | Config Key | Status |
|---------|--------------|------------|--------|
| CLI | *(built-in)* | — | Default |
| WebUI | `web` | — | Default (port 8080) |
| Telegram | `telegram` | `COGNITHOR_TELEGRAM_TOKEN` | Production |
| Discord | `discord` | `COGNITHOR_DISCORD_TOKEN` | Production |
| Slack | `slack` | `COGNITHOR_SLACK_BOT_TOKEN` | Production |
| WhatsApp | *(external API)* | `COGNITHOR_WHATSAPP_TOKEN` | Beta |
| Signal | *(external API)* | — | Beta |
| Matrix | `matrix` | `COGNITHOR_MATRIX_HOMESERVER` | Production |
| IRC | `irc` | `COGNITHOR_IRC_SERVER` | Production |
| Mattermost | `slack` | `COGNITHOR_MATTERMOST_URL` | Beta |
| Teams | *(Azure SDK)* | `COGNITHOR_TEAMS_APP_ID` | Beta |
| Google Chat | *(google-api)* | `COGNITHOR_GCHAT_CREDENTIALS` | Beta |
| Feishu | *(built-in)* | `COGNITHOR_FEISHU_APP_ID` | Beta |
| iMessage | *(macOS only)* | — | Experimental |
| Twitch | `twitch` | `COGNITHOR_TWITCH_TOKEN` | Beta |
| Voice | `web` | — | Experimental |
| REST API | `web` | `COGNITHOR_API_TOKEN` | Production |

---

## Telegram

### Setup

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Set the token:
   ```bash
   export COGNITHOR_TELEGRAM_TOKEN="123456:ABC-DEF..."
   ```
3. Restrict access (recommended):
   ```bash
   export COGNITHOR_TELEGRAM_ALLOWED_USERS="12345678,87654321"
   ```
   Get your user ID by messaging [@userinfobot](https://t.me/userinfobot).

4. Enable in config:
   ```yaml
   channels:
     telegram:
       enabled: true
   ```

### Features

- Text messages with Markdown formatting
- Voice messages (auto-transcribed via Whisper)
- Photo/document uploads (auto-analyzed)
- ORANGE action approval via inline keyboards
- Streaming responses (token-by-token)
- Status updates (thinking, searching, executing)

---

## Discord

### Setup

1. Create a bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Enable **Message Content Intent** in Bot settings
3. Set the token:
   ```bash
   export COGNITHOR_DISCORD_TOKEN="MTIz..."
   ```
4. Invite bot to server with `bot` and `applications.commands` scopes

### Features

- Text and slash commands
- File upload handling
- Embed formatting for responses
- Multi-server support

---

## Slack

### Setup

1. Create a Slack App at [api.slack.com/apps](https://api.slack.com/apps)
2. Add Bot Token Scopes: `chat:write`, `im:history`, `im:read`
3. Install to workspace
4. Set tokens:
   ```bash
   export COGNITHOR_SLACK_BOT_TOKEN="xoxb-..."
   export COGNITHOR_SLACK_APP_TOKEN="xapp-..."  # Socket Mode
   ```

---

## Matrix

### Setup

1. Create a bot account on your Matrix homeserver
2. Configure:
   ```bash
   export COGNITHOR_MATRIX_HOMESERVER="https://matrix.example.com"
   export COGNITHOR_MATRIX_USER="@jarvis:example.com"
   export COGNITHOR_MATRIX_PASSWORD="..."
   ```

---

## WebUI

The WebUI runs automatically when starting Cognithor. No additional setup needed.

- **Development**: `cd ui && npm run dev` (Vite auto-launches backend)
- **Production**: WebUI is served at port 8080, backend at 8741

### WebSocket Protocol

See [API.md](API.md#websocket-protocol) for the complete message protocol.

---

## REST API

For programmatic access without WebSocket:

```bash
# Get auth token
TOKEN=$(curl -s http://localhost:8741/api/v1/bootstrap | jq -r .token)

# Send message
curl -X POST http://localhost:8741/api/v1/message \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "What time is it?"}'
```

See [API.md](API.md) for full endpoint reference.

---

## Multi-Channel Setup

Multiple channels can run simultaneously:

```yaml
channels:
  telegram:
    enabled: true
  discord:
    enabled: true
  slack:
    enabled: true
```

Each channel creates independent sessions. Memory and knowledge graph are
shared across all channels.
