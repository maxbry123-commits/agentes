# Readme arquitectura Yaiwes

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Corte forense:** 2026-09-02  
**Documento relacionado, no fusionado:** [Readme arquitectura Wordflow Code](https://github.com/maxbry123-commits/nct-core/blob/main/Readme%20arquitectura%20wordflow%20code.md)

Este archivo contiene exclusivamente la arquitectura del agente YAIWES, TEAM Kernel, SDPA y sus capas de gobierno. La arquitectura del motor Wordflow Code vive separada en NCT Core.

## 1. Fuentes utilizadas

### Arquitectura del repositorio

- [PLAN_100 — estructura definitiva](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md)
- [STRUCTURE — árbol materializado](https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/STRUCTURE.md)
- [TEAM Kernel v3](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/03_TEAM_KERNEL_PARTE1.md)
- [Perfil TEAM SEALS](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/06_PERFIL_MAESTRO_TEAM_SEALS.md)
- [Kernel Thought Protocol](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/10_KERNEL_THOUGHT_PROTOCOL.md)
- [Arquitectura Wordflow Kernel](https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/ARQUITECTURA_02_KERNEL.md)
- [Auditoría raíz R5 — TEAM/Kernel](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-RAIZ-R5-YAIWES-TEAM-KERNEL-XRAY-2026-09-01.md)

### Crazy Wall aportados

- [Crazy Wall v2](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v2.html)
- [Crazy Wall v3](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v3.html)
- [Crazy Wall v4](https://github.com/maxbry123-commits/agentes/blob/main/FUENTE-GROK-YAIWES-CRAZY-WALL-v4.html)

### SDPA aportado

- [Arquitectura SDPA](https://github.com/maxbry123-commits/agentes/blob/main/Documentos%20proyectos%20Yaiwes/Documentos%20proyectos%20Yaiwes%201/Arquitectura%20SDPA/SDPA_Architecture_Document.md)
- [Resumen SDPA](https://github.com/maxbry123-commits/agentes/blob/main/Documentos%20proyectos%20Yaiwes/Documentos%20proyectos%20Yaiwes%201/Arquitectura%20SDPA/RESUMEN-PROPUESTA-SDPA.md)

## 2. Ubicación del código fuente del kernel

No existe una sola carpeta ejecutable llamada `Agente TEAM`. El código fuente real está distribuido.

### Kernel de control operativo

- [extensions/wordflow_kernel](https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow_kernel)
- [workflow.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/workflow.py)
- [runtime.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/runtime.py)
- [fail_closed.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/fail_closed.py)
- [preflight.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/preflight.py)
- [instance.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/instance.py)
- [instance_store.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/instance_store.py)
- [ledger.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/ledger.py)
- [checkpoint.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/checkpoint.py)
- [engine_registry.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/engine_registry.py)
- [gateway/intelligence.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/gateway/intelligence.py)
- [gateway/router_http.py](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow_kernel/gateway/router_http.py)

### Nueva estructura del kernel YAIWES

- [agente-yaiwes/kernel-principal](https://github.com/maxbry123-commits/agentes/tree/main/agente-yaiwes/kernel-principal)
- [extension-kernel](https://github.com/maxbry123-commits/agentes/tree/main/agente-yaiwes/kernel-principal/extension-kernel)
- [reasoning-kernel](https://github.com/maxbry123-commits/agentes/tree/main/agente-yaiwes/kernel-principal/reasoning-kernel)
- [resource-governance](https://github.com/maxbry123-commits/agentes/tree/main/agente-yaiwes/kernel-principal/resource-governance)

Los archivos `runtime.py` y `workflow.py` de `kernel-principal` tienen el mismo blob SHA que sus equivalentes en `extensions/wordflow_kernel`. Son un espejo parcial, no un segundo kernel independiente.

## 3. Arquitectura YAIWES separada

```text
main/
└── agente-yaiwes/
    ├── kernel-principal/
    │   ├── extension-kernel/
    │   │   ├── capability-registry/
    │   │   ├── capability-passport/
    │   │   ├── abi-mount/
    │   │   ├── mount-guard/
    │   │   └── native-learning/
    │   ├── reasoning-kernel/
    │   │   ├── decision-on-demand/
    │   │   ├── expert-panel-router/
    │   │   ├── consensus-trigger/
    │   │   ├── goal-dual-driver/
    │   │   └── workflow-capacity/
    │   ├── resource-governance/
    │   │   ├── resource-broker-gate/
    │   │   ├── circuit-breaker/
    │   │   ├── retry-policy/
    │   │   ├── lease-management/
    │   │   └── watchdog/
    │   ├── internal-bus/
    │   ├── kernel-router/
    │   ├── stages/
    │   ├── workflow.py
    │   └── runtime.py
    ├── input-layer/
    │   ├── cli-entry/
    │   ├── route-entry/
    │   ├── reception/
    │   └── cross-tool-session-import/
    ├── definition-registry/
    │   ├── workflow-definition/
    │   ├── task-definition/
    │   ├── tool-definition/
    │   ├── skill-definition/
    │   ├── schema-contracts/
    │   └── authorization-model/
    ├── control-governance/
    │   ├── sheriff-sentinel-council/
    │   ├── forensic-core/
    │   ├── verdict-authority/
    │   ├── llm-control-deny/
    │   └── gap-registry/
    ├── multi-workflow-engine/
    │   ├── shared-services/
    │   └── instances/workflow-N/
    ├── execution-orchestration/
    │   ├── state-machine-executor/
    │   ├── dag-executor/
    │   ├── task-generation/
    │   ├── classifier-scheduler/
    │   └── deterministic-execution/
    ├── execution-engine-pool/
    │   ├── adapter-layer/
    │   ├── capability-matching/
    │   ├── worktree-isolation/
    │   ├── result-normalization/
    │   └── auxiliary-role-agents/
    └── observability/
        └── trace-history/
```

## 4. Regla de las tres preguntas

Para cada pieza nueva:

1. Si ofrece el mismo resultado con el mismo input y no requiere juicio, es una **capacidad** y se registra en `extension-kernel/capability-registry/`.
2. Si es una secuencia fija que combina capacidades, es un **workflow** y vive en `multi-workflow-engine/instances/workflow-N/`.
3. Si razona, mantiene memoria propia o no puede desmontarse sin perder valor, es un **agente de pool** y se conecta mediante `execution-engine-pool/` y `agent-fleet-parallelism/`.

### Ubicación de objetivos y tareas

```text
objetivo primario/secundarios
→ kernel-principal/reasoning-kernel/goal-dual-driver/

entrada cruda
→ input-layer/reception/
→ definition-registry/task-definition/
→ execution-orchestration/task-generation/
```

## 5. Responsabilidades de extension-kernel

| Subraíz | Responsabilidad | Estado detectado |
|---|---|---|
| capability-registry | Catálogo de capacidades | Parcial |
| capability-passport | Fuente, licencia, versión, fingerprint | Parcial |
| abi-mount | Puerto técnico estable | Parcial |
| mount-guard | Licencia, seguridad, ABI y permisos | Principalmente placeholder |
| native-learning | Historial de confianza y fiabilidad | Placeholder |

Regla de aislamiento: el kernel no debe importar directamente un repositorio externo. Importa el puerto de `abi-mount`; el adaptador encapsula el código externo.

## 6. Selección determinista de workflows

```text
input-layer
→ task-definition
→ classifier-scheduler
→ workflow-definition registry
→ match alto: ejecutar sin LLM
→ match ambiguo: expert-panel-router
→ consensus-trigger
→ decision-on-demand
→ workflow elegido o sintetizado
```

La secuencia anterior es el objetivo arquitectónico. La auditoría no encontró una prueba E2E que demuestre que toda la cadena se ejecuta actualmente.

## 7. Mythos/EURS/DRE

Mythos no debe convertirse en un segundo kernel. Debe ser contenido versionado bajo:

```text
reasoning-kernel/
└── decision-on-demand/
    └── prompts/
        ├── mythos_40.md
        ├── eurs_standard.md
        ├── eurs_turbo.md
        └── dre_by_score.md
```

`classifier-scheduler` selecciona LOW/MEDIUM/HIGH/EXTREME. Mythos no decide cuándo ejecutarse a sí mismo.

## 8. Método de poda para componentes externos

Patrones usados:

- Anti-Corruption Layer: evita que el modelo de otro agente contamine YAIWES.
- Ports & Adapters: el kernel consume contratos propios.
- Strangler Fig: permite migración gradual sin reescritura completa.

Proceso:

```text
responsabilidad única
→ separar “decide” de “hace”
→ conservar ejecución
→ descartar cerebro externo redundante
→ definir puerto YAIWES
→ adaptar
→ sandbox
→ tests
→ capability passport
→ mount guard
→ registro
```

## 9. Grok Build: qué corresponde a YAIWES

El repositorio oficial es [xai-org/grok-build](https://github.com/xai-org/grok-build). xAI anunció su apertura el 15 de julio de 2026; el repositorio declara Rust y Apache-2.0.

Fuentes:

- https://x.ai/news/grok-build-open-source
- https://github.com/xai-org/grok-build
- https://github.com/xai-org/grok-build/blob/main/LICENSE
- https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/16-subagents.md
- https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/tutorial/06-worktrees.md

### Piezas aprovechables para el agente

| Pieza Grok Build | Destino YAIWES | Tratamiento |
|---|---|---|
| Subagentes y coordinación | execution-engine-pool + agent-fleet-parallelism | Adaptar contrato; no copiar razonamiento |
| Worktrees aislados | execution-engine-pool/worktree-isolation | Extraer como capacidad |
| Skills | definition-registry/skill-definition | Registrar por passport |
| Hooks y guard de shell | mount-guard + control-governance | Adaptar reglas |
| TUI | control-plane-ui | Opcional |
| Bucle decisor del agente | Ninguno | Descartar: duplicaría reasoning-kernel |

La documentación oficial confirma subagentes paralelos y concurrencia configurable. No se encontró evidencia oficial de que ocho sea el límite fijo de ejecución; el número 8 encontrado en la UI corresponde a elementos visibles antes de colapsarlos.

### Riesgo de seguridad

En julio de 2026 se reportó que una versión de Grok Build enviaba repositorios completos y su historial a almacenamiento de xAI en Google Cloud. El reporte motivó la desactivación del mecanismo automático según cobertura posterior.

Fuentes:

- https://thehackernews.com/2026/07/grok-build-uploads-entire-git.html
- https://www.theverge.com/ai-artificial-intelligence/965600/spacexai-grok-build-repository-upload

Consecuencia arquitectónica:

```text
Grok Build extraído
→ sandbox sin red
→ inspección de egress
→ secret scan
→ filesystem allowlist
→ mount-guard
→ solo entonces capability-registry
```

## 10. Auditoría X-Ray actual

| Evidencia | Resultado |
|---|---|
| agente-yaiwes | 586 entradas; 234 Python; 124 placeholders |
| kernel-principal | 49 Python; 18 placeholders; 0 tests propios |
| wordflow_kernel operativo | 94 Python; 27 tests |
| raíz Agente TEAM | No existe |
| CLI canónica python -m agente | No existe |
| Ask-Consil 12 ejecutable | No localizado |
| OpenClaw/Hermes | Stubs |
| DecisionEngine SDPA único | No localizado |
| Estado Merkle global | No demostrado |
| objetivos goal-dual-driver | Carpeta presente, cuerpo incompleto |
| pool de motores | Puertos parciales; adapters reales pendientes |

## 11. GAPS prioritarios

1. Declarar un manifest único de componentes TEAM.
2. Crear entrada canónica del agente.
3. Cerrar los 18 placeholders de kernel-principal.
4. Implementar goal-dual-driver, decision-on-demand y consensus-trigger reales.
5. Versionar puertos y adaptadores.
6. Hacer obligatorios ledger, checkpoint, trace y mission_id.
7. Sustituir Fake/Stub en pruebas de producción.
8. Implementar fallback determinista e idempotencia.
9. Conectar pool, fleet y worktree isolation.
10. Probar reception→mission→decision→execution→evidence→closure.

## 12. Veredicto

YAIWES/TEAM tiene arquitectura coherente y piezas ejecutables, pero no constituye todavía un agente autónomo completo. El núcleo operativo más confiable sigue siendo `extensions/wordflow_kernel`; `kernel-principal` continúa como destino parcial. Estado: **FAIL-CLOSED / PARCIAL**.
