# Hook `on-gateway-start`

## Cuándo
Una sola vez: al arrancar el gateway, antes de aceptar el primer request.

## Contrato

```yaml
name: on_gateway_start
trigger: "gateway.startup"
input: { gateway_id: string, config_path: string }
output:
  init_log: array
  loaded_skills: array
  warnings: array
```

## Comportamiento
1. Lee config.
2. Carga los 6 skills prioritarios.
3. Ping a MCPs críticos.
4. Verifica que las API keys requeridas estén presentes.
5. Devuelve un `init_log` legible.

## Pendiente
- [ ] Cuál es el orden de carga de los 6 skills prioritarios.
- [ ] Si un skill crítico falla, ¿bloqueamos el startup o seguimos degradados?
