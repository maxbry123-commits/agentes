# N21 Dagu — PASO 1 X-Ray (GROK) 2026-09-10T11:27Z

lock: CLAIMED owner=GROK current_step=1 status=PENDING_STEP1_MOVE
contrato: YAIWES-INTEGRATION-3-STEPS
watchdog_hourly: 185067ee-2602-45ea-8491-4b37287f25d1 next=2026-09-10T12:00:00Z

## ANALYZE_CLASSIFY
- runtime: Go single-binary workflow engine (dagu start-all)
- entrypoint: cmd + engine/executor
- IO: DAG YAML in → shell/docker/k8s/ssh steps out; run history local files
- deps: no external DBMS/broker
- state: local file history, retries, cron
- capability: schedule + DAG + workers
- ABC: **B** (workflow/DAG/scheduler/workers/loop)

## DESTINO
- `Agente Yaiwes principal/execution-orchestration/state-machine-executor/dagu/`
- parent EXISTS; dest dagu/ ABSENT → MOVE required

## MOVE
- Motor4 blob lock `9a21facfe11327cf60a2afca8f415ad52f0ecbe5`
- GAP_MOTOR4: `motor_4_move_batches.py` not in main
- do not reuse yaiwes-3step-move.yml as Motor4

## NOT DONE
- no PASO 2 (FABLES pending) / no PASO 3 / no RELEASE / no PASS
