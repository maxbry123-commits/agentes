# Skill Router — GitHub Edition

Router que conecta los 4 grupos A/B/C/D con las skills del repo BIBLIOTECA.

## Arquitectura

```
Max (Max) → claude-code-vps-A (coder) → GitHub API (este router) → BIBLIOTECA (skills) → back to claude/mimo
       → claude-code-vps-B (verifier) ← audita resultado
       → mimo-code-vps-A (coder)    → VPS health
       → mimo-code-vps-B (verifier)  ← audita VPS
```

## Skills que cada grupo puede usar

| Grupo | Lee skills de | Escribe en |
|---|---|---|
| claude-code-vps-A | BIBLIOTECA/manuales/, BIBLIOTECA/prompts/ | GitHub (16+5 repos) |
| claude-code-vps-B | BIBLIOTECA/referencias/ | Solo audita, no escribe |
| mimo-code-vps-A | BIBLIOTECA/dsl/, BIBLIOTECA/arquitectura/ | VPS (/opt/nct/) |
| mimo-code-vps-B | BIBLIOTECA/plantillas/ | Solo audita, no escribe |
| claude-code-vps-C | Backup de A | Backup |
| mimo-code-vps-C | Backup de mimo-A | Backup |
| claude-code-vps-D | Backup de claude-B | Backup |
| mimo-code-vps-D | Backup de mimo-B | Backup |

## Como se invoca una skill

```bash
# Desde open-webui
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -d '{"model": "cerebras-coder", "messages": [{"role": "user", "content": "usar skill: add(a,b)"}]}'

# Desde telegram
/status
/claude usar skill: add(a,b)
```

## Estado actual

- 5 categorias de skills en /opt/nct/skills/ (registry, vault, judge, cache, metadata)
- 0 skills aprobadas (esperando BLOCK_NCT_SKILL_002)
- 4 grupos A/B + 4 grupos C/D configurados en /opt/nct/repos/agentes/
