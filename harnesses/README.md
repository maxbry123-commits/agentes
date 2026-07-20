# 🏗️ Harnesses — Dónde se ejecuta cada skill

> Documento canónico: prompt M3 DSL DAG SHERIFF V7, sección D.

## Comparativa

| # | nombre | tier | tipo | mejor para |
|---|--------|------|------|------------|
| 1 | **Daytona**         | ⭐⭐⭐⭐⭐ | cloud IDE | programación |
| 2 | **E2B**             | ⭐⭐⭐⭐⭐ | microvm | skill aislada |
| 3 | **Sandbank**        | ⭐⭐⭐⭐⭐ | contenedor | capa unificada (rutea a otros) |
| 4 | **Agent/Mellona Hive** | ⭐⭐⭐⭐☆ | multi-tenant | multi-agent hive |

## Routing rules (de la sección K del prompt M3)

```
tarea.code      → daytona
tarea.skill     → e2b
tarea.gpu       → hf-space
tarea.edge      → cloudflare-sb
default         → sandbank
```

## Patrón de uso

El orquestador:
1. Recibe la tarea del usuario.
2. Pregunta al AI Registry (recomendador) → devuelve `{agent, skill, harness, model}`.
3. El harness toma la skill + el contexto y la ejecuta.
4. Devuelve resultado + logs.
5. El Memory Registry registra success/failure.

## Estado
- 4/4 carpetas creadas.
- 0/4 specs detallados.
- Próximo paso: completar README de cada harness con auth, endpoints, ejemplos, y pricing.

## Reglas duras
- **NO** usar Daytona para tareas que solo necesitan HTTP+parse (overkill).
- **NO** usar E2B para sesiones largas (>30min) — usa HF Space o Daytona.
- **NO** asumir que un harness está vivo: siempre `ping` antes de `exec`.
- **NO** instalar Daytona/E2B en el VPS — son servicios externos.
