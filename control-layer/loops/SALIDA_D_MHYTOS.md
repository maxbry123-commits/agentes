# Salida D/6 — MHYTOS dentro de ejecutar

## Hecho
- `strategy=sequential` → dispatch único
- `parallel|adversarial|consensus` → MHYTOSExecutor 6 fases
- consensus = mayoría · adversarial = all ok · parallel = threads + merge ordenado

## Uso
ctx.strategy o inputs strategy antes de run_iteration

## Siguiente E/6
Progress desde outputs de fase (tests/evidence reales)
