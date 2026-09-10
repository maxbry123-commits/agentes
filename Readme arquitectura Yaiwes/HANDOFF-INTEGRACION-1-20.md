# HANDOFF — INTEGRACIÓN YAIWES — 27 NODOS — 3 PASOS

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Estado:** `ACTIVE_LOOP / 5X_REVIEWED`  
**Para:** Grok / GPT-5.6 Sol / Astra  
**Regla:** exactamente 3 pasos. Nada fuera de ellos.

## 1. Contrato único

```text
POR CADA COMPONENTE = 1 NODO

PASO 1 — DESTINO A/B/C + MOVE
PASO 2 — PODAR SOLO SI HACE FALTA + ENCHUFE FABLES
PASO 3 — TEST REAL

FAIL → reparar el mismo nodo y repetir el paso responsable.
NO PASO 4.
```

### PASO 1 — DESTINO A/B/C + MOVE

Leer únicamente lo necesario del código/README para identificar la función real.

- **A — AGENTE/SUBAGENTE:** tiene goal/lifecycle/tools/context o decisiones autónomas.
- **B — MOTOR DE TRABAJO:** scheduler, DAG, workflow, queue, workers, durable execution, multi-step o loop.
- **C — CAPACIDAD:** schema, policy, storage, memory, routing, research, sandbox, validator, herramienta u otra función modular.

Después elegir una raíz **ya existente** dentro de `Agente Yaiwes principal/` que corresponda a esa función y mover con `motor_4_move_batches.py`, hash + read-back. Si el MOVE ya está demostrado, no repetirlo.

Si A/B/C o el destino no se puede demostrar: dejar `GAP_DESTINATION`, no adivinar.

### PASO 2 — PODA MÍNIMA + FABLES OBLIGATORIO

- Conservar upstream.
- Podar solamente archivos/duplicados demostrados como innecesarios para la capacidad integrada.
- Cablear mediante el **Enchufe Universal FABLES obligatorio**.
- FABLES parte 1: `universal_plugin_bus_v2_integrated.py` / `UniversalPluginBus.enchufar()`.
- FABLES parte 2: `ficha_contract_v2.py` / `validar()` + ficha v2.
- Crear solamente adapter/port/WIRING que conecte la capacidad real.
- `source_probe()` o comprobar que existe una carpeta NO es integración.
- Tests prohibidos como cierre de este paso.

### PASO 3 — TEST REAL

```text
ficha valida
→ adapter/import/build
→ enchufar FABLES
→ capacidad real: caso positivo
→ failure path / fail-closed
→ health/evidence cuando aplique
→ read-back
→ PASS | GAP
```

Si falla: localizar el código responsable; corregir adapter/código, podar si hace falta o hacer fork cuando sea necesario; repetir el test. Todo ocurre dentro de PASO 2/3.

## 2. Coordinación multi-IA — Crazy Wall

`📂 Bitácora stated JSON Craxy wall.json` es la pizarra compartida.

Cada componente tiene un nodo independiente con:

```text
node_id
component
owner
lock
current_step
status
abc
target
checkpoint.before
checkpoint.after
evidence[]
history[]
```

Protocolo obligatorio:

1. Leer Crazy Wall fresco desde `main`.
2. Elegir un nodo `lock=FREE`.
3. Escribir `owner=GROK|SOL|ASTRA`, `lock=CLAIMED` y `checkpoint.before` antes de tocar código.
4. Solo el owner modifica ese nodo/componente.
5. Ejecutar únicamente el paso actual del nodo.
6. Escribir `checkpoint.after` + commit/run/test/evidence.
7. Avanzar `current_step` o cerrar `PASS`.
8. Liberar `lock=FREE`, `owner=null` al terminar la unidad.
9. Si un nodo está `CLAIMED`, otra IA toma otro nodo libre. No se pisan.

## 3. Estado de los primeros 20

MOVE 20/20 ya demostrado por:

- workflow `YAIWES Motor4 Final MOVE 20`
- run `34445710787`
- job `102771861495`
- commit `a3cf705f58f95cce65d1c230cb00abcab39732b2`

Nodos 1–5 — `PENDING_STEP3_REVALIDATION`: APScheduler, AWS-Step-Functions-DS-SDK, Ajv, Apache-APISIX, Apache-Airflow. Preservar integración histórica; revalidar comportamiento real.

Nodos 6–20 — `PENDING_STEP2_FABLES`: Argo-Workflows, Azure-Durable-Functions, BAML, Burr, Caddy, Camunda, Cedar, Celery, Cerberus, Cerbos, Chroma, ClawHub, Cloudflare-Workers-SDK, Coconut, CodeUltraFeedback. MOVE no se repite.

Destinos de los primeros 20 siguen siendo los ya publicados en `Agente Yaiwes principal/`; no cambiarlos sin evidencia de error.

## 4. Nuevos componentes detectados en `Core kernel Yaiwes/`

Se añadieron siete nodos nuevos. Están en **PASO 1** porque primero debe verificarse código/función/destino antes de mover:

| Nodo | Componente | A/B/C candidato | Destino candidato — VERIFICAR ANTES DE MOVE |
|---:|---|---|---|
| 21 | Dagu | B | `Agente Yaiwes principal/execution-orchestration/state-machine-executor/dagu/` |
| 22 | Hatchet | B | `Agente Yaiwes principal/execution-orchestration/state-machine-executor/hatchet/` |
| 23 | PostgreSQL | C | `Agente Yaiwes principal/state-events-durability/run-state-store/postgresql/` |
| 24 | Redis | C | `Agente Yaiwes principal/state-events-durability/redis/` |
| 25 | Workalendar | C | `Agente Yaiwes principal/execution-orchestration/task-classifier-scheduler/workalendar/` |
| 26 | gVisor | C | `Agente Yaiwes principal/execution-orchestration/container-pod-isolation/gvisor/` |
| 27 | pgvector | C | `Agente Yaiwes principal/tools-models-memory-knowledge/memory-microservices/pgvector/` |

APScheduler y Celery también existen en `Core kernel Yaiwes/`, pero pertenecen a los primeros 20: no crear nodos duplicados.

## 5. FABLES — regla de integridad

Las dos fuentes entregadas por el usuario son el contrato de cableado obligatorio:

- `ficha_contract_v2.py` — SHA256 entregado/auditado: `759d0d7855d8df106462b966bfc4ee543f24a3e789a27048f253159b58ff8d1a`.
- `universal_plugin_bus_v2_integrated.py` — SHA256 entregado/auditado: `5e4595a86bfd68a3c1fde70ba614ce7b9ec6ea4d6c867912e836cca33c626fc3`.

En la revisión 5× estos archivos exactos todavía no quedaron demostrados dentro de `main`; por tanto `FABLES_REPO_STATE=PENDING_MATERIALIZATION`. Grok puede trabajar PASO 1 y revalidaciones que no alteren el enchufe, pero ningún nodo de PASO 2 puede declararse cerrado hasta materializar/verificar estas dos piezas exactas.

## 6. Watchdog del trabajo

El Watchdog supervisa el contrato, no añade pasos:

```text
SCAN Core kernel Yaiwes/
→ registrar componente nuevo como nodo FREE/PASO1
→ detectar nodos FREE
→ IA reclama nodo
→ checkpoint.before
→ PASO 1 | PASO 2 | PASO 3
→ checkpoint.after + evidence
→ PASS: cerrar
→ GAP: mantener nodo y repetir paso
→ liberar lock
```

Reglas Watchdog: no crear tareas laterales; no descargar reemplazos sin GAP; no aceptar carpeta/README como PASS; no editar nodo de otro owner; no declarar cierre sin evidence/read-back.

## 7. Inicio exacto para Grok

```text
READ 1: PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md
READ 2: este HANDOFF
READ 3: 📂 Bitácora stated JSON Craxy wall.json
READ 4: estado físico actual de main

THEN:
- toma el primer nodo FREE apropiado;
- escribe owner=GROK + lock=CLAIMED + checkpoint.before;
- ejecuta solamente su current_step;
- actualiza evidence/checkpoint;
- no inventa Paso 4 ni arquitectura nueva.
```

## 8. Enlaces

- Handoff: https://github.com/maxbry123-commits/agentes/blob/main/Readme%20arquitectura%20Yaiwes/HANDOFF-INTEGRACION-1-20.md
- Recovery: https://github.com/maxbry123-commits/agentes/blob/main/PARCHE-RECUPERACION-CORE-INTEGRACION-WATCHDOG.md
- Crazy Wall: https://github.com/maxbry123-commits/agentes/blob/main/%F0%9F%93%82%20Bit%C3%A1cora%20stated%20JSON%20Craxy%20wall.json
- Watchdog machine plan: https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json
