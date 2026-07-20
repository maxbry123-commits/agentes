---
name: git
description: "Wrapper de git con sub-comandos seguros. status, branch, commit, push, pr, clone, diff, log. Bloquea force-push a main/master salvo override. Use when un agente necesita mover código entre local y GitHub o crear PRs. Trigger with 'git' o 'commit' o 'push'."
license: MIT
version: 0.1.0
author: Max Bryant <maxbry123@gmail.com>
allowed-tools: "Bash, github-mcp:*"
compatibility: "Designed for OpenClaw. Compatible con Claude Code, Codex, Cursor."
tags: [vcs, git, github, devops]
metadata:
  category: devops
  tier: core
  source: core
  schema: agentskills.io/0.2.0
  openclaw_skill: true
---

# git

Wrapper seguro de git.

## Acciones

| acción  | args clave | descripción |
|---------|------------|-------------|
| `status` | `repo` | `git status --short` |
| `branch` | `repo`, `name` | `git checkout -b <name>` |
| `commit` | `repo`, `message`, `files?` | add + commit |
| `push`   | `repo`, `remote?`, `branch?`, `force?` | push (bloquea force a main/master) |
| `pr`     | `repo`, `title`, `body?`, `base?` | crea PR en GitHub |
| `clone`  | `url`, `dest?` | clone |
| `diff`   | `repo` | `git diff --stat` |
| `log`    | `repo`, `n?` | `git log --oneline -n <N>` |

## Seguridad

- `--force` a `main`/`master` → denegado (override manual con `force=true` + log warning).
- El token se inyecta por env var `GITHUB_PAT_MAXBRY` (nunca como argumento).
- Compatible con `mcp/github` cuando esté disponible (en este spec, llama API directo).

## Ejemplos

```bash
# branch + commit + push + pr
echo '{"action":"branch","repo":".","name":"feature/registries"}' | openclaw skill run git
echo '{"action":"commit","repo":".","message":"feat: registries v0.1","files":["registries/"]}' | openclaw skill run git
echo '{"action":"push","repo":".","branch":"feature/registries"}' | openclaw skill run git
echo '{"action":"pr","repo":".","title":"feat: registries v0.1","body":"first cut","base":"main"}' | openclaw skill run git
```

## Output (pr)

```json
{ "ok": true, "stdout": "{\"number\":42,...}" }
```

## Pendiente (v0.2)
- Integración con `mcp/github` (en lugar de curl directo).
- Confirmación interactiva para `push --force` (política elevada).
