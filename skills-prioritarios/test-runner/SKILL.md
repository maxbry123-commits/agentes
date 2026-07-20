---
name: test-runner
description: "Detecta y ejecuta tests del proyecto target (pytest, vitest, jest, go test, cargo test). Devuelve resumen estructurado con pass/fail/skip, duración y archivos fallidos. Use when un agente necesita validar código antes de commit, en CI local, o después de cada cambio. Trigger with 'run tests' o 'test-runner'."
license: MIT
version: 0.1.0
author: Max Bryant <maxbry123@gmail.com>
allowed-tools: "Bash, Read"
compatibility: "Designed for OpenClaw. Compatible con Claude Code, Codex, Cursor."
tags: [qa, test, ci, devops]
metadata:
  category: qa
  tier: core
  source: core
  schema: agentskills.io/0.2.0
  openclaw_skill: true
---

# test-runner

Skill para correr tests de un proyecto target.

## Frameworks soportados (v0.1)

| framework | detect | comando |
|-----------|--------|---------|
| `pytest`  | `pyproject.toml` o `pytest.ini` | `python3 -m pytest -q --tb=line --no-header` |
| `vitest`  | `package.json` con `vitest`     | `npx vitest run --reporter=json` |
| `jest`    | `package.json` con `jest`        | `npx jest --json` |
| `go`      | `go.mod`                         | `go test -json ./...` |
| `cargo`   | `Cargo.toml`                     | `cargo test --message-format=json` |

`auto` = detecta por archivos del dir.

## Acciones (CLI)

| input | descripción |
|-------|-------------|
| `path`           | dir del proyecto (default ".") |
| `framework`      | `auto` (default) o uno de la tabla |
| `max_duration_s` | timeout total (default 120) |
| `fail_fast`      | abortar en el primer fail (default false) |

## Output shape

```json
{
  "ok": true,
  "framework": "pytest",
  "duration_s": 12.3,
  "returncode": 0,
  "stdout_tail": "...",
  "stderr_tail": "..."
}
```

## Ejemplo

```bash
echo '{"path":".","framework":"auto","max_duration_s":60}' \
  | openclaw skill run test-runner
```

## Pendiente (v0.2)
- Parseo JSON de output de cada framework (hoy: solo returncode + tail).
- Detección de tests flaky y reintento automático.

## Tests
`scripts/validate.py` requiere `pytest` instalado. En el sandbox no está; en HF Space sí.
