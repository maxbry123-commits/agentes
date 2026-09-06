# RECOVERY — Integración componentes YAIWES

<!-- YAIWES_RECOVERY_V1 -->
Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Último cierre recuperable
- Componente: `Ajv`
- Estado: `VERIFIED_CLOSED`
- Destino: `Agente Yaiwes principal/definition-registry/schema-contracts/ajv/`
- MOVE commit: `95713304ee644b053efed4c9947af75bf71fd87c`
- CI final commit: `b69d38dc8500164849a82daa21c15d98705655b5`
- Run: `34061366845`
- Job: `101562375081`
- Repeticiones runtime: `10/10 PASS`

## Reanudación exacta
- Nodo raíz: `Core kernel Yaiwes/Componentes recuperados A`
- Componente activo: `Apache-APISIX`
- Clasificación: `B`
- Destino: `Agente Yaiwes principal/mesh-routing-collaboration/apisix-api-gateway/`
- Próximo gate: mover solo código runtime útil, cablear Universal Plugin Bus/Ficha v2 y verificar runtime OpenResty real.
- GAP abierto: `OPENRESTY_RUNTIME_GATE_PENDING`.

## Regla de recuperación
Releer `README arquitectura` + `PLAN` + `CHECKPOINT.json` + `state.json` + `BITACORA.md`; validar HEAD/diffs/runs; si la evidencia diverge, volver a RESEARCH con StrategyDelta distinto. Nunca reconstruir estado por suposición.
