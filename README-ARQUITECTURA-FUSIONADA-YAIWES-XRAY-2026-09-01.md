# README — Arquitectura fusionada YAIWES · X-Ray

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Fecha de corte:** 2026-09-01  
**Regla:** GitHub y el código ejecutable son la verdad. Una carpeta o documento no demuestra que una capacidad esté operativa.

## 1. Fuentes fusionadas y trazabilidad

1. [Índice raíz de arquitectura YAIWES](https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20estructura%20ra%C3%ADz%20de%20agente%20Yaiwes%20wordflow.md)
2. [PLAN_100 — árbol definitivo](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md)
3. [STRUCTURE — estructura materializada](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/STRUCTURE.md)
4. [README canónico de agente-yaiwes](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/README.md)
5. [Foto de producción y GAPS](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/Agente_YAIWES_v.1_en_PRODUCCION.md)
6. [Mapa de organización del código real](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md)
7. [Arquitectura Wordflow consolidada](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMACION_CONSOLIDADA.md)
8. [Pasada 1 — Structure](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_01_STRUCTURE.md)
9. [Pasada 2 — Connectivity](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_02_CONNECTIVITY.md)
10. [Pasada 3 — Behavior](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_03_BEHAVIOR.md)
11. [Pasada 4 — Cierre](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/FORENSE_PASADA_04_CIERRE.md)

## 2. Leyenda X-Ray

- **REAL:** código ejecutable materializado.
- **PARCIAL:** existe una parte, espejo o cableado incompleto.
- **ESQ:** scaffold/placeholder; no equivale a capacidad.
- **REF:** puntero a la fuente canónica.
- **FALTANTE:** requerido por la arquitectura y no demostrado por código o pruebas.

## 3. Arquitectura completa fusionada — cuatro niveles

```text
main/
└── agente-yaiwes/
    ├── code-programming-engine/                         [PARCIAL/REF]
    │   ├── engine-modules/
    │   │   ├── code_path_runner.py                     [REF al hot path]
    │   │   ├── programming_pipeline.py                 [REF al hot path]
    │   │   └── cognitive_loop.py                       [REF/PARCIAL]
    │   ├── code-path-execution/
    │   │   ├── programming-modular-v1/
    │   │   ├── p01...p12                               [FALTANTE en main]
    │   │   └── evidence/                               [PARCIAL]
    │   ├── standards-forensic/
    │   ├── schema-contracts-io/
    │   ├── external-motor-bridge/
    │   ├── multi-account-bridge/
    │   ├── inbox-normalization/
    │   └── module-tests/
    ├── kernel-principal/
    │   ├── control-layer/
    │   │   └── SOURCE.md                               [REF]
    │   ├── extension-kernel/
    │   │   ├── abi-mount/
    │   │   ├── capability-registry/
    │   │   ├── capability-passport/
    │   │   ├── native-learning/
    │   │   └── mount-guard/
    │   ├── reasoning-kernel/
    │   │   ├── decision-on-demand/
    │   │   ├── expert-panel-router/
    │   │   ├── consensus-trigger/
    │   │   ├── goal-dual-driver/
    │   │   └── workflow-capacity/
    │   ├── resource-governance/
    │   │   ├── resource-broker-gate/
    │   │   ├── lease-management/
    │   │   ├── watchdog/
    │   │   ├── circuit-breaker/
    │   │   └── retry-policy/
    │   ├── internal-bus/
    │   └── execution-manifest/
    ├── input-layer/
    │   ├── cli-entry/
    │   ├── route-entry/
    │   ├── cross-tool-session-import/
    │   └── reception/
    ├── definition-registry/
    │   ├── workflow-definition/
    │   │   ├── yaml-dag/
    │   │   ├── step-template/
    │   │   └── source-hierarchy/
    │   ├── agent-definition/
    │   ├── task-definition/
    │   ├── tool-definition/
    │   ├── skill-definition/
    │   ├── schema-contracts/
    │   ├── domain-specific-contracts/
    │   ├── declared-dependency-catalog/
    │   └── authorization-model/
    ├── control-governance/
    │   ├── contracts-and-gates/
    │   ├── sheriff-sentinel-council/
    │   ├── forensic-verdict/
    │   ├── symbol-test-requirement-index/
    │   ├── policy-guardrails-permissions/
    │   ├── refute-repair/
    │   ├── pre-post-closure-gates/
    │   └── gap-registry-and-tasks/
    ├── multi-workflow-engine/
    │   ├── shared-services/
    │   │   ├── workflow-registry/
    │   │   ├── runner-host/
    │   │   ├── dashboard-budget/
    │   │   └── control-ops/
    │   └── instances/
    │       ├── workflow-1/
    │       ├── workflow-2/
    │       ├── workflow-3/
    │       └── workflow-N/
    ├── execution-orchestration/
    │   ├── state-machine-executor/
    │   ├── dag-executor/
    │   ├── sequential-parallel-loop-route/
    │   ├── container-pod-isolation/
    │   ├── task-generation/
    │   ├── deterministic-execution/
    │   ├── mission-planning-goal-lock/
    │   ├── classifier-scheduler/
    │   ├── dependency-injection-context/
    │   └── programming-pipeline/
    ├── agent-fleet-parallelism/
    ├── execution-engine-pool/
    │   ├── adapter-layer/                              [PARCIAL]
    │   ├── capability-matching/
    │   ├── parallel-dispatch/
    │   ├── worktree-isolation/
    │   ├── result-normalization/
    │   └── auxiliary-role-agents/                      [STUBS]
    ├── mesh-routing-collaboration/
    ├── pipeline-runtime/
    ├── codebase-intelligence/
    ├── session-resilience/
    ├── identity-config/
    ├── human-in-the-loop/
    ├── communication-notifications/
    ├── control-plane-ui/
    ├── state-events-durability/
    │   └── dead-letter-handling/
    ├── tools-models-memory-knowledge/
    │   └── mcp-transport/
    ├── research-evidence/
    ├── security-auth/
    ├── observability/
    │   └── trace-history/
    ├── multi-project-orchestration/
    ├── artifact-output-storage/
    ├── deploy-publish/
    │   ├── multi-account-registry/
    │   ├── push-injection/
    │   ├── publish-schema-layer/
    │   ├── remote-crud-ops/
    │   └── deployment-target-selector/
    ├── extensions/                                    [REF]
    ├── PIPELINE/                                      [REF]
    ├── agents/                                        [REF]
    └── .github-workflows-refs/                        [REF]
```

## 4. Código operativo real y Wordflow actual

La arquitectura nueva no sustituyó por completo el runtime anterior. El flujo ejecutable principal permanece aquí:

```text
main/
└── extensions/
    ├── wordflow/
    │   ├── reception/
    │   │   └── convert / normalización
    │   ├── planner/
    │   │   └── misión / tareas / clasificación
    │   ├── engine/
    │   │   ├── code_path_runner.py                    [HOT PATH REAL]
    │   │   ├── programming_pipeline.py                [REAL]
    │   │   ├── programming_kwargs.py                  [REAL]
    │   │   ├── input_quality_bar.py                   [REAL]
    │   │   ├── skill_native_compiler.py               [REAL]
    │   │   ├── goal_lock.py                           [REAL]
    │   │   └── cognitive_loop.py                      [REAL/PARCIAL]
    │   ├── motors/
    │   ├── codegen/
    │   ├── connectors/
    │   ├── contracts/
    │   ├── schemas/
    │   ├── standards/
    │   ├── state/
    │   ├── store/
    │   ├── policies/
    │   ├── accounts/
    │   └── tests/
    └── wordflow_kernel/
        ├── gateway/
        │   ├── intelligence.py                        [PUNTO DE ENCHUFE]
        │   └── router_http.py                         [ADAPTADOR HTTP]
        ├── runtime/
        ├── contracts/
        └── auxiliary/
            ├── openclaw_stub.py                       [STUB]
            └── hermes_stub.py                         [STUB]
```

### Flujo transversal

```text
Entrada
→ reception.convert
→ goals / goal_lock
→ mission + planner
→ task_classifier
→ programming_pipeline
→ code_path_runner
→ motors / tools / adapters
→ evidence
→ gates forenses
→ artefacto / despliegue
```

## 5. Qué existe y qué falta

| Área | Evidencia actual | Estado | Falta demostrable |
|---|---|---:|---|
| Árbol PLAN_100 | Scaffold materializado | PARCIAL | Sustituir ESQ por cuerpos reales y probarlos |
| Hot path de programación | `extensions/wordflow/engine/code_path_runner.py` | REAL | Mantener hasta paridad de tests |
| Pipeline de programación | `programming_pipeline.py` y módulos asociados | REAL/PARCIAL | Cadena integral verificada |
| Kernel Wordflow | `extensions/wordflow_kernel/` | PARCIAL | Adaptadores reales y pruebas E2E |
| Router de inteligencia | `gateway/intelligence.py`, `router_http.py` | PARCIAL | Providers reales y failover probado |
| Motor modular p01–p12 | Declarado/documentado | FALTANTE | Archivos ejecutables p01–p12 |
| OpenClaw/Hermes auxiliares | Archivos stub | ESQ | Adaptadores funcionales |
| Índice de símbolos | Referenciado | FALTANTE | Export Markdown verificable |
| Esquemas por etapa | Parciales/globales | FALTANTE | Contratos input/output por etapa |
| Índice test→assert | No demostrado | FALTANTE | Trazabilidad requisito→test→assert |
| Evidencia CI en observabilidad | Dispersa | PARCIAL | Ingesta en `trace-history` |
| Estado global persistente | Fragmentado | PARCIAL | Máquina durable única |
| GapRegistry persistente | Parcial | PARCIAL | Persistencia y transición probada |
| FourPassController global | Documentos/piezas | PARCIAL | Controlador único ejecutable |
| Recepción y handoff | Parcial | PARCIAL | Auto-load y handoff verificable |
| Cadena DOC→OUTPUT | No cerrada E2E | FALTANTE | DOC→REQ→CODE→TEST→EVIDENCE→OUTPUT_CONSUMED |
| Historial append-only | Ledger parcial | PARCIAL | Garantía y prueba de inmutabilidad |
| Protección post-verify | No cerrada | PARCIAL | Sin bypass y defaults seguros |

## 6. Veredicto de cuatro pasadas

1. **STRUCTURE:** el árbol objetivo está descrito y materializado, pero contiene referencias y placeholders; no prueba implementación completa.
2. **CONNECTIVITY:** hay puntos de conexión reales, pero quedan catálogos desactualizados, rutas fantasma, dual homes y dependencias externas.
3. **BEHAVIOR:** el hot path es real; no existe evidencia suficiente para afirmar que toda la arquitectura nueva impone el comportamiento declarado.
4. **FORENSIC_CLOSURE:** **FAIL-CLOSED / PARCIAL**. Los PASS de descargas, carpetas o GitHub Actions no cierran los GAPS del runtime.

## 7. Regla de evolución

No mover ni reescribir `extensions/wordflow/engine/code_path_runner.py` hasta alcanzar paridad de imports, contratos, tests y evidencia. La ruta segura es **REUSE → COPY con SHA → ADAPT → TEST → CUTOVER**, manteniendo trazabilidad origen→destino.
