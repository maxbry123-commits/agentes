# SKILL VIVO — Orquestación, adquisición, integración y verificación YAIWES

**Estado:** vivo / acumulativo / fail-closed  
**Arquitectura canónica:** `Readme arquitectura Yaiwes/README.md`  
**Crazy Wall:** `Readme arquitectura Yaiwes/Crazy Wall Orquestador/HOJA-DE-RUTA-MAESTRA.md`  
**Principio:** `REUSE > PATCH > ADAPT > GENERATE`  
**Calidad mínima:** producción/SaaS/ingeniería de software de alto nivel. **MVP prohibido** salvo autorización literal del Director.  
**Velocidad:** resolver bien y rápido, con paralelismo útil y cero sobreingeniería.

---

# 1. OBJETIVO GENERAL PRINCIPAL 🎯

Convertir cada lote documental recibido en cualquier proyecto en requisitos verificables, arquitectura trazable, gaps concretos y código real integrado sin reescribir desde cero.

Patrón de entrada:

```text
main/
  Documentos proyectos <NOMBRE_PROYECTO>/
    lote-01/
    lote-02/
    ...
```

Cadena objetivo:

```text
DOCUMENTO
→ REQUISITO
→ CAPACIDAD
→ ¿EXISTE?
→ ¿ESTÁ CABLEADA?
→ ¿TIENE CONTRATO/SCHEMA?
→ ¿TIENE TEST?
→ ¿HAY EVIDENCIA?
→ GAP REAL
→ REUSE | MOVE | PATCH | ADAPT | GENERATE | REJECT
```

Un documento, nombre de archivo o claim de otro agente nunca demuestra por sí solo que una función esté terminada.

---

# 2. FUENTE DE VERDAD

Orden de autoridad:

1. código ejecutable + tests reproducibles + evidencia;
2. arquitectura canónica del repo;
3. instrucciones literales del Director;
4. contratos, schemas, DAG y anexos de trabajo aprobados;
5. documentos del proyecto/Claude como requisitos y gaps;
6. investigación externa como candidatos, nunca PASS automático.

Estados X-Ray:

`REAL | PARCIAL | ESQ | FALTANTE | DECLARADO_NO_VERIFICADO | VERIFIED_CLOSED`

`UNKNOWN` o evidencia insuficiente = FAIL CLOSED.

---

# 3. AUDITORÍA DOCUMENTAL — 4 ESCANEOS

Cada documento de `Documentos proyectos <repo>/` se procesa 4 veces:

## Escaneo 1 — literal
Extraer requisitos, funciones, inputs, outputs, restricciones y definition of done. Clasificar `FACT / EVIDENCE / INFERENCE / UNKNOWN`.

## Escaneo 2 — arquitectura
Mapear cada requisito a componente/ruta; detectar contradicciones, duplicados, monolitos y ubicación incorrecta.

## Escaneo 3 — código
Localizar archivos, símbolos, imports, wiring, registries, contratos y tests. Distinguir `REAL/PARCIAL/ESQ/FALTANTE`.

## Escaneo 4 — verificación cruzada
Cruzar documento ↔ arquitectura ↔ código ↔ contrato ↔ test ↔ evidencia y producir GAP + siguiente acción.

Checklist:

```text
[ ] requisito identificado
[ ] ubicación arquitectónica
[ ] código localizado o falta demostrada
[ ] wiring localizado
[ ] contrato/schema localizado
[ ] test localizado/ejecutado
[ ] evidencia reproducible
[ ] contradicciones registradas
[ ] GAP exacto
[ ] siguiente acción y responsable
```

---

# 4. DE DÓNDE SALE EL CÓDIGO

## A. Código ya existente en el mismo repo
Primera opción. Revisar antes de generar o descargar.

## B. Biblioteca interna Maxbry
Buscar en todos los repositorios accesibles de Maxbry, con prioridad a `Agentes-motores-Wordflow-YAIWES` y su biblioteca de agentes/software/componentes.

## C. Código subido por el Director
Puede llegar a una raíz `download code <NOMBRE_REPO>/`. Se estudia y se mueve total/parcialmente solo a destino arquitectónico aprobado.

## D. OSS / GitHub / otras fuentes verificables
Director, Sol u otro chat puede proponer. Sol valida URL oficial, licencia, versión/tag/SHA, mantenimiento, módulos útiles, dependencias, seguridad y tests.

Flujo:

`PROPUESTA → VERIFICAR ORIGEN → GITHUB ACTION → SHA/ÁRBOL → X-RAY → CLASIFICAR → DESTINO`.

## E. Codex
`GENERATE` es último recurso: solo cuando la capacidad no existe o queda un delta real que debe escribirse.

---

# 5. CORE KERNEL — INCORPORACIÓN

Una raíz `core kernel <NOMBRE_PROYECTO>/` contiene código candidato a ser parte fundamental del kernel, no solo otra capa Wordflow.

Si un componente trae kernel/core/loop propio:

1. estudiar capacidad real;
2. separar infraestructura útil de su cerebro/loop;
3. detectar incompatibilidad con el kernel rector;
4. presentar al Director:
   - `PODAR_Y_REUSAR_CAPACIDADES`;
   - `CONVERTIR_EN_AGENTE_HIJO`;
   - `ADAPTAR_COMO_PLUGIN`;
   - `RECHAZAR`.

Nunca fusionar kernels completos a ciegas. Nunca crear monolito.

El crecimiento es modular, reemplazable y editable mediante piezas pequeñas + contratos + adapters + registry/plugins.

---

# 6. ENCHUFE UNIVERSAL / FICHA / REGISTRY

Fuentes reales localizadas en `Readme arquitectura Yaiwes/`:

- `🔌 enchufe universal parte 1 fusion fables Kimi k 3 universal_plugin_bus_v2_integrated.py`
- `🔌✅ enchufe universal parte 2 fusión de Kimi k 3 y fables ficha_contract_v2.py`
- documento JSON/DSL del enchufe universal.

Piezas localizadas en fuente:

- `ContractGenerator.generate()`;
- `AdapterFactory.create()`;
- `PluginRegistry` con slots;
- `UniversalPluginBus.enchufar()`;
- `HotSwapManager.shadow_load()`;
- `run_shadow_tests()`;
- `atomic_swap()`;
- evidencia, health, failover, telemetría y budget governor.

Estado: `SOURCE_REAL_EN_ANEXO / PENDIENTE_DE_INTEGRACIÓN_PRODUCTIVA`.

Flujo:

```text
COMPONENTE
→ X-RAY
→ FICHA
→ VALIDAR FICHA
→ CONTRACT
→ PASSTHROUGH O ADAPTER
→ SHADOW LOAD
→ SHADOW TESTS
→ SLOT NUEVO
→ ENCHUFAR
→ TEST INTEGRACIÓN
→ EVIDENCE
→ ACTIVAR/SWAP
```

Preferir adapter a reescritura del código original.

---

# 7. FICHA DE COMPONENTE

```yaml
component_id:
source_repo:
source_url:
source_sha:
license:
source_path:
capability:
xray: REAL|PARCIAL|ESQ|FALTANTE
integration: TOTAL|PARCIAL|ADAPTADOR|AGENTE_HIJO|REJECT
kernel_role:
target_path:
contract:
adapter:
plugin_slot:
dependencies:
security:
tests:
rollback:
gaps_closed:
status: AWAITING_DIRECTOR_APPROVAL
```

No mover antes de aprobación del Director.

---

# 8. MOVIMIENTO — RESPONSABLE SOL

Sol prepara y ejecuta/proporciona el movimiento parcial o total por GitHub Action.

Patrón:

```text
SOURCE exacto
→ DESTINATION exacto
→ precheck
→ git mv/cp
→ hash/cmp
→ git diff --name-status
→ validar SOLO rutas autorizadas
→ commit único
→ SHA
→ auditoría destino
```

Entre repos: `checkout×2 → copy explícito → hash → commit destino`.

Si son `≤10` archivos y el cableado es local, determinista, pequeño y sin cambio arquitectónico, Sol puede mover y cablear. Si no, Codex.

---

# 9. ROLES

## CHAT A — SOL GPT
Arquitecto/orquestador/integrador: documentos, X-Ray, arquitectura, gaps, búsqueda, mapas de destino, MissionContract/GoalLock, DAG/schemas/contracts, movimientos, Crazy Wall y verificación final.

## CHAT B — CODEX OPENAI
Implementador senior de una sola task. No rediseña arquitectura global. Máximo estimado 2000 LOC por task y 500 LOC por bloque. Producción/SaaS, nunca MVP. Debe devolver manifest, tests, contratos, dependencias, calidad, trazabilidad y EvidencePacket.

## CHAT C — GROK
Frontend/UI únicamente. Cada UI vive en repo `frontend`, raíz separada por proyecto (`UI YAIWES`, `UI ROUTER...`). Usa el skill frontend del Director. El Sol dueño del repo correspondiente audita esa UI.

## LUNA
Checker independiente: reejecuta pruebas, valida integración y evidencia cuando se requiera maker-checker.

Backend↔UI siempre mediante API/contract/schema explícitos; frontend no entra al kernel.

---

# 10. ANEXOS DE TRABAJO — HANDOFF A CODEX

Patrón:

```text
Readme arquitectura <REPO>/
  anexo trabajos en curso 1/
  anexo trabajos en curso 2/
```

Cada trabajo contiene:

- MissionContract + GoalLock;
- TASK_ID / ROOT_ID / DAG_NODE;
- allowed/forbidden files;
- destino exacto;
- JSON/YAML;
- schemas/contracts;
- sheriff/validator/sentinel/verifier/supervisor/judge/guardian;
- tests;
- rollback;
- output schema;
- Crazy Wall de trabajo;
- state JSON append-only/event-driven.

Sol entrega al Director un mini-prompt con repo + ruta + TASK_ID. Codex abre el anexo, ejecuta solo ese nodo y escribe resultados/evidencia/estado en el mismo anexo.

---

# 11. RUNTIME DETERMINISTA CODEX

```text
INPUT_BLOCK
→ SENTINEL
→ MISSION_CONTRACT
→ GOAL_LOCK
→ SHERIFF
→ VALIDATOR
→ DAG SELECT
→ IDEMPOTENCIA
→ CAPABILITY
→ VALIDAR INPUT
→ EXECUTE
→ TEST
→ TRIBUNAL
→ GOAL CHECK
→ EVIDENCE
→ STATE EVENT
→ DONE | RECOVERY
```

Nodo mínimo:

```yaml
node_id:
literal_instruction:
input_schema:
output_schema:
depends_on:
preconditions:
postconditions:
allowed_files:
forbidden_files:
allowed_actions:
forbidden_actions:
validation:
tests:
evidence:
rollback:
status:
```

Codex no puede ampliar alcance, crear tareas, replanificar el proyecto o tocar archivos fuera de contrato.

---

# 12. FAIL-CLOSED / LOOP

Contrato rector: `tel.workflow/v3`.

`SHERIFF → VALIDATOR → SIMULATE → RESEARCH → RANK → EXECUTE → SENTINEL → VERIFY → SUPERVISOR → JUDGE → GUARDIAN → CODA → verify_final`.

Research por nodo:

1. consulta desde nodo literal;
2. chat/historial;
3. código/repos/docs oficiales;
4. comunidad secundaria;
5. filtrar/deduplicar;
6. rankear y guardar URL/versión/SHA/fecha.

Sin evidencia real = `insufficient_evidence=true`.

Fallo: `GAP → RESEARCH con DELTA distinto → EXECUTE → VERIFY`.

Checks reales dependientes de runtime pueden repetirse hasta 10x para detectar flakiness; comprobaciones puras/deterministas una vez.

---

# 13. REGLA ANTI-SOBREINGENIERÍA — 100%

Objetivo operativo: **resolver lo pedido de la forma más corta, segura, mantenible y rápida que alcance calidad SaaS**.

No se optimiza por cantidad de documentos, capas, agentes, archivos, abstracciones ni LOC. Se optimiza por resultado verificable.

Orden:

```text
REUSE
→ MOVE/COPY
→ PATCH PEQUEÑO
→ ADAPTER
→ GENERATE SOLO EL DELTA
```

Prohibido crear por rutina:

- capas sin consumidor real;
- wrappers redundantes;
- DSL adicional si JSON/YAML resuelve;
- microservicios sin necesidad operativa;
- registries duplicados;
- agentes separados para una tarea trivial;
- documentos duplicados;
- abstracciones “por si acaso”;
- frameworks nuevos si una función estándar resuelve;
- refactors masivos fuera del gap.

Gate antes de añadir una pieza:

```text
¿Resuelve un requisito/gap real?
¿Existe ya?
¿Puede resolverse con menos piezas?
¿Reduce riesgo/tiempo o solo añade estructura?
¿Tiene consumidor, contrato y test?
```

Si alguna respuesta crítica es NO, no se añade.

---

# 14. REGLA DE 3 SIMULACIONES CUANDO APARECE UNA MEJOR MANERA

Si Sol detecta una alternativa que puede ser claramente mejor que el plan activo, **no cambia el plan silenciosamente**. Ejecuta 3 simulaciones/dry-runs comparables antes de proponérsela al Director.

Las tres simulaciones deben usar el mismo objetivo y comparar como mínimo:

```text
1. tiempo estimado / pasos
2. número de archivos y piezas nuevas
3. riesgo de integración/regresión
4. reutilización de código existente
5. complejidad operativa
6. reversibilidad/rollback
7. tests necesarios
8. calidad SaaS alcanzable
```

Formato de salida:

```yaml
opcion_actual:
alternativa:
simulacion_1: {resultado:, riesgos:, tiempo:, piezas:}
simulacion_2: {resultado:, riesgos:, tiempo:, piezas:}
simulacion_3: {resultado:, riesgos:, tiempo:, piezas:}
veredicto: MANTENER_ACTUAL|PROPONER_ALTERNATIVA
razon:
```

Las simulaciones no mutan código ni arquitectura. Si la alternativa gana claramente las 3, Sol la presenta al Director; solo se cambia con autorización cuando afecte arquitectura/destino/alcance.

---

# 15. TRABAJO EN GRUPOS Y PARALELO

Trabajar rápido significa **paralelizar únicamente tareas independientes**.

Agrupación recomendada:

```text
GRUPO A — inventario/X-Ray
GRUPO B — investigación/reutilización
GRUPO C — mapas de destino/contratos
GRUPO D — movimientos aprobados
GRUPO E — cableado/implementación
GRUPO F — tests/verificación
```

Reglas:

- ramas/nodos sin dependencia pueden correr en paralelo;
- tareas que tocan el mismo archivo/contrato se serializan;
- máximo paralelismo se decide por conflictos reales, no por llenar agentes;
- fan-out para análisis, fan-in para decisión;
- cada grupo devuelve un artefacto pequeño y verificable;
- nunca crear coordinación más costosa que la tarea.

Meta: **menos esperas, menos handoffs y menos re-trabajo**.

---

# 16. CALIDAD — NO MVP

Todo código nuevo debe cubrir lo aplicable:

`correctness | contracts | schemas | typing | security | idempotency | timeout/deadline | errors | observability | maintainability | tests | regression | rollback | traceability | evidence`.

Prohibido:

- demo disfrazado de producción;
- placeholder/fake en hot path;
- `try/except: pass`;
- secretos en prompts/logs/manifests;
- dependencia sin origen/versión cuando aplique;
- refactor masivo no pedido;
- generar LOC para llenar cuota;
- monolitos evitables.

Nivel SaaS **no significa sobrearquitectura**: significa robustez verificable en el alcance real.

---

# 17. CHECKLIST PRE-CODE

```text
[ ] objetivo congelado
[ ] documentos escaneados 4 veces
[ ] arquitectura revisada
[ ] código actual revisado
[ ] biblioteca Maxbry revisada
[ ] OSS revisado si sigue faltando
[ ] componente clasificado
[ ] origen/licencia/SHA registrados
[ ] destino exacto aprobado
[ ] ficha/contract definidos cuando aplica
[ ] se aplicó REUSE>PATCH>ADAPT>GENERATE
[ ] se descartó sobreingeniería
[ ] riesgo/sandbox/timeout definidos
[ ] task dimensionada
[ ] responsable Sol|Codex|Grok|Luna
[ ] rollback definido
[ ] tests definidos
[ ] dependencias paralelizables identificadas
```

---

# 18. CHECKLIST POST-MOVIMIENTO / POST-CODE

```text
[ ] archivos esperados en destino
[ ] ningún archivo extra modificado
[ ] SHA/hash comprobado
[ ] imports resuelven
[ ] ficha válida cuando aplica
[ ] contract compatible
[ ] adapter probado cuando aplica
[ ] registry/slot correcto cuando aplica
[ ] shadow test cuando aplica
[ ] unit/integration/contract tests
[ ] negative/edge tests aplicables
[ ] regression
[ ] evidencia independiente cuando aplica
[ ] architecture↔code cross-check
[ ] Crazy Wall/state actualizado
[ ] rollback comprobable
[ ] cero gaps críticos ocultos
[ ] no quedó estructura innecesaria añadida
```

---

# 19. TRAZABILIDAD

```text
PROJECT
→ SOURCE_DOCUMENT
→ REQUIREMENT
→ GOAL
→ COMPONENT
→ SOURCE_REPO/SHA
→ ARCHITECTURE_NODE
→ DAG_NODE
→ TASK_ID
→ AGENT
→ ROOT_ID
→ FILE
→ FUNCTION
→ CONTRACT
→ TEST
→ EVIDENCE
→ RESULT
```

---

# 20. VIGILANCIA

Cada Sol mantiene Crazy Wall + anexos. El Director puede informar finalización; opcionalmente un watchdog horario revisa tareas en curso y solo notifica cambios accionables.

Un `DONE` declarado por otro agente nunca basta: Sol revalida destino, tests y evidencia.

---

# 21. CIERRE

`VERIFIED_CLOSED` exige código real + wiring + contract/schema + tests verdes + evidencia + trazabilidad + destino verificado + cross-check documental + rollback cuando aplica.

Si falta algo: `GAP | BLOCKED | CLOSED_UNVERIFIED | INCONCLUSIVE`.

---

# 22. JSON FUERTE — CONTRATO OPERATIVO

```json
{
  "skill": "orquestacion_integracion_maxbry",
  "version": "2.1.0",
  "mode": "fail-closed",
  "quality": "production_saas_only",
  "mvp_allowed": false,
  "anti_overengineering": {
    "mandatory": true,
    "optimize_for": ["correctness", "speed", "reuse", "maintainability", "low_coordination_cost"],
    "forbid": ["unused_layers", "duplicate_wrappers", "extra_dsl", "speculative_abstractions", "unneeded_microservices", "scope_creep", "mass_refactor"],
    "decision_order": ["REUSE", "MOVE_OR_COPY", "PATCH_SMALL", "ADAPT", "GENERATE_DELTA_LAST"]
  },
  "better_method_gate": {
    "simulations_required": 3,
    "dry_run_only": true,
    "compare": ["time", "pieces", "risk", "reuse", "complexity", "rollback", "tests", "saas_quality"],
    "silent_plan_change": false,
    "director_approval_if_architecture_scope_destination_changes": true
  },
  "parallel_work": {
    "enabled": true,
    "parallelize_only_independent_nodes": true,
    "serialize_shared_files_or_contracts": true,
    "fan_out_analysis_fan_in_decision": true,
    "goal": "minimum_waits_minimum_handoffs_minimum_rework"
  },
  "document_ingestion": {
    "root_pattern": "Documentos proyectos <REPO>/",
    "mandatory_scans_per_document": 4,
    "cross_check": ["document", "architecture", "source_code", "contracts", "tests", "evidence"]
  },
  "code_sources_priority": [
    "existing_code_same_repo",
    "maxbry_internal_repositories",
    "Agentes-motores-Wordflow-YAIWES",
    "director_download_code",
    "verified_open_source",
    "codex_generate_last"
  ],
  "component_gate": {
    "classify": ["TOTAL", "PARCIAL", "ADAPTADOR", "AGENTE_HIJO", "REJECT"],
    "move_before_director_approval": false,
    "monolithic_kernel_merge": false,
    "external_kernel_requires_director_decision": true
  },
  "plugin_integration": {
    "require_ficha_when_applicable": true,
    "require_contract": true,
    "prefer_adapter_over_rewrite": true,
    "require_registry_slot_when_plugin": true,
    "require_shadow_test_before_swap": true
  },
  "roles": {
    "chat_a": "SOL_ORCHESTRATOR_ARCHITECT_INTEGRATOR",
    "chat_b": "CODEX_IMPLEMENTER_MAX_2000_EST_LOC_PER_TASK_MAX_500_PER_BLOCK",
    "chat_c": "GROK_FRONTEND_UI_ONLY",
    "checker": "LUNA_INDEPENDENT_VERIFICATION"
  },
  "sol_small_change_rule": {
    "max_files": 10,
    "allowed_only_if": "local_deterministic_wiring_no_architecture_change"
  },
  "codex": {
    "may_redesign_global_architecture": false,
    "may_expand_scope": false,
    "requires": ["mission_contract", "goal_lock", "dag", "schemas", "contracts", "allowed_files", "tests", "evidence", "rollback"]
  },
  "ui": {
    "lives_in_repo": "frontend",
    "root_per_project": "UI <PROJECT>",
    "backend_owner": "each_project_repo",
    "frontend_builder": "GROK",
    "audit_owner": "SOL_OF_EACH_PROJECT"
  },
  "closure": {
    "pass_word": "VERIFIED_CLOSED",
    "requires": ["code", "wiring", "contract", "tests", "evidence", "traceability", "destination_audit", "document_cross_check"],
    "unknown_is_pass": false
  }
}
```

---

# 23. ACTUALIZACIÓN DEL SKILL

El Skill es vivo y acumulativo. Cada regla nueva compatible se añade. Si una nueva regla contradice una regla estructural previa, se registra el conflicto y se consulta al Director antes de cambiarla.