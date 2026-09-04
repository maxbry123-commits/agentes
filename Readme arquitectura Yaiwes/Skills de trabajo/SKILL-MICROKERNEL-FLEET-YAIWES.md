# SKILL — MICROKERNEL + FLEET YAIWES

**Tipo:** extensión operativa del `SKILL-ORQUESTACION-YAIWES.md`  
**Estado:** RESEARCHED_PROPOSAL / AWAITING_DIRECTOR_ARCHITECTURE_APPROVAL  
**Regla madre:** cero sobreingeniería; reutilizar infraestructura probada antes de escribir control-plane propio.  
**Calidad:** producción/SaaS; MVP prohibido salvo orden literal del Director.

---

# 1. OBJETIVO 🎯

Convertir los recursos de ejecución disponibles del ecosistema Maxbry en una flota útil para cerrar tareas de los proyectos en paralelo, sin construir otro sistema monolítico de agentes.

El microkernel NO debe contener la lógica de los cientos de agentes ni de los proveedores de IA. Solo debe gobernar:

```text
INTAKE / TASK CONTRACT
→ CAPABILITY LOOKUP
→ POLICY / ROUTING
→ QUEUE / DISPATCH
→ EXECUTOR
→ TEST / EVIDENCE
→ STATE / CLOSURE
```

La ejecución pesada vive fuera: APIs, modelos, workers HF, agentes internos, Codex, Luna y futuros backends.

---

# 2. INPUT DEL DIRECTOR — ESTADO DECLARADO

El Director declara disponibles o en fase final de conectividad:

- múltiples APIs de proveedores de IA (>20 según Director);
- Hugging Face para almacenamiento y modelos;
- modelos locales y modelos de proveedores;
- tres recursos HF de 32 GB RAM cada uno;
- biblioteca `maxbry123-commits/Agentes-motores-Wordflow-YAIWES` con gran cantidad de agentes/software/componentes;
- Luna GPT para tareas pequeñas, siempre con verificación porque puede producir resultados no fiables;
- una instancia Codex OpenAI para trabajos estructurados en cola.

**Regla fail-closed:** estas capacidades se registran como `DIRECTOR_DECLARED` hasta que conectividad, autenticación, permisos, ejecución mínima y evidencia hayan sido comprobados desde el runtime real.

El repositorio `maxbry123-commits/Agentes-motores-Wordflow-YAIWES` sí fue localizado y es accesible. La existencia de carpetas/agentes no demuestra que cada agente sea ejecutable ni compatible: cada capacidad se incorpora mediante ficha/contrato/test.

---

# 3. HALLAZGO PRINCIPAL DE INVESTIGACIÓN

No conviene escribir desde cero un scheduler + broker + queue + watchdog + retries + worker manager + dashboard.

La mejor división actual es:

```text
YAIWES THIN MICROKERNEL
  ├─ MissionContract / GoalLock
  ├─ capability registry + Ficha
  ├─ UniversalPluginBus / adapters
  ├─ routing policy
  └─ evidence / closure contract
          │
          ▼
EXISTING ORCHESTRATION RUNTIME
  ├─ schedules / triggers
  ├─ work queues
  ├─ concurrency
  ├─ worker pools
  ├─ retries / states
  └─ watchdog / automations
          │
          ▼
EXECUTION BACKENDS
  ├─ API providers
  ├─ HF worker 1
  ├─ HF worker 2
  ├─ HF worker 3
  ├─ Codex-1
  ├─ Luna-small
  └─ repo deterministic jobs
```

El microkernel decide **qué capacidad puede ejecutar una tarea y bajo qué contrato**. El runtime especializado decide **cuándo, en qué cola y en qué worker se ejecuta**.

---

# 4. ALTERNATIVAS INVESTIGADAS

## Opción A — Prefect 3 como control-plane de ejecución — RECOMENDADA PARA PILOTO

Prefect ya ofrece workers ligeros, work pools, work queues con prioridad/concurrencia, deployments manuales/programados/event-driven, estados persistidos, triggers, automations y detección de ausencia de eventos. Esto cubre gran parte de trigger + cola + scheduler + watchdog sin escribirlo nuevamente.

Diseño:

```text
YAIWES contracts/registry
→ Prefect deployment
→ work pool / queue
→ worker
→ capability adapter
→ evidence back to YAIWES
```

Ventajas:
- menor cantidad de código propio;
- queues y límites de concurrencia explícitos;
- ejecución por horario, evento o llamada manual;
- posibilidad de pull de código desde GitHub;
- worker status + events/automations para watchdog;
- self-host con PostgreSQL para producción.

Riesgo:
- añade dependencia de plataforma;
- hay que validar latencia y comportamiento con nuestros workloads antes de declararlo estándar.

## Opción B — Ray como compute fabric — RECOMENDADA DESPUÉS, SOLO SI HACE FALTA

Ray distribuye tasks/actors y permite asignar CPU/GPU/memoria/recursos personalizados entre nodos. Es especialmente útil si los tres recursos HF necesitan ejecutar inferencia/trabajo Python en paralelo.

Ventajas:
- excelente uso de un cluster de cómputo;
- tasks asíncronas y actors stateful;
- resource-aware scheduling;
- retries y task events.

Riesgo:
- Ray no sustituye por sí mismo todo el control-plane de proyecto;
- si se usa como orquestador principal obligaría a crear más scheduler/estado/watchdog/cola propios.

**Uso recomendado:** backend de cómputo enchufado detrás de Prefect/YAIWES cuando exista evidencia de que los tres workers HF lo necesitan.

## Opción C — Temporal — RESERVA PARA WORKFLOWS CRÍTICOS Y MUY DURABLES

Temporal está diseñado para ejecución durable y reanudación tras crashes/fallos de red/infra, incluso en procesos largos y agentes de IA.

Ventajas:
- máxima durabilidad de workflows largos;
- recovery y reanudación son parte del modelo;
- apropiado para tareas críticas/human-in-the-loop de horas o días.

Riesgo:
- mayor infraestructura y curva operativa;
- para el estado actual puede ser más complejo que el problema que queremos resolver.

**Uso recomendado:** adoptar solo si la operación real demuestra que Prefect + checkpoints del proyecto no cubren un gap de durabilidad crítico.

---

# 5. TRES SIMULACIONES — MISMO OBJETIVO

Objetivo común: tomar tareas del Crazy Wall, ejecutar en paralelo usando APIs/agentes/HF/Codex/Luna, vigilar bloqueos y devolver evidencia.

## SIMULACIÓN 1 — Thin YAIWES + Prefect

```yaml
pasos: 6
codigo_control_propio: BAJO
piezas_nuevas: [adapter_runtime, deployment_templates, queue_policy]
paralelismo: ALTO
watchdog: NATIVO_POR_EVENTS_AUTOMATIONS
colas: NATIVAS
codex_concurrency: 1
hf_workers: 3_POOLS_OR_QUEUES
rollback: ALTO
riesgo_integracion: MEDIO_BAJO
calidad_saas: ALTA
veredicto: GANADOR_PILOTO
```

## SIMULACIÓN 2 — Thin YAIWES + Ray + scheduler propio

```yaml
pasos: 9
codigo_control_propio: MEDIO_ALTO
piezas_nuevas: [ray_cluster, scheduler, durable_state, watchdog, queue_adapter]
paralelismo: MUY_ALTO
watchdog: REQUIERE_GLUE
colas: REQUIERE_GLUE
hf_workers: EXCELENTE
rollback: MEDIO
riesgo_integracion: MEDIO_ALTO
calidad_saas: ALTA_SI_SE_COMPLETA_GLUE
veredicto: NO_COMO_CONTROL_PLANE_INICIAL
```

## SIMULACIÓN 3 — Thin YAIWES + Temporal

```yaml
pasos: 8
codigo_control_propio: MEDIO
piezas_nuevas: [temporal_service, workers, workflow_contracts]
paralelismo: ALTO
durabilidad: MUY_ALTA
watchdog_recovery: MUY_ALTO
hf_workers: ADAPTER_NECESARIO
rollback: MUY_ALTO
riesgo_integracion: MEDIO
complejidad_operativa: ALTA
calidad_saas: MUY_ALTA
veredicto: RESERVAR_PARA_GAP_DURABILIDAD_REAL
```

**Resultado de las 3 simulaciones:** empezar con Opción A. No meter Ray ni Temporal hasta que un benchmark/gap real justifique la pieza adicional.

---

# 6. FLEET LANES — NO CREAR 300 WORKFLOWS

No crear un workflow, servicio o proceso permanente por cada agente. Eso sería sobreingeniería.

Crear un catálogo de capabilities y un ejecutor genérico:

```text
execute_capability(capability_id, task_contract)
```

Cada agente/modelo/tool tiene ficha + capability passport. El dispatcher selecciona uno y lo manda a una lane.

Lanes iniciales propuestas:

```yaml
lanes:
  api_io:
    purpose: llamadas a proveedores/API
    concurrency: configurable_por_rate_limit
  hf_worker_1:
    purpose: local_model_or_compute
  hf_worker_2:
    purpose: local_model_or_compute
  hf_worker_3:
    purpose: local_model_or_compute
  codex_1:
    purpose: coding_task_contract
    concurrency: 1
    requires: [approved_task, exact_files, tests, evidence]
  luna_small:
    purpose: low_risk_small_tasks
    restrictions: [no_architecture_mutation, no_unverified_pass]
    checker_required: true
  repo_ops:
    purpose: deterministic_git_file_test_jobs
```

Capacidades se asignan dinámicamente; las lanes son pocas y estables.

---

# 7. ROUTING — LO MÁS SIMPLE QUE FUNCIONE

Orden de selección:

```text
1. operación determinista local/tool
2. capability ya existente en el repo
3. agente/software validado en Agentes-motores-Wordflow-YAIWES
4. modelo local/HF
5. proveedor API según capability/coste/rate-limit
6. Codex si la tarea es implementación delimitada
7. generar nueva capacidad solo si las anteriores no cubren el gap
```

Nunca seleccionar por nombre o fama del agente. Seleccionar por:

`contract_match + health + authorization + resource_fit + cost + evidence_history`.

---

# 8. TRIGGERS, LOOP Y WATCHDOG

Triggers permitidos:

- horario/cron;
- evento GitHub/estado;
- nueva tarea aprobada;
- dependencia completada;
- Director `GO`;
- ausencia de heartbeat/evento esperado.

Loop operativo:

```text
TRIGGER
→ READ CRAZY WALL / ACTIVE TASKS
→ SELECT READY NODES
→ CONTRACT VALIDATION
→ QUEUE
→ EXECUTE
→ HEARTBEAT/CHECKPOINT
→ VERIFY
→ DONE
```

Si falla:

```text
FAIL
→ CHECKPOINT
→ CLASSIFY
→ RETRY CON DELTA si es recuperable
→ ELSE BLOCKED
→ NOTIFY SOL/DIRECTOR
```

Watchdog no “piensa” ni modifica arquitectura. Solo observa:
- run sin heartbeat;
- timeout/deadline;
- worker offline;
- cola atascada;
- retries agotados;
- tarea Codex/Luna terminada pendiente de verificación;
- evidence packet ausente.

---

# 9. MÉTODO DE TRABAJO OBLIGATORIO

Se hereda íntegramente de `SKILL-ORQUESTACION-YAIWES.md`:

```text
DOCUMENTOS 4 PASADAS
→ X-RAY
→ REUSE SEARCH
→ GAP
→ 3 SIMULACIONES SI HAY ALTERNATIVA
→ PLAN MÍNIMO
→ DIRECTOR GATE CUANDO AFECTA ARQUITECTURA/DESTINO
→ MOVE/ADAPT
→ CODEX SOLO DELTA NECESARIO
→ TEST
→ LUNA/CHECKER CUANDO APLICA
→ EVIDENCE
→ VERIFIED_CLOSED
```

Regla de velocidad:
- fan-out investigación/X-Ray independiente;
- fan-in una sola decisión;
- ejecución en paralelo solo si no hay conflictos de archivo/contrato/recurso;
- no crear un agente para coordinar a otro agente si una cola/estado determinista lo resuelve.

---

# 10. PILOTO MÍNIMO DE PRODUCCIÓN — NO MVP

“Mínimo” significa mínima superficie, no baja calidad.

Piloto propuesto:

1. una instancia self-hosted de Prefect con PostgreSQL;
2. `api_io` + una lane HF + `codex_1` + `luna_small`;
3. registrar 3–5 capabilities reales, no 300 de golpe;
4. una tarea programada, una por evento y una manual;
5. un watchdog por timeout/ausencia de evento;
6. evidence packet y state link para cada run;
7. medir latencia, fallos, retries, tiempo humano y coste;
8. si PASS, conectar los otros dos workers HF y ampliar catálogo por demanda.

No migrar 300 agentes antes de demostrar el carril con 3–5 capacidades reales.

---

# 11. CHECKLIST DE VALIDACIÓN

```text
[ ] conectividad real con runtime
[ ] auth sin secretos en logs
[ ] worker heartbeat visible
[ ] queue priority/concurrency comprobada
[ ] trigger horario PASS
[ ] trigger evento PASS
[ ] timeout/stuck detection PASS
[ ] retry con delta/recovery PASS
[ ] capability ficha válida
[ ] adapter/registry PASS
[ ] API provider rate-limit respetado
[ ] HF worker ejecuta tarea real
[ ] Codex lane concurrency=1
[ ] Luna output nunca cierra sin checker
[ ] evidence packet por run
[ ] task_id/trace_id/run_id enlazados
[ ] rollback/cancel probado
[ ] ninguna mutación fuera del contrato
[ ] no se crearon workflows por agente innecesariamente
[ ] benchmark contra ejecución manual
[ ] 3 simulaciones repetidas si aparece alternativa mejor
```

`VERIFIED_CLOSED` del microkernel fleet solo existe después de pruebas reales. Este documento es una propuesta investigada, no evidencia de despliegue.

---

# 12. FUENTES REALES — OFICIAL + COMUNIDAD

## Prefect
- https://docs.prefect.io/v3/concepts/deployments
- https://docs.prefect.io/v3/concepts/workers
- https://docs.prefect.io/v3/concepts/work-pools
- https://docs.prefect.io/v3/concepts/automations
- https://docs.prefect.io/v3/how-to-guides/automations/creating-deployment-triggers
- https://docs.prefect.io/v3/concepts/server

## Ray
- https://docs.ray.io/en/latest/ray-core/tasks.html
- https://docs.ray.io/en/latest/ray-core/key-concepts.html
- https://docs.ray.io/en/latest/ray-core/scheduling/resources.html

## Temporal
- https://docs.temporal.io/

## Comunidad desarrolladores
- https://www.reddit.com/r/dataengineering/comments/1uvnu24/what_orchestrator_should_you_use/
- https://www.reddit.com/r/dataengineering/comments/1vf4h4m/removed/
- https://www.reddit.com/r/ITManagers/comments/1tqwxer/what_are_people_actually_using_for_workflow/
- https://www.reddit.com/r/dataengineering/comments/1dhupkb/how_do_you_orchestrate_realtime_workflows/

Se usa comunidad como señal secundaria. Las decisiones técnicas se sostienen primero en documentación/código oficial y pruebas locales.

---

# 13. JSON FUERTE — CONTRATO DE PROPUESTA

```json
{
  "skill": "microkernel_fleet_yaiwes",
  "version": "1.0.0",
  "status": "RESEARCHED_PROPOSAL_AWAITING_DIRECTOR_APPROVAL",
  "parent_skill": "SKILL-ORQUESTACION-YAIWES.md",
  "quality": "production_saas",
  "mvp": false,
  "anti_overengineering": true,
  "microkernel_owns": [
    "task_contract",
    "capability_registry",
    "routing_policy",
    "authorization",
    "evidence_contract",
    "closure"
  ],
  "runtime_recommendation": {
    "phase_1": "PREFECT_3",
    "phase_2_if_compute_gap": "RAY_AS_BACKEND",
    "phase_3_if_durability_gap": "TEMPORAL"
  },
  "do_not_add_now_without_gap": [
    "custom_scheduler",
    "custom_message_broker",
    "custom_watchdog_framework",
    "one_workflow_per_agent",
    "second_plugin_registry",
    "ray_as_full_control_plane",
    "temporal_before_durability_need"
  ],
  "fleet_lanes": [
    "api_io",
    "hf_worker_1",
    "hf_worker_2",
    "hf_worker_3",
    "codex_1",
    "luna_small",
    "repo_ops"
  ],
  "codex_concurrency": 1,
  "luna_requires_checker": true,
  "capability_execution": "execute_capability(capability_id, task_contract)",
  "director_declared_resources_require_runtime_verification": true,
  "closure": "CODE+CONNECTIVITY+QUEUE+TRIGGER+WATCHDOG+TEST+EVIDENCE"
}
```
