# Hook `before_agent_reply`

## Cuándo
Inmediatamente antes de que el gateway envíe la respuesta del agente al usuario.

## Contrato

```yaml
name: before_agent_reply
trigger: "agent.reply.pre"
input:
  reply_text: string
  agent_id: string
  session_id: string
  user_id: string
output:
  final_text: string
  truncated: boolean
  reason: string (si se mutó)
```

## Comportamiento esperado
1. Recibe el texto crudo que el agente quiere enviar.
2. Aplica reglas de formato (para Max: ≤6 líneas).
3. Si el agente es Mavis y la respuesta tiene >6 líneas → truncar + agregar footer.
4. Si el usuario pidió expansión explícita → no truncar.
5. Devuelve `final_text` listo para enviar.

## Ejemplo (regla de Max)

```python
def handle(event):
    text = event["reply_text"]
    user_id = event["user_id"]
    if user_id != "maxbry":
        return {"final_text": text, "truncated": False}
    # 6 líneas máx
    lines = text.splitlines()
    if len(lines) <= 6:
        return {"final_text": text, "truncated": False}
    kept = "\n".join(lines[:6])
    return {
        "final_text": kept + "\n\n[…truncado, pedí 'expandir' si querés todo]",
        "truncated": True,
        "reason": "max-6-lines policy"
    }
```

## Pendiente
- [ ] Detección de "el usuario pidió expandir" (regex sobre historial).
- [ ] Footer opcional con TODOs pendientes.
