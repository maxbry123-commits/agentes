# P0 mejoras cerradas

## Hecho
1. BudgetGovernor.charge en cada iteración → detectors automáticos
2. ProgressEvaluator + AdaptiveIteration → stall/no_progress + override policy
3. RiskEngine + HumanGate → high risk PAUSED
4. StrategyMemory.suggest_strategy en start
5. StrategyMemory.record al cerrar
6. ResultCache L2 por fingerprint
7. Idempotency_key dedup
8. memory.checkpoint al cerrar
9. persist.JsonlStore (JSONL listo)

## Archivos
- engine.py (rewire)
- persist.py
- tests/test_engine_p0.py

Score implementación: ~7.5/10 (antes 6)
