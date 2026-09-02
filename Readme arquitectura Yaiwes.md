# Readme arquitectura Yaiwes

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Corte forense:** 2026-09-02  
**Documento relacionado, no fusionado:** [Readme arquitectura Wordflow Code](https://github.com/maxbry123-commits/nct-core/blob/main/Readme%20arquitectura%20wordflow%20code.md)

Este archivo contiene exclusivamente la arquitectura del agente YAIWES, TEAM Kernel, SDPA y sus capas de gobierno. La arquitectura del motor Wordflow Code vive separada en NCT Core.


## Índice navegable

- [1. Fuentes utilizadas](#1-fuentes-utilizadas)
- [2. Ubicación del código fuente del kernel](#2-ubicacion-del-codigo-fuente-del-kernel)
- [3. Arquitectura YAIWES separada](#3-arquitectura-yaiwes-separada)
- [4. Regla de las tres preguntas](#4-regla-de-las-tres-preguntas)
- [5. Responsabilidades de extension-kernel](#5-responsabilidades-de-extension-kernel)
- [6. Selección determinista de workflows](#6-seleccion-determinista-de-workflows)
- [7. Mythos/EURS/DRE](#7-mythoseursdre)
- [8. Método de poda para componentes externos](#8-metodo-de-poda-para-componentes-externos)
- [9. Grok Build: qué corresponde a YAIWES](#9-grok-build-que-corresponde-a-yaiwes)
- [10. Auditoría X-Ray actual](#10-auditoria-x-ray-actual)
- [11. GAPS prioritarios](#11-gaps-prioritarios)
- [12. Huella forense reproducible del árbol real](#12-huella-forense-reproducible-del-arbol-real)
- [13. Método común para reciclar código open source sin copiar otro cerebro](#13-metodo-comun-para-reciclar-codigo-open-source-sin-copiar-otro-cerebro)
- [14. Veredicto](#14-veredicto)

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
| agente-yaiwes | 586 entradas; 234 Python; 123 placeholders |
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

## 12. Huella forense reproducible del árbol real

**Commit de árbol auditado:** `20a030af86129b5d388eef4f10983b385123740e`.

| Raíz comprobada | Archivos | Python | Tests localizados | PLACEHOLDER.md | Lectura forense |
|---|---:|---:|---:|---:|---|
| `agente-yaiwes/` | 430 | 234 | 1 | 123 | Estructura amplia, pero todavía dominada por scaffolding |
| `kernel-principal/` | 71 | 49 | 0 | 18 | Kernel destino parcial; sin suite propia |
| `kernel-principal/extension-kernel/` | 23 | 15 | 0 | 5 | ABI, passport y registry existen parcialmente |
| `kernel-principal/reasoning-kernel/` | 9 | 4 | 0 | 5 | El ciclo cognitivo no está cerrado |
| `input-layer/` | 12 | 3 | 0 | 5 | Reception existe; entrada de producto canónica no |
| `control-governance/` | 80 | 55 | 1 | 22 | Es la zona más materializada del árbol nuevo |
| `multi-workflow-engine/` | 16 | 4 | 0 | 12 | Forma declarada; instancias casi vacías |
| `execution-orchestration/` | 36 | 23 | 0 | 11 | Piezas presentes, E2E no demostrado |
| `execution-engine-pool/` | 26 | 16 | 0 | 7 | Puertos y stubs; adaptadores reales incompletos |
| `observability/` | 10 | 6 | 0 | 2 | Evidencia parcial, no cierre global |
| `extensions/wordflow_kernel/` | 101 | 94 | 27 | 0 | Kernel operativo heredado más verificable |
| `extensions/wordflow/` | 379 | 310 | 134 | 0 | Runtime Wordflow vivo; documentado aparte |

Los conteos son de archivos Git observados, no una afirmación de cobertura funcional. Un archivo Python no equivale a una función terminada y un test localizado no demuestra por sí solo integración E2E.

### Árbol funcional completo de YAIWES

```text
agente-yaiwes/
├── input-layer/                       entrada, recepción y sesiones
├── definition-registry/               contratos de agente/tarea/tool/skill/workflow
├── kernel-principal/                  propietario de política y decisión
│   ├── control-layer/
│   ├── extension-kernel/              registry → passport → ABI → guard
│   ├── reasoning-kernel/              goals → panel → consenso → decisión
│   ├── resource-governance/           broker → lease → retry → breaker
│   ├── internal-bus/
│   ├── kernel-router/
│   ├── execution-manifest/
│   └── stages/
├── control-governance/                sheriff, sentinel, council y forense
├── multi-workflow-engine/             recetas/DAG e instancias aisladas
├── execution-orchestration/           clasificación, planificación y scheduler
├── execution-engine-pool/             adapters, motores y normalización
├── agent-fleet-parallelism/            despacho y supervisión paralela
├── state-events-durability/            checkpoint, recovery y dead letter
├── tools-models-memory-knowledge/      tools, RAG, MCP y memoria
├── codebase-intelligence/              verdad del repositorio y grafo
├── security-auth/                      secretos y permisos
├── observability/                      evidencia, trazas e historial
├── deploy-publish/                     publicación y destinos
└── artifact-output-storage/            salida final
```

### TEAM Kernel: ubicación y diagnóstico

El nombre **TEAM Kernel** describe el conjunto, no un único ejecutable. La cadena verificable está repartida entre:

1. `agente-yaiwes/kernel-principal/`: destino arquitectónico.
2. `agente-yaiwes/control-governance/`: gobierno y verificación.
3. `extensions/wordflow_kernel/`: cuerpo operativo heredado con tests.
4. `extensions/wordflow/`: runtime que ejecuta misiones y produce evidencia.

Por eso la afirmación “TEAM Kernel está completo” no está demostrada. Existen piezas reales, pero falta un entrypoint único que conecte entrada → contrato → decisión → ejecución → evidencia → cierre sin usar stubs o rutas paralelas.

## 13. Método común para reciclar código open source sin copiar otro cerebro

Este método también se aplica a Wordflow Code, pero cada documento conserva su propietario:

1. Fijar repositorio, licencia, versión y commit.
2. Generar fingerprint/SHA y SBOM.
3. Auditar secretos, dependencias y conexiones salientes.
4. Localizar una responsabilidad única.
5. Separar funciones que **deciden** de funciones que **hacen**.
6. Rechazar el bucle decisor externo cuando duplica `reasoning-kernel`.
7. Definir primero el puerto/ABI de YAIWES.
8. Encapsular el código ejecutor con una Anti-Corruption Layer.
9. Ejecutar en sandbox sin red por defecto.
10. Comparar paridad con el origen.
11. Registrar capability passport, permisos, fallos y fallback.
12. Montar mediante `mount-guard`; nunca importar el repositorio externo directamente desde el kernel.
13. Incorporar gradualmente con Strangler Fig y conservar rollback.
14. Enviar estado, trazas y evidencia a observabilidad.

```text
fuente fijada
→ auditoría
→ poda decide/hace
→ puerto YAIWES
→ adaptador
→ sandbox
→ pruebas de paridad
→ passport
→ mount-guard
→ registry
→ workflow o pool
```

Criterio de destino:

- **Capacidad:** resultado estable sin juicio → `extension-kernel/capability-registry/`.
- **Workflow:** secuencia fija de capacidades → `multi-workflow-engine/instances/`.
- **Agente:** conserva juicio o memoria propia → `execution-engine-pool/`, siempre aislado.


## 14. Veredicto

YAIWES/TEAM tiene arquitectura coherente y piezas ejecutables, pero no constituye todavía un agente autónomo completo. El núcleo operativo más confiable sigue siendo `extensions/wordflow_kernel`; `kernel-principal` continúa como destino parcial. Estado: **FAIL-CLOSED / PARCIAL**.
