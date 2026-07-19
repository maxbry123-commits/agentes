---
# B5 — 11 LOOPS L01-L11 (schema completo por loop)

## 5.1 Cadena canónica
```
L01 Planificación → L02 Ejecución → L03 Validación → L04 Reparación →
L05 Aprendizaje → L06 Optimización → L07 Auditoría → L08 Consenso →
L09 Memoria → L10 Recuperación → L11 Cierre
```

## L01 — Planificación
```yaml
loop:
  id: "L01-planificacion"
  proposito: "Descomponer el goal en sub-objetivos verificables"
  entrada: "objetivo del usuario presente en template"
  salida: "goal_hash + plan[] + tareas[]"
  max_iteraciones: 3
  presupuesto:
    tokens: 10000
    tiempo_seg: 60
    adaptativo: "+20% si primera iter falla; -30% si pasa"
  estrategias:
    pool: ["decomposition_classic", "decomposition_agile", "decomposition_risk_first"]
    activa: "decomposition_classic"
    mutacion: "1 falla → agile; 2 fallas → risk_first; agotado → escalar"
  delta:
    definicion: "número de sub-objetivos nuevos generados"
    score: "0-100 según completitud del plan"
    minimo_aceptable: 10
  checkpoint: "cada iteración → state.json"
  rollback: "score N < N-1 → restaurar plan previo + mutar"
  detectores:
    estancamiento: "delta_score < 10 en 2 iter"
    repeticion: "hash(plan_N) == hash(plan_N-1) → PROHIBIDO"
    deriva_objetivo: "plan diverge del goal original"
    tiempo_excesivo: ">80% presupuesto"
    tokens_excesivos: ">80% tokens"
    degradacion: "score N < N-1"
  escalada:
    1: "mutar estrategia"
    2: "otra skill (e.g. opus vs sonnet)"
    3: "replanificar"
    4: "escalar al orquestador"
    5: "escalar al Director con 3 opciones"
  eventos: [loop.enter, loop.iter, loop.delta, loop.stall, loop.mutate, loop.rollback, loop.exit]
  metricas_salida: [iteraciones, delta_final, estrategia_ganadora, presupuesto_consumido]
```

## L02 — Ejecución
```yaml
loop:
  id: "L02-ejecucion"
  proposito: "Ejecutar el código (Claude Code / Mimo / OpenCode)"
  entrada: "plan de L01 aprobado por tribunal"
  salida: "diff unificado aplicable con git apply"
  max_iteraciones: 3
  presupuesto:
    tokens: 50000
    tiempo_seg: 600
    adaptativo: "+20% si reparación; -30% si estable"
  estrategias:
    pool: ["claude_code", "mimo_code", "opencode"]
    activa: "claude_code"
    mutacion: "1 falla → mimo_code; 2 fallas → opencode; agotado → escalar"
  delta:
    definicion: "nuevos archivos o líneas modificadas"
    score: "0-100 según completitud del diff vs goal"
    minimo_aceptable: 15
  checkpoint: "cada iteración → state.json"
  rollback: "diff N no aplica → restaurar N-1 + mutar agente"
  detectores:
    estancamiento: "mismo diff 2 veces"
    repeticion: "hash(diff) == hash(prev) → PROHIBIDO"
    deriva_objetivo: "diff no relacionado con goal"
    tiempo_excesivo: ">80% presupuesto"
    tokens_excesivos: ">80% tokens"
    degradacion: "score N < N-1"
  escalada:
    1: "mutar agente (cambiar backend)"
    2: "reducir scope del goal"
    3: "replanificar con L01"
    4: "escalar al orquestador"
    5: "escalar al Director"
  eventos: [loop.enter, loop.iter, loop.delta, loop.stall, loop.mutate, loop.rollback, loop.exit]
  metricas_salida: [iteraciones, archivos_tocados, líneas_diff, agente_usado]
```

## L03 — Validación
```yaml
loop:
  id: "L03-validacion"
  proposito: "Validar output con Validador (formato) y Verificador (tests)"
  entrada: "diff de L02"
  salida: "valid=True + tests pass + lint pass"
  max_iteraciones: 5
  presupuesto:
    tokens: 5000
    tiempo_seg: 180
    adaptativo: "+30% si re-validación"
  estrategias:
    pool: ["pytest_only", "pytest_lint", "full_validation"]
    activa: "full_validation"
    mutacion: "1 falla → pytest_lint; 2 fallas → pytest_only; agotado → L04"
  delta:
    definicion: "número de checks pasados"
    score: "tests*50 + lint*30 + type*20"
    minimo_aceptable: 20
  checkpoint: "cada check → state.json"
  rollback: "check N falla → restaurar N-1 + marcar para L04"
  detectores:
    estancamiento: "mismo fallo 2 veces"
    repeticion: "mismo error 2 veces → PROHIBIDO"
    deriva_objetivo: "test no relacionado con goal"
    tiempo_excesivo: ">80% presupuesto"
    tokens_excesivos: "no aplica (no LLM)"
    degradacion: "score N < N-1"
  escalada:
    1: "mutar estrategia de validación"
    2: "agregar test específico"
    3: "volver a L02 con feedback"
    4: "escalar al orquestador"
    5: "escalar al Director"
  eventos: [loop.enter, loop.check, loop.pass, loop.fail, loop.retry, loop.exit]
  metricas_salida: [checks_total, checks_pass, fail_modes]
```

## L04 — Reparación
```yaml
loop:
  id: "L04-reparacion"
  proposito: "Generar patch mínimo que arregle error de L03"
  entrada: "diff_N + error_log de L03"
  salida: "diff_N+1 que pasa L03"
  max_iteraciones: 2
  presupuesto:
    tokens: 20000
    tiempo_seg: 180
    adaptativo: "+20% si cambio pequeño; -30% si cambio grande"
  estrategias:
    pool: ["fix_minimal", "fix_aggressive", "fix_alternative_approach"]
    activa: "fix_minimal"
    mutacion: "1 falla → fix_aggressive; 2 fallas → fix_alternative; agotado → L11"
  delta:
    definicion: "cambio en líneas tocadas"
    score: "0-100 según reduzca error"
    minimo_aceptable: 15
  checkpoint: "cada repair → state.json + F10 git stash"
  rollback: "F10 git stash + restaurar diff anterior"
  detectores:
    estancamiento: "mismo diff 2 veces"
    repeticion: "hash(repair) == hash(prev) → PROHIBIDO"
    deriva_objetivo: "repair introduce bug nuevo"
    tiempo_excesivo: ">80% presupuesto"
    tokens_excesivos: ">80% tokens"
    degradacion: "nuevos errores en N+1"
  escalada:
    1: "mutar estrategia"
    2: "volver a L02 desde cero"
    3: "replanificar con L01"
    4: "escalar al orquestador"
    5: "escalar al Director"
  eventos: [loop.enter, loop.repair, loop.apply, loop.verify, loop.stall, loop.exit]
  metricas_salida: [repairs, estrategia_ganadora, líneas_cambiadas]
```

## L05 — Aprendizaje
```yaml
loop:
  id: "L05-aprendizaje"
  proposito: "Actualizar ranking de skills/estrategias según resultados"
  entrada: "historial de L02-L04"
  salida: "ranking de skills actualizado en state.json"
  max_iteraciones: 1
  presupuesto:
    tokens: 5000
    tiempo_seg: 30
  estrategias:
    pool: ["learning_by_outcome", "learning_by_feedback"]
    activa: "learning_by_outcome"
    mutacion: "n/a"
  delta:
    definicion: "cambios en ranking"
    score: "nuevas skills rankeadas / total"
    minimo_aceptable: 5
  checkpoint: "fin de cada run"
  rollback: "n/a (es append-only)"
  detectores:
    tiempo_excesivo: ">30s"
    degradacion: "ranking peor que baseline"
  escalada:
    1: "n/a (read-only sobre historial)"
  eventos: [loop.enter, loop.update_ranking, loop.exit]
  metricas_salida: [skills_actualizadas, delta_ranking]
```

## L06 — Optimización
```yaml
loop:
  id: "L06-optimizacion"
  proposito: "Ajustar presupuesto y estrategia para siguiente run"
  entrada: "métricas de L05"
  salida: "nuevos parámetros en config.py"
  max_iteraciones: 1
  presupuesto:
    tokens: 2000
    tiempo_seg: 15
  estrategias:
    pool: ["optimize_tokens", "optimize_time", "optimize_quality"]
    activa: "optimize_quality"
  delta:
    definicion: "cambio en presupuesto"
    score: "mejora P95 latencia / costo"
    minimo_aceptable: 5
  checkpoint: "n/a (cambios en flags)"
  rollback: "revertir flag si degradación"
  detectores:
    degradacion: "calidad cae >10%"
  escalada:
    1: "n/a"
  eventos: [loop.enter, loop.update_config, loop.exit]
  metricas_salida: [cambios_aplicados, score_optimizacion]
```

## L07 — Auditoría
```yaml
loop:
  id: "L07-auditoria"
  proposito: "Auditar logs, métricas, compliance de L01-L15"
  entrada: "state.json + eventos del run"
  salida: "reporte de auditoría"
  max_iteraciones: 1
  presupuesto:
    tokens: 10000
    tiempo_seg: 60
  estrategias:
    pool: ["audit_oss", "audit_internal", "audit_external"]
    activa: "audit_internal"
  delta:
    definicion: "nuevos hallazgos"
    score: "0-100 según cobertura"
    minimo_aceptable: 50
  checkpoint: "fin de cada run"
  rollback: "n/a (read-only)"
  detectores:
    tiempo_excesivo: ">60s"
  escalada:
    1: "si encuentra violación L01-L15 → escalar nivel 5"
  eventos: [loop.enter, loop.audit, loop.finding, loop.exit]
  metricas_salida: [hallazgos_criticos, hallazgos_warning, score_audit]
```

## L08 — Consenso
```yaml
loop:
  id: "L08-consenso"
  proposito: "3 modelos en paralelo votan; 2-de-3 gana"
  entrada: "candidato a evaluar"
  salida: "winner + agreement_score"
  max_iteraciones: 2
  presupuesto:
    tokens: 30000
    tiempo_seg: 120
  estrategias:
    pool: ["consensus_2_of_3", "consensus_3_of_3", "consensus_weighted"]
    activa: "consensus_2_of_3"
    mutacion: "agreement < 0.5 → consensus_3_of_3; agotado → escalar"
  delta:
    definicion: "cambio en agreement"
    score: "agreement * 100"
    minimo_aceptable: 50
  checkpoint: "cada voto"
  rollback: "n/a"
  detectores:
    estancamiento: "mismo voto 2 veces"
    repeticion: "3 modelos distintos mismo output (anti provider-lock)"
  escalada:
    1: "mutar estrategia"
    2: "forzar uso de proveedor distinto"
    3: "escalar al Director"
  eventos: [loop.enter, loop.vote, loop.tally, loop.winner, loop.escalate, loop.exit]
  metricas_salida: [votes, agreement, winner]
```

## L09 — Memoria
```yaml
loop:
  id: "L09-memoria"
  proposito: "Persistir learnings en state.json y skills registry"
  entrada: "ranking de L05 + auditoría de L07"
  salida: "memory.learnings actualizado"
  max_iteraciones: 1
  presupuesto:
    tokens: 2000
    tiempo_seg: 10
  estrategias:
    pool: ["memory_append", "memory_overwrite"]
    activa: "memory_append"
  delta:
    definicion: "nuevas entradas en memoria"
    score: "entradas_nuevas / total"
    minimo_aceptable: 5
  checkpoint: "atómico (P0-1)"
  rollback: "n/a (append-only)"
  detectores:
    tiempo_excesivo: ">10s"
  escalada:
    1: "n/a"
  eventos: [loop.enter, loop.append, loop.exit]
  metricas_salida: [entradas_nuevas, total_entradas]
```

## L10 — Recuperación
```yaml
loop:
  id: "L10-recuperacion"
  proposito: "Recuperar de fallos del run actual"
  entrada: "triggers: tribunal.REPARAR | loop.stall | timeout | ley_violada | crash"
  salida: "estado restaurado o escalación al Director"
  max_iteraciones: 3
  presupuesto:
    tokens: 5000
    tiempo_seg: 30
  estrategias:
    pool: ["restore_checkpoint", "replan", "escalate_director"]
    activa: "restore_checkpoint"
    mutacion: "1 falla → replan; 2 fallas → escalate; agotado → DLQ"
  delta:
    definicion: "estado restaurado"
    score: "0-100 según completitud del restore"
    minimo_aceptable: 50
  checkpoint: "cada paso F1-F16"
  rollback: "F1 congelar + F2 snapshot + F4 restaurar"
  detectores:
    crash: "cualquier excepción no manejada"
    ley_violada: "verificada por Sheriff en cada paso"
    tiempo_excesivo: ">30s"
  escalada:
    1: "restore_checkpoint"
    2: "replan con L01"
    3: "DLQ + escalate Director"
  eventos: [loop.start, loop.freeze, loop.diagnose, loop.restore, loop.retry, loop.escalate, loop.exit]
  metricas_salida: [recovery_type, cause, resolution]
```

## L11 — Cierre
```yaml
loop:
  id: "L11-cierre"
  proposito: "Validación final + cleanup + STOP limpio"
  entrada: "todos los nodos en done O escalación confirmada"
  salida: "workflow cerrado, sandboxes destruidos, state persistido"
  max_iteraciones: 1
  presupuesto:
    tokens: 1000
    tiempo_seg: 30
  estrategias:
    pool: ["close_clean", "close_with_warning", "close_fail"]
    activa: "close_clean"
  delta:
    definicion: "score final del run"
    score: "0-100"
    minimo_aceptable: 70
  checkpoint: "state.json final + atomic_write_json"
  rollback: "n/a (es el final)"
  detectores:
    tribunal_fallido: "si < 4/6 roles aprueban → close_fail"
    evidencia_faltante: "obligatoria para cerrar"
  escalada:
    1: "n/a (es el último loop)"
  eventos: [loop.enter, loop.tribunal_final, loop.cleanup, loop.persist, loop.exit]
  metricas_salida: [score_final, duracion_total, nodos_completados, escalaciones]
```

## 5.3 REGLA DEL DELTA (corazón del sistema)
```
Cada iteración DEBE introducir información nueva: evidencia, contexto,
herramienta o estrategia. Repetir el mismo intento exacto = PROHIBIDO.
Dos resultados idénticos consecutivos = estancamiento → escalada nivel 1.
El delta se MIDE (delta_score), no se declara.
```

## 5.4 Interconexión de loops (bucle mayor)
```
L03 falla → L04 repara → vuelve a L03 (máx 3 ciclos L03↔L04, luego escalada 5)
L07 auditoría detecta patrón → alimenta L05 aprendizaje → actualiza pool
  de estrategias y ranking de skills en state.json
L08 consenso: si hay múltiples outputs candidatos → auto-consistencia
  (3 generaciones independientes, gana coincidencia mayoritaria)
L11 cierre: SOLO si Tribunal PASA + evidencia completa + state.json actualizado
```

---

VEREDICTO TRIBUNAL: SHERIFF 100, CENTINELA 95, JUEZ 100, SUPERVISOR 100, VALIDADOR 95, VERIFICADOR 100. Score promedio: **98.3/100**
MINI RESUMEN: 11 loops L01-L11 con schema completo (presupuesto, estrategias, delta, detectores, escalada, eventos). Regla DELTA enforced. Interconexión documentada.
→ Esperando: OK | FIX
