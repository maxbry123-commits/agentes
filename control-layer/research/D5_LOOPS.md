# D5 · loops — Investigación

## Fuentes
- UOOS L01–L11 + regla del delta
- Agent patterns: self-correct → fallback → degrade → escalate
- Circuit breaker: CLOSED/OPEN/HALF_OPEN
- max_iter + stall detection (hash identical 2×)
- budgets tokens/time fijos (no ML adaptativo)

## Skills transforms
1. parse_loop_yaml
2. validate_loop_schema
3. delta_score_gate (min_aceptable)
4. stall_detector (hash)
5. escalate_level (1..5)
