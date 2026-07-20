# ⚡ Skills Prioritarios — los 6 desde el día 1

> **Estándar**: [agentskills.io](https://agentskills.io) — SKILL.md + frontmatter YAML.
> Compatible con: Claude Code, Gemini, Cursor, Kiro, Codex, Antigravity, OpenCode, **OpenClaw**.

| # | id | descripción | tools requeridos |
|---|----|-------------|------------------|
| 1 | `task-manager` | Gestiona TODOs del orquestador | Bash, filesystem |
| 2 | `test-runner`  | Corre tests del proyecto target | Bash, filesystem |
| 3 | `git`          | Wrapper de git (branch, commit, push, PR) | Bash |
| 4 | `terminal`     | Terminal controlado (sandboxed) | Bash |
| 5 | `web-search`   | Búsqueda web (Serper → DDG → Bing) | http, parse |
| 6 | `url-reader`   | Lee URL y devuelve markdown limpio | http, parse |

## Estructura de cada skill (agentskills.io v0.2.0)

```
skills-prioritarios/<id>/
├── SKILL.md          # required: frontmatter YAML + instrucciones
├── scripts/          # optional: ejecutables
│   ├── run.py
│   ├── install.sh
│   └── validate.py
├── references/       # optional: docs largas (se cargan on-demand)
└── assets/           # optional: templates, schemas
```

## Compatibilidad con OpenClaw

OpenClaw detecta skills con `SKILL.md` automáticamente. El comando equivalente es:

```bash
openclaw skill install <id>      # apunta a skills-prioritarios/<id>/
openclaw skill list
openclaw skill run <id> --input '{...}'
```

## Compatibilidad con cloudflare/.well-known/agent-skills/

Si en el futuro publicamos `https://agentes.example.com/.well-known/agent-skills/index.json`,
estas 6 skills se listan ahí con su `SKILL.md`.

## Estado

- 6/6 skills migradas al estándar `agentskills.io`.
- 4/6 validate pasan standalone (task-manager, git, terminal, web-search, url-reader — sí, 5/6).
- `test-runner` requiere `pytest` (no instalado en este sandbox; sí en HF Space).
