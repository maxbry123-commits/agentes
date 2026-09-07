# RECOVERY — Integración componentes YAIWES

<!-- YAIWES_RECOVERY_V1 -->
Contrato histórico del snapshot de componentes: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Método de recuperación vigente para nuevas operaciones

Autoridad de ejecución: `tel.workflow/v4` / `FAIL_CLOSED_EXECUTION_LOOP`.

Guía canónica:
`➡️📂 Wordflow LOOP Yaiwes/GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md`

Recovery v4 obligatorio:
1. Leer `state.json` + `CHECKPOINT.json` + `PLAN` + `RECOVERY` + `BITACORA` + guía v4.
2. Leer HEAD real y Actions/escrituras concurrentes relevantes.
3. Tratar divergencia entre snapshot y repo real como `STALE_STATE/GAP`, nunca como permiso para reescribir historial.
4. Adoptar trabajo concurrente equivalente; reinyectar solo lo que falte; nunca force.
5. Recuperar el último `VERIFIED_CLOSED` real y el nodo activo real.
6. Ejecutar solo un delta 1×1 seguro.
7. Si falla, registrar `FAILED_STRATEGY + EVIDENCE + DO_NOT_REPEAT + NEW_STRATEGY` y ejecutar un StrategyDelta distinto.
8. Un mock/injection/wiring no sustituye runtime real cuando el gate exige ejecución real.
9. Persistir de nuevo STATE/CHECKPOINT/PLAN/RECOVERY/BITACORA después del delta.

Esta sección replica **el método**, no el proyecto UI YAIWES. Provenance fuente: `maxbry123-commits/frontend`, guía UI blob `7aa569945037a228f36eeed1747b7557b1adc5b6`.

## Último cierre recuperable del snapshot histórico
- Componente: `Ajv`
- Estado: `VERIFIED_CLOSED`
- Destino: `Agente Yaiwes principal/definition-registry/schema-contracts/ajv/`
- MOVE commit: `95713304ee644b053efed4c9947af75bf71fd87c`
- CI final commit: `b69d38dc8500164849a82daa21c15d98705655b5`
- Run: `34061366845`
- Job: `101562375081`
- Repeticiones runtime: `10/10 PASS`

## Reanudación exacta registrada históricamente
- Nodo raíz: `Core kernel Yaiwes/Componentes recuperados A`
- Componente activo del snapshot: `Apache-APISIX`
- Clasificación registrada: `B`
- Destino: `Agente Yaiwes principal/mesh-routing-collaboration/apisix-api-gateway/`
- Próximo gate histórico: mover solo código runtime útil, cablear Universal Plugin Bus/Ficha v2 y verificar runtime OpenResty real.
- GAP histórico: `OPENRESTY_RUNTIME_GATE_PENDING`.

**Advertencia v4:** estos campos son historial recuperable, no verdad fresca. Antes de usarlos se debe cruzar con HEAD, commits/runs y state/checkpoint actuales.

## Regla de recuperación
Releer `README arquitectura` + `PLAN` + `CHECKPOINT.json` + `state.json` + `BITACORA.md` + guía v4; validar HEAD/diffs/runs; si la evidencia diverge, volver a RESEARCH con StrategyDelta distinto. Nunca reconstruir estado por suposición.
