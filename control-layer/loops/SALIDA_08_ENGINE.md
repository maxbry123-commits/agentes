# Salida 8/12 — LoopEngine

## Entregado
`engine.py` — start · run_iteration
Wire: StateMachine → PhaseRunner/Sheriff → PolicyEngine → RecoveryEngine → Memory/Graph plugins (NoOp)

## Flujo 1 iteración
CREATED→LOCKED→RUNNING → 9 phases → VALIDATING → DECIDING → recovery → terminal|RUNNING

## Fase 2 núcleo engine CERRADA (5–8)

## Siguiente (9/12) Fase 3
ProgressEvaluator + Adaptive Iteration (ligero)
