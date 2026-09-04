# Auditoría TEAM/SDPA 02 — CONNECTIVITY X-Ray

**Corte:** 2026-09-01 · **Repo:** `maxbry123-commits/agentes@main`  
**Anterior:** [01 — Estructura](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-01-ESTRUCTURA-XRAY-2026-09-01.md) · **Siguiente:** [03 — Comportamiento](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-03-COMPORTAMIENTO-XRAY-2026-09-01.md) · **Índice:** [YAIWES](https://github.com/maxbry123-commits/agentes/blob/main/README-ARQUITECTURA-FUSIONADA-YAIWES-XRAY-2026-09-01.md)

## Cadena que sí está conectada

```text
ficha_loader
→ fail_closed
→ preflight
→ spawn / instance / instance_store
→ workflow
→ forensic + gap_tasks
→ ledger + checkpoint + trace
```

También existe:

```text
EngineRequest
→ OpenClawEngine o HermesEngine
→ IntelligenceGateway
→ RouterHTTPGateway
→ ROUTER_URL
```

## Conexiones reales

| Origen | Destino | Evidencia | Estado |
|---|---|---|---|
| `preflight.py` | `fail_closed.py` + `ficha_loader.py` | imports directos | REAL |
| `bootstrap_multi.py` | instancia persistente + spawn | imports directos | REAL |
| `workflow.py` | forensic + gap compiler + repo truth | imports directos | REAL/PARCIAL |
| `OpenClawEngine` | IntelligenceGateway | contrato común | PARCIAL |
| `HermesEngine` | IntelligenceGateway | contrato común | PARCIAL |
| `router_http.py` | Router HTTP externo | urllib + entorno | REAL condicionado |
| `stages/engine.py` | Plan/LoopState/StepFn | FSM simple | REAL |
| `ast_scanner.py` | AST Python | módulo `ast` | REAL limitado |
| `dependency_graph.py` | imports del repositorio | scanner de imports | REAL limitado |
| `simulation/engine.py` | UniversalPlugin | simulación básica | REAL limitado |

## Roturas y falsos cierres

1. `workflow.py` crea `FakeRepoTruth` cuando no recibe repo. El default no demuestra operación contra GitHub real.
2. `bootstrap_v1.py` termina en `FakeGitDataPort` y declara modo `fake_stub`; no es despliegue productivo.
3. `intelligence.py` incluye gateway de texto fijo `GATEWAY_STUB`.
4. OpenClaw y Hermes están nombrados explícitamente como `stub`; estructuran envelopes, no son controladores completos.
5. `RouterHTTPGateway` depende de `ROUTER_URL`, disponibilidad, autenticación y contrato externo; no hay cierre integral del proveedor en esta raíz.
6. Los 502 ZIP no se importan, registran ni montan automáticamente en el kernel.
7. Los placeholders de `reasoning-kernel` no están conectados como una única cadena Ask-Consil/SDPA.
8. No aparece una cadena ejecutable completa:
   `InputBlock → DecisionEngine SDPA → AST universal → Inventory → Simulation → Integration → Verification → Wordflow → deploy real`.

## Cableado SDPA detectado

| Capa SDPA | Equivalente actual | Conectividad |
|---|---|---|
| 0 Kernel | wordflow_kernel + control-layer | Fragmentada |
| 1 Parser | `control-layer/evolution/analysis/ast_scanner.py` | Solo Python |
| 2 Inventory | symbol index + dependency graph + knowledge index | Sin motor único |
| 3 Simulation | evolution simulation + sandbox manager + ops_sim | Parcial |
| 4 Integration | enchufe_gate + goals_extractor | Sin merge AST |
| 5 Verification | forensic + evidence_verifier + test_runner | Parcial |
| 6 Wordflow | extensions/wordflow + kernel | Real, no cierre SDPA |

## Veredicto

**CONNECTIVITY: FAIL-CLOSED.**  
Existen conexiones internas útiles, pero varias rutas de demostración usan Fakes/Stubs y no hay cable E2E que materialice TEAM/SDPA como sistema completo.