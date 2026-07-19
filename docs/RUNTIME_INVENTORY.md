 <t/runtime-baseline/RUNTIME_INVENTORY.md 2>/dev/null
# RUNTIME INVENTORY
Date: 2026-07-10T01:48:07Z

## OpenClaw
- nombre: openclaw
- version: OpenClaw 2026.6.11 (e085fa1)
- binary: lrwxrwxrwx 1 root root 41 Jul  9 22:14 /usr/bin/openclaw -> ../lib/node_modules/openclaw/openclaw.mjs
- install_path: /usr/lib/node_modules/openclaw/
- user: root
- permissions: 777 root:root
- env: OPENCLAW_GATEWAY_PORT=18789
- config: /root/.openclaw/openclaw.json
- port: 127.0.0.1:18789
- process: openclaw-gateway.service (systemd user)
- start: systemctl --user start openclaw-gateway
- stop: systemctl --user stop openclaw-gateway
- restart: systemctl --user restart openclaw-gateway
- health: curl http://127.0.0.1:18789/health

## Claude Code
- nombre: claude
- version: 2.1.205 (Claude Code)
- binary: lrwxrwxrwx 1 root root 42 Jul  9 22:13 /root/.local/bin/claude -> /root/.local/share/claude/versions/2.1.205
lrwxrwxrwx 1 root root 23 Jul  9 22:16 /usr/local/bin/claude -> /root/.local/bin/claude
- install_path: /root/.local/share/claude/versions/2.1.205
- user: root
- permissions: 777 root:root
- env: ANTHROPIC_BASE_URL=http://127.0.0.1:4000, ANTHROPIC_MODEL=cerebras-coder
- config: /root/.claude/settings.json
- port: n/a (CLI one-shot)
- process: n/a (background supervisor sock /tmp/cc-daemon-0)
- start: n/a (CLI)
- stop: n/a
- restart: n/a
- health: claude --version

## MiMo Code
- nombre: mimo (mimocode)
- version: 0.1.5
- binary: lrwxrwxrwx 1 root root 41 Jul  9 22:13 /usr/bin/mimo -> ../lib/node_modules/@mimo-ai/cli/bin/mimo
- install_path: /usr/lib/node_modules/@mimo-ai/cli/
- user: root
- permissions: 777 root:root
- env: MIMOCODE_SERVER_PASSWORD (unset), default bind 127.0.0.1:4096
- config: /root/.mimo/mimocode.json
- port: 127.0.0.1:4096
- process: mimocode serve (PID 71298)
- start: mimo serve --port 4096 --hostname 127.0.0.1
- stop: pkill -f mimocode
- restart: pkill -f mimocode && nohup mimo serve --port 4096 --hostname 127.0.0.1 > /opt/mimo-logs/serve.log 2>&1 &
- health: curl http://127.0.0.1:4096/global/health

## LiteLLM
- nombre: litellm
- version: litellm (venv /opt/nct/apps/litellm/venv)
- binary: /opt/nct/apps/litellm/venv/bin/litellm
- install_path: /opt/nct/apps/litellm/
- user: root
- config: /opt/litellm/cerebras-config.yaml
- port: 127.0.0.1:4000
- process: litellm.service (PID 28503)
- start: systemctl start litellm.service
- stop: systemctl stop litellm.service
- restart: systemctl restart litellm.service
- health: curl http://127.0.0.1:4000/health/liveliness

## Telegram Bot
- nombre: nct-telegram-bot
- version: bot.py custom (python-telegram-bot lib)
- binary: /usr/bin/python3 /opt/nct/telegram-bot/bot.py
- config: /opt/nct/secrets/providers/telegram.env
- chat_id: 1232223511 (whitelist Max)
- bot_username: @NCTTurboAssistantBot
- service: nct-telegram.service
- health: systemctl status nct-telegram.service
root@vmi3428294:~# echo 