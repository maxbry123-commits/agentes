# Auditoría TEAM/SDPA 03 — BEHAVIOR X-Ray

**Corte:** 2026-09-01 · **Repo:** `maxbry123-commits/agentes@main`  
**Anterior:** [02 — Conectividad](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-02-CONECTIVIDAD-XRAY-2026-09-01.md) · **Siguiente:** [04 — Cierre y GAPS](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-04-CIERRE-GAPS-XRAY-2026-09-01.md) · **Índice:** [YAIWES](https://github.com/maxbry123-commits/agentes/blob/main/README-ARQUITECTURA-FUSIONADA-YAIWES-XRAY-2026-09-01.md)

## Contrato esperado según SDPA aportado

```text
mismo input + mismo estado
→ misma decisión
→ mismo plan
→ mismo output
→ traza reproducible
```

SDPA exige siete capas: Kernel, Parser, Inventory, Simulation, Integration, Verification y Wordflow; además Ask-Consil de 12 pasos, Merkle state, seis modos de integración y rollback verificable.

## Verificación capa por capa

| Capa | Código detectado | Resultado |
|---|---|---|
| Kernel determinista | fail_closed, stages, workflow, ledger, checkpoint, council | PARCIAL: no hay `DecisionEngine` SDPA único |
| State Manager Merkle | ledger/checkpoint/state stores | FALTANTE: no hay Merkle root global demostrado |
| Deterministic Logger | ledger + trace | PARCIAL: no reproduce toda decisión SDPA |
| Parser universal | `ast_scanner.py` | PARCIAL: Python; no AST universal multilenguaje |
| Inventory Engine | dependency_graph, symbol_index, knowledge_index | PARCIAL: no VectorDB+GraphDB+history unido |
| Simulation | simulation engine, sandbox manager, ops_sim | PARCIAL: no blast radius/recursos/deadlock integral |
| Integration Engine | enchufe_gate y piezas de extracción | FALTANTE: no merge semántico 3-way por AST |
| Verification Engine | tests, forensic, evidence verifier | PARCIAL: no pipeline único Static→Unit→Integration→Simulation→Performance |
| Wordflow Agent | reception/planner/engine/kernel/UI gateway | PARCIAL: UI gateway provisional; no presentador SDPA completo |
| Ask-Consil 12 | council/goals aislados | FALTANTE: búsqueda de árbol no encuentra `ask_consil` |
| Seis modos | documentos SDPA | FALTANTE como FSM ejecutable |
| TEAM 90/10 | documentos TEAM | NO DEMOSTRADO como política global ejecutable |

## Comportamiento real observado

- `ParallelRuntime` ejecuta tareas con `ThreadPoolExecutor`; es paralelismo básico, no scheduler TEAM con sharding/time-wheel.
- `WordflowKernel` ejecuta audit→gaps→tasks y puede persistir memoria/checkpoints.
- El test de integración usa `LocalRepoTruth` y `MockIntelligenceGateway`; prueba componentes, no producción remota.
- `OpenClawEngine` y `HermesEngine` delegan razonamiento al gateway, pero siguen marcados como stubs.
- El hot path de programación real continúa en `extensions/wordflow/engine/code_path_runner.py`.
- El claim `PIPELINE/28_WORDFLOW_CORE_COMPLETED.md` limita expresamente su 100%: no incluye retry/recovery/evolution, C10 ni skill compiler. No demuestra TEAM/SDPA completo.

## Diferencia entre documentos y código

Los documentos TEAM describen InputBlock, MissionBuilder, DSL→DAG, 85 contratos, Sheriff FSM, scheduler, multi-API fabric, MYTHOS 40 pasos, recovery y certificación. El árbol contiene piezas equivalentes dispersas, pero no una prueba de que esa secuencia corra completa y fail-closed.

Los documentos SDPA añaden DecisionEngine, Merkle Tree, parser universal, inventario vector+grafo, simulación avanzada, merge AST y benchmark. Esos nombres y contratos no aparecen materializados como sistema integrado.

## Veredicto

**BEHAVIOR: FAIL-CLOSED / IMPLEMENTACIÓN PARCIAL.**  
Grok tenía base técnica para indicar que estaba incompleto: existe núcleo funcional parcial, pero los comportamientos TEAM y SDPA no están demostrados de extremo a extremo.