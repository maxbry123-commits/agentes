# 12 · Policy Registry

## Propósito
Catálogo de **reglas, permisos y límites** que el sheriff valida antes de ejecutar cualquier acción. Una policy = 1 regla declarativa (allow / deny / require / rate-limit / approve).

## Schema (v0.1)
```json
{
  "title": "Policy",
  "type": "object",
  "required": ["id", "effect", "resource", "action"],
  "properties": {
    "id":         { "type": "string" },
    "effect":     { "type": "string", "enum": ["allow","deny","require_approval","rate_limit","redact"] },
    "subject":    { "type": "string", "description": "agent_id, role, user_id, o '*'" },
    "action":     { "type": "string" },
    "resource":   { "type": "string" },
    "conditions": { "type": "object" },
    "priority":   { "type": "integer" }
  }
}
```

## Catálogo seed (las del prompt M3)

| id | effect | subject | action | resource |
|----|--------|---------|--------|----------|
| `pol.no-vps-write`    | deny            | *                  | write_file | `vps://*` (excepto healthcheck) |
| `pol.max-6-lines`     | require_approval| Mavis              | respond    | chat (default Max) |
| `pol.no-real-install` | deny            | M3                 | shell.exec | `sandbox://*` (modo investigación) |
| `pol.elevated-tools`  | require_approval| M3                 | tool.invoke | `tool:docker`, `tool:bash(destructive)` |
| `pol.daily-quota`     | rate_limit      | agent_id:*         | *          | budget: 100k tokens/día |
| `pol.pii-redact`      | redact          | *                  | *          | regex: email|phone|credit_card |
| `pol.git-force-push`  | deny            | *                  | git.push   | `--force` |
| `pol.repo-public`     | deny            | *                  | repo.create_visibility | `public` |
| `pol.hf-space-write`  | allow           | M3                 | hf.write   | `space:*` (de HF_TOKEN_*) |
| `pol.gh-pat-rotation` | require_approval| Mavis              | secret.update | `GITHUB_PAT_MAXBRY` |

## Tareas pendientes
- [ ] Implementar evaluador de policies en `core/sheriff.py` (referencia, no instalador).
- [ ] Política de firma/audit log de cada decisión del sheriff.
- [ ] Dif visual entre versiones de una policy.
