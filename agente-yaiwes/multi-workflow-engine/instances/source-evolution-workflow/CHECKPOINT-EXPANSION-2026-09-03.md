# CHECKPOINT — Expansión de autoevolución YAIWES

Fecha de corte: 2026-09-03 UTC

## Estado

`IN_PROGRESS` — no declarar 100% PASS mientras existan jobs activos o pruebas pendientes.

## Completado

- Contrato de 50 goals de entrada y 12 goals de salida.
- Presupuesto de investigación: 100 candidatos/señales por carril activo.
- 12 Ask Consilio, 3 simulaciones y 3 refutaciones como gates obligatorios.
- Controladores Sheriff, Validator, Sentinel, Supervisor, Judge y Guardian.
- Constitución de workspace y system prompt limitado a propuesta; el LLM no autoriza ni muta.
- DAG ampliado: investigación → autorización → adquisición → sandbox → adapter/bus → pruebas → KPI → cierre/rollback/NCT.
- LOOP horario activo hasta `VERIFIED_CLOSED`.

## GitHub Actions activos

1. Reparación quirúrgica del GAP `source-provenance` y cableado del plugin bus:
   https://github.com/maxbry123-commits/agentes/actions/runs/33704929697
2. Copia directa y trazable de fuentes aprobadas:
   https://github.com/maxbry123-commits/agentes/actions/runs/33705038428

## Fuentes seleccionadas

| Fuente | Uso | Commit fijado | Licencia | Destino |
|---|---|---|---|---|
| SIA | feedback y mejora por generaciones | `7fd04d07bd2f47a110115674432b73622ebf7455` | MIT | `source-evolution-workflow/feedback-improvement/vendor/sia` |
| MemOS | memoria de fallos, recuperación y skills | `28dfb4e7d3adad1c93fd5574675f913921367d36` | Apache-2.0 | `source-evolution-workflow/continuous-memory/vendor/memos` |
| Agenvoy | MCP, scheduling y tool forge controlado | `71d0f828dedde8949d6a22184f74642f4fcc5541` | Apache-2.0 | `source-evolution-workflow/tool-forge/vendor/agenvoy` |
| HyperAgents (Meta) | referencia arquitectónica | `59a68f672dfb92c74aeb7e61535d776fb36e172d` | CC BY-NC-SA 4.0 | `research-references`; no ejecutable |

## Pendiente para cierre

- Confirmar ambos Actions en PASS.
- Si hay fallo, crear reparación aislada solo para el GAP.
- Generar índice forense de capacidades después de la copia.
- Validar hashes, licencias, rutas, duplicados y read-back.
- Probar Registry, Adapter, BUS, Schema, watchdog, autorización, sandbox y memoria estructurada.
- Ejecutar tres simulaciones, tres refutaciones y E2E.
- Probar hot-swap y rollback.
- Emitir checkpoint final únicamente con cero GAPS y cero jobs activos.

## Iteración — microkernel paralelo

- Run de reparación del plugin bus y provenance: **PASS**.
  https://github.com/maxbry123-commits/agentes/actions/runs/33704929697
- El run inicial de adopción falló únicamente en un predicado de deduplicación demasiado amplio; las tres copias y sus SHA habían pasado antes del gate.
- Reparación nueva y aislada, con identidad `URL + commit + destino`:
  https://github.com/maxbry123-commits/agentes/actions/runs/33706085153
- Estado de la reparación al corte: `IN_PROGRESS`.
- Añadido `README.md` operativo inspirado en los patrones de contexto de Claude Code y workspace de OpenClaw.
- Añadido microkernel paralelo con autorización por huella, concurrencia limitada, timeout, proceso sin shell, entorno mínimo, ledger nuevo y aislamiento de fallos.
- Pruebas locales: `4/4 PASS`; la prueba CI permanece pendiente dentro del run activo.
- Cableado actualizado en ambos sentidos entre `source-evolution-workflow` y `extension-kernel/plugin-bus`.
- Candidatos evaluados: Inspect AI/Sandboxing recomendado previa deduplicación/autorización; Agent Lightning y ART diferidos; LangMem solapado con MemOS; AnyIO innecesario en esta versión.
