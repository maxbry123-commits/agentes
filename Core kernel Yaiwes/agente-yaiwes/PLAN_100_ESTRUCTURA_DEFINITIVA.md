# PLAN 100% — Estructura definitiva Agente YAIWES (yaiwes-omega)

**Repo:** maxbry123-commits/agentes · **rama:** `main`  
**Fuente de estructura:** README canónico yaiwes-omega §3  
https://github.com/maxbry123-commits/agentes/blob/a082104e76247c79539b675b129c582bb9b00837/agente-yaiwes/README.md

**Reglas:**
- NO reescribir `extensions/wordflow` operativo (LEGACY hasta cutover autorizado).
- Solo copiar (Git Data API / mismos blob SHA o M1–M5) o crear PLACEHOLDER + descripción + `PENDIENTE_CODE`.
- `code-programming-engine` es pieza única **fuera** de `kernel-principal` / extension-kernel.
- YAML ejecutables solo en `.github/workflows/`. Evidencia/manifiestos en `despliegue/`.

---

## Orden de ejecución (obligatorio)

```text
1. SALIDA 1  → Crear TODOS los archivos/carpetas de la nueva raíz (estructura definitiva completa)
2. SALIDA 5  → DESPLIEGUE 1 (documentos Opción A)  ← inmediatamente después de la raíz
3. SALIDA 2  → Espejo motor → code-programming-engine/
4. SALIDAS 0/3/4/6/7/8 según dependencia (contrato puede ir antes; cierre al final)
```

**Director:** Despliegue 1 va **de primero después** de materializar los archivos de la nueva raíz (no al final del plan).

| Prioridad | Salida | Nombre |
|-----------|--------|--------|
| 1º | **1** | Archivos de la nueva raíz (árbol completo) |
| 2º | **5** | **Despliegue 1** |
| 3º | **2** | Espejo code-programming-engine |
| 4º | 3, 4, 6, 7, 8 | REFs, docs, modular, enganche, cierre |

---

## Árbol definitivo al 100% (sin recortes)

```text
agente-yaiwes/
│
├── code-programming-engine/                 [MIX]  ※ también raíz hermana en main/
│   ├── engine-modules/                      [REAL]
│   ├── code-path-execution/                 [MIX]
│   ├── standards-forensic/                  [REAL]
│   ├── schema-contracts-io/                 [MIX]
│   ├── external-motor-bridge/               [REAL]
│   ├── multi-account-bridge/                [REAL]
│   ├── inbox-normalization/                 [REAL]
│   └── module-tests/                        [REAL]
│
├── kernel-principal/                        [MIX]
│   ├── control-layer/                       [REAL]
│   ├── extension-kernel/
│   │   ├── abi-mount/                       [MIX]
│   │   ├── capability-registry/             [MIX]
│   │   ├── capability-passport/             [ESQ]
│   │   ├── native-learning/                 [ESQ]
│   │   └── mount-guard/                     [ESQ]
│   ├── reasoning-kernel/
│   │   ├── decision-on-demand/              [ESQ]
│   │   ├── expert-panel-router/             [MIX]
│   │   ├── consensus-trigger/               [ESQ]
│   │   ├── goal-dual-driver/                [ESQ]
│   │   └── workflow-capacity/               [ESQ]
│   ├── resource-governance/
│   │   ├── resource-broker-gate/            [MIX]
│   │   ├── lease-management/                [MIX]
│   │   ├── watchdog/                        [MIX]
│   │   ├── circuit-breaker/                 [MIX]
│   │   └── retry-policy/                    [MIX]
│   ├── internal-bus/                        [MIX]
│   └── execution-manifest/                  [ESQ]
│
├── input-layer/                             [MIX]
│   ├── cli-entry/                           [ESQ]
│   ├── route-entry/                         [ESQ]
│   ├── cross-tool-session-import/           [ESQ]
│   └── reception/                           [REAL]
│
├── definition-registry/                     [MIX]
│   ├── workflow-definition/
│   │   ├── yaml-dag/
│   │   ├── step-template/
│   │   └── source-hierarchy/
│   ├── agent-definition/
│   ├── task-definition/
│   ├── tool-definition/
│   ├── skill-definition/
│   ├── schema-contracts/                    [REAL]
│   ├── domain-specific-contracts/           [REAL]
│   ├── declared-dependency-catalog/         [REAL]
│   └── authorization-model/                 [ESQ]
│
├── control-governance/                      [MIX]
│   ├── contracts-base/
│   ├── contracts-C00-C85/
│   ├── sheriff-bridge/
│   ├── sentinel/
│   ├── council/
│   ├── forensic-core/
│   ├── verdict-authority/
│   ├── symbol-index-wiring-graph/
│   ├── workflow-validation/
│   ├── policy-engine/
│   ├── guardrails-validation/
│   ├── structured-output-validation/
│   ├── evaluation-scoring-report/
│   ├── permission-check-engine/
│   ├── refute-repair/
│   ├── llm-control-deny/
│   ├── pre-post-gates/
│   ├── closure-engine/
│   ├── quality-dag/
│   ├── gap_tasks/
│   └── gap_registry/
│
├── multi-workflow-engine/
│   ├── shared-services/
│   │   ├── workflow-registry/
│   │   ├── runner-host/
│   │   ├── dashboard/
│   │   ├── budget/
│   │   └── control-ops/
│   └── instances/
│       ├── workflow-1/
│       │   ├── definition-binding/
│       │   ├── execution-state/
│       │   ├── task-queue/
│       │   ├── engine-pool-binding/
│       │   └── programming-engine-binding/
│       ├── workflow-2/   (misma forma)
│       ├── workflow-3/   (misma forma)
│       └── workflow-N/   (misma forma)
│
├── execution-orchestration/
│   ├── state-machine-executor/
│   ├── dag-executor/
│   ├── sequential-parallel-loop-route/
│   ├── container-pod-isolation/
│   ├── task-generation/
│   ├── deterministic-execution/
│   ├── mission-planning/
│   ├── goal-lock/                           [REF única]
│   ├── task-classifier-scheduler/
│   ├── dependency-injection-context/
│   └── programming-pipeline/                [REF → code-programming-engine]
│
├── agent-fleet-parallelism/
├── execution-engine-pool/
│   ├── adapter-layer/
│   ├── capability-matching/
│   ├── parallel-dispatch/
│   ├── worktree-isolation/
│   ├── result-normalization/
│   └── auxiliary-role-agents/
│
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
│
├── extensions/
│   ├── wordflow-engine-module/              [REF → ../../extensions/wordflow]
│   ├── wordflow-kernel-module/              [REF → ../../extensions/wordflow_kernel]
│   ├── source-evolution-module/
│   ├── project-bootstrap-module/
│   ├── audit-forensic-module/
│   ├── maxbry_loop/
│   ├── github_deploy/
│   ├── github_publisher/
│   ├── adapters/
│   └── knowledge/
│
├── PIPELINE/                                [REF → ../../PIPELINE]
├── agents/                                  [REF → ../../agents]
├── .github-workflows-refs/                  [REF índice; no mueve .github real]
├── ORIGIN_MAP.md
├── COPY_MANIFEST.json
└── PLAN_100_ESTRUCTURA_DEFINITIVA.md        [este archivo]
```

**Raíz hermana en `main/`:** `code-programming-engine/` (misma forma interna; no dentro del kernel).

**Representar en REF (no borrar en main):**  
`.github/workflows`, `PIPELINE`, `agents`, `control-layer`, `docs`, `extensions/*`, `groups`, `memory`, `scripts`, `tools`, `wordflow/`, `despliegue/`, método ZIP, guías.

---

## Nodos obligatorios que no pueden faltar (§4.1)

- capability-passport
- expert-panel-router, goal-dual-driver
- resource-broker-gate, lease-management, watchdog, circuit-breaker, retry-policy
- internal-bus, execution-manifest
- cross-tool-session-import
- declared-dependency-catalog, domain-specific-contracts
- symbol-index-wiring-graph
- human-in-the-loop
- communication-notifications
- control-plane-ui
- dead-letter-handling
- mcp-transport
- artifact-output-storage
- deployment-target-selector
- code-programming-engine como raíz propia
- programming-engine-binding en cada workflow-N

---

## Detalle de cada salida

### SALIDA 0 — Contrato (puede ir junto a Salida 1)
- Lista nodos REAL / MIX / ESQ / REF
- Este PLAN en main (hecho)
- `despliegue/auditoria/migration_plan.yaml` estado PENDING

### SALIDA 1 — Nueva raíz completa (1º)
- Materializar **todas** las carpetas del árbol de arriba.
- Por cada hoja ESQ/MIX sin body: `PLACEHOLDER.md` con descripción del diseño + `PENDIENTE_CODE`.
- Por cada REF: `SOURCE.md` con path canónico en el repo.
- **No** inventar implementación.
- Volumen estimado: ~120–160 archivos de estructura.

### SALIDA 5 — DESPLIEGUE 1 (2º, justo después de Salida 1)
Fuente: `despliegue/` + documentos Opción A (`INSTRUCCIONES_GROK_OPCION_A.md` u equivalente en despliegue).

| Entrega | Acción |
|---------|--------|
| Capability registration | `component_catalog` + `connect_catalog` (idempotente) |
| Pool / instance / registration / metering | Body desde paquete A (copy, no inventar) en `code-programming-engine/` o paths del doc |
| classifier_hook | Según doc A |
| `despliegue/manifests/deployment_01.yaml` | Actualizado |
| `despliegue/auditoria/verification.yaml` | Evidencia PASS/FAIL/GAP |
| `.github/workflows/` | Solo thin entry si el doc lo exige |

Volumen estimado: ~10–20 archivos.

### SALIDA 2 — Espejo motor (3º)
Método: Git Data API (mismos blob SHA) o cp + 1 commit.

| Origen | Destino |
|--------|--------|
| `extensions/wordflow/engine/**` | `code-programming-engine/engine-modules/` |
| `extensions/wordflow/standards/**` | `code-programming-engine/standards-forensic/` |
| `extensions/wordflow/schemas/**` | `code-programming-engine/schema-contracts-io/` |
| tests C-19 | `code-programming-engine/module-tests/` |
| store/catalogs relevantes | `code-programming-engine/store/` + `catalogs/` |

Verify sha origen = destino. Origen **no** se borra.

### SALIDA 3 — REFs a piezas REALES
SOURCE hacia: control-layer, reception, schemas, catalogs, gateway, openclaw/hermes stubs, maxbry_loop, github_deploy, etc.

### SALIDA 4 — Docs mapa
ORIGIN_MAP.md, COPY_MANIFEST.json, READMEs por bloque principal.

### SALIDA 6 — Modular / binding
code-path-execution, programming-engine-binding, refs p01–p12 si existen en rama modular; sin reimplementar monolito.

### SALIDA 7 — Enganche LEGACY
Pocos archivos: catálogos/connect; marker LEGACY en wordflow viejo. No apagar hot path.

### SALIDA 8 — Cierre 100%
Checklist §4.1–4.3 + `despliegue/auditoria/cierre_estructura_100.yaml`.

---

## Volumen total estimado

| Concepto | Cantidad |
|----------|----------|
| Salidas | 9 (2 puede partirse 2a/2b) |
| Archivos estructura + copia + despliegue | ~280–380 |

---

## Criterio de cierre 100%

- [ ] Cero nodos del árbol definitivo faltantes
- [ ] Cero ítems §4.1 faltantes
- [ ] Salida 1 hecha
- [ ] **Despliegue 1** hecho y auditado (verification.yaml)
- [ ] Espejo motor o GAP explícito documentado
- [ ] `extensions/wordflow` LEGACY intacto
- [ ] ESQ = solo PLACEHOLDER + descripción, sin código inventado

---

## Estado al publicar este archivo

| Ítem | Estado |
|------|--------|
| PLAN en main | HECHO (este archivo) |
| Salida 1 (raíz completa) | PENDIENTE |
| Salida 5 (Despliegue 1) | PENDIENTE — **siguiente tras Salida 1** |
| Salida 2 (espejo motor) | PENDIENTE |

**Siguiente orden del Director:** ejecutar **Salida 1**, luego **Salida 5 (Despliegue 1)**.
