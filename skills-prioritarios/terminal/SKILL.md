---
name: terminal
description: "Wrapper de bash con sandboxing. Ejecuta un comando arbitrario con timeout, output cap, y blacklist de comandos peligrosos (rm -rf /, mkfs, dd, fork bomb, curl|bash, shutdown, reboot). Use when una skill necesita ejecutar un comando no cubierto por skills específicas. Trigger with 'terminal' o 'run command'."
license: MIT
version: 0.1.0
author: Max Bryant <maxbry123@gmail.com>
allowed-tools: "Bash"
compatibility: "Designed for OpenClaw. Compatible con Claude Code, Codex, Cursor."
tags: [shell, exec, sandbox, security]
metadata:
  category: devops
  tier: core
  source: core
  schema: agentskills.io/0.2.0
  openclaw_skill: true
---

# terminal

Bash sandboxed con blacklist.

## Input

| campo | default | descripción |
|-------|---------|-------------|
| `cmd`              | (req)  | comando a ejecutar |
| `cwd`              | "."    | working dir |
| `timeout_s`        | 30     | timeout total |
| `max_output_bytes` | 1MB    | cap al output |
| `env`              | {}     | env vars adicionales |

## Blacklist (regex)

| patrón | bloquea |
|--------|---------|
| `rm -rf /$`         | borrar root |
| `rm -rf / `         | borrar root (con espacio) |
| `rm -rf --no-preserve-root` | borrar root forzado |
| `chmod -R 777 /`    | perms inseguros |
| `mkfs`              | formatear disco |
| `dd if=`            | copiar bloque |
| `:() {`             | fork bomb |
| `shutdown`          | apagar |
| `reboot`            | reiniciar |
| `iptables -F`       | flush firewall |
| `curl ... \| bash`  | RCE via web |

Si matchea, devuelve `ok: false, blocked_reason: "matched: <regex>"` SIN ejecutar.

## Output

```json
{ "ok": true, "returncode": 0, "stdout": "...", "stderr": "...", "duration_s": 0.123 }
```

## Ejemplo

```bash
echo '{"cmd":"ls -la","cwd":".","timeout_s":10}' | openclaw skill run terminal
echo '{"cmd":"ps aux | grep openclaw | grep -v grep","timeout_s":5}' | openclaw skill run terminal
```

## Tests
`scripts/validate.py` testea echo, timeout, y 3 patrones de blacklist. PASS.
