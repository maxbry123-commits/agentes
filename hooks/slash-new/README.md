# Hook `/new` (slash command)

## Cuándo
Cuando el usuario tipea `/new` en el chat (cualquier agente).

## Contrato

```yaml
name: slash_new
trigger: "user.message.match"
match: "^/new\\b"
input: { user_id: string, session_id: string }
output:
  new_session_id: string
  message_to_user: string
  persist_context: object
```

## Comportamiento
1. Crea una sesión nueva (uuid).
2. NO copia el historial (limpieza total).
3. Mensaje al usuario: "Sesión nueva creada. Decime qué necesitás."
4. Opcional: persistir un resumen de la sesión anterior al `08-memory` registry.

## Pendiente
- [ ] Definir si la memoria compartida entre sesiones es por user_id o global.
- [ ] Política de retención de la sesión anterior.
