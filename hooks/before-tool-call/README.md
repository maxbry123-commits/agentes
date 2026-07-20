# Hook `before_tool_call`

## Cuándo
Inmediatamente antes de que el gateway ejecute una tool, después de que el agente la eligió.

## Contrato

```yaml
name: before_tool_call
trigger: "tool.invoke.pre"
input:
  tool_id: string
  tool_args: object
  agent_id: string
  session_id: string
output:
  allow: boolean
  mutated_args: object (opcional)
  reason: string (si deny)
```

## Comportamiento esperado
1. Recibe `(tool_id, tool_args, agent_id, session_id)`.
2. Aplica policies del `12-policy` registry.
3. Si OK → `allow=true, mutated_args=tool_args` (posiblemente redactado).
4. Si NO → `allow=false, reason="..."` y el gateway aborta la ejecución.

## Ejemplo de uso (handler de Mavis)

```python
def handle(event):
    # 1. PII redaction
    args = redact_pii(event["tool_args"])
    # 2. policy: bash destructivo
    if event["tool_id"] == "bash" and is_destructive(args):
        return {"allow": False, "reason": "pol.destructive-bash"}
    # 3. policy: rate limit
    if rate_limited(event["agent_id"]):
        return {"allow": False, "reason": "pol.daily-quota"}
    return {"allow": True, "mutated_args": args}
```

## Tests pendientes
- [ ] Llamar con tool peligrosa → deny + reason correcto.
- [ ] Llamar con PII en args → mutated_args redactado.
- [ ] Llamar 1000 veces seguidas → rate limit activa.
