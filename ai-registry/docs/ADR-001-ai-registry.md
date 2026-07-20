# ADR-001 — ¿Por qué un AI Registry intermedio y no consultar los 12 directo?

## Estado
Aceptado. Fecha: 2026-07-20.

## Contexto
Los 12 registries cubren todo el dominio (agents, skills, tools, prompts, mcps, capabilities, knowledge, memory, workflows, harnesses, models, policies). Pero el orquestador, el gateway, y el panel necesitan responder consultas como:

- "Dada esta tarea, ¿qué agente + skill + harness + modelo uso?"
- "Dame la vista 360° de este agente (skills, mcps, latencia, costo)."
- "¿Qué cambió en los registries en las últimas 24h?"

Si cada consumidor habla con 12 registries, hay N×12 acoplamientos, N caches distribuidos, y N politicas de consistencia. Inmanejable.

## Decisión
Crear una **capa intermedia** (AI Registry) que:
1. Sincroniza los 12 registries a su propio modelo (cards).
2. Calcula enrichments (live_ping, success_rate, costo, etc.).
3. Expone una API única con 3 endpoints (`recommend`, `cards/{kind}/{id}`, `health`).
4. Mantiene caché por tipo de entry.

## Consecuencias
**Positivas**:
- Consumidores simples: 1 API, 3 endpoints.
- Cambios en un registry se propagan centralizadamente.
- Métricas agregadas (latencia, éxito) en un solo lugar.
- Recomendador puede vivir aquí (no en cada registry).

**Negativas**:
- Punto único de falla (mitigable con caché local + read-only fallback).
- Eventual consistency: la card puede tener minutos de desfase vs la fuente.
- Más código que mantener (la API, el sync, el recomendador).

## Alternativas consideradas
- **A)** Dejar que cada consumidor consulte los 12 directo → descartada por acoplamiento.
- **B)** Hacer un mega-registry único → descartada porque pierde la separación de concerns (un policy tiene lifecycle distinto de un mcp).
- **C)** GraphQL federado → viable pero más complejo de operar que un REST simple.
