---
# LOOP ENGINE — 10 Loops + 16 Razonamiento + 16 Recuperación

## 10 LOOPS PRINCIPALES

```
L1   Goal Lock + Plan
L2   Consensus Plan (3 modelos → Juez)
L3   Asignar Sandbox (round-robin / capacidad)
L4   EXECUTE (Claude Code: escribe código)
L5   VERIFY (Mimo Code: pytest + diff)
L6   REPAIR (Mimo Code: patch si L5 falla)
L7   VALIDATE (Mimo Code: ruff/black/mypy)
L8   Loop repair (L6→L7, max 2 ciclos)
L9   Sentinel + OpenManus watchdog
L10  Juez: 3 simulaciones + baseline write
```

### L1 — Goal Lock + Plan
Input: plantilla del usuario
- Parse: objetivo, planificar, organizar, tareas, metas, propósito, refutaciones
- Goal Lock: hash(objetivo) → workflow_state.goal_hash
- Plan: descomponer objetivo en sub-objetivos atómicos
Output: {goal, plan[], goal_hash}

### L2 — Consensus Plan
- 3 sandboxes (Claude, Mimo, OpenCode) reciben MISMO plan
- Cada uno propone: orden de ejecución, dependencias, riesgos
- Juez compara y elige el plan 2-de-3
- Si los 3 disienten → escala a Director
Output: {consensus_plan, votes, judge_pick}

### L3 — Asignar Sandbox
- Router decide sandbox por sub-tarea
- Criterio: round-robin o capacidad (CPU/RAM libres)
- Circuit breaker: si sandbox tiene 5 fallos → skip, asignar otro
Output: {assignments: {task_id: sandbox_id}}

### L4 — EXECUTE (Claude Code)
- Sandbox Claude recibe: goal + plan + contexto
- Claude escribe código (no ejecuta, solo propone diff)
- Output: {diff, files_changed, rationale}
- Sandbox kill tras timeout (default 300s)

### L5 — VERIFY (Mimo Code)
- Sandbox Mimo recibe: diff de L4
- Ejecuta: pytest, build, smoke tests
- Output: {pass, fail_count, error_log, coverage}
- Si pass=False → trigger L6

### L6 — REPAIR (Mimo Code)
- Sandbox Mimo recibe: diff L4 + error_log L5
- Genera patch mínimo que arregle el error
- Output: {new_diff, fix_description}
- Trigger L7

### L7 — VALIDATE (Mimo Code)
- Sandbox Mimo ejecuta: ruff, black --check, mypy
- Output: {pass, lint_errors[]}
- Si pass=False → vuelve a L6

### L8 — Loop Repair
- Counter repair[node]++
- Si counter < 2 → L6 con nuevo error
- Si counter == 2 → ESCALATE (Telegram + DLQ)

### L9 — Sentinel + OpenManus
- Recolecta métricas: tokens, tiempo, errores, retries
- OpenManus vigila: rate_per_s, ejecuciones por nodo, errores repetidos
- Output: {metrics, alerts, healthy}

### L10 — Juez
- 3 simulaciones:
  - **real**: corre la app/tests con el diff aplicado
  - **adversarial**: fuzzing + inputs maliciosos
  - **regression**: compara con baseline_output.json
- Si 3/3 GO → atomic_write_json(baseline_output.json, ...)
- Output: {simulations, all_passed, baseline_written}

---

## 16 PASOS DE RAZONAMIENTO (R1-R16)

```
R1   Parsear mensaje usuario → extraer goal + constraints
R2   Goal Lock: congelar goal, hashear, persistir
R3   Scope Lock: definir sandbox_id, recursos, timebox
R4   Cargar memoria relevante (último estado del goal similar)
R5   Construir DSL: nodos = agentes/skills/verificadores
R6   Construir DAG: topológico, depends_on explícitos
R7   Validar DAG: nodos existen, gates existen, no ciclos
R8   Asignar sandbox por nodo (round-robin o por capacidad)
R9   Inyectar prompt al sandbox (goal + contexto + skills)
R10  Esperar respuesta o timeout (kill sandbox si excede)
R11  Recolectar output + metadatos (tokens, tiempo, errores)
R12  Validar formato (Validador: required_fields, schema)
R13  Verificar contenido (Verificador: tests/lint/diff)
R14  Si pasa → Juez (3 simulaciones) → FINISH
R15  Si falla → REPAIR (max 2) con feedback específico
R16  Si REPAIR agotado → ESCALATE (Telegram + DLQ) + STOP
```

Nota: R1-R16 se ejecutan UNA vez por goal (no por nodo).
Los nodos individuales solo pasan por R8-R13 (assign + inject + await + collect + validate + verify).

---

## 16 PASOS DE RECUPERACIÓN (F1-F16)

```
F1   Detectar tipo de fallo (sandbox_crash / timeout / gate_fail / verify_fail)
F2   Snapshot del estado actual (workflow_state.json atómico)
F3   Clasificar severidad (low / medium / critical)
F4   Si sandbox_crash → reiniciar contenedor con mismo image
F5   Si timeout → matar proceso, reintentar con timebox × 1.5
F6   Si gate_fail (Sheriff) → loguear, no avanzar
F7   Si verify_fail → extraer mensaje de error del test/lint
F8   Construir prompt de repair: goal + error + diff anterior
F9   Re-inyectar al MISMO sandbox si está sano, sino nuevo
F10  Limpiar artefactos parciales (git stash, archivos temp)
F11  Re-ejecutar nodo con prompt reparado
F12  Re-verificar (Validador + Verificador)
F13  Si pasa → continuar DAG desde ese nodo
F14  Si falla otra vez → incrementar counter repair[node]
F15  Si counter == 2 → escalar (Telegram + DLQ) + STOP
F16  Si counter < 2 → volver a F7 con nuevo error
```

### Diagrama de decisión

```
         ┌─ sandbox_crash ──► F4 ──┐
         │                        │
F1 ──────┼─ timeout       ──► F5 ──┤
         │                        ├──► F8 ──► F9 ──► F10 ──► F11 ──► F12
         ├─ gate_fail     ──► F6 ──┤                                    │
         │                        │                                    ▼
         └─ verify_fail   ──► F7 ──┘                              F13 pass?
                                                                       │
                                                              ┌────────┴────────┐
                                                              │yes              │no
                                                              ▼                 ▼
                                                        continue DAG    F14 counter++
                                                                                │
                                                                       ┌────────┴────────┐
                                                                       │counter<2        │counter==2
                                                                       ▼                 ▼
                                                                  F7 con nuevo err   F15 escalate + STOP
```
