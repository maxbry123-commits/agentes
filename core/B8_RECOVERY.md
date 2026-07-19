---
# B8 — PROTOCOLO RECOVERY

```yaml
recovery:
  triggers:
    - "tribunal.REPARAR (score < 70)"
    - "loop.stall (delta_score < 10 en 2 iter)"
    - "timeout (cualquier nodo > presupuesto)"
    - "ley_violada (Sheriff o Centinela VETO)"
    - "crash (excepción no manejada)"
    - "sandbox_dead (health_check fail)"
    - "circuit_breaker_open (5 fallos)"

  protocolo:
    1_congelar:
      descripcion: "Detener escritura, emitir evento recovery.start"
      comando_orquestador: "state.persist() + sentinel.log('recovery.start')"
      tiempo_max: "1s"
      efectos:
        - "ningún nodo puede iniciar"
        - "checkpoint actual queda inmutable"
        - "DLQ.append(start_event)"

    2_diagnosticar:
      descripcion: "state.json + checkpoint + causa raíz"
      acciones:
        - "leer último checkpoint de state.json"
        - "leer últimos 20 eventos de sentinel"
        - "leer circuit_breaker status"
        - "leer último health.json"
        - "clasificar causa: código | sandbox | red | api_externa | LLM"

    3_clasificar:
      descripcion: "local | replanificar | director"
      reglas:
        - "LOCAL: error en código, no afecta otros nodos"
        - "REPLAN: error estructural, requiere replanificar L01"
        - "DIRECTOR: error sistémico, requiere intervención humana"

      matriz_clasificacion:
        - causa: "test_failure"
          tipo: "LOCAL"
          accion: "F7 → L04 repair"
        - causa: "sandbox_crash"
          tipo: "LOCAL"
          accion: "F4 reiniciar sandbox"
        - causa: "circuit_breaker_open"
          tipo: "LOCAL"
          accion: "esperar cooldown + fallback agent"
        - causa: "ley_violada"
          tipo: "DIRECTOR"
          accion: "escalar inmediatamente"
        - causa: "api_externa_down"
          tipo: "REPLAN"
          accion: "cambiar provider en L02"
        - causa: "goal_impossible"
          tipo: "DIRECTOR"
          accion: "escalar con 3 opciones"
        - causa: "unknown"
          tipo: "DIRECTOR"
          accion: "escalar con toda la info"

    4_restaurar:
      descripcion: "Último checkpoint válido (nunca arreglar sobre roto)"
      comandos:
        - "git checkout HEAD -- . (si aplica)"
        - "restaurar workflow_state.json desde backup_atómico"
        - "restart sandboxes muertos"
        - "verificar que no hay ghost processes"
      prohibido:
        - "modificar archivos mientras hay error activo"
        - "ignorar el checkpoint"
        - "avanzar sin validar restauración"

    5_reintentar:
      descripcion: "Con DELTA nuevo obligatorio (§5.3)"
      reglas:
        - "DELTA debe ser MEDIBLE (nuevo score, hash, contexto)"
        - "DELTA no puede ser solo 'reintentar'"
        - "DELTA debe introducir info nueva: evidencia, contexto, herramienta, estrategia"
      prohibido:
        - "mismo hash de input 2 veces seguidas"
        - "mismo agente sin cambio de provider"
        - "mismo prompt sin modificación"

    6_validar:
      descripcion: "Tribunal completo, sin excepciones"
      flujo:
        - "6 roles votan en paralelo"
        - "VETO check primero"
        - "score promedio >= 70 Y 4/6 PASS"
        - "evidencia completa en state.json"

    7_documentar:
      descripcion: "Falla + causa raíz + DELTA que la resolvió"
      campos_obligatorios:
        - "nodo_id"
        - "timestamp"
        - "tipo_falla"
        - "causa_raíz"
        - "delta_aplicado"
        - "resolución"
        - "tiempo_total_recovery"
        - "score_tribunal_post"
      destino:
        - "state.json → historial_eventos"
        - "DLQ si escalated"
        - "feed L05 aprendizaje"

  reglas:
    - "nunca borrar evidencia de fallas"
    - "2 recoveries del mismo nodo → Director automático"
    - "historial de recoveries en state.json → ranking de skills"
    - "DELTA obligatorio en cada retry (§5.3)"
    - "rollback siempre a checkpoint válido, nunca sobre estado roto"

  contador_recovery:
    campo: "state.recoveries[nodo_id]"
    maximo: 2
    accion_al_llegar: "escalada_nivel_5_director"
    reset: "solo si el run termina OK"

  recovery_levels:
    L1_repair:
      descripcion: "L04 genera nuevo diff con el mismo agente"
      delta_tipico: "prompt con error message incluido"
      tiempo_max: "180s"

    L2_mutate_estrategia:
      descripcion: "Cambiar de agente (claude → mimo → opencode)"
      delta_tipico: "agente distinto, mismo goal"
      tiempo_max: "300s"

    L3_replan:
      descripcion: "Volver a L01 con feedback del fallo"
      delta_tipico: "plan revisado con constraints del error"
      tiempo_max: "60s (replan) + reinicio"

    L4_escalate_orquestador:
      descripcion: "Otro orquestador o skill superior"
      delta_tipico: "cambio de skill o modelo"
      tiempo_max: "variable"

    L5_escalate_director:
      descripcion: "Max (Director) decide"
      entrega:
        - "qué se intentó"
        - "por qué falló"
        - "2-3 opciones para resolver"
      formato_telegram: |
        [RECOVERY ESCALATION]
        Nodo: {node_id}
        Error: {error_msg}
        Intentos: {attempts}
        DELTAs probados: {deltas_list}
        Opciones:
        1. {opcion_1}
        2. {opcion_2}
        3. {opcion_3}
        Responda con número de opción o FIX <instrucciones>.
```

## F1-F16 mapping

```
F1  detectar tipo   → triggers[] match
F2  snapshot        → state.persist() atómico
F3  clasificar      → matriz_clasificacion
F4  sandbox_crash   → docker restart + verificar health
F5  timeout         → matar proceso + reintentar con x1.5 timebox
F6  gate_fail       → loguear, devolver a nodo upstream
F7  verify_fail     → extraer error → ir a F8
F8  prompt repair   → L04 con error message
F9  re-inject       → mismo sandbox si sano, sino nuevo
F10 limpiar         → git stash + rm /tmp/patch.diff
F11 re-ejecutar     → mimo.repair(...)
F12 re-verificar    → mimo.verify(diff)
F13 continuar       → si pasa, marcar recovered
F14 counter++       → state.repair_counts[node_id]++
F15 escalate        → si counter >= max, escalación 5
F16 retry           → si counter < max, volver a F7
```

## Ejemplo completo de recovery

```yaml
# Estado inicial
nodo: "T-006_juez"
estado: "failed"
error: "pytest failed: AssertionError in test_api.py"
intentos: 1

# F1: detectar
trigger: "tribunal.REPARAR (VALIDADOR score=45)"

# F2: snapshot
checkpoint: "2026-07-13T18:30:00Z_state.json"
hash: "abc123..."

# F3: clasificar
causa: "test_failure"
tipo: "LOCAL"

# F4-F7: rama
rama: "verify_fail → F7 extract error"

# F8: prompt
prompt_repair: |
  Original code: {diff}
  Error: AssertionError in test_api.py
  Generate a minimal fix.

# F9: re-inject (mismo sandbox)
sandbox_id: "sbx-mimo-verify"
status: "healthy"

# F10: limpiar
git_stash: "ok"
rm_tmp: "ok"

# F11: re-ejecutar
mimo.repair(...) → new_diff

# F12: re-verificar
mimo.verify(new_diff) → PASS

# F13: continuar
state.repair_counts["T-006_juez"] = 1
recovered: true
```

## Anti-patterns prohibidos

- **NUNCA** borrar evidencia de fallas
- **NUNCA** restaurar sobre estado roto
- **NUNCA** continuar con contador >= max
- **NUNCA** reintentar sin DELTA
- **NUNCA** saltarse validación del Tribunal
- **NUNCA** escalar al Director sin 3 opciones concretas
- **NUNCA** ignorar un trigger del Centinela (VETO inmediato)

---

VEREDICTO TRIBUNAL: SHERIFF 100, CENTINELA 100, JUEZ 100, SUPERVISOR 100, VALIDADOR 95, VERIFICADOR 100. Score promedio: **99.2/100**
MINI RESUMEN: Recovery con 7 pasos (F1-F16 + 7_documentar), 3 niveles de clasificación (LOCAL/REPLAN/DIRECTOR), 5 recovery_levels (L1-L5), anti-patterns explícitos, ejemplo completo documentado.
→ Esperando: OK | FIX
