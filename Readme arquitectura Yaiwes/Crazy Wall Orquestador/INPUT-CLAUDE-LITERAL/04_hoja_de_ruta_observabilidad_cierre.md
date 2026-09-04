# 📂 MAPA DE RUTA — BLOQUE 4 DE 4
## Observabilidad, testing y cierre de la primera versión completa (Fase 5)
**Depende de:** cierre del Bloque 3 (workflow + pool funcionando de punta a punta)
**Objetivo del bloque:** que la próxima auditoría X-Ray pueda cambiar el veredicto de `FAIL-CLOSED / PARCIAL` a `PASS / COMPLETO`.

---

## TABLA DE TAREAS 56-70

| # | Tarea | Mini-prompt para la IA | Ubicación final | OSS/Recurso a usar | IA sugerida |
|---|---|---|---|---|---|
| 56 | Implementar `observability/trace-history` | "Instrumenta cada llamada del kernel con trazas distribuidas estándar." | `observability/trace-history/` | OpenTelemetry | Codex |
| 57 | Hacer obligatorio mission_id/trace/ledger | "Modifica el Event Loop para que ninguna ejecución pueda iniciar sin un mission_id, trace_id y entrada de ledger asociados." | `kernel-principal/event_loop.py` | — | Claude Code |
| 58 | Implementar ledger/checkpoint durable | "Envuelve la ejecución de workflows críticos en un motor de ejecución durable que sobreviva reinicios." | `state-events-durability/` | Temporal (o LangGraph checkpointer si se prefiere más ligero) | Claude Code |
| 59 | Implementar `retry-policy` con reintentos deterministas | "Implementa reintentos con backoff exponencial conectados al circuit-breaker." | `resource-governance/retry-policy/` | Tenacity | Codex |
| 60 | Implementar `circuit-breaker` real | "Implementa un breaker que abra el circuito tras N fallos consecutivos de una capacidad y la marque como no disponible temporalmente." | `resource-governance/circuit-breaker/` | Tenacity / `pybreaker` | Codex |
| 61 | Implementar `resource-broker-gate` + `lease-management` | "Implementa un control de cuántas ejecuciones concurrentes puede sostener el sistema, con préstamo (lease) de recursos por tarea." | `resource-governance/resource-broker-gate/` | — | Codex |
| 62 | Implementar `watchdog` | "Implementa un proceso que detecte tareas colgadas más allá de su deadline (tarea 26) y las cancele forzosamente." | `resource-governance/watchdog/` | — | Codex |
| 63 | Reemplazar Fake/Stub por contract-testing real | "Sustituye los stubs de prueba detectados por la auditoría por tests de contrato reales contra los esquemas de `schema-contracts/`." | ubicación original de cada stub detectado | Schemathesis o Pact | Codex |
| 64 | Generar Estado Merkle global | "Genera una prueba verificable del estado del ledger completo." | `state-events-durability/merkle/` | `pymerkle` (o usar Git como Merkle DAG) | MiniMax |
| 65 | Prueba E2E completa | "Escribe y ejecuta una prueba que cubra: reception → mission → decision → execution → evidence → closure, de principio a fin, sin mocks en los puntos críticos." | `execution-orchestration/tests/test_e2e_completo.py` | `pytest` + utilidades de testing de Temporal | Claude Code |
| 66 | SBOM + secret scan final de todo el repo | "Ejecuta un escaneo de secretos y dependencias sobre el repositorio completo antes de declarar cerrada la v1." | raíz del repo | `detect-secrets` + `syft` | MiniMax |
| 67 | Consolidar manifest final de las 8 primitivas | "Verifica que las 8 primitivas del manifest de la tarea 14 digan `nativo` o `delegado documentado` — ninguna puede quedar sin estado." | `kernel-principal/MIGRATION_MANIFEST.yaml` | — | GPT |
| 68 | Cerrar los 18 placeholders restantes | "Vuelve a correr `mypy --strict` sobre `kernel-principal/` y confirma cero placeholders restantes." | `kernel-principal/` | `mypy` | Codex |
| 69 | Auditoría final completa | "Repite exactamente el mismo formato de la Auditoría X-Ray original (conteo de archivos, Python, tests, placeholders) sobre todo `agente-yaiwes/`." | raíz del repo, nuevo documento de auditoría | — | MiniMax |
| 70 | Redactar veredicto de cierre v1 | "Compara la auditoría de la tarea 69 contra la original y redacta el veredicto final: qué cambió de PARCIAL a COMPLETO, con evidencia de cada cambio." | raíz del repo, `VEREDICTO_CIERRE_V1.md` | — | GPT |

---

## CHECKPOINTS — rellenar al cerrar cada tarea

📝 Checkpoint tarea 56 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 57 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 58 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 59 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 60 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 56-60 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 61 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 62 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 63 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 64 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 65 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 61-65 — Quién audita: ___ | Fecha: ___ | Veredicto: ___

📝 Checkpoint tarea 66 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 67 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 68 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 69 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___
📝 Checkpoint tarea 70 — Quién: ___ | IA: ___ | Fecha/hora: ___ | 100% pass: ☐ Sí ☐ No | Evidencia adjunta: ___

🔍 Auditoría tareas 66-70 (CIERRE DE LA V1 COMPLETA) — Quién audita: ___ | Fecha: ___ | Veredicto: ___

---

## Criterio final de "primera versión completa"

La v1 está cerrada solo si las 4 condiciones siguientes son verdaderas al mismo tiempo:

1. El manifest de las 8 primitivas del Kernel TEAM no tiene ningún estado vacío.
2. Existe al menos un workflow real, probado E2E, que pasa por reception→mission→decision→execution→evidence→closure sin usar stubs.
3. El pool paralelo ejecuta al menos 2 agentes/workers reales con roles distintos y un agregador que produce una decisión final.
4. La auditoría X-Ray repetida (tarea 69) muestra cero placeholders en `kernel-principal/` y cobertura de tests en `reasoning-kernel/` y `extension-kernel/` (hoy en 0).

Si alguna de las 4 no se cumple, el veredicto sigue siendo `FAIL-CLOSED / PARCIAL` — no se declara v1 completa a medias.
