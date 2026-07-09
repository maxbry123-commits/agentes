# OpenClaw — en repo agentes

OpenClaw es el ORQUESTADOR del sistema. Vive como servicio systemd en el VPS (`systemctl status openclaw`).
Este directorio contiene su configuración versionada para que se pueda restaurar/replicar.

## Identidad
- **Servicio systemd**: `openclaw.service`
- **Puerto**: 18789 (loopback)
- **Provider**: Cerebras nativo (plugin oficial `@openclaw/cerebras-provider`)
- **Modelos**: `cerebras/gpt-oss-120b` (default) + `cerebras/gemma-4-31b` (fast)
- **API keys**: 2 perfiles en `auth-profiles` de OpenClaw (primary + failover)

## Como el grupo A y B se conectan
OpenClaw **NO invoca** directamente a claude-code-vps o mimo-code-vps. Es un gateway HTTP.
Los clientes externos (Telegram bot, web UI, scripts) hacen requests a `http://127.0.0.1:18789/...`
y OpenClaw enruta a cerebras directamente.

Los grupos A y B (claude/mimo code) usan LiteLLM (puerto 4000) que es OTRO gateway.
LiteLLM -> cerebras (con los 4 modelos: coder/verifier + failovers).
