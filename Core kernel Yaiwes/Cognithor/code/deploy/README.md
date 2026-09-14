# Cognithor · Deployment Guide

## Quick Start: Docker

```bash
# 1. Clone and build
git clone https://github.com/team-soellner/jarvis.git
cd jarvis

# 2. Copy and edit environment
cp .env.example .env
# Edit .env: set JARVIS_API_TOKEN, JARVIS_TELEGRAM_TOKEN, etc.

# 3a. Development (CLI-Modus)
docker compose up -d
docker attach jarvis

# 3b. Production (headless + WebUI + Ollama)
docker compose -f docker-compose.prod.yml up -d

# 4. Check health
curl http://localhost:8741/api/v1/health
curl http://localhost:8080/api/v1/health
```

### Docker Profiles

```bash
# Default: jarvis + webui + ollama
docker compose -f docker-compose.prod.yml up -d

# + PostgreSQL (pgvector)
docker compose -f docker-compose.prod.yml --profile postgres up -d

# + Nginx reverse proxy (TLS)
docker compose -f docker-compose.prod.yml --profile nginx up -d

# Everything
docker compose -f docker-compose.prod.yml --profile postgres --profile nginx up -d
```

### GPU Support (Ollama)

Uncomment the `deploy` section in `docker-compose.prod.yml` for NVIDIA GPU access.
Requires [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

---

## Quick Start: Bare-Metal (Ubuntu/Debian)

```bash
# Download and run
sudo bash deploy/install-server.sh \
    --domain jarvis.example.com \
    --email admin@example.com

# Or with self-signed certificate
sudo bash deploy/install-server.sh \
    --domain test.local \
    --self-signed
```

### install-server.sh Options

| Flag | Description |
|------|-------------|
| `--domain DOMAIN` | Server domain (required) |
| `--email EMAIL` | Email for Let's Encrypt |
| `--no-ollama` | Skip Ollama installation |
| `--no-nginx` | Skip Nginx installation |
| `--self-signed` | Use self-signed TLS certificate |
| `--uninstall` | Remove installation (keeps data) |

### Installed Paths

| Path | Content |
|------|---------|
| `/opt/cognithor/` | Application + venv |
| `/var/lib/cognithor/` | Data, config, logs |
| `/var/lib/cognithor/.env` | Environment variables |
| `/etc/systemd/system/cognithor.service` | Core service |
| `/etc/systemd/system/cognithor-webui.service` | WebUI service |

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JARVIS_HOME` | `~/.jarvis` | Data directory |
| `JARVIS_API_HOST` | `127.0.0.1` | Control Center API bind address |
| `JARVIS_API_TOKEN` | *(none)* | Bearer token for API auth |
| `JARVIS_API_CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `JARVIS_WEBUI_HOST` | `0.0.0.0` | WebUI bind address (factory mode) |
| `JARVIS_WEBUI_CORS_ORIGINS` | `*` | WebUI CORS origins |
| `JARVIS_SSL_CERTFILE` | *(none)* | TLS certificate path |
| `JARVIS_SSL_KEYFILE` | *(none)* | TLS private key path |
| `JARVIS_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `JARVIS_LOGGING_LEVEL` | `INFO` | Log level |
| `JARVIS_TELEGRAM_TOKEN` | *(none)* | Telegram bot token |
| `JARVIS_TELEGRAM_ALLOWED_USERS` | *(none)* | Comma-separated Telegram user IDs |

### CLI Arguments

```
cognithor [--config PATH] [--log-level LEVEL] [--no-cli]
          [--api-port PORT] [--api-host HOST]
          [--init-only] [--version]
```

---

## TLS / HTTPS

### Option A: Nginx (docker-compose.prod.yml)

```bash
# Place certificates
mkdir -p deploy/certs
cp /path/to/fullchain.pem deploy/certs/
cp /path/to/privkey.pem deploy/certs/

# Start with nginx profile
docker compose -f docker-compose.prod.yml --profile nginx up -d
```

### Option B: Caddy (automatic Let's Encrypt)

```bash
docker run -d --name caddy \
    -p 80:80 -p 443:443 \
    -v caddy_data:/data \
    -v ./deploy/Caddyfile:/etc/caddy/Caddyfile:ro \
    --network cognithor-internal \
    -e DOMAIN=jarvis.example.com \
    caddy:alpine
```

### Option C: Direct TLS (no reverse proxy)

```bash
# Set in .env
JARVIS_SSL_CERTFILE=/path/to/fullchain.pem
JARVIS_SSL_KEYFILE=/path/to/privkey.pem
```

---

## Reverse Proxy Endpoints

| Path | Backend | Description |
|------|---------|-------------|
| `/` | webui:8080 | Web UI (static + REST) |
| `/ws/` | webui:8080 | WebSocket (upgrade) |
| `/control/` | jarvis:8741 | Control Center API (prefix stripped) |
| `/health` | webui:8080 | Health check (no auth) |

---

## Monitoring

### Health Checks

```bash
# WebUI health
curl -s http://localhost:8080/api/v1/health | python3 -m json.tool

# Control Center API health
curl -s http://localhost:8741/api/v1/health | python3 -m json.tool

# Behind Nginx
curl -s https://jarvis.example.com/health
```

### Systemd

```bash
systemctl status cognithor
systemctl status cognithor-webui
journalctl -u cognithor -f
journalctl -u cognithor-webui -f --since "1 hour ago"
```

### Docker

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f jarvis
docker compose -f docker-compose.prod.yml logs -f webui
```

---

## Troubleshooting

### WebUI returns 503

The `create_app()` factory runs standalone without a Gateway. `POST /api/v1/message` returns 503 — this is expected. The WebUI communicates via WebSocket which requires the Gateway to be running and connected.

### Ollama not reachable from Docker

```bash
# Ensure Ollama listens on all interfaces
# Edit /etc/systemd/system/ollama.service:
#   Environment="OLLAMA_HOST=0.0.0.0"
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### Permission denied on data directory

```bash
sudo chown -R cognithor:cognithor /var/lib/cognithor
```

### TLS certificate errors

```bash
# Verify certificate
openssl x509 -in /path/to/fullchain.pem -text -noout

# Test TLS connection
openssl s_client -connect jarvis.example.com:443
```

### Service won't start

```bash
# Check logs
journalctl -u cognithor --no-pager -n 50

# Test manually
sudo -u cognithor /opt/cognithor/venv/bin/jarvis --no-cli --api-host 0.0.0.0
```

---

## Ollama Models

### Required

```bash
ollama pull qwen3:8b           # Executor (6 GB VRAM)
ollama pull nomic-embed-text   # Embeddings (0.5 GB VRAM)
```

### Recommended

```bash
ollama pull qwen3:32b          # Planner (20 GB VRAM)
```

### VRAM Profiles

| GPU | VRAM | Planner | Executor |
|-----|------|---------|----------|
| RTX 5090 | 32 GB | qwen3:32b | qwen3:8b |
| RTX 4090 | 24 GB | qwen3:32b | qwen3:8b |
| RTX 3090 | 24 GB | qwen3:32b-q4 | qwen3:8b |
| RTX 4070 | 12 GB | qwen3:14b | qwen3:8b |
| 8 GB | 8 GB | qwen3:8b | qwen3:8b |
