# ⚡ Skills Prioritarios — los 6 desde el día 1

> Documento canónico: prompt M3 DSL DAG SHERIFF V7, sección B.

| # | id | descripción | tools requeridos |
|---|----|-------------|------------------|
| 1 | `task-manager` | Gestiona TODOs del orquestador | bash, fs |
| 2 | `test-runner`  | Corre tests del proyecto target | bash, fs |
| 3 | `git`          | Wrapper de git (branch, commit, push, PR) | bash |
| 4 | `terminal`     | Terminal controlado (sandboxed) | bash |
| 5 | `web-search`   | Búsqueda web (DuckDuckGo/Serper) | http, parse |
| 6 | `url-reader`   | Lee URL y devuelve markdown limpio | http, parse |

## Estructura de cada skill

```
skills-prioritarios/<id>/
├── README.md          # qué hace + cuándo se usa
├── skill.yaml         # manifest (id, version, entry, required_tools, tags)
├── install.sh         # openclaw skill install <id>  (idempotente, no-op si ya está)
├── validate.py        # test mínimo de smoke (1 caso)
└── examples/
    └── basic.md       # 1 ejemplo de uso
```

## Convención de nombres
- `id` = kebab-case
- `version` = semver
- `entry` = ruta al script principal (`./run.sh` o `./run.py`)

## Comando OpenClaw (prompt M3 F)
```bash
openclaw skill install <id>          # instala desde el repo local
openclaw skill list                   # lista skills disponibles
openclaw skill validate <id>          # corre validate.py
openclaw skill run <id> --input '{...}'  # ejecuta con payload JSON
```

## Aliases heredados
- `clawbot setup <id>` = `openclaw skill install <id>` (compatibilidad).

## Estado
- 6/6 carpetas creadas con `skill.yaml` + `install.sh` + `validate.py` + `README.md` + ejemplo.
- Tests: 0 corridos todavía (este turno solo dejamos la spec y los scripts; ejecución real en próximo turno con `openclaw` instalado en HF Space).
