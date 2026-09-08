from pathlib import Path
import json

ROOT = Path('.')
README = ROOT / 'Readme arquitectura Yaiwes/README.md'
STATE = ROOT / 'Core kernel Yaiwes/Crack wall bitácora stated JSON/STATE.json'
PLAN = ROOT / 'Core kernel Yaiwes/Crack wall bitácora stated JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json'
MEMORY = ROOT / 'Core kernel Yaiwes/readme-memoria.md'
MARKER = '<!-- YAIWES_MULTI_WATCHDOG_BACKEND_V1 -->'

STACK = [
    ('APScheduler', 'TIME_AUTHORITY'),
    ('Workalendar', 'WORK_CALENDAR'),
    ('Celery', 'SIMPLE_JOB_WORKERS'),
    ('Redis', 'EVENT_TRANSPORT'),
    ('Hatchet', 'DURABLE_LONG_JOB'),
    ('Dagu', 'MULTI_STEP_JOB'),
    ('PostgreSQL', 'DURABLE_SOURCE_OF_TRUTH'),
    ('pgvector', 'SEMANTIC_MEMORY'),
    ('gVisor', 'SANDBOX_ISOLATION'),
    ('S3-Compatible-Backblaze-B2', 'ARTIFACT_SNAPSHOTS'),
]

SECTION = '''<!-- YAIWES_MULTI_WATCHDOG_BACKEND_V1 -->
## Integración — Sistema adaptativo Watchdog / programación, memoria y sandbox — PENDIENTE

**Estado:** `PENDIENTE` hasta X-Ray de código, adquisición/extracción cuando aplique, adapter/Ficha v2/WIRING, runtime real, UniversalPluginBus, health/evidence, memoria+sandbox y read-back independiente.

**Bitácora activa:** [Crack wall bitácora stated JSON / STATE.json](https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/STATE.json)

**Plan activo:** [PLAN-WATCHDOG-PROGRAMMING-V2.json](https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/Crack%20wall%20bit%C3%A1cora%20stated%20JSON/PLAN-WATCHDOG-PROGRAMMING-V2.json)

**Memoria del Watchdog:** [readme-memoria.md](https://github.com/maxbry123-commits/agentes/blob/main/Core%20kernel%20Yaiwes/readme-memoria.md)

### Componentes pendientes aprobados para estudio/integración

1. **APScheduler** — autoridad del tiempo: jobs inmediatos, futuros, recurrentes, cron/calendario y persistencia de schedules.
2. **Workalendar** — política de horario laboral: días hábiles, festivos y calendarios para decidir si una ejecución corresponde.
3. **Celery** — pool distribuido de ejecución: workers, queues, retries y fan-out de jobs simples.
4. **Redis** — transporte/eventos rápidos: Streams, consumer groups, locks/leases y señalización de workers; no es la memoria canónica.
5. **Hatchet** — ejecución durable para trabajos largos: retries, pasos persistentes, recovery y workers de larga duración.
6. **Dagu** — workflow multi-paso para una tarea programada compleja: dependencias, pequeños DAG/LOOP operativos, pausa y aprobación humana.
7. **PostgreSQL** — fuente durable de verdad para Watchdogs, schedules, runs, checkpoints, idempotencia, outbox y estado.
8. **pgvector** — memoria semántica sobre PostgreSQL para recuperar contexto/conocimiento relevante del trabajo.
9. **gVisor** — aislamiento de sandbox para ejecutar código/herramientas reduciendo el blast radius sobre el host.
10. **S3 compatible / Backblaze B2** — almacenamiento de artefactos, snapshots y workspaces pesados recuperables.

### Separación de responsabilidades

`APScheduler = cuándo` · `Workalendar = si corresponde trabajar` · `Celery = worker simple` · `Redis = transporte rápido` · `Hatchet = durable largo` · `Dagu = multi-paso` · `PostgreSQL = verdad durable` · `pgvector = memoria semántica` · `gVisor = aislamiento` · `S3/B2 = artefactos/snapshots`.

**Flujo horizontal:** `Tarea programada → calendario → scheduler → cola → clasificador → Celery | Hatchet | Dagu → sandbox → agente/modelo → checkpoint → resultado/evidence`.

**Flujo transversal:** `Chat/UI → Watchdog Registry → PostgreSQL → APScheduler → Redis/colas → runtime seleccionado → Memory Orchestrator → sandbox aislado → Sheriff/Judge → checkpoint/recovery → UI event stream`.

**Regla de fallo:** `FAIL ≠ RESET`; localizar → checkpoint → rollback/reparar o fork → reanudar. Se persiste estado operativo verificable; no se guarda chain-of-thought privado.
'''

MEMORY_TEXT = '''# readme-memoria — Watchdog YAIWES

## Propósito
La memoria del Watchdog conserva estado operativo verificable para que una tarea programada sobreviva cierres de chat, fallos de workers y reemplazos de sandbox. No persiste chain-of-thought privado; persiste contratos, entradas, decisiones explícitas, artefactos, evidencia, checkpoints y deltas de estado.

## Capas
`WORKING MEMORY → tarea actual/context pack`

`PERSISTENT MEMORY → conocimiento y estado durable`

`EPISODIC LOG → historial de ejecuciones y decisiones explícitas`

`VERSION GRAPH → branches + checkpoints + artefactos`

`RECOVERY → localizar → rollback/repair/fork → resume`

## Contrato Memory Orchestrator
El Workflow puede solicitar objetos estructurados: `GET_CONTEXT`, `GET_MEMORY`, `GET_EVIDENCE`, `GET_ARTIFACTS`, `GET_STATE`, `GET_HISTORY`, `GET_RELEVANT_RELATIONS`, `AUDIT_MEMORY`, `SAVE_STATE`, `SAVE_ARTIFACT`, `SAVE_CONSOLIDATION`, `CREATE_CHECKPOINT`.

El Memory Orchestrator recupera, rerankea, audita, ensambla y valida contexto; no decide el objetivo global, no modifica instrucciones del usuario, no convierte hipótesis en hechos y no autoriza operaciones peligrosas.

## Persistencia
- **PostgreSQL:** Watchdog, schedule, run, workflow, current_step, checkpoints, idempotency keys, outbox y estado durable.
- **pgvector:** memoria semántica y recuperación por relevancia.
- **Redis:** eventos, consumer groups, locks/leases, cola rápida y heartbeats; no reemplaza la verdad durable.
- **S3 compatible / Backblaze B2:** snapshots, artefactos grandes y workspaces.

## Sandbox y recovery
Cada ejecución recibe un workspace aislado. El sandbox mantiene `heartbeat`; si queda stale, el sistema crea/reasigna un sandbox, carga el último estado durable, remonta el workspace/snapshot, retoma locks con TTL y reanuda desde el último step verificable.

`FAIL ≠ RESET`

`FAIL → LOCALIZE → CHECKPOINT → ROLLBACK → REPAIR/FORK → RESUME`

## Sandbox Fork
Desde un `MASTER CHECKPOINT` pueden abrirse ramas aisladas con la misma policy, task contract, input references y validation schema, pero diferente modelo/estrategia/contexto local. Judge/Sheriff comparan evidencia y promueven una rama a `CANONICAL STATE`; las demás quedan como alternativas o evidencia de fallo.

## Flujo con el Watchdog
`SCHEDULE → WATCHDOG RUN → MEMORY REQUEST → CONTEXT PACK → SANDBOX → AGENT/MODEL → STATE DELTA → AUDIT → CONSOLIDATE → MEMORY UPDATE → CHECKPOINT → NEXT STEP / COMPLETE`

## Paralelismo
El sistema puede fan-out cientos de trabajos pendientes, pero controla concurrencia mediante priority queues, pools especializados, batching, deduplicación, backpressure e idempotencia. Cientos de tareas programadas no significan cientos de procesos sin límite.

## Regla canónica
El modelo piensa y propone; el runtime controla; la memoria recuerda; el sandbox aísla; Sheriff/Judge verifican; el Watchdog programa, despierta, supervisa y reanuda.
'''


def main():
    text = README.read_text(encoding='utf-8')
    if MARKER not in text:
        raise SystemExit('GAP: architecture marker not found')
    README.write_text(text.split(MARKER, 1)[0].rstrip() + '\n\n' + SECTION, encoding='utf-8')

    state = json.loads(STATE.read_text(encoding='utf-8'))
    state['watchdog_programming_system_v2'] = {
        'status': 'PENDING_XRAY_AND_INTEGRATION',
        'task_id': 'YAIWES-WATCHDOG-PROGRAMMING-V2',
        'destination': 'Core kernel Yaiwes/',
        'plan': str(PLAN),
        'memory_doc': str(MEMORY),
        'components': [{'name': n, 'role': r, 'status': 'PENDING'} for n, r in STACK],
        'lanes': {
            'deterministic': 'user strict workflow -> DSL/DAG/schema/system contract -> deterministic execution',
            'adaptive': 'goal -> YAIWES reasoning -> dynamic plan/loops/research -> pre-execution review -> controlled execution',
        },
        'research_pending': [
            'small LOOP/step engines',
            'cascade/waterfall task planning',
            'research engines inside task loop',
            'pre-execution reasoning/replan gate',
            'Claude Cowork/Claude Code concepts',
            'Grok Automations/Grok Bot concepts',
            'open-source UI modules for chat integration',
        ],
        'source_of_truth': 'physical_repo_state',
    }
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    plan = {
        'schema': 'yaiwes.watchdog-programming-plan/v2',
        'status': 'ACTIVE_LOOP',
        'goal': 'Programar y supervisar tareas simples, durables y multi-paso con memoria persistente, sandbox y dos vías de planificación: determinista y adaptativa.',
        'queue': [
            'X-Ray 10 componentes base',
            'investigar motores de LOOP/cascada/research/replan',
            'seleccionar 3 OSS por GAP adicional',
            'investigar UI modular para chat',
            'definir contratos WatchdogTask/Run/Checkpoint/Approval',
            'integrar 1x1 y probar',
            'cablear UniversalPluginBus + health/evidence',
            'cerrar PENDIENTE solo con read-back',
        ],
        'base_components': [{'name': n, 'role': r, 'state': 'PENDING'} for n, r in STACK],
        'acceptance': [
            'schedule persistente y timezone-aware',
            'priority queue y backpressure',
            'simple/durable/multi-step routing',
            'checkpoint + resume + idempotency',
            'sandbox aislado + heartbeat + recovery',
            'memoria operativa estructurada sin chain-of-thought privado',
            'UI con estado, historial, approvals y event stream',
            'evidencia física y tests reales',
        ],
    }
    PLAN.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    MEMORY.write_text(MEMORY_TEXT, encoding='utf-8')


if __name__ == '__main__':
    main()
