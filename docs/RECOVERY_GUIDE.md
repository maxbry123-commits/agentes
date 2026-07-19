 </nct/runtime-baseline/RECOVERY_GUIDE.md 2>/dev/null
# RECOVERY GUIDE — orden exacto para reconstruir el VPS desde cero

## 0. Prerrequisitos
- VPS Ubuntu 24.04 LTS root, 11GB RAM, 6 vCPU, 193GB disco
- Acceso SSH + password root
- IPs: 95.111.232.89 (IPv4), 2a02:c207:2342:8294::1 (IPv6)

## 1. Instalación de los 4 agentes oficiales (en este orden)

### 1.1 OpenClaw
```
npm install -g openclaw@latest
openclaw daemon install --force
# configurar: openclaw models auth paste-api-key --provider cerebras --profile-id cerebras-primary
systemctl --user enable openclaw-gateway
systemctl --user start openclaw-gateway
```

### 1.2 Claude Code
```
curl -fsSL https://claude.ai/install.sh | bash
ln -sf /root/.local/bin/claude /usr/local/bin/claude
# config: /root/.claude/settings.json con ANTHROPIC_BASE_URL=http://127.0.0.1:4000
```

### 1.3 MiMo Code
```
npm install -g @mimo-ai/cli@latest
# Configurar /root/.mimo/mimocode.json con provider.openai.baseURL=http://127.0.0.1:4000/v1
nohup mimo serve --port 4096 --hostname 127.0.0.1 > /opt/mimo-logs/serve.log 2>&1 &
```

### 1.4 LiteLLM (Cerebras Router)
```
# Asumir venv en /opt/nct/apps/litellm/venv/
# Config en /opt/litellm/cerebras-config.yaml
systemctl enable litellm.service
systemctl start litellm.service
```

## 2. Configuración de OpenClaw (CRÍTICO)

El primary model debe ser `litellm/cerebras-coder` (router, no direct cerebras):

```python
# /root/.openclaw/openclaw.json
{
  "agents": {"defaults": {"model": {"primary": "litellm/cerebras-coder"}}},
  "models": {
    "providers": {
      "litellm": {
        "baseUrl": "http://127.0.0.1:4000/v1",
        "apiKey": "sk-mavis-cerebras-router",
        "api": "openai-completions",
        "models": [
          {"id": "cerebras-coder", "name": "cerebras-coder"},
          {"id": "cerebras-verifier", "name": "cerebras-verifier"},
          {"id": "cerebras-coder-failover", "name": "cerebras-coder-failover"},
          {"id": "cerebras-verifier-failover", "name": "cerebras-verifier-failover"}
        ]
      }
    }
  }
}
```

## 3. Verificación post-instalación

```bash
# Health checks (todos deben responder OK)
openclaw --version
claude --version
mimo --version
curl http://127.0.0.1:4000/health/liveliness

# Test funcional
openclaw agent --agent main --message-file <(echo "reply OK") --json
claude -p "reply OK"
mimo run --format json "reply OK" < /dev/null
curl -X POST http://127.0.0.1:4000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"cerebras-coder","messages":[{"role":"user","content":"reply OK"}],"max_tokens":15,"reasoning_effort":"none"}'
```

## 4. Servicios systemd requeridos

```bash
# /etc/systemd/system/litellm.service
# /etc/systemd/system/nct-open-webui.service
# /etc/systemd/system/nct-telegram.service
# /etc/systemd/system/nct-alarma.timer + nct-alarma.service
# /root/.config/systemd/user/openclaw-gateway.service
```

## 5. Secretos requeridos (en /opt/nct/secrets/providers/)

- openclaw_primary.env (CEREBRAS_API_KEY=...)
- openclaw_failover.env
- telegram.env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
- github_pat.env, anthropic.env, cloudflare.env, etc.

root@vmi3428294:~# echo 