 <ntime-baseline/RUNTIME_CONFIGURATION.md 2>/dev/null
# RUNTIME CONFIGURATION
Date: 2026-07-10T01:48:11Z

## OpenClaw models (12 total)
  - litellm/cerebras-coder                   tags=['default', 'configured'] missing=False
  - litellm/zai-glm-4.7                      tags=['configured'] missing=False
  - litellm/gemma-4-31b                      tags=['configured'] missing=False
  - litellm/cerebras-verifier                tags=['configured'] missing=False
  - litellm/cerebras-coder-failover          tags=['configured'] missing=False
  - litellm/cerebras-verifier-failover       tags=['configured'] missing=False
  - cerebras/gemma-4-31b                     tags=[] missing=False
  - cerebras/zai-glm-4.7                     tags=[] missing=False
  - claude-cli/claude-opus-4-6               tags=[] missing=False
  - claude-cli/claude-opus-4-7               tags=[] missing=False
  - claude-cli/claude-opus-4-8               tags=[] missing=False
  - claude-cli/claude-sonnet-4-6             tags=[] missing=False

## OpenClaw provider litellm
  baseUrl: http://127.0.0.1:4000/v1
  apiKey: sk-mavis-infra-test-...
  api: openai-completions
  models: ['cerebras-coder', 'cerebras-verifier', 'cerebras-coder-failover', 'cerebras-verifier-failover']

## LiteLLM models (router)
  - cerebras-coder
  - cerebras-verifier
  - cerebras-coder-failover
  - cerebras-verifier-failover

## MiMo provider config
  baseURL: http://127.0.0.1:4000/v1
  apiKey: sk-mavis-cerebras-ro...
  primary: cerebras-coder
  small: cerebras-coder

## Claude Code env (active)
      "ANTHROPIC_BASE_URL": "http://127.0.0.1:4000",
      "ANTHROPIC_AUTH_TOKEN": "sk-mavis-cerebras-router",
      "ANTHROPIC_API_KEY": "",
      "ANTHROPIC_MODEL": "cerebras-coder",
      "ANTHROPIC_SMALL_FAST_MODEL": "cerebras-coder",
      "ANTHROPIC_DEFAULT_HAIKU_MODEL": "cerebras-coder",
      "ANTHROPIC_DEFAULT_SONNET_MODEL": "cerebras-coder",
      "ANTHROPIC_DEFAULT_OPUS_MODEL": "cerebras-verifier",
      "DISABLE_TELEMETRY": "1",

## Ports in use (LISTEN)
  - 0.0.0.0:22 users:(("sshd",pid=932,fd=3),("systemd",pid=1,fd=157))
  - 127.0.0.1:4096 users:((".mimocode",pid=71298,fd=18))
  - 127.0.0.1:18789 users:(("node",pid=78726,fd=27))
  - 127.0.0.1:4000 users:(("litellm",pid=28503,fd=13))
  - 0.0.0.0:8080 users:(("open-webui",pid=58291,fd=32))
  - [::]:22 users:(("sshd",pid=932,fd=4),("systemd",pid=1,fd=158))
  - [::1]:18789 users:(("node",pid=78726,fd=28))

## systemd services (running)
  -     OpenClaw LiteLLM Service (Cerebras Router)
  -     NCT Open WebUI - maxbry chat vps
  -     NCT Telegram Bot
root@vmi3428294:~# echo 