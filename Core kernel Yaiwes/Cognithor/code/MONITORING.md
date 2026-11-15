# Monitoring Guide

> Observability, health checks, and metrics for Cognithor deployments.

## Table of Contents

- [Health Endpoints](#health-endpoints)
- [Swagger UI](#swagger-ui)
- [Monitoring Dashboard](#monitoring-dashboard)
- [Grafana Setup](#grafana-setup)
- [Systemd Status](#systemd-status)
- [Docker Health Checks](#docker-health-checks)
- [Key Metrics](#key-metrics)
- [Alerting](#alerting)

---

## Health Endpoints

### Basic Health Check

```
GET /api/v1/health
```

Returns system status. This endpoint does **not** require authentication and is rate-limit exempt.

```json
{
  "status": "ok",
  "version": "0.35.5",
  "uptime_seconds": 3600,
  "ollama_connected": true,
  "models_loaded": ["qwen3:32b", "qwen3:8b"],
  "active_sessions": 2
}
```

Use this for load balancer health checks and container liveness probes.

### Bootstrap Endpoint

```
GET /api/v1/bootstrap
```

Returns the session API token. Also unprotected -- used by the frontend to obtain auth credentials on first load.

### Monitoring Dashboard

```
GET /api/v1/monitoring/dashboard
```

Returns a comprehensive JSON snapshot:

```json
{
  "snapshot": {
    "active_sessions": 3,
    "total_messages_processed": 1542,
    "tool_calls_total": 8721,
    "tool_errors_total": 43,
    "avg_response_time_ms": 2340,
    "memory_entries": 12500,
    "uptime_seconds": 86400
  }
}
```

### Prometheus Metrics

```
GET /api/v1/monitoring/metrics
```

Exposes metrics in Prometheus text format for scraping.

---

## Swagger UI

Cognithor serves interactive API documentation via FastAPI's built-in OpenAPI support:

| URL | Description |
|-----|-------------|
| `http://localhost:8741/api/docs` | Swagger UI -- interactive endpoint testing |
| `http://localhost:8741/api/redoc` | ReDoc -- alternative read-only documentation |

Both are auto-generated from the route definitions. Protected endpoints require a Bearer token obtained from `/api/v1/bootstrap`.

### Testing Endpoints via Swagger

1. Open `http://localhost:8741/api/docs`
2. Click "Authorize" (lock icon)
3. Enter `Bearer <token>` (get token from `/api/v1/bootstrap`)
4. Try any endpoint interactively

---

## Grafana Setup

### Prerequisites

- Grafana 9+ installed
- Prometheus configured to scrape Cognithor

### Prometheus Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'cognithor'
    scrape_interval: 15s
    metrics_path: '/api/v1/monitoring/metrics'
    static_configs:
      - targets: ['localhost:8741']
    # If auth is required:
    # bearer_token: '<your-token>'
```

### Import Dashboard

If a pre-built Grafana dashboard JSON is available in `deploy/grafana-dashboard.json`, import it:

1. Open Grafana UI
2. Go to Dashboards -> Import
3. Upload the JSON file or paste its contents
4. Select Prometheus as the data source
5. Click "Import"

### Recommended Dashboard Panels

Create panels for these key metrics:

| Panel | Query | Type |
|-------|-------|------|
| Response Time (p50/p95) | `histogram_quantile(0.95, cognithor_response_duration_seconds_bucket)` | Time series |
| Tool Call Rate | `rate(cognithor_tool_calls_total[5m])` | Time series |
| Error Rate | `rate(cognithor_tool_errors_total[5m]) / rate(cognithor_tool_calls_total[5m])` | Gauge |
| Active Sessions | `cognithor_active_sessions` | Stat |
| Memory Entries | `cognithor_memory_entries_total` | Stat |
| PGE Iterations | `histogram_quantile(0.5, cognithor_pge_iterations_bucket)` | Time series |
| Ollama Latency | `cognithor_ollama_request_duration_seconds` | Time series |

---

## Systemd Status

For Linux systemd deployments, check service status:

```bash
# Service status
systemctl status cognithor

# Recent logs
journalctl -u cognithor -n 100 --no-pager

# Follow logs in real time
journalctl -u cognithor -f

# Restart
systemctl restart cognithor
```

Example systemd unit file (`/etc/systemd/system/cognithor.service`):

```ini
[Unit]
Description=Cognithor AI Assistant
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=cognithor
WorkingDirectory=/opt/cognithor
ExecStart=/opt/cognithor/venv/bin/python -m jarvis --no-cli --api-port 8741
Restart=on-failure
RestartSec=10
Environment=JARVIS_HOME=/opt/cognithor/data
Environment=OLLAMA_HOST=http://localhost:11434

[Install]
WantedBy=multi-user.target
```

---

## Docker Health Checks

### Dockerfile HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8741/api/v1/health || exit 1
```

### Docker Compose

```yaml
services:
  cognithor:
    image: cognithor:latest
    ports:
      - "8741:8741"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8741/api/v1/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
```

### Check Container Health

```bash
docker inspect --format='{{.State.Health.Status}}' cognithor
# Output: healthy | unhealthy | starting

docker inspect --format='{{json .State.Health}}' cognithor | jq .
```

---

## Key Metrics

### What to Monitor

| Category | Metric | Why It Matters |
|----------|--------|----------------|
| **Latency** | Response time (p50, p95, p99) | User experience |
| **Throughput** | Messages processed/minute | Capacity planning |
| **Errors** | Tool error rate, Gatekeeper blocks | System reliability |
| **Resources** | VRAM usage, CPU, RAM, disk | Infrastructure health |
| **LLM** | Ollama latency, model load time | Backend performance |
| **Memory** | Vector index size, compaction rate | Long-term stability |
| **Sessions** | Active sessions, WebSocket connections | Load monitoring |
| **GEPA** | Evolution cycles, proposals applied, rollbacks | Self-improvement health |

### Log-Based Monitoring

Cognithor uses structured logging. Parse logs for patterns:

```bash
# Count errors in the last hour
grep "ERROR" ~/.jarvis/logs/jarvis.log | tail -100

# Tool failures
grep "tool_execution_failed" ~/.jarvis/logs/jarvis.log

# Gatekeeper blocks
grep "GATEKEEPER.*BLOCKED" ~/.jarvis/logs/jarvis.log

# WebSocket disconnects
grep "ws_disconnected" ~/.jarvis/logs/jarvis.log
```

---

## Alerting

### Recommended Alert Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| Service Down | `/api/v1/health` returns non-200 for 2 min | Critical |
| High Error Rate | Tool error rate > 10% for 5 min | Warning |
| High Latency | p95 response time > 10s for 5 min | Warning |
| Ollama Disconnected | `ollama_connected: false` for 1 min | Critical |
| VRAM Full | CUDA OOM errors in logs | Critical |
| Disk Full | Data directory > 90% capacity | Warning |
| WebSocket Storm | > 100 reconnects/min | Warning |

### Prometheus Alertmanager Example

```yaml
groups:
  - name: cognithor
    rules:
      - alert: CognithorDown
        expr: up{job="cognithor"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Cognithor is down"

      - alert: HighErrorRate
        expr: rate(cognithor_tool_errors_total[5m]) / rate(cognithor_tool_calls_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Tool error rate above 10%"
```
