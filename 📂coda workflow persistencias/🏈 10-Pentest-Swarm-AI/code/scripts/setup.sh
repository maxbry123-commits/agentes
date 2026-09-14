#!/usr/bin/env bash
set -euo pipefail

echo "=== pentestswarm development setup ==="
echo ""

# Check prerequisites
command -v go >/dev/null 2>&1 || { echo "ERROR: Go is not installed. Install from https://go.dev/dl/"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker is not installed. Install from https://docker.com"; exit 1; }

echo "[1/6] Installing Go development tools..."
go install github.com/air-verse/air@latest 2>/dev/null || echo "  air already installed or skipped"
go install github.com/sqlc-dev/sqlc/cmd/sqlc@latest 2>/dev/null || echo "  sqlc already installed or skipped"
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest 2>/dev/null || echo "  golangci-lint already installed or skipped"

echo "[2/6] Installing security toolchain (httpx, nuclei, katana, ...)..."
echo "  (Go tools compile from source — first run takes a few minutes.)"
make tools || echo "  WARNING: some security tools failed to install — run 'pentestswarm doctor' to see what's missing"

echo "[3/6] Starting services (PostgreSQL, Redis, Ollama)..."
docker compose -f deploy/docker-compose.dev.yml up -d

echo "[4/6] Waiting for services to be healthy..."
for _ in $(seq 1 30); do
    if docker compose -f deploy/docker-compose.dev.yml ps --format json 2>/dev/null | grep -q '"healthy"' || \
       docker compose -f deploy/docker-compose.dev.yml ps 2>/dev/null | grep -q "healthy"; then
        break
    fi
    sleep 1
done

echo "[5/6] Building pentestswarm..."
make build

echo "[6/6] Running health check..."
./bin/pentestswarm --version
echo ""
echo "Tip: run './bin/pentestswarm doctor' to confirm every security tool is installed."

echo ""
echo "=== Setup complete ==="
echo ""
echo "Services running:"
echo "  PostgreSQL: localhost:5432 (user: pentestswarm, password: pentestswarm_dev)"
echo "  Redis:      localhost:6379"
echo "  Ollama:     localhost:11434"
echo ""
echo "Quick start:"
echo "  make dev        # Start with hot-reload"
echo "  make test       # Run tests"
echo "  make lint       # Run linter"
echo ""
