# Hook `/reset` (slash command)

## Cuándo
Cuando el usuario tipea `/reset` en el chat.

## Diferencia con `/new`
- `/new` → crea sesión **nueva** (uuid distinto).
- `/reset` → **mantiene** el session_id pero borra el contexto (historial, scratchpad, herramientas cargadas).

## Contrato

```yaml
name: slash_reset
trigger: "user.message.match"
match: "^/reset\\b"
input: { user_id: string, session_id: string }
output:
  session_id: string   # mismo
  cleared_keys: array
  message_to_user: string
```

## Pendiente
- [ ] Definir exactamente qué se borra (¿variables globales? ¿state de skills?).
- [ ] Confirmar si la memoria persistente del agent (08-memory) sobrevive al reset.
