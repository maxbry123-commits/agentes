# CODE CANDIDATE MANIFEST — PLAN30 T02–T09

Contrato: `tel.workflow/v3` · modo: `FAIL_CLOSED_LOOP` · política: `REUSE > COPY/MOVE > PATCH QUIRÚRGICO > ADAPTER > GENERATE`.

## Decisiones verificadas

| ID | Mecanismo | Origen verificable | SHA/blob | Evidencia funcional | Destino YAIWES | Decisión |
|---|---|---|---|---|---|---|
| C01 | Cola determinista 1×1 | `maxbry123-commits/Agentes-motores-Wordflow-YAIWES/Loop Engineer/Loop-Engineer/loop/runner.py` | `daa32a5d6dfeb0d21a975b8a5b8384d68a8aa08e` | `select_next_task()` devuelve primer pending con deps hechas; `dispatch_once()` ejecuta como máximo un dispatch durable | `Agente Yaiwes principal/execution-orchestration/deterministic-execution/` | `COPY+ADAPTER`; destino actual es placeholder |
| C02 | Pause/resume event-sourced | `maxbry123-commits/Agentes-motores-Wordflow-YAIWES/Loop Engineer/Loop-Engineer/loop/runcontrol.py` | `2c6aff845c97b600d4b3851b5ee9a6e0ee23defb` | `pause_run/resume_run`, control de conflictos, append transaccional de eventos | `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/` | `ADAPTER`; preservar CheckpointStore existente y añadir control durable sin duplicar API |
| C03 | Identidad de reinyección/checkpoint provenance | `dta-au/elspeth/src/elspeth/contracts/identity.py` @ `720d441336434d227c2a00caaac100db48a07d5c` | `98b791e350e3a2829fb2c2977cc0fbc25beb4321` | `TokenInfo` frozen conserva `token_id`, `resume_attempt_offset`, `resume_checkpoint_id` mediante `with_updated_data()` | `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/` + contracts | `ADAPTER`; reutilizar patrón, no copiar imports/dependencias Elspeth completas |
| C04 | node_id + attempt + input_hash | `dta-au/elspeth/src/elspeth/contracts/audit.py` @ `720d441336434d227c2a00caaac100db48a07d5c` | `c89a5d9d2354ae549845aeab9a90cc3ab14f853e` | `NodeStateOpen/Pending/Completed/Failed` son frozen e incluyen `node_id`, `attempt`, `input_hash` | `Agente Yaiwes principal/state-events-durability/checkpoint-recovery/` + run-state contract | `ADAPTER`; extender checkpoint local para fijar INPUT literal y node identity |
| C05 | StrategyDelta distinto / no retry idéntico | `Alex-v-p/indexer-core/packages/rag_core/retrieval/retry/rules.py` @ `efcfcb20f09117504b00f682ada1bfff2b04b649` | `7704a6bd73d8b073df88651bbaf232f1f3dbfd6b` | `_next_strategy()` omite `attempted_strategies`; `decide()` retorna `NO_EFFECTIVE_FALLBACK` si query/top-k/strategy/targets no cambian | `Agente Yaiwes principal/control-governance/` | `ADAPTER`; extraer contrato/predicado genérico de delta sin arrastrar RAG |

## Comparación contra destino actual

- `execution-orchestration/deterministic-execution/` contiene solo `PLACEHOLDER.md` (blob `594c69b0cf98b6b102aebbea831a1001cfbab607`): **C01 no existe todavía**.
- `state-events-durability/checkpoint-recovery/checkpoint.py` blob `3c1aaa20a31256d0b2e43ec293202db53184a1d2` ya persiste `Checkpoint(... stable_hash(state))`, pero no fija `node_id + original INPUT_BLOCK hash + resume checkpoint provenance`: **REUSE parcial, GAP C03/C04 real**.
- `execution-orchestration/gap_bridge.py` blob `01e466302b1c6ac5609876be867dc41dafebeb90` compila GAP→TaskSpec→code_path jobs, pero no recuerda/bloquea `StrategyDelta` repetido: **REUSE del bridge + GAP C05 real**.
- `control-governance/` ya contiene contratos, sheriff/audit/application machinery; C05 debe vivir como guard separado, no como monolito nuevo.

## Dependencias/compatibilidad

1. `runner.py` original depende de varios módulos `loop.*`; **no se copia ciegamente**. Se reutiliza su algoritmo probado de selección/dispatch mediante adapter compatible con el runtime YAIWES.
2. `runcontrol.py` depende del event store de Loop Engineer; YAIWES ya tiene persistencia propia. Se porta únicamente la semántica de pause/resume/conflict como adapter sobre su store.
3. `identity.py`/`audit.py` son patrones de contrato; se adapta el conjunto mínimo de campos e invariantes a los modelos YAIWES.
4. `rules.py` es específico de retrieval; se adapta solo la regla general: `failed_delta_hash/attempted_strategy` no puede repetirse y el siguiente intento debe cambiar materialmente o cerrar `NO_EFFECTIVE_FALLBACK`.
5. Ninguna decisión autoriza monolito ni reemplazo masivo de código existente.

## Cierre T02–T09

- T02 inventario candidato: `VERIFIED_CLOSED` por ruta+SHA+lectura real.
- T03 runner 1×1: `VERIFIED_CLOSED` como candidato.
- T04 runcontrol: `VERIFIED_CLOSED` como candidato.
- T05 identidad/reinyección: `VERIFIED_CLOSED` como patrón candidato; implementación sigue en O03.
- T06 input_hash/node state: `VERIFIED_CLOSED` como patrón candidato; implementación sigue en O03.
- T07 StrategyDelta: `VERIFIED_CLOSED` como patrón candidato.
- T08 mapeo destino: `VERIFIED_CLOSED` por comparación contra árbol físico YAIWES.
- T09 provenance/compatibilidad: `VERIFIED_CLOSED` por este manifiesto.

Siguiente nodo 1×1: `PLAN30_T10` — integrar cola 1×1 en `execution-orchestration/deterministic-execution/`, conservando trazabilidad al blob fuente `daa32a...` y sin importar el paquete Loop Engineer completo.