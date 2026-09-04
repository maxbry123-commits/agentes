# SKILL VIVO — Orquestación, adquisición, integración y verificación YAIWES

**Estado:** vivo / acumulativo / fail-closed  
**Arquitectura canónica:** `Readme arquitectura Yaiwes/README.md`  
**Crazy Wall:** `Readme arquitectura Yaiwes/Crazy Wall Orquestador/HOJA-DE-RUTA-MAESTRA.md`  
**Principio:** `REUSE > PATCH > ADAPT > GENERATE`  
**Calidad mínima:** producción/SaaS/ingeniería de software de alto nivel. **MVP está prohibido** salvo autorización literal del Director.

---

# 1. OBJETIVO GENERAL PRINCIPAL 🎯

Convertir cada lote documental recibido en la raíz de un proyecto en arquitectura verificable, gaps concretos y código real integrado sin reescribir desde cero.

Patrón por proyecto:

```text
main/
  Documentos proyectos <NOMBRE_PROYECTO>/
    lote-01/
    lote-02/
    ...
```

Cada documento de entrada se contrasta contra:

1. arquitectura canónica del proyecto;
2. código fuente real;
3. tests, contracts, schemas y wiring;
4. Crazy Wall / estado / evidencia.

Resultado buscado:

```text
DOCUMENTO → REQUISITO → CAPACIDAD → ¿EXISTE? → ¿ESTÁ CABLEADA? → ¿TIENE TEST? → GAP REAL
```

Nunca se considera cumplida una función porque esté descrita en un documento o porque exista un archivo con nombre parecido.

---

# 2. FUENTE DE VERDAD Y ORDEN DE AUTORIDAD

1. Código ejecutable + tests reproducibles + evidencia.
2. Arquitectura canónica del repo correspondiente.
3. Instrucciones literales del Director.
4. Contratos, schemas, DAG y anexos de trabajo aprobados.
5. Documentos del proyecto, Claude y otros diseñadores como requisitos/gaps.
6. Investigación externa como fuente de candidatos, nunca como PASS automático.

Estados X-Ray obligatorios:

`REAL | PARCIAL | ESQ | FALTANTE | DECLARADO_NO_VERIFICADO | VERIFIED_CLOSED`

`UNKNOWN`, ausencia de evidencia o conflicto documental = **FAIL CLOSED**, nunca PASS.

---

# 3. AUDITORÍA DE DOCUMENTOS — 4 ESCANEOS OBLIGATORIOS

Cada archivo dentro de `Documentos proyectos <repo>/` se lee **4 veces**. En cada pasada se aplican los ejes de auditoría necesarios: completitud, objetivo, código, arquitectura, dependencias, contratos/datos, ejecución, calidad, trazabilidad y consistencia.

## Escaneo 1 — significado literal
- extraer requisitos, funciones, restricciones, inputs, outputs y definition of done;
- separar `FACT / EVIDENCE / INFERENCE / UNKNOWN`;
- no corregir ni reinterpretar silenciosamente al autor.

## Escaneo 2 — arquitectura
- mapear cada requisito a componente/ruta de la arquitectura;
- detectar contradicciones, duplicados, componentes monolíticos y responsabilidades mal ubicadas;
- identificar si pertenece a kernel, runtime, workflow, tool, agent, UI, memoria, seguridad o integración.

## Escaneo 3 — código real
- localizar símbolos, archivos, imports, clases, funciones, registries, tests y wiring;
- distinguir archivo existente de capacidad operativa;
- comprobar si hay código completo, parcial, stub, fake, duplicado o no conectado.

## Escaneo 4 — verificación cruzada y gaps
- documento ↔ arquitectura ↔ código ↔ test ↔ evidencia;
- generar GAP únicamente donde falte una prueba real;
- producir siguiente acción concreta: `REUSE | MOVE | PATCH | ADAPT | GENERATE | REJECT`.

Checklist documental mínimo:

```text
[ ] requisito identificado
[ ] ubicación arquitectónica
[ ] código localizado o FALTANTE demostrado
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

El código puede llegar por cuatro vías controladas:

## A. OSS / GitHub / software externo
El Director, Sol u otro chat propone repositorios. Sol verifica antes de adoptar:

- URL oficial;
- organización/autor;
- licencia;
- versión/tag/commit SHA;
- actividad/mantenimiento;
- árbol y módulos útiles;
- dependencias;
- superficie de seguridad;
- tests;
- qué función evita escribir desde cero.

Flujo:

`PROPUESTA → VERIFICAR ORIGEN → DESCARGA GITHUB ACTION → SHA/ÁRBOL → X-RAY → CLASIFICAR → DESTINO`.

## B. Biblioteca interna Maxbry
Antes de investigar fuera, revisar **todos los repositorios accesibles de la cuenta Maxbry**, con prioridad especial a la biblioteca `Agentes-motores-Wordflow-YAIWES` y sus más de 300 agentes/software/componentes cuando exista la capacidad buscada.

## C. Código subido por el Director
Cada proyecto puede tener una raíz tipo:

`download code <NOMBRE_REPO>/`

Ese código se considera candidato estructurado por el Director. No se rediseña de entrada: se analiza, clasifica y mueve total/parcialmente a la ruta arquitectónica aprobada.

## D. Código generado por Codex
`GENERATE` es el último recurso. Solo se pide a Codex cuando la función no existe internamente ni en un OSS adecuado, o cuando el delta faltante requiere implementación nueva.

---

# 5. CORE KERNEL — REGLA DE INCORPORACIÓN

Una raíz `core kernel <NOMBRE_PROYECTO>/` contiene código candidato a ser **parte fundamental del kernel**, no una simple capa Wordflow.

Si el componente externo trae su propio core/kernel/loop de decisión:

1. estudiar su capacidad real;
2. determinar qué parte es infraestructura reutilizable;
3. detectar cerebro/loop/arquitectura incompatible;
4. proponer al Director una de estas opciones:
   - `PODAR_Y_REUSAR_CAPACIDADES`;
   - `CONVERTIR_EN_AGENTE_HIJO`;
   - `ADAPTAR_COMO_PLUGIN`;
   - `RECHAZAR`.

**Nunca fusionar dos kernels completos a ciegas. Nunca crear un monolito.**

El kernel crece por módulos pequeños y reemplazables:

```text
kernel-principal/
  kernel-1/
  kernel-2/
  kernel-3/
  kernel-4/
  ...
  registry/
  adapters/
  contracts/
```

La numeración es conceptual: la ruta final debe respetar la arquitectura real de cada repo.

---

# 6. ENCHUFE UNIVERSAL / FICHA / PLUGIN REGISTRY

Fuentes localizadas en `Readme arquitectura Yaiwes/`:

- `🔌 enchufe universal parte 1 fusion fables Kimi k 3 universal_plugin_bus_v2_integrated.py`
- `🔌✅ enchufe universal parte 2 fusión de Kimi k 3 y fables ficha_contract_v2.py`
- `🏗️🏗️🔌🔌 JSON para IA ... enchufe ... .md`

Estado documental actual: **SOURCE_REAL_EN_ANEXO / PENDIENTE_DE_INTEGRACIÓN_PRODUCTIVA**. Que el código exista en el anexo no demuestra que esté cableado en el kernel final.

El Universal Plugin Bus contiene como piezas verificables en la fuente:

- `ContractGenerator.generate()`;
- `AdapterFactory.create()`;
- `PluginRegistry` con slots;
- `UniversalPluginBus.enchufar()`;
- `HotSwapManager.shadow_load()`;
- `run_shadow_tests()` y `atomic_swap()`;
- evidencia, health, failover, telemetría y budget governor.

La Ficha v2 define schema + normalización + validador de 36 invariantes, incluyendo identidad, versión, input/output, ejecución, idempotencia, sandbox, timeout/deadline, categoría, etapa, perfiles, presupuesto, evidencia, failover, salud y trazas.

Flujo obligatorio de integración:

```text
COMPONENTE
→ X-RAY
→ FICHA
→ VALIDAR FICHA
→ GENERAR/VERIFICAR CONTRACT
→ DECIDIR PASSTHROUGH O ADAPTER
→ SHADOW LOAD
→ SHADOW TESTS
→ SLOT NUEVO EN REGISTRY
→ ENCHUFAR
→ TEST DE INTEGRACIÓN
→ EVIDENCE
→ ACTIVAR / SWAP
```

Nunca modificar la lógica original si un adaptador puede resolver compatibilidad.

---

# 7. CLASIFICACIÓN DE COMPONENTES

Todo componente recibe una ficha de decisión:

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

No mover antes de `AWAITING_DIRECTOR_APPROVAL → APPROVED`.

---

# 8. MOVIMIENTO DE ARCHIVOS — RESPONSABLE SOL

Sol es responsable de preparar y ejecutar/proporcionar el movimiento parcial o total de componentes mediante GitHub Action.

Patrón preferido: **manifest explícito**, no comodines ambiguos.

```text
SOURCE exacto
→ DESTINATION exacto
→ precheck existe/no colisión
→ git mv o cp
→ hash/cmp
→ git diff --name-status
→ validar SOLO rutas autorizadas
→ commit único
→ SHA de commit
→ auditoría destino
```

Para otro repo: `checkout ×2 → copy explícito → hash → commit destino`.

Artifacts sirven para transportar resultados entre jobs, no sustituyen una integración Git.

Si son **≤10 archivos y el cableado es pequeño, local, determinista y sin cambio arquitectónico**, Sol puede mover y cablear. Si supera esa simplicidad, pasa a Codex.

---

# 9. ROLES CHAT A / CHAT B / CHAT C

## CHAT A — SOL GPT ORQUESTADOR / ARCHITECT

Responsable de:
- leer documentos;
- X-Ray;
- arquitectura;
- gaps;
- búsqueda/reutilización;
- mapa componente→destino;
- MissionContract/GoalLock;
- DAG/schemas/contracts;
- división de tareas;
- movimientos GitHub;
- Crazy Wall;
- verificación e integración final.

No acepta PASS por texto de otro agente.

## CHAT B — CODEX OPENAI / SENIOR IMPLEMENTER

Codex **implementa una tarea delimitada**. No rediseña el proyecto.

Reglas base derivadas del método maduro Chat A→B:
- máximo estimado por task: 2000 LOC;
- máximo por bloque de código: 500 LOC;
- una task funcional coherente por Chat B;
- production/SaaS, nunca MVP;
- reutilizar antes de generar;
- output con manifest, tests, contracts, dependencias, quality, traceability y EvidencePacket.

## CHAT C — GROK / FRONTEND UI

Grok se usa para construir **componentes frontend/UI**, no para decidir el backend global del proyecto.

Cada proyecto mantiene su backend en su propio repo. Cada UI vive en el repo `frontend`, bajo una raíz independiente, por ejemplo:

`frontend/UI YAIWES/`
`frontend/UI ROUTER UNIVERSAL INTELIGENTE/`

Grok recibe prompts modulares y construye archivos/componentes separados siguiendo el **skill frontend del Director**. Si ese skill no está disponible, estado = `BLOCKED_PENDING_DIRECTOR_FRONTEND_SKILL`; no inventar reglas visuales.

El Sol encargado de cada repo audita su propia UI:
- Sol YAIWES audita UI YAIWES;
- Sol Router audita UI Router;
- etc.

Backend↔UI se conecta por contratos/API/schema explícitos; no mezclar frontend dentro del kernel.

## LUNA — VERIFICADOR INDEPENDIENTE

Luna recibe el prompt de auditoría/test cuando se requiere separación Maker-Checker. Reejecuta tests, verifica integración y entrega evidencia independiente. El agente que produjo el código no es la única autoridad para aprobarlo.

---

# 10. ANEXO DE TRABAJOS EN CURSO — CÓMO CODEX RECIBE LA TAREA

Cada repo debe poder mantener, dentro de su raíz documental de arquitectura:

```text
Readme arquitectura <NOMBRE_REPO>/
  anexo trabajos en curso 1/
  anexo trabajos en curso 2/
  ...
```

Cada trabajo contiene un contrato autónomo para Codex con:

- MissionContract + GoalLock;
- TASK_ID / ROOT_ID / DAG_NODE;
- archivos permitidos/prohibidos;
- destino exacto;
- JSON/YAML declarativo;
- schemas/contracts;
- sheriff/validator/sentinel/verifier/supervisor/judge/guardian;
- tests;
- rollback;
- output schema;
- Crazy Wall del trabajo;
- `state.json` append-only/event-driven.

Sol entrega al Director un **mini-prompt de handoff** con repo + ruta del anexo + TASK_ID. El Director se lo pasa a Codex. Codex abre ese archivo y ejecuta únicamente el nodo/tarea indicada.

Al terminar, Codex escribe resultados/evidencia/estado en el mismo anexo de trabajo, sin modificar la arquitectura global por su cuenta.

---

# 11. RUNTIME DETERMINISTA PARA CODEX

Cadena mínima:

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

Codex no recibe una orden ciega. Recibe nodos con contrato verificable.

Por nodo:

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

El ejecutor no puede replanificar el proyecto entero, cambiar alcance, inventar tareas o tocar archivos fuera del contrato.

---

# 12. MÉTODO DE TRABAJO FAIL-CLOSED / LOOP

Contrato rector: `tel.workflow/v3`.

Cadena:

`SHERIFF → VALIDATOR → SIMULATE → RESEARCH → RANK → EXECUTE → SENTINEL → VERIFY → SUPERVISOR → JUDGE → GUARDIAN → CODA → verify_final`.

Investigación por nodo:

1. consulta construida desde el nodo literal;
2. revisar chat/historial para no repetir;
3. código/repos/docs oficiales;
4. comunidad como señal secundaria;
5. filtrar + deduplicar;
6. rankear `código oficial > skills/chat > comunidad` y guardar URL/versión/SHA/fecha.

Sin URL/evidencia real = `insufficient_evidence=true`.

Si falla:

`GAP → volver a RESEARCH con DELTA distinto → EXECUTE → VERIFY`.

No repetir el mismo intento. Las comprobaciones de artefactos reales pueden repetirse hasta 10 veces para detectar flakiness; checks puros/deterministas no requieren repetición artificial.

---

# 13. CALIDAD DE CÓDIGO — NO MVP

Toda implementación nueva debe apuntar a ingeniería de producción:

```text
correctness
contracts
schemas
typing
security
idempotency
timeout/deadline
error handling
observability
maintainability
testability
regression
rollback
traceability
evidence
```

Prohibido:
- código demo disfrazado de producción;
- placeholders/fakes en hot path;
- `try/except: pass`;
- secretos en prompts/logs/manifests;
- dependencia sin origen/versión cuando sea relevante;
- refactor masivo no pedido;
- generación para llenar LOC;
- monolitos cuando existen límites de responsabilidad claros.

Una función o módulo nuevo necesita razón, contrato, destino, test y evidencia.

---

# 14. CHECKLIST PRE-CODE

```text
[ ] objetivo congelado
[ ] documento escaneado 4 veces
[ ] arquitectura revisada
[ ] código actual revisado
[ ] biblioteca interna Maxbry revisada
[ ] OSS investigado si sigue faltando
[ ] componente clasificado
[ ] licencia/origen/SHA registrados
[ ] destino exacto aprobado
[ ] ficha/contract definidos
[ ] riesgo/sandbox/timeout definidos
[ ] task dimensionada
[ ] responsable definido: Sol | Codex | Grok
[ ] rollback definido
[ ] tests de aceptación definidos
```

# 15. CHECKLIST POST-MOVIMIENTO / POST-CODE

```text
[ ] archivos esperados en destino
[ ] ningún archivo extra modificado
[ ] SHA/hash comprobado cuando aplica
[ ] imports resuelven
[ ] ficha valida
[ ] contract compatible
[ ] adapter probado
[ ] registry/slot correcto cuando aplica
[ ] shadow test antes de swap cuando aplica
[ ] unit tests
[ ] integration tests
[ ] contract tests
[ ] negative/edge tests
[ ] regression
[ ] evidencia independiente
[ ] architecture↔code cross-check
[ ] Crazy Wall/state actualizado
[ ] rollback comprobable
[ ] cero gaps críticos ocultos
```

`VERIFIED_CLOSED` solo si todas las comprobaciones obligatorias del alcance tienen evidencia real.

---

# 16. TRAZABILIDAD OBLIGATORIA

Toda modificación debe poder seguirse:

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

Ningún cambio queda fuera del grafo de trazabilidad.

---

# 17. VIGILANCIA DE TRABAJOS EN CURSO

Cada Sol de repo mantiene el Crazy Wall y anexos de trabajos en curso como fuente de estado. El Director puede informar manualmente que Codex/Luna terminó; además puede existir un watchdog horario que revise tareas pendientes y solo notifique cambios accionables.

El watchdog no sustituye verificación: si detecta `DONE` declarado por otro agente, Sol debe leer resultados, revalidar destino, tests y evidencia antes de cerrar.

---

# 18. CIERRE

`VERIFIED_CLOSED` exige simultáneamente:

- implementación real;
- cableado real;
- contrato/schema válido;
- tests relevantes verdes;
- ausencia de placeholders críticos en alcance;
- evidencia registrada;
- trazabilidad completa;
- cross-check contra arquitectura y documentos;
- destino verificado;
- rollback/recuperación definido cuando aplica.

Si falta cualquiera: `GAP`, `BLOCKED`, `CLOSED_UNVERIFIED` o `INCONCLUSIVE` según corresponda; nunca “listo” por confianza.

---

# 19. JSON FUERTE — CONTRATO OPERATIVO DEL SKILL

```json
{
  "skill": "orquestacion_integracion_maxbry",
  "version": "2.0.0",
  "mode": "fail-closed",
  "quality": "production_saas_only",
  "mvp_allowed": false,
  "principle": ["REUSE", "PATCH", "ADAPT", "GENERATE_LAST"],
  "document_ingestion": {
    "root_pattern": "Documentos proyectos <REPO>/",
    "mandatory_scans_per_document": 4,
    "cross_check": ["document", "architecture", "source_code", "tests", "evidence"]
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
    "require_ficha": true,
    "require_contract": true,
    "prefer_adapter_over_rewrite": true,
    "require_registry_slot": true,
    "require_shadow_test_before_swap": true,
    "source_status": "SOURCE_REAL_IN_ARCHITECTURE_ROOT_NOT_PRODUCTION_WIRED"
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
    "audit_owner": "SOL_OF_EACH_PROJECT",
    "director_frontend_skill_required": true
  },
  "closure": {
    "pass_word": "VERIFIED_CLOSED",
    "requires": ["code", "wiring", "contract", "tests", "evidence", "traceability", "destination_audit", "document_cross_check"],
    "unknown_is_pass": false
  }
}
```

---

# 20. ACTUALIZACIÓN DEL SKILL

Este archivo es vivo. Cada nueva regla del Director se añade sin borrar reglas anteriores compatibles. Si aparece contradicción, se registra y se pide decisión del Director antes de mutar una regla estructural.
