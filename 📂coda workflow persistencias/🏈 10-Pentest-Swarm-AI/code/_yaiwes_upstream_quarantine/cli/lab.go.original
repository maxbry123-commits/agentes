package cli

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

// labProfile describes a bundled, intentionally-vulnerable target that
// `scan --lab` can spin up on localhost. Every profile is legal to attack,
// binds only to loopback, and is torn down when the scan finishes.
type labProfile struct {
	name     string // --lab-target value, e.g. "juiceshop"
	display  string // human-facing name for logs
	compose  string // docker-compose contents (kept in sync with deploy/lab/)
	target   string // URL the swarm scans
	scope    string // scope string passed to the swarm
	readyURL string // GET this and expect 200 once the target is ready
	// upTimeout bounds `docker compose up` (image pull + container start);
	// readyTimeout bounds the readiness poll that follows.
	upTimeout    time.Duration
	readyTimeout time.Duration
	// note is an optional one-line heads-up printed before boot (resources,
	// expected boot time). Empty means no note.
	note string
}

// labCompose is OWASP Juice Shop, the canonical modern vulnerable web app —
// a single Node container. Kept in sync with the human-facing copy at
// deploy/lab/docker-compose.yml.
const labCompose = `services:
  juice-shop:
    image: bkimminich/juice-shop:latest
    container_name: pentestswarm-lab-juiceshop
    ports:
      - "3000:3000"
`

// labCrapiCompose is OWASP crAPI (completely ridiculous API): a realistic,
// multi-container service mesh — identity/community/workshop/chatbot APIs, an
// nginx web tier on :8888, Postgres, MongoDB, ChromaDB, MailHog, and an API
// gateway. Vendored from OWASP/crAPI (main) and kept in sync with
// deploy/lab/crapi/docker-compose.yml. Needs ~4GB RAM free and a few minutes
// to boot on first run.
//
// One deliberate change from upstream: the hardcoded `container_name:` values
// (mongodb, postgresdb, chromadb, mailhog, api.mypremiumdealership.com, …) are
// removed so Compose namespaces the real container names under the per-run
// project (pentestswarm-lab-<hash>). Those generic global names collide with
// any pre-existing container on a shared dev machine and abort the boot.
// Inter-service DNS is unaffected: every hostname crAPI references is also a
// Compose *service* key, and service keys resolve on the network regardless.
const labCrapiCompose = `# Vendored from OWASP/crAPI (main), deploy/docker/docker-compose.yml.
# Licensed under the Apache License, Version 2.0.
services:

  crapi-identity:
    image: crapi/crapi-identity:${VERSION:-latest}
    volumes:
      - ./keys:/app/keys
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - DB_NAME=crapi
      - DB_USER=admin
      - DB_PASSWORD=crapisecretpassword
      - DB_HOST=postgresdb
      - DB_PORT=5432
      - SERVER_PORT=${IDENTITY_SERVER_PORT:-8080}
      - ENABLE_SHELL_INJECTION=${ENABLE_SHELL_INJECTION:-false}
      - JWT_SECRET=crapi
      - MAILHOG_HOST=mailhog
      - MAILHOG_PORT=1025
      - MAILHOG_DOMAIN=example.com
      - SMTP_HOST=smtp.example.com
      - SMTP_PORT=587
      - SMTP_EMAIL=user@example.com
      - SMTP_PASS=xxxxxxxxxxxxxx
      - SMTP_FROM=no-reply@example.com
      - SMTP_AUTH=true
      - SMTP_STARTTLS=true
      - JWT_EXPIRATION=604800000
      - ENABLE_LOG4J=${ENABLE_LOG4J:-false}
      - API_GATEWAY_URL=https://api.mypremiumdealership.com
      - TLS_ENABLED=${TLS_ENABLED:-false}
      - TLS_KEYSTORE_TYPE=PKCS12
      - TLS_KEYSTORE=classpath:certs/server.p12
      - TLS_KEYSTORE_PASSWORD=passw0rd
      - TLS_KEY_PASSWORD=passw0rd
      - TLS_KEY_ALIAS=identity
    depends_on:
      postgresdb:
        condition: service_healthy
      mongodb:
        condition: service_healthy
      mailhog:
        condition: service_healthy
    healthcheck:
      test: /app/health.sh
      interval: 15s
      timeout: 15s
      retries: 15
    deploy:
      resources:
        limits:
          cpus: '0.8'
          memory: 384M

  crapi-community:
    image: crapi/crapi-community:${VERSION:-latest}
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - IDENTITY_SERVICE=crapi-identity:${IDENTITY_SERVER_PORT:-8080}
      - DB_NAME=crapi
      - DB_USER=admin
      - DB_PASSWORD=crapisecretpassword
      - DB_HOST=postgresdb
      - DB_PORT=5432
      - SERVER_PORT=${COMMUNITY_SERVER_PORT:-8087}
      - MONGO_DB_HOST=mongodb
      - MONGO_DB_PORT=27017
      - MONGO_DB_USER=admin
      - MONGO_DB_PASSWORD=crapisecretpassword
      - MONGO_DB_NAME=crapi
      - TLS_ENABLED=${TLS_ENABLED:-false}
      - TLS_CERTIFICATE=certs/server.crt
      - TLS_KEY=certs/server.key
    depends_on:
      postgresdb:
        condition: service_healthy
      mongodb:
        condition: service_healthy
      crapi-identity:
        condition: service_healthy
    healthcheck:
      test: /app/health.sh
      interval: 15s
      timeout: 15s
      retries: 15
    deploy:
      resources:
        limits:
          cpus: '0.3'
          memory: 192M

  crapi-workshop:
    image: crapi/crapi-workshop:${VERSION:-latest}
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - IDENTITY_SERVICE=crapi-identity:${IDENTITY_SERVER_PORT:-8080}
      - DB_NAME=crapi
      - DB_USER=admin
      - DB_PASSWORD=crapisecretpassword
      - DB_HOST=postgresdb
      - DB_PORT=5432
      - SERVER_PORT=${WORKSHOP_SERVER_PORT:-8000}
      - MONGO_DB_HOST=mongodb
      - MONGO_DB_PORT=27017
      - MONGO_DB_USER=admin
      - MONGO_DB_PASSWORD=crapisecretpassword
      - MONGO_DB_NAME=crapi
      - SECRET_KEY=crapi
      - API_GATEWAY_URL=https://api.mypremiumdealership.com
      - TLS_ENABLED=${TLS_ENABLED:-false}
      - TLS_CERTIFICATE=certs/server.crt
      - TLS_KEY=certs/server.key
      - FILES_LIMIT=1000
    depends_on:
      postgresdb:
        condition: service_healthy
      mongodb:
        condition: service_healthy
      crapi-identity:
        condition: service_healthy
      crapi-community:
        condition: service_healthy
    healthcheck:
      test: /app/health.sh
      interval: 15s
      timeout: 15s
      retries: 15
    deploy:
      resources:
        limits:
          cpus: '0.3'
          memory: 128M

  crapi-chatbot:
    image: crapi/crapi-chatbot:${VERSION:-latest}
    environment:
      - TLS_ENABLED=${TLS_ENABLED:-false}
      - SERVER_PORT=${CHATBOT_SERVER_PORT:-5002}
      - WEB_SERVICE=crapi-web
      - IDENTITY_SERVICE=crapi-identity:${IDENTITY_SERVER_PORT:-8080}
      - DB_NAME=crapi
      - DB_USER=admin
      - DB_PASSWORD=crapisecretpassword
      - DB_HOST=postgresdb
      - DB_PORT=5432
      - MONGO_DB_HOST=mongodb
      - MONGO_DB_PORT=27017
      - MONGO_DB_USER=admin
      - MONGO_DB_PASSWORD=crapisecretpassword
      - MONGO_DB_NAME=crapi
      - API_USER=admin@example.com
      - API_PASSWORD=Admin!123
      - OPENAPI_SPEC=/app/resources/crapi-openapi-spec.json
      - DEFAULT_MODEL=gpt-4o-mini
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
    depends_on:
      mongodb:
        condition: service_healthy
      crapi-identity:
        condition: service_healthy
      chromadb:
        condition: service_healthy

  crapi-web:
    image: crapi/crapi-web:${VERSION:-latest}
    ports:
      - "${LISTEN_IP:-127.0.0.1}:8888:80"
      - "${LISTEN_IP:-127.0.0.1}:30080:80"
      - "${LISTEN_IP:-127.0.0.1}:8443:443"
      - "${LISTEN_IP:-127.0.0.1}:30443:443"
    environment:
      - COMMUNITY_SERVICE=crapi-community:${COMMUNITY_SERVER_PORT:-8087}
      - IDENTITY_SERVICE=crapi-identity:${IDENTITY_SERVER_PORT:-8080}
      - WORKSHOP_SERVICE=crapi-workshop:${WORKSHOP_SERVER_PORT:-8000}
      - CHATBOT_SERVICE=crapi-chatbot:${CHATBOT_SERVER_PORT:-5002}
      - MAILHOG_WEB_SERVICE=mailhog:8025
      - TLS_ENABLED=${TLS_ENABLED:-false}
    depends_on:
      crapi-community:
        condition: service_healthy
      crapi-identity:
        condition: service_healthy
      crapi-workshop:
        condition: service_healthy
    healthcheck:
      test: curl 0.0.0.0:80/health
      interval: 15s
      timeout: 15s
      retries: 15
    deploy:
      resources:
        limits:
          cpus: '0.3'
          memory: 128M

  postgresdb:
    image: 'postgres:14'
    command: ["postgres", "-c", "max_connections=500"]
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: crapisecretpassword
      POSTGRES_DB: crapi
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready" ]
      interval: 15s
      timeout: 15s
      retries: 15
    volumes:
      - postgresql-data:/var/lib/postgresql/data/
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

  mongodb:
    image: 'mongo:4.4'
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: crapisecretpassword
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongo mongodb:27017/test --quiet
      interval: 15s
      timeout: 15s
      retries: 15
      start_period: 20s
    volumes:
      - mongodb-data:/data/db
    deploy:
      resources:
        limits:
          cpus: '0.3'
          memory: 128M

  chromadb:
    image: 'chromadb/chroma:latest'
    environment:
      IS_PERSISTENT: 'TRUE'
    healthcheck:
      test: [ "CMD", "/bin/bash", "-c", "cat < /dev/null > /dev/tcp/localhost/8000" ]
      interval: 15s
      timeout: 15s
      retries: 15
      start_period: 20s
    volumes:
      - chromadb-data:/data

  mailhog:
    user: root
    image: crapi/mailhog:${VERSION:-latest}
    environment:
      MH_MONGO_URI: admin:crapisecretpassword@mongodb:27017
      MH_STORAGE: mongodb
    ports:
      - "${LISTEN_IP:-127.0.0.1}:8025:8025"
    healthcheck:
      test: [ "CMD", "nc", "-z", "localhost", "8025" ]
      interval: 15s
      timeout: 15s
      retries: 15
    deploy:
      resources:
        limits:
          cpus: '0.3'
          memory: 128M

  api.mypremiumdealership.com:
    image: crapi/gateway-service:${VERSION:-latest}
    healthcheck:
      test: bash -c 'echo -n "GET / HTTP/1.1\n\n" > /dev/tcp/127.0.0.1/443'
      interval: 15s
      timeout: 15s
      retries: 15
      start_period: 15s
    deploy:
      resources:
        limits:
          cpus: '0.1'
          memory: 50M

volumes:
  mongodb-data:
  postgresql-data:
  chromadb-data:
`

// labVampiCompose is VAmPI (Vulnerable API), erev0s' intentionally-vulnerable
// Flask REST API built to demonstrate the OWASP API Security Top 10 — BOLA,
// excessive data exposure, mass assignment, injection, and broken
// authentication among them. A single lightweight container serving on
// :5000. Kept in sync with deploy/lab/vampi/docker-compose.yml.
const labVampiCompose = `services:
  vampi:
    image: erev0s/vampi:latest
    environment:
      - VULNERABLE=1
    ports:
      - "127.0.0.1:5000:5000"
`

// labDvgaCompose is DVGA (Damn Vulnerable GraphQL Application), dolevf's
// intentionally-vulnerable GraphQL API — introspection left enabled,
// injection (OS command and SQL), denial-of-service via unbounded/nested
// queries, stored XSS, and broken access control among its planted flaws. A
// single lightweight container serving on :5013 with its GraphQL endpoint at
// /graphql. Kept in sync with deploy/lab/dvga/docker-compose.yml.
const labDvgaCompose = `services:
  dvga:
    image: dolevf/dvga:latest
    environment:
      - WEB_HOST=0.0.0.0
    ports:
      - "127.0.0.1:5013:5013"
`

// labProfiles maps a --lab-target value to its bundled target definition.
var labProfiles = map[string]labProfile{
	"juiceshop": {
		name:         "juiceshop",
		display:      "OWASP Juice Shop",
		compose:      labCompose,
		target:       "http://localhost:3000",
		scope:        "127.0.0.1/32,localhost",
		readyURL:     "http://localhost:3000/rest/admin/application-version",
		upTimeout:    6 * time.Minute,
		readyTimeout: 4 * time.Minute,
	},
	"crapi": {
		name:         "crapi",
		display:      "OWASP crAPI (multi-container API mesh)",
		compose:      labCrapiCompose,
		target:       "http://localhost:8888",
		scope:        "127.0.0.1/32,localhost",
		readyURL:     "http://localhost:8888/health",
		upTimeout:    15 * time.Minute,
		readyTimeout: 8 * time.Minute,
		note:         "crAPI runs ~10 containers — give it ~4GB RAM free and a few minutes on first run",
	},
	"vampi": {
		name:         "vampi",
		display:      "VAmPI (Vulnerable API)",
		compose:      labVampiCompose,
		target:       "http://localhost:5000",
		scope:        "127.0.0.1/32,localhost",
		readyURL:     "http://localhost:5000/createdb",
		upTimeout:    5 * time.Minute,
		readyTimeout: 3 * time.Minute,
	},
	"dvga": {
		name:         "dvga",
		display:      "DVGA (Damn Vulnerable GraphQL Application)",
		compose:      labDvgaCompose,
		target:       "http://localhost:5013",
		scope:        "127.0.0.1/32,localhost",
		readyURL:     "http://localhost:5013/graphql",
		upTimeout:    5 * time.Minute,
		readyTimeout: 3 * time.Minute,
	},
}

// resolveLabProfile looks up a lab target by name, defaulting to Juice Shop
// when the name is empty. Unknown names produce a helpful error listing the
// available targets.
func resolveLabProfile(name string) (labProfile, error) {
	if name == "" {
		name = "juiceshop"
	}
	p, ok := labProfiles[name]
	if !ok {
		return labProfile{}, fmt.Errorf(
			"unknown --lab-target %q; available targets: juiceshop, crapi, vampi, dvga", name)
	}
	return p, nil
}

// startLab writes the profile's compose file to a temp dir, brings the lab
// up (pulling images on first run), waits for it to pass its readiness
// check, and returns the target + scope to scan plus a teardown func.
//
// This is the "watch it find real vulns on my laptop — free and legal" path:
// no external target, no legal risk, and no API key required if you point
// `--provider ollama` at a local model. Plan reference: D.9.1.
func startLab(profile labProfile, quiet bool) (target, scope string, teardown func(), err error) {
	if _, lookErr := exec.LookPath("docker"); lookErr != nil {
		return "", "", nil, fmt.Errorf(
			"--lab needs Docker, which isn't on your PATH.\n  Install Docker (https://docs.docker.com/get-docker/) and re-run.")
	}

	dir, err := os.MkdirTemp("", "pentestswarm-lab-")
	if err != nil {
		return "", "", nil, fmt.Errorf("preparing lab workdir: %w", err)
	}
	composePath := filepath.Join(dir, "docker-compose.yml")
	if err := os.WriteFile(composePath, []byte(profile.compose), 0o644); err != nil {
		_ = os.RemoveAll(dir)
		return "", "", nil, fmt.Errorf("writing lab compose file: %w", err)
	}

	teardown = func() {
		if !quiet {
			fmt.Println("  " + colorDim("[lab] tearing down the practice target…"))
		}
		down := exec.Command("docker", "compose", "-f", composePath, "down", "-v")
		_ = down.Run()
		_ = os.RemoveAll(dir)
	}

	if !quiet {
		msg := "  " + colorCyan("[lab]") + " starting " + colorBold(profile.display) + " at " + colorBold(profile.target) +
			colorDim("  (first run pulls images — give it a minute)")
		fmt.Println(msg)
		if profile.note != "" {
			fmt.Println("  " + colorDim("[lab] "+profile.note))
		}
	}

	ctx, cancel := context.WithTimeout(context.Background(), profile.upTimeout)
	defer cancel()
	up := exec.CommandContext(ctx, "docker", "compose", "-f", composePath, "up", "-d")
	// Surface docker's pull progress so a slow first run doesn't look like
	// a hang.
	up.Stdout = os.Stderr
	up.Stderr = os.Stderr
	if runErr := up.Run(); runErr != nil {
		teardown()
		return "", "", nil, fmt.Errorf(
			"bringing up the lab failed: %w\n  Is the Docker daemon running? (docker info)", runErr)
	}

	// Wait for readiness by polling the app from the host — more reliable
	// than the in-container healthcheck across the image-pull + boot window.
	if !quiet {
		fmt.Print("  " + colorDim("[lab] waiting for the target to boot"))
	}
	client := &http.Client{Timeout: 3 * time.Second}
	deadline := time.Now().Add(profile.readyTimeout)
	ready := false
	for time.Now().Before(deadline) {
		resp, getErr := client.Get(profile.readyURL)
		if getErr == nil {
			_ = resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				ready = true
				break
			}
		}
		if !quiet {
			fmt.Print(colorDim("."))
		}
		time.Sleep(3 * time.Second)
	}
	if !quiet {
		fmt.Println()
	}
	if !ready {
		teardown()
		return "", "", nil, fmt.Errorf("the lab target didn't become ready within %s at %s",
			profile.readyTimeout.Round(time.Minute), profile.target)
	}

	if !quiet {
		fmt.Println("  " + colorGreen("[lab]") + " target is up — pointing the swarm at it.")
		fmt.Println()
	}
	return profile.target, profile.scope, teardown, nil
}
