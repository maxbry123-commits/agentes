# Daytona — ⭐⭐⭐⭐⭐

## Datos básicos
- **URL**: `daytona.io` (a confirmar con research)
- **Tipo**: cloud IDE / dev environment
- **Tier**: el más alto para programación según el prompt M3

## Por qué para programación
- Workspace persistente (archivos sobreviven entre invocaciones).
- VSCode-in-the-browser nativo.
- Soporta git, docker, terminal.
- Larga duración de sesión (horas, no minutos).

## Integración
- **Auth**: API key (env var `DAYTONA_API_KEY`).
- **Endpoint**: `https://api.daytona.io/v1/` (a confirmar).
- **SDK**: Python (`daytona-sdk`) o REST directo.

## Spec del wrapper (no código todavía)
```python
# spec, NO instalable en sandbox
def run_code(skill_id, code, *, timeout_s=900):
    workspace = daytona.workspace.create(template="python-3.11")
    workspace.upload(skill.bundle)
    result = workspace.exec(code, timeout=timeout_s)
    workspace.destroy()
    return result
```

## Riesgos
- Sesión puede terminar por timeout del provider.
- File-system ephemeral si no se guarda explícitamente.
- Pricing por minuto de compute.

## Pendiente
- [ ] Confirmar pricing y free tier.
- [ ] Probar `workspace.create` con cred de prueba (en HF Space, no VPS).
- [ ] Medir cold-start real.
