# SALIDA W03 — Policy DSL + Recovery 11

**Estado: CERRADA 100%**

## Policy DSL
| Archivo | Rol |
|---------|-----|
| `loops/policy/engine.py` | eval rules → PolicyDecision |
| `loops/policy/default_policy.yaml` | reglas base YAML |

- Input: detectors + progress + budget + risk
- Output: `PolicyDecision{action, reason, params}`
- 0% LLM en el path de decisión

## RecoveryEngine (`loops/recovery.py`)

**11+ acciones:**
RETRY · REPAIR · REFRAME · CHANGE_STRATEGY · CHANGE_MODEL · CHANGE_AGENT · REDUCE_SCOPE · ROLLBACK · ISOLATE · CHECKPOINT · ESCALATE · ABORT

(+ CONTINUE / CLOSE / HUMAN_GATE vía policy)

| Acción | next_state típico |
|--------|-------------------|
| RETRY | RUNNING |
| REPAIR | REPAIRING |
| CHANGE_* / REFRAME / REDUCE / ISOLATE | RUNNING |
| ROLLBACK / CHECKPOINT | CHECKPOINT |
| HUMAN_GATE | PAUSED |
| ESCALATE | ESCALATED |
| ABORT | FAILED |
| CLOSE | CLOSED |

**Regla:** `repair_count >= retry_budget` → ESCALATE automático.

## Siguiente
**W04** — Engine A–F (adapter, progress, MHYTOS, bootstrap loops)
