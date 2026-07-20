# E2B — ⭐⭐⭐⭐⭐

## Datos básicos
- **URL**: `e2b.dev` (a confirmar)
- **Tipo**: microvm sandboxed (Firecracker)
- **Tier**: el más alto para skills aisladas

## Por qué para skill aislada
- Arranca en <200ms.
- Sandbox real (no comparte kernel).
- Ideal para ejecutar código no-confiable.
- Sesiones cortas (≤30min).

## Integración
- **Auth**: API key (env var `E2B_API_KEY`).
- **SDK**: Python (`e2b`) o REST.

## Spec del wrapper
```python
# spec, NO instalable en sandbox
def run_skill(skill_id, payload, *, timeout_s=120):
    sandbox = e2b.Sandbox.create(template="base")
    sandbox.upload(skill.bundle)
    result = sandbox.exec(skill.entry, payload=payload, timeout=timeout_s)
    sandbox.kill()
    return result
```

## Riesgos
- No persistente: si la skill necesita memoria cross-invocación, hay que pasarla por payload.
- Limitado a Linux x86_64.

## Pendiente
- [ ] Confirmar default template y si tiene `python-3.11` listo.
- [ ] Probar `e2b.Sandbox.create()` real.
- [ ] Documentar tamaño máximo de bundle.
