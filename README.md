# 🦞 agentes — Orquestador Universal VPS

Complete migration of the Orquestador Universal stack from VPS `95.111.232.89` (Contabo EU2, Ubuntu 22.04) to a reproducible, deployable GitHub repository.

## 📋 What this repository contains

| Component | Description | Port | Status |
|-----------|-------------|------|--------|
| **OpenClaw Gateway** | Multi-agent LLM gateway with 11 agents | 18789 | ✅ |
| **Core V8 (Orchestrator)** | DSL DAG SHERIFF pipeline N00→N10 | 9095 | ✅ |
| **Core V9** | Extended orchestrator | 9096 | ✅ |
| **Conector V2** | Original production orchestrator | 9090 | ✅ |
| **Claude_Code_VPS Agent** | Headless Claude Code runtime | 8081 | ✅ |
| **Mimo_Code_VPS Agent** | Headless Mimo Code runtime | 8082 | ✅ |
| **OpenClaw_VPS Agent** | Headless OpenClaw runtime | 8083 | ✅ |
| **Open WebUI** | Chat interface | 8080 | ✅ |
| **MAXBRY Backend** | Router backend (FastAPI) | 8000 | ✅ |
| **LiteLLM** | Cerebras router (OpenAI-compat) | 4000 | ✅ |
| **MCP Bridge** | OpenClaw MCP server | 18791 | ✅ |
| **Extras Gateway** | OpenClaw extras | 18790 | ✅ |
| **clawd_panel** | Custom chat panel | 18792 | ✅ |
| **Telegram Bot** | NCT chat bot | — | ✅ |
| **Nginx** | 5 DuckDNS reverse proxies | 8443, 2053 | ✅ |

## 🗂️ Repository structure

```
agentes/
├── openclaw/                    # OpenClaw config + custom code
│   ├── openclaw.json.template    # Sanitized config (no API keys)
│   ├── clawd_panel.py            # Custom panel
│   ├── mcp_bridge.py             # MCP server
│   ├── extras_gateway.py         # Extras gateway
│   ├── chat_injector.py          # Chat injector
│   ├── chat_loader.py            # Loader
│   ├── final_loader.py           # Final loader
│   └── deploy/                   # Restart scripts
├── core/                        # Orchestrator core
│   ├── orchestrator_core_v8/     # Core V8 isolated (port 9095)
│   │   ├── orchestrator_core_v8.py
│   │   ├── lobster/              # DSL workflows
│   │   ├── state/
│   │   ├── tests/
│   │   └── ...
│   ├── orchestrator_core_v9.py
│   ├── conector_v2.py
│   ├── main.py
│   ├── main_dsl.py
│   ├── main_runtime.py
│   ├── vps_exec.py
│   ├── setup.sh
│   ├── dockerfiles/
│   ├── docs/
│   ├── sandboxes/
│   ├── tareas/
│   ├── tests/
│   ├── README.md
│   ├── B1-B8_*.md
│   ├── INSTRUCCIONES_PARA_MAESTRO.md
│   └── INDICE_FINAL.md
├── lobster/                     # DSL DAG SHERIFF workflows
│   ├── dsl-dag-sheriff.lobster
│   └── dsl-dag-sheriff-real.lobster
├── agents/                      # NCT agent runtimes
│   ├── claude_vps_runtime.py     # Claude_Code_VPS (port 8081)
│   ├── mimo_vps_runtime.py       # Mimo_Code_VPS (port 8082)
│   ├── openclaw_vps_runtime.py   # OpenClaw_VPS (port 8083)
│   ├── nct-agents/               # Original NCT agents
│   ├── nct-keep/                 # Memory + dispatchers
│   ├── nct-chat-app/             # Chat app
│   ├── nct-anchors/              # IDENTITY.md per agent
│   ├── nct-foundation/           # TAREA-1, BIBLIOTECA
│   ├── nct-scripts/              # Health, audit, backup scripts
│   ├── nct-runtime-baseline/     # RUNTIME_*.md
│   ├── nct-loops/                # HF loops
│   ├── nct-validation/           # Community report
│   ├── nct-apps/                 # WebUI, Vercel chatbot
│   ├── m3_selftest.py
│   ├── RUNTIME_CONFIGURATION.md
│   ├── RUNTIME_INVENTORY.md
│   ├── RECOVERY_GUIDE.md
│   ├── RUNTIME_VALIDATION.md
│   └── runtime-lock.json
├── bridges/                     # Inter-component bridges
│   ├── openclaw_bridge_daemon.py
│   └── claude_stdio_bridge.py
├── channels/                    # User-facing channels
│   └── telegram-bot.py
├── nginx/                       # Reverse proxy configs
│   ├── sites-available/
│   └── sites-enabled/
├── systemd/                     # Service unit files
│   ├── core-v8.service
│   ├── openclaw.service
│   ├── nct-v3.service
│   ├── nct-watchdog.service
│   ├── nct-watchdog.timer
│   ├── nct-agent-claude-vps.service
│   ├── nct-agent-mimo-vps.service
│   ├── nct-agent-openclaw-vps.service
│   ├── nct-telegram.service
│   ├── nct-open-webui.service
│   ├── nct-memory.service
│   ├── nct-sandbox-tarea1.service
│   ├── nct-claude-chat.service
│   ├── litellm.service
│   ├── serveo-tunnel.service
│   └── maxbry-backend.service
├── scripts/                     # Operations scripts
│   ├── setup.sh
│   ├── deploy.sh
│   ├── audit.sh
│   └── deploy/
├── docs/                        # Documentation
│   ├── RUNTIME_CONFIGURATION.md
│   ├── RUNTIME_INVENTORY.md
│   ├── RECOVERY_GUIDE.md
│   ├── RUNTIME_VALIDATION.md
│   ├── openclaw-vps-IDENTIDAD.md
│   ├── claude-vps-IDENTIDAD.md
│   ├── mimo-vps-IDENTIDAD.md
│   ├── INSTRUCCIONES_PARA_MAESTRO.md
│   └── INDICE_FINAL.md
├── skills/                      # OpenClaw skills
│   ├── s.md
│   ├── claude-code.md
│   └── mimo-code.md
├── .env.example                 # Template for secrets
├── .gitignore                   # Excludes .env, *.key, backups
├── LICENSE                      # Proprietary
└── README.md                    # This file
```

## 🔐 Security

**This repository is PUBLIC.** All API keys, tokens, and secrets have been:
- **Sanitized** in `openclaw/openclaw.json.template` (replaced with `${ENV_VAR}` references)
- **Excluded** via `.gitignore` (`.env`, `*.key`, `*.pem`, etc.)
- **Replaced** in config files with environment variable references

To deploy, you must provide your own secrets via `.env` file (see `.env.example`).

## 🚀 Quick deploy (fresh VPS)

```bash
# 1. Clone
git clone https://github.com/maxbry1-commits/agentes.git
cd agentes

# 2. Configure secrets
cp .env.example .env
nano .env  # Fill in real API keys

# 3. Run setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# 4. Start services
sudo systemctl daemon-reload
sudo systemctl enable --now openclaw nct-v3 nct-agent-claude-vps nct-agent-mimo-vps
```

## 🧪 Test the stack

```bash
# Health check all services
curl -s -H "Authorization: Bearer $OC_GATEWAY_TOKEN" http://127.0.0.1:18789/health
curl -s http://127.0.0.1:9095/health
curl -s http://127.0.0.1:8081/health

# Test chat
curl -X POST http://127.0.0.1:18789/v1/chat/completions \
  -H "Authorization: Bearer $OC_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"openclaw/m3","messages":[{"role":"user","content":"Hi"}],"max_tokens":30}'
```

## 🦞 OpenClaw agents

11 agents configured:

| Agent | Provider | Model |
|-------|----------|-------|
| `m3-research` | MiniMax | MiniMax-M3 (default) |
| `m3` | MiniMax | MiniMax-M3 |
| `m25` | MiniMax | MiniMax-M2.7 |
| `gemma` | Cerebras | Gemma-4-31B |
| `groq` | Groq | Llama 3.1 8B |
| `nvmxb` | NVIDIA | M2.7 maxbry |
| `nvbrs` | NVIDIA | M2.7 briseida |
| `nvmos` | NVIDIA | M2.7 movistar |
| `nvwmx` | NVIDIA | M2.7 wow-maxbry |
| `nvwbr` | NVIDIA | M2.7 wow-brisa |
| `nvgpt` | NVIDIA | Llama 3.1 8B |

## 🌐 DuckDNS external URLs

| Subdomain | Service | Port |
|-----------|---------|------|
| maxbry1.duckdns.org | OpenClaw chat | 18789 |
| maxbry2.duckdns.org | clawd_panel | 18792 |
| maxbry3.duckdns.org | MCP bridge | 18791 |
| maxbry4.duckdns.org | Extras gateway | 18790 |
| maxbry5.duckdns.org | Alias OpenClaw | 18789 |

## 🔄 DSL DAG SHERIFF pipeline

Lobster workflow `dsl-dag-sheriff.lobster` defines the 11-step pipeline:

```
N00_RECEIVE → N01_SCHEMA → N02_SHERIFF → N03_DAG_BUILD →
N04_ROUTER → N05_RUNTIME → N06_SANDBOX → N07_VERIFY →
N08_CONSENSUS → N09_STATE → N10_RESPONSE
```

Production endpoints: only `Claude_Code_VPS` (port 8081) and `Mimo_Code_VPS` (port 8082) allowed.

## 📊 Origin

- **VPS**: Contabo EU2 (`95.111.232.89`)
- **OS**: Ubuntu 22.04, kernel 6.8.0-134-generic
- **RAM**: 11 GB total
- **Disk**: 193 GB (39 GB used)
- **Container ID**: `vmi3428294`
- **Customer ID**: `15169759`
- **Firewall ID**: `787810c4-e9a2-4634-99d7-79d24ff9fa99`

## 📜 License

Proprietary - © Max Bryant. All rights reserved.

## 🆘 Support

For issues, see `docs/RECOVERY_GUIDE.md` and `docs/RUNTIME_TROUBLESHOOTING.md`.
