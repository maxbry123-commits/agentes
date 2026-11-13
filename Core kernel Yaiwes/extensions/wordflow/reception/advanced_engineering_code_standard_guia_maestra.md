# Advanced Engineering Code Standard
## Guía maestra para código de alto nivel, arquitectura escalable y desarrollo AI-Native

**Versión:** 1.0 consolidada  
**Fecha:** 2026-08-17  
**Idioma:** Español  
**Estado:** Propuesta normativa / base para implementación

---

## 0. Propósito

Este documento consolida y mejora el trabajo realizado en el chat sobre estándares de programación avanzada, arquitectura modular, escalabilidad, auditabilidad, dependencias y desarrollo asistido por IA.

El objetivo no es definir solamente «código limpio». El objetivo es establecer un **sistema de ingeniería** capaz de crecer durante años, ser auditado por humanos y agentes, limitar el acoplamiento, impedir regresiones arquitectónicas y permitir que herramientas como Cursor, GitHub Copilot y otros agentes modifiquen el repositorio bajo políticas verificables.

### Principio rector

> La calidad de un sistema avanzado se mide por su capacidad de evolucionar sin perder corrección, seguridad, trazabilidad, rendimiento, mantenibilidad ni control arquitectónico.

---

# 1. Resultado de las cinco auditorías

Se realizaron cinco pasadas conceptuales sobre el material desarrollado en el chat:

### Auditoría 1 — Cobertura

Se verificó que estuvieran cubiertos:

- calidad de código;
- arquitectura;
- modularidad;
- separación de responsabilidades;
- dependencias;
- escalabilidad;
- pruebas;
- seguridad;
- observabilidad;
- auditoría;
- límite de 300–800 LOC por archivo;
- Cursor;
- GitHub Copilot;
- agentes de programación;
- CI/CD;
- P0/P1/P2.

**Resultado:** cobertura alta, pero faltaban gobierno de agentes, procedencia de cambios, análisis de impacto y reproducibilidad.

### Auditoría 2 — Arquitectura

Se comprobó la dirección de dependencias y separación:

`Domain → Application → Ports → Adapters → Infrastructure`

Se detectó la necesidad de reforzar:

- contratos versionados;
- ausencia de ciclos;
- límites de módulos;
- superficie pública;
- ownership;
- reglas de importación.

### Auditoría 3 — AI-Native Engineering

Se incorporaron conceptos que no deben tratarse como simples «prompts»:

- contexto del repositorio;
- reglas persistentes;
- AGENTS.md;
- instrucciones globales;
- instrucciones por ruta;
- skills;
- niveles de autoridad;
- permisos de herramientas;
- sandbox;
- verificación de código generado;
- procedencia del cambio.

GitHub documenta actualmente el uso combinado de `copilot-instructions.md`, instrucciones específicas por ruta, `AGENTS.md` y skills para personalizar revisiones y agentes. Cursor también utiliza reglas de proyecto y contexto del repositorio para orientar el comportamiento de sus agentes.

### Auditoría 4 — Escalabilidad y auditabilidad

Se añadió:

- Repository Truth;
- Dependency Graph;
- Change Impact Analysis;
- Change Risk Score;
- Architecture Fitness Tests;
- EvidencePacket;
- Ledger;
- checkpoints;
- reproducibilidad;
- versionado de contratos.

### Auditoría 5 — Seguridad y producción

Se comprobó que el estándar debía incluir:

- least privilege;
- separación entre agente y producción;
- secretos fuera del código;
- análisis de dependencias;
- supply-chain security;
- SBOM;
- trazabilidad;
- observabilidad;
- recuperación;
- pruebas de fallos;
- gates de CI.

**Resultado final de auditoría:** el estándar queda definido como un **Advanced Engineering Standard**, no simplemente como una guía de estilo.

---

# 2. Fundamentos externos considerados

El estándar se alinea conceptualmente con prácticas publicadas por organizaciones y herramientas de ingeniería.

Google describe la revisión de código alrededor de diseño, funcionalidad, complejidad y mantenibilidad, además de pruebas y claridad.  
AWS Well-Architected organiza la arquitectura alrededor de excelencia operativa, seguridad, fiabilidad, eficiencia de rendimiento, optimización de costes y sostenibilidad.  
GitHub Copilot incorpora instrucciones a nivel de repositorio, instrucciones específicas por ruta, `AGENTS.md` y skills para orientar revisiones y agentes.  

Fuentes de referencia:

- Google Engineering Practices: https://google.github.io/eng-practices/review/
- AWS Well-Architected: https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html
- GitHub Copilot Code Review: https://docs.github.com/en/copilot/concepts/agents/code-review
- GitHub Copilot custom instructions: https://docs.github.com/en/copilot/tutorials/customize-code-review
- Cursor Agent: https://docs.cursor.com/agent
- Cursor Rules: https://docs.cursor.com/context/rules

Estas fuentes deben volver a comprobarse cuando se conviertan en requisitos de implementación concretos, porque productos y documentación evolucionan.

---

# 3. Definición de código de alto nivel

Un código de nivel avanzado debe cumplir simultáneamente:

1. Correctness.
2. Diseño coherente.
3. Baja complejidad accidental.
4. Modularidad.
5. Bajo acoplamiento.
6. Alta cohesión.
7. Contratos explícitos.
8. Dependencias controladas.
9. Testabilidad.
10. Seguridad.
11. Fiabilidad.
12. Observabilidad.
13. Auditabilidad.
14. Escalabilidad.
15. Reproducibilidad.
16. Evolución controlada.
17. Automatización de calidad.
18. Gobierno de agentes de IA.

No se debe clasificar el nivel únicamente por LOC, número de clases o cantidad de abstracciones.

---

# 4. Regla de archivos: 300–800 LOC

## 4.1 Regla principal

Cada archivo de código debe mantenerse preferentemente entre **300 y 800 líneas de código**.

Esta regla limita el tamaño **por archivo**, no el tamaño total del proyecto.

Por tanto:

- 10.000 LOC de proyecto: permitido.
- 100.000 LOC: permitido.
- 1.000.000 LOC: permitido.
- Archivo de 700 LOC: permitido.
- Archivo de 1.200 LOC: requiere revisión.

## 4.2 Política

| Tamaño | Política |
|---|---|
| <300 | permitido si representa una unidad completa |
| 300–650 | rango preferido |
| 651–800 | permitido |
| >800 | revisión arquitectónica |
| >1.000 | candidato obligatorio a refactor |
| >1.500 | excepción crítica |

No se deben añadir líneas artificialmente para alcanzar 300.

## 4.3 Excepción

Una excepción debe registrar:

- motivo;
- responsable;
- fecha;
- riesgo;
- plan de división;
- fecha objetivo de revisión.

---

# 5. El proyecto total NO tiene límite de LOC

La regla correcta es:

`FILE_LOC_LIMIT != PROJECT_LOC_LIMIT`

El proyecto escala mediante:

- nuevos módulos;
- nuevos componentes;
- nuevos adapters;
- nuevos ports;
- nuevos servicios;
- nuevos workers;
- nuevos dominios.

Nunca mediante megaarchivos.

---

# 6. Métricas adicionales al LOC

LOC nunca debe ser la única métrica.

Controlar:

- cyclomatic complexity;
- cognitive complexity;
- nesting depth;
- function length;
- public API surface;
- direct dependencies;
- dependency depth;
- coupling;
- cohesion;
- test coverage;
- mutation score;
- build time;
- latency;
- error rate;
- security findings;
- architecture violations.

Un archivo de 400 LOC puede ser peor que uno de 900 si contiene complejidad o acoplamiento excesivo.

---

# 7. Principio de responsabilidad

Cada módulo debe tener una responsabilidad principal y un límite claro.

Evitar:

`mega_engine.py`

que combine:

- base de datos;
- HTTP;
- GitHub;
- autenticación;
- planificación;
- IA;
- filesystem;
- validación;
- ejecución;
- logging.

Preferir módulos independientes.

---

# 8. Arquitectura recomendada

```text
src/
├── kernel/
│   ├── contracts/
│   ├── domain/
│   ├── policies/
│   └── state/
│
├── orchestration/
│   ├── planning/
│   ├── routing/
│   ├── scheduling/
│   └── execution/
│
├── capabilities/
│   ├── registry/
│   ├── compiler/
│   ├── loader/
│   └── runtime/
│
├── ports/
│   ├── model/
│   ├── storage/
│   ├── repository/
│   ├── search/
│   ├── execution/
│   └── network/
│
├── adapters/
│   ├── github/
│   ├── huggingface/
│   ├── llm/
│   ├── ssh/
│   ├── mcp/
│   └── http/
│
├── runtime/
│   ├── sandbox/
│   ├── workers/
│   ├── queues/
│   └── processes/
│
├── audit/
│   ├── ledger/
│   ├── evidence/
│   ├── trace/
│   └── validation/
│
├── security/
│   ├── credentials/
│   ├── permissions/
│   └── policies/
│
└── tests/
    ├── unit/
    ├── integration/
    ├── contract/
    └── architecture/
```

---

# 9. Regla de dirección de dependencias

Modelo:

```text
Domain
   ↑
Application
   ↑
Ports
   ↑
Adapters
   ↑
Infrastructure
```

La implementación externa depende de contratos internos.

El dominio no debe conocer:

- GitHub SDK;
- HTTP;
- base de datos;
- CLI;
- filesystem específico;
- proveedor de LLM.

Ejemplo correcto:

```text
MissionService
      ↓
GitRepositoryPort
      ↑
GitHubAdapter
      ↓
GitHub API
```

---

# 10. Ports y Adapters

Todo sistema externo importante debe pasar por una frontera.

Ejemplos:

- `ModelPort`
- `RepositoryPort`
- `StoragePort`
- `SearchPort`
- `ExecutionPort`
- `NetworkPort`

Adapters:

- `OpenAIAdapter`
- `HFAdapter`
- `GitHubAdapter`
- `SSHAdapter`
- `MCPAdapter`
- `HTTPAdapter`

Esto permite cambiar proveedores sin modificar el núcleo.

---

# 11. Dependencias: reglas obligatorias

Cada módulo debe declarar:

```yaml
module:
  allowed_dependencies:
  forbidden_dependencies:
  direct_dependencies:
  external_dependencies:
```

Reglas:

1. Cero dependencias circulares.
2. No imports prohibidos.
3. Dependencias externas justificadas.
4. Versiones fijadas.
5. Dependencias transitivas auditadas.
6. Sin dependencias innecesarias.
7. Ninguna dependencia debe introducirse solo por conveniencia.

---

# 12. Dependency Budget

Como política inicial:

```yaml
dependency_policy:
  max_direct_dependencies: 12
  circular_dependencies: 0
  forbidden_imports: strict
  dependency_review: required
```

El número 12 es un presupuesto inicial, no una ley universal. Debe ajustarse al dominio.

---

# 13. Ficha de dependencia

Cada dependencia importante debería poder describirse:

```yaml
dependency:
  name:
  version:
  purpose:
  owner:
  license:
  security_status:
  runtime_required:
  build_required:
  direct_or_transitive:
  replacement_strategy:
  failure_behavior:
  upgrade_policy:
  removal_plan:
```

---

# 14. Contratos

Cada frontera debe declarar:

- input;
- output;
- errores;
- versión;
- estado;
- timeout;
- retry;
- idempotencia;
- requisitos de seguridad.

Ejemplo:

```yaml
contract:
  name: ExecutionPort
  version: 1

  input:
    task_id: string
    command: string
    workspace: path

  output:
    status: enum
    result: object
    evidence: object

  errors:
    - TIMEOUT
    - PERMISSION_DENIED
    - EXECUTION_FAILED
    - RESOURCE_UNAVAILABLE
```

---

# 15. Evolución de contratos

No romper contratos silenciosamente.

Migración:

```text
v1
 ↓
v2
 ↓
compatibility layer
 ↓
migration
 ↓
deprecation
 ↓
removal
```

Antes de eliminar v1:

- encontrar consumidores;
- ejecutar tests;
- verificar contratos;
- migrar;
- observar;
- eliminar.

---

# 16. Public API mínima

Cada módulo debe exponer una superficie pública pequeña.

```text
PUBLIC:
  MissionService
  Mission
  MissionResult
  MissionPort
```

Interno:

```text
_internal_state
_helpers
_cache
_transport
_implementation
```

Regla:

`PUBLIC API << INTERNAL IMPLEMENTATION`

Una API pública pequeña reduce la superficie de ruptura.

---

# 17. Estado

Separar:

- estado;
- lógica;
- I/O.

Componentes recomendados:

- `StateStore`;
- `MissionState`;
- `TaskState`;
- `Checkpoint`;
- `Ledger`.

Esto permite:

- checkpoint;
- rollback;
- recovery;
- replay;
- audit.

---

# 18. Control plane vs execution plane

Para sistemas complejos:

```text
CONTROL PLANE
├── Mission
├── Planning
├── Policy
├── Routing
├── Scheduling
├── State
└── Audit

EXECUTION PLANE
├── Workers
├── Sandbox
├── Models
├── Tools
├── Git
├── HF
├── SSH
├── HTTP
└── MCP
```

El control plane decide **qué, por qué y bajo qué reglas**.

El execution plane ejecuta **cómo**.

---

# 19. AI-Native Engineering

Con agentes de programación, el código ya no es producido únicamente por humanos.

Por tanto:

```text
Generate
 ↓
Inspect
 ↓
Plan
 ↓
Edit
 ↓
Test
 ↓
Verify
 ↓
Review
 ↓
Evidence
 ↓
Merge
```

Nunca:

```text
Generate
 ↓
Merge
```

La generación no es evidencia de corrección.

---

# 20. Repository Truth

Debe existir una fuente estructurada de verdad del repositorio:

```yaml
repository_truth:
  version: 1

modules:
  - id:
    path:
    owner:
    responsibility:
    stability:
    public_api:
    dependencies:
```

Debe poder responder:

- qué existe;
- dónde está;
- qué hace;
- quién depende;
- qué contrato tiene;
- qué versión;
- qué estado;
- qué riesgos.

---

# 21. Architecture Constitution

Crear:

`ARCHITECTURE_CONSTITUTION.md`

Debe contener:

1. Misión.
2. Principios.
3. Límites de módulos.
4. Dependencias permitidas.
5. Dependencias prohibidas.
6. Contratos.
7. Política de estado.
8. Seguridad.
9. Tests.
10. Observabilidad.
11. Auditoría.
12. Reglas de agentes.
13. CI gates.
14. Migraciones.

Debe ser normativa, no solo descriptiva.

---

# 22. Instrucciones para agentes

Estructura recomendada:

```text
AGENTS.md

.github/
├── copilot-instructions.md
├── instructions/
│   ├── backend.instructions.md
│   ├── security.instructions.md
│   └── tests.instructions.md
└── skills/

.cursor/
└── rules/
```

GitHub documenta que estas capas tienen propósitos distintos:

- `copilot-instructions.md`: reglas generales del repositorio;
- `*.instructions.md`: reglas específicas por ruta;
- `AGENTS.md`: reglas permanentes compartidas entre agentes;
- skills: workflows específicos.

No duplicar reglas sin necesidad.

---

# 23. Context Engineering

El agente debe recibir contexto suficiente y relevante.

Dimensiones:

```text
CQ1 Repository Map
CQ2 Architecture Rules
CQ3 Domain Context
CQ4 Relevant Files
CQ5 Contracts
CQ6 Tests
CQ7 Dependency Graph
CQ8 Historical Decisions
```

`Context Quality != prompt length`.

El objetivo es contexto relevante, verificable y mínimo.

---

# 24. Agent Authority Levels

Definir autoridad por niveles:

```text
L0 READ
L1 PROPOSE
L2 EDIT
L3 EXECUTE
L4 AUTONOMOUS
L5 DEPLOY
```

Ejemplo:

```yaml
agent:
  authority: L3

  permissions:
    read: true
    write: true
    execute: true
    network: false
    credentials: false
    deploy: false
```

No conceder L5 por defecto.

---

# 25. Tool Permissions

Separar:

- READ;
- WRITE;
- EXECUTE;
- NETWORK;
- CREDENTIAL;
- DEPLOY.

Esto permite least privilege para agentes.

---

# 26. Agent Sandbox

Regla:

`AGENT_EXECUTION != PRODUCTION_EXECUTION`

Flujo:

```text
Agent
 ↓
Sandbox
 ↓
Workspace
 ↓
Tests
 ↓
Evidence
 ↓
Review
 ↓
Merge
 ↓
Deployment
```

Los agentes autónomos deben trabajar en entornos controlados.

---

# 27. Agent Policy

```yaml
agent_policy:
  identity:
  role:
  authority_level:

  allowed_paths:
  denied_paths:

  allowed_tools:
  denied_tools:

  allowed_commands:
  denied_commands:

  allowed_networks:
  denied_networks:

  max_files_changed:
  max_lines_changed:

  required_tests:
  required_reviews:

  can_modify_dependencies: false
  can_modify_security: false
  can_deploy: false
```

---

# 28. Change Impact Analysis

Antes de cambiar código:

```text
Change Request
 ↓
Dependency Graph
 ↓
Consumer Discovery
 ↓
Contract Analysis
 ↓
State Impact
 ↓
Security Impact
 ↓
Performance Impact
 ↓
Test Impact
 ↓
Change Plan
```

La pregunta clave:

> Si cambio X, ¿qué componentes pueden romperse?

---

# 29. Change Risk Score

Modelo:

```text
CHANGE_RISK =
  dependency_impact
+ contract_impact
+ state_impact
+ security_impact
+ runtime_impact
+ data_impact
+ deployment_impact
```

Escala:

| Score | Riesgo | Política |
|---:|---|---|
| 0–20 | Low | verificación automática |
| 21–40 | Moderate | tests + revisión |
| 41–60 | High | arquitectura + revisión |
| 61–80 | Critical | autorización explícita |
| 81–100 | Extreme | plan + aprobación + rollout controlado |

---

# 30. Cambios pequeños

Preferir:

- una intención por cambio;
- diffs revisables;
- refactors separados;
- tests incluidos;
- evidencia.

Evitar combinar en un mismo cambio:

`FEATURE + MASSIVE REFACTOR`

salvo necesidad explícita.

Para workflows internos que impongan límites adicionales, puede utilizarse un límite de diff/commit inferior al límite de archivo.

---

# 31. AI Provenance

Para cambios realizados por agentes:

```yaml
change_provenance:
  change_id:
  agent_id:
  model:
  model_version:
  instructions_version:
  repository_revision:
  files_changed:
  commands_executed:
  tests_executed:
  validation_result:
  reviewer:
```

No significa almacenar secretos ni prompts sensibles. Significa poder reconstruir qué sistema produjo el cambio.

---

# 32. EvidencePacket

Una afirmación de completitud debe tener evidencia.

Formato mínimo:

```yaml
evidence:
  mission_id:
  task_id:
  change_id:
  repository_revision:
  paths:
  blob_shas:
  tests:
  ci:
  docs:
  validation:
  status:
```

Una afirmación `COMPLETED` no debe basarse solamente en la palabra del agente.

---

# 33. Ledger y Checkpoint

Para tareas largas:

```text
Mission
 ↓
Task
 ↓
Checkpoint
 ↓
Execution
 ↓
Evidence
 ↓
Validation
 ↓
Checkpoint
```

El ledger debe ser:

- append-only;
- identificable;
- correlacionable;
- recuperable.

Permite rollback y reconstrucción.

---

# 34. Arquitectura Fitness Tests

Las reglas arquitectónicas deben convertirse en pruebas.

Ejemplos:

```text
domain_must_not_import_infrastructure
no_circular_dependencies
max_file_loc <= 800
no_secrets_in_source
public_api_requires_contract
ports_have_adapters
forbidden_imports == 0
```

La arquitectura debe ser **machine-enforced**, no una recomendación humana.

---

# 35. Quality Gates

Pipeline recomendado:

```text
FORMAT
 ↓
LINT
 ↓
TYPE CHECK
 ↓
STATIC ANALYSIS
 ↓
UNIT TEST
 ↓
INTEGRATION TEST
 ↓
CONTRACT TEST
 ↓
SECURITY SCAN
 ↓
DEPENDENCY SCAN
 ↓
ARCHITECTURE TEST
 ↓
BUILD
 ↓
AUDIT
 ↓
PASS
```

Los fallos críticos deben producir:

`FAIL CLOSED`

---

# 36. Testing avanzado

Niveles:

```text
L0 Static Analysis
L1 Unit
L2 Contract
L3 Integration
L4 Component
L5 End-to-End
L6 Failure
L7 Performance
L8 Security
L9 Architecture
```

Para sistemas AI-native añadir:

- evaluation tests;
- regression prompts;
- tool-use tests;
- agent policy tests;
- context tests.

---

# 37. Seguridad

Mínimos:

- secrets fuera del código;
- least privilege;
- autenticación;
- autorización;
- validación de entrada;
- cifrado cuando corresponda;
- dependency scanning;
- secret scanning;
- SBOM;
- gestión de credenciales;
- auditoría;
- threat modeling;
- pruebas de seguridad.

---

# 38. Supply Chain

Registrar:

```text
Direct dependency
Transitive dependency
Runtime dependency
Build dependency
Optional dependency
Dev dependency
```

Y evaluar:

- licencia;
- vulnerabilidades;
- versión;
- procedencia;
- integridad;
- mantenimiento.

---

# 39. Reproducibilidad

Para reconstruir una versión:

```text
SOURCE VERSION
+
DEPENDENCY LOCK
+
BUILD ENVIRONMENT
+
CONFIGURATION
+
TOOL VERSION
+
MODEL VERSION
```

Para AI-native engineering añadir:

```text
MODEL
MODEL_VERSION
RULE_VERSION
SKILL_VERSION
TOOL_VERSION
```

---

# 40. Observabilidad

No limitarse a logs.

Usar:

```text
Logs
Metrics
Traces
Events
Evidence
Audit Ledger
```

Correlacionar:

```text
mission_id
task_id
operation_id
trace_id
workspace_id
```

---

# 41. Auditoría

Un log:

`Started task 42`

no es evidencia suficiente.

Una operación crítica debe poder reconstruirse:

```text
Input
 ↓
Decision
 ↓
Execution
 ↓
Output
 ↓
Evidence
 ↓
Validation
 ↓
Result
```

---

# 42. Reliability

Cada operación importante debería definir:

- timeout;
- retry;
- backoff;
- idempotency;
- recovery;
- circuit breaker cuando corresponda;
- límites;
- comportamiento ante fallo.

Nunca hacer retries ciegos.

---

# 43. Performance

Medir antes de optimizar.

Registrar:

- latency;
- throughput;
- memory;
- CPU;
- I/O;
- network;
- concurrency;
- queue time;
- token usage cuando haya IA.

No introducir optimizaciones que aumenten complejidad sin evidencia.

---

# 44. Cost Engineering

Para sistemas con APIs y modelos:

```text
cost/request
cost/task
cost/mission
tokens/input
tokens/output
tool_calls
compute_time
storage
network
```

El router puede decidir entre:

- motor determinista;
- modelo barato;
- modelo potente;
- procesamiento local;
- procesamiento paralelo.

La regla:

> No utilizar un LLM cuando un motor determinista puede resolver correctamente la operación.

---

# 45. Deterministic-first

Para sistemas de agentes:

```text
Task
 ↓
Can deterministic engine solve?
 ├── YES → deterministic execution
 └── NO
       ↓
     LLM/Agent
```

Esto reduce:

- coste;
- latencia;
- variabilidad;
- alucinaciones.

---

# 46. Multi-engine

Para múltiples modelos/proveedores:

```text
Router
 ↓
ModelPort
 ├── Provider A
 ├── Provider B
 ├── Provider C
 ├── Local
 └── Custom
```

El core no debe estar acoplado a un proveedor.

---

# 47. Capabilities

Las capacidades deben ser objetos registrables.

```text
Capability
├── identity
├── version
├── input_schema
├── output_schema
├── permissions
├── dependencies
├── execution_mode
├── evidence_policy
└── adapter
```

Para arquitecturas complejas, Skills, Datasets y Adapters pueden registrarse mediante un runtime de recursos/knowledge separado del microkernel.

---

# 48. Separación Kernel / Runtime

Principio:

```text
MICROKERNEL
├── contracts
├── policies
├── state
└── orchestration primitives

RESOURCE / KNOWLEDGE RUNTIME
├── skills
├── datasets
├── adapters
├── packages
├── versions
└── evidence
```

El kernel no debe cargar toda la complejidad externa permanentemente.

---

# 49. Regla de evolución

Agregar capacidad debe preferir:

```text
NEW MODULE
NEW ADAPTER
NEW PORT
NEW CAPABILITY
```

antes que:

```text
MODIFICAR CORE
```

El core debe crecer lentamente.

---

# 50. Clasificación de ingeniería

Propuesta:

| Nivel | Características |
|---|---|
| Basic | funciona |
| Clean | legible y organizado |
| Professional | modular + tests + CI |
| Senior | contratos + dependencias + seguridad |
| Advanced | arquitectura + observabilidad + escalabilidad |
| Principal/Staff | gobierno arquitectónico + evolución + sistemas |
| Elite Production | automatización, auditoría, resiliencia, supply chain |
| Research/Exceptional | reproducibilidad, agentes, evaluación, sistemas complejos |

---

# 51. Score de 1000 puntos

| Área | Puntos |
|---|---:|
| Architecture | 150 |
| Correctness | 120 |
| Testing | 120 |
| Security | 120 |
| Maintainability | 100 |
| Reliability | 100 |
| Scalability | 80 |
| Performance | 70 |
| Observability | 60 |
| Dependency Management | 50 |
| AI/Agent Governance | 30 |
| Documentation/DX | 30 |
| **TOTAL** | **1000** |

Clasificación:

```text
0–399      Bajo
400–549    Profesional
550–699    Senior
700–799    Advanced
800–899    Principal / Staff
900–949    Elite Production
950–1000   Exceptional / Research Grade
```

---

# 52. P0 / P1 / P2

## P0 — bloqueo

- vulnerabilidad crítica;
- filtración de credenciales;
- corrupción de datos;
- ruptura de contrato;
- dependencia circular;
- operación destructiva no autorizada;
- cambio que rompe producción.

## P1 — obligatorio

- alto acoplamiento;
- falta de tests críticos;
- violation arquitectónica;
- dependencia no controlada;
- error handling deficiente;
- observabilidad insuficiente.

## P2 — mejora

- naming;
- documentación;
- refactor menor;
- DX;
- optimización no crítica.

---

# 53. Arquitectura de alto nivel

```text
                    HUMAN ENGINEER
                           |
                    ENGINEERING POLICY
                           |
                 AI AGENT / IDE
                 / Cursor / Copilot
                           |
                   REPOSITORY TRUTH
                           |
                    ARCHITECTURE
                           |
          CODE + CONTRACTS + DEPENDENCIES
                           |
        TESTS + SECURITY + ARCHITECTURE CHECKS
                           |
                  AUTOMATED VERIFICATION
                           |
                     HUMAN REVIEW
                           |
                       MERGE
                           |
                     DEPLOYMENT
                           |
                    OBSERVABILITY
                           |
                     FEEDBACK LOOP
                           |
                     IMPROVEMENT
```

---

# 54. Checklist de archivo

- [ ] Responsabilidad única clara.
- [ ] 300–800 LOC o excepción documentada.
- [ ] Dependencias declaradas.
- [ ] Sin imports prohibidos.
- [ ] Sin dependencia circular.
- [ ] API pública mínima.
- [ ] Contratos claros.
- [ ] Errores definidos.
- [ ] Tests disponibles.
- [ ] Logs apropiados.
- [ ] Seguridad revisada.
- [ ] Sin secretos.
- [ ] Documentación necesaria.
- [ ] Complejidad aceptable.

---

# 55. Checklist de módulo

- [ ] Boundary definido.
- [ ] Owner definido.
- [ ] API pública definida.
- [ ] Dependencias permitidas.
- [ ] Dependencias prohibidas.
- [ ] Ports definidos.
- [ ] Adapters separados.
- [ ] Estado aislado.
- [ ] Tests.
- [ ] Contract tests.
- [ ] Architecture tests.
- [ ] Observabilidad.
- [ ] Recovery.
- [ ] Versionado.

---

# 56. Checklist de cambio

- [ ] Objetivo definido.
- [ ] Tipo de cambio clasificado.
- [ ] Dependencias analizadas.
- [ ] Consumidores identificados.
- [ ] Impacto calculado.
- [ ] Riesgo calculado.
- [ ] Plan creado.
- [ ] Diff revisable.
- [ ] Tests ejecutados.
- [ ] Seguridad comprobada.
- [ ] Arquitectura comprobada.
- [ ] EvidencePacket generado.
- [ ] Revisión completada.
- [ ] CI verde.

---

# 57. Checklist de agente

- [ ] Identidad definida.
- [ ] Rol definido.
- [ ] Authority level definido.
- [ ] Paths permitidos.
- [ ] Paths prohibidos.
- [ ] Tools permitidas.
- [ ] Commands permitidos.
- [ ] Network definida.
- [ ] Credentials prohibidas por defecto.
- [ ] Sandbox activo.
- [ ] Límites de cambios.
- [ ] Tests obligatorios.
- [ ] Evidencia obligatoria.
- [ ] Deploy bloqueado salvo autorización.

---

# 58. Estándar final obligatorio

```text
RULE-001  FILE_LOC <= 800
RULE-002  PROJECT_LOC unlimited
RULE-003  NO circular dependencies
RULE-004  NO forbidden imports
RULE-005  Domain isolated from infrastructure
RULE-006  External systems through ports/adapters
RULE-007  Public contracts versioned
RULE-008  Critical operations produce evidence
RULE-009  Critical changes require verification
RULE-010  Architecture rules machine-enforced
RULE-011  Agents operate under explicit authority
RULE-012  Production access is not default
RULE-013  Secrets never enter source
RULE-014  Dependencies are auditable
RULE-015  Changes require impact analysis
RULE-016  AI output is never proof of correctness
RULE-017  Deterministic execution preferred where correct
RULE-018  Project scales through modules, not mega-files
RULE-019  State and side effects have explicit ownership
RULE-020  CI fails closed on critical violations
```

---

# 59. Principio final

El objetivo no es construir «mucho código».

El objetivo es construir:

```text
SMALL BOUNDED COMPONENTS
+
STRONG CONTRACTS
+
CONTROLLED DEPENDENCIES
+
AUTOMATED VERIFICATION
+
EXPLICIT AGENT AUTHORITY
+
AUDITABLE EVIDENCE
+
REPRODUCIBLE BUILDS
+
SAFE EVOLUTION
```

Eso permite que una arquitectura de 10.000, 100.000 o millones de líneas continúe siendo gobernable.

La regla de 300–800 LOC funciona entonces como una **restricción local de diseño**, mientras que la arquitectura completa escala mediante composición.

---

# 60. Referencias

1. Google Engineering Practices — Code Review  
   https://google.github.io/eng-practices/review/

2. AWS Well-Architected Framework — Pillars  
   https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html

3. GitHub Copilot — Code Review and Custom Instructions  
   https://docs.github.com/en/copilot/concepts/agents/code-review

4. GitHub Copilot — Customize Code Review  
   https://docs.github.com/en/copilot/tutorials/customize-code-review

5. Cursor — Agent  
   https://docs.cursor.com/agent

6. Cursor — Rules / Context  
   https://docs.cursor.com/context/rules

---

# 61. Estado de la guía

Esta versión debe considerarse una **especificación base de ingeniería**.

Para convertirla en un estándar ejecutable de un repositorio, las reglas deben implementarse como:

- linters;
- type checks;
- dependency graph checks;
- architecture fitness tests;
- LOC gates;
- security scanners;
- dependency scanners;
- contract tests;
- CI gates;
- agent policies;
- EvidencePacket;
- audit ledger.

La meta final es:

`POLICY → AUTOMATION → EVIDENCE → REVIEW → SAFE EVOLUTION`

y no simplemente:

`POLICY → DOCUMENTO`.

