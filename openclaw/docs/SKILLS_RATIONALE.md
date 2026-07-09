# OpenClaw como capa de Skills

OpenClaw tiene su propio sistema de skills. **No** se conecta a /opt/nct/skills/ directamente.
Los skills de OpenClaw son archivos `.md` en `~/.openclaw/skills/` o registrados en `openclaw.json`.

Para skills compartidas entre los 3 grupos (OpenClaw + Claude Code + MiMo Code), el sistema de
referencia es `/opt/nct/skills/vault/approved/` (Skill Router).

Flujo:
1. Skill se descubre → entra a `/opt/nct/skills/cache/staging/`
2. Judge la valida (security, integrity, deps, sandbox, quality, compat)
3. Si PASS → `/opt/nct/skills/vault/approved/<tipo>/`
4. OpenClaw puede consultarla via `openclaw skills list` (o equivalente)
