# D2 · state.json — Salida investigación

## Fuentes
- Vercel workflow: pending|running|completed|failed|cancelled + runId, updatedAt
- LangGraph checkpoints: thread_id, checkpoint_id, values, next[], parentConfig (resume)
- Mastra: shared stateSchema vs per-step subset
- Temporal/Dapr: workflow state ≠ conversation memory (dos stores)
- AWS Step Functions / coinbase step: Retry, Catch → RecoveryState; Fail vs Succeed terminal
- governance global_state: schema_version, system_status, active_sections, blocking_reason
- XState/Stately: máquina decide transiciones legales; modelo solo elige eventos permitidos
- UOOS RT: pending→running→validating→done|failed→recovered

## Gaps plantilla previa
1. Sin schema_version / version monotónica
2. Sin run_id / session_id / workflow_id
3. active_tasks sin status enum cerrado ni agent_id
4. Sin allowed transitions documentadas
5. Sin last_error / recovery_pointer
6. Mezcla riesgo con definiciones (ya corregido: solo runtime)

## Principios 100×
- state.json = snapshot vivo; NUNCA agent definitions
- Enums cerrados; transiciones ilegales = Sheriff reject
- failed → recovered → running; NUNCA failed → done
- checkpoint_id opcional para resume
- updated_at ISO obligatorio en cada mutación
