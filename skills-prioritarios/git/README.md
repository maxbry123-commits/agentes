# git

## Qué hace
Wrapper de git con sub-comandos seguros:
- `clone`, `branch`, `commit`, `push`, `pr`, `status`, `diff`, `log`.
- Bloquea `--force` a `main`/`master` salvo override explícito.
- Maneja el PAT desde `${GITHUB_PAT_MAXBRY}`.

## Cuándo se usa
- Cada vez que un agente necesita mover código entre local y GitHub.
- En el workflow `wf.git.pr`.

## Schema
```yaml
id: git
version: 0.1.0
entry: ./run.py
required_tools: [bash]
required_mcps: [github]
tags: [vcs, git, github]
source: core
```

## Uso
```bash
openclaw skill run git --input '{"action":"status","repo":"."}'
openclaw skill run git --input '{"action":"branch","repo":".","name":"feature/x"}'
openclaw skill run git --input '{"action":"commit","repo":".","message":"wip"}'
openclaw skill run git --input '{"action":"pr","repo":".","title":"x","body":"y","base":"main"}'
```

## Seguridad
- `--force` requiere `policy.git-force-push` con efecto `allow` (default: deny).
- El token se inyecta por env var, nunca como argumento.

## Estado
- Spec completa, scripts en este dir.
- Pendiente: integración con `mcp/github` cuando esté disponible.
