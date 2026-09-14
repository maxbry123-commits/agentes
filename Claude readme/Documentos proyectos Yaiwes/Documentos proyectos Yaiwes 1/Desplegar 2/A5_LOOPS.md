# A5_LOOPS.md — B5 (UOOS v2.0)

Los 11 loops completos, sin reducción. Cadena canónica:
`L01→L02→L03→L04→L05→L06→L07→L08→L09→L10→L11`.

**Presupuesto de tokens:** el único punto que consume tokens reales de LLM
es G2/G3 dentro de T-005 (leer la guía oficial de instalación de CUALQUIER
software). Todo lo demás es determinista, presupuesta tiempo/reintentos, no tokens.

---

```yaml
loop:
  id: "L01-planificacion"
  proposito: "Seleccionar la ESTRATEGIA de ejecución del nodo activo
              cuando existe más de una válida (ej. método de adquisición
              del pool de T-006 según el source_type resuelto), sin
              redefinir el DAG ni el goal del nodo."
  entrada: "Recipe compilada (T-005) + nodo activo con >1 estrategia posible"
  salida: "plan_ejecucion = {estrategia_primaria, orden_de_fallback}"
  max_iteraciones: 1
  presupuesto: {tokens: 5000, tiempo_seg: 60, adaptativo: "no aplica"}
  estrategias:
    pool: ["según recipe.source_type: git_native | github_api | archive
            | hf_hub | release_binary | package_manager"]
    activa: "la de mayor ranking histórico (L05) para ese source_type"
    mutacion: "no muta aquí — ocurre en L04/L05 si falla en ejecución"
  delta: {definicion: "no aplica (1 iteración)", score: "N/A", minimo_aceptable: "N/A"}
  checkpoint: "plan_ejecucion persistido en state.json"
  rollback: "N/A — sin estrategia válida, escalada directa a RT-80"
  detectores:
    estancamiento: "N/A"
    repeticion: "N/A"
    deriva_objetivo: "plan_ejecucion no coincide con recipe.source_type → replanificar"
    tiempo_excesivo: ">80% de 60s → escalar"
    tokens_excesivos: ">80% de 5000 → comprimir y forzar decisión"
    degradacion: "N/A"
  escalada: {1: "estrategia por defecto de tabla fija", 2: "N/A", 3: "N/A",
             4: "escalar al orquestador", 5: "escalar al Director"}
  eventos: [loop.enter, loop.exit]
  metricas_salida: [estrategia_elegida, tiempo_usado]
```

```yaml
loop:
  id: "L02-ejecucion"
  proposito: "Ejecutar el nodo T-XXX activo con la estrategia de L01."
  entrada: "plan_ejecucion válido + nodo en running"
  salida: "output conforme al contrato.output.schema"
  max_iteraciones: 5
  presupuesto:
    tokens: "0 salvo cuando el nodo activo es T-005 (G2/G3) → 40000"
    tiempo_seg: "según timeout_seg del nodo (A3)"
    adaptativo: "delta_score sube 2 iter → +20% presupuesto; baja → -30% y evaluar salida"
  estrategias:
    pool: ["estrategia_primaria de L01", "fallback_1", "fallback_2"]
    activa: "estrategia_primaria"
    mutacion: "detector activado → rotar; pool agotado → escalar nivel 3"
  delta:
    definicion: "avance verificable = subgoal completado del nodo (A3)"
    score: "0-100 contra criterio_exito del contrato"
    minimo_aceptable: 10
  checkpoint: "cada iteración → state.json.nodos.T-XXX.checkpoint"
  rollback: "iteración N empeora vs N-1 → restaurar N-1 + mutar estrategia"
  detectores:
    estancamiento: "delta_score < 10 en 2 iter consecutivas"
    repeticion: "hash(intento_N)==hash(anterior) → PROHIBIDO, fuerza mutación"
    deriva_objetivo: "output diverge del contrato → L01"
    tiempo_excesivo: ">80% presupuesto → checkpoint + decidir"
    tokens_excesivos: ">80% (solo T-005) → comprimir o escalar"
    degradacion: "score_tribunal baja → rollback + mutación"
  escalada: {1: "mutar estrategia (pool L01)", 2: "solicitar skill/adapter
             equivalente en registry", 3: "replanificar → L01",
             4: "escalar al orquestador",
             5: "escalar al Director: qué se intentó, por qué falló, 2-3 opciones"}
  eventos: [loop.enter, loop.iter, loop.delta, loop.stall, loop.mutate, loop.rollback, loop.exit]
  metricas_salida: [iteraciones_usadas, delta_final, estrategia_ganadora, presupuesto_consumido]
```

```yaml
loop:
  id: "L03-validacion"
  proposito: "Pasar el output por el Tribunal (A6) en los 3 puntos
              críticos, no en los 12 nodos completos por sistema."
  entrada: "output + evidencia SOLO en: post-T-005 (Recipe), pre-T-009
            (antes de promover/publicar), post-T-009 (antes de cerrar PR)"
  salida: "veredicto Tribunal: PASA (score≥70 y 4/6 roles) o FALLA"
  max_iteraciones: 3
  presupuesto: {tokens: 0, tiempo_seg: 300, adaptativo: "no aplica"}
  estrategias: {pool: ["N/A — el Tribunal solo evalúa"], activa: "N/A", mutacion: "N/A"}
  delta: {definicion: "diferencia de score entre validación N y N-1", score: "0-100", minimo_aceptable: 70}
  checkpoint: "cada veredicto → state.json.nodos.T-XXX.score_tribunal"
  rollback: "FALLA → L04 (máx 3 ciclos L03↔L04, luego escalada 5)"
  detectores:
    estancamiento: "3 vetos consecutivos del mismo rol → escalada 5 directa"
    repeticion: "N/A"
    deriva_objetivo: "N/A"
    tiempo_excesivo: ">80% de 300s → escalar"
    tokens_excesivos: "N/A"
    degradacion: "score cae entre ciclos de reparación → escalada 5"
  escalada: {1: "N/A", 2: "N/A", 3: "devolver a L04 con causa exacta",
             4: "escalar tras 3 ciclos L03↔L04", 5: "escalar al Director"}
  eventos: [loop.enter, node.validate, loop.exit]
  metricas_salida: [score_final, roles_aprobaron, ciclos_reparacion_usados]
```

```yaml
loop:
  id: "L04-reparacion"
  proposito: "Reintentar un nodo que falló L03, con DELTA obligatorio."
  entrada: "node.failed o Tribunal FALLA"
  salida: "nodo pasa a done vía nuevo intento, o escalada 5"
  max_iteraciones: "según retry.max del nodo (A3, típico 2-3)"
  presupuesto: {tokens: 0, tiempo_seg: "timeout_seg × retry.max",
                adaptativo: "cada retry reduce 20% el presupuesto restante"}
  estrategias:
    pool: ["limpiar estado de dependencias generado (node_modules/.venv/
            vendor/target/etc. según el toolchain que declare la Recipe)
            y reintentar misma estrategia", "rotar a siguiente estrategia
            del pool de L02", "solicitar decisión del Director vía ASK_COUNCIL"]
    activa: "la primera del pool"
    mutacion: "cada intento fallido rota a la siguiente"
  delta:
    definicion: "qué cambió respecto al intento anterior (ej: intento 1
                 falló por lockfile desincronizado → intento 2 limpia el
                 estado de dependencias del toolchain correspondiente
                 antes de reinstalar — el toolchain concreto lo define
                 la Recipe, no está fijo a ningún lenguaje). Un retry que
                 repite el comando exacto sin cambio = PROHIBIDO."
    score: "0-100, mide si el delta resolvió la causa raíz"
    minimo_aceptable: 10
  checkpoint: "cada intento → state.json.nodos.T-XXX.intentos + recoveries"
  rollback: "restaurar último checkpoint limpio ANTES del intento fallido"
  detectores:
    estancamiento: "2 intentos con delta_score < 10 → escalada nivel 3"
    repeticion: "hash(intento_N)==hash(N-1) → PROHIBIDO, aborta el intento"
    deriva_objetivo: "el fix no ataca la causa raíz reportada → L01"
    tiempo_excesivo: ">80% del presupuesto acumulado → checkpoint + decidir"
    tokens_excesivos: "N/A"
    degradacion: "score empeora tras el 'fix' → rollback inmediato"
  escalada: {1: "mutar estrategia (siguiente del pool)", 2: "solicitar
             skill/adapter equivalente", 3: "replanificar → L01",
             4: "escalar al orquestador",
             5: "escalar al Director (2do recovery del mismo nodo = automático nivel 5)"}
  eventos: [loop.enter, loop.iter, loop.delta, loop.rollback, loop.exit, node.recovered]
  metricas_salida: [intentos_usados, causa_raiz, delta_que_resolvio]
```

```yaml
loop:
  id: "L05-aprendizaje"
  proposito: "Actualizar el ranking de estrategias del pool (adquisición
              de CUALQUIER source_type: git nativo → GitHub API → archive,
              hf_hub, release_binary, package_manager) según qué ganó en
              misiones pasadas, para que L01 futuras decidan mejor."
  entrada: "loop.exit de cualquier L02/L04 con estrategia_ganadora registrada"
  salida: "state.json.rankings actualizado (global, no solo de esta misión)"
  max_iteraciones: 1
  presupuesto: {tokens: 0, tiempo_seg: 30, adaptativo: "no aplica"}
  estrategias: {pool: ["N/A — este loop rankea, no ejecuta"], activa: "N/A", mutacion: "N/A"}
  delta: {definicion: "cambio en el ranking vs estado anterior", score: "N/A", minimo_aceptable: "N/A"}
  checkpoint: "rankings persistidos en registro global"
  rollback: "N/A"
  detectores: {estancamiento: "N/A", repeticion: "N/A", deriva_objetivo: "N/A",
               tiempo_excesivo: ">80% de 30s → abortar sin bloquear la misión",
               tokens_excesivos: "N/A", degradacion: "N/A"}
  escalada: {1: "N/A", 2: "N/A", 3: "N/A", 4: "N/A",
             5: "solo si el registro global está corrupto → Director"}
  eventos: [loop.enter, loop.exit]
  metricas_salida: [ranking_actualizado, estrategia_promovida]
```

```yaml
loop:
  id: "L06-optimizacion"
  proposito: "Ajustar presupuesto adaptativo (tiempo/reintentos) de los
              nodos largos (T-006, T-008) según tendencia de delta_score
              histórico, por source_type, no por un software particular."
  entrada: "métricas acumuladas de L02 de misiones previas del mismo source_type"
  salida: "presupuesto ajustado para la próxima ejecución de ese tipo de nodo"
  max_iteraciones: 1
  presupuesto: {tokens: 0, tiempo_seg: 30, adaptativo: "no aplica (este loop AJUSTA presupuestos)"}
  estrategias: {pool: ["N/A"], activa: "N/A", mutacion: "N/A"}
  delta: {definicion: "diferencia entre presupuesto sugerido nuevo vs anterior", score: "N/A", minimo_aceptable: "N/A"}
  checkpoint: "presupuestos base actualizados en registro global"
  rollback: "si el ajuste degrada el éxito histórico → revertir"
  detectores: {estancamiento: "N/A", repeticion: "N/A", deriva_objetivo: "N/A",
               tiempo_excesivo: "N/A", tokens_excesivos: "N/A",
               degradacion: "tasa de éxito baja tras el ajuste → revertir"}
  escalada: {1: "revertir ajuste", 2: "N/A", 3: "N/A", 4: "N/A",
             5: "Director si la degradación persiste 3 misiones"}
  eventos: [loop.enter, loop.exit]
  metricas_salida: [presupuesto_anterior, presupuesto_nuevo, justificacion]
```

```yaml
loop:
  id: "L07-auditoria"
  proposito: "Analizar el journal.jsonl de TODAS las misiones (cualquier
              software) para detectar patrones recurrentes de falla y
              alimentar a L05."
  entrada: "cierre de cada misión (T-011 done) → dispara análisis diferido"
  salida: "reporte de patrones + actualización del pool vía L05"
  max_iteraciones: 1
  presupuesto: {tokens: 0, tiempo_seg: 120, adaptativo: "no aplica"}
  estrategias: {pool: ["N/A"], activa: "N/A", mutacion: "N/A"}
  delta: {definicion: "patrones nuevos vs histórico conocido", score: "N/A", minimo_aceptable: "N/A"}
  checkpoint: "reporte persistido en registro global de patrones"
  rollback: "N/A"
  detectores: {estancamiento: "N/A", repeticion: "mismo patrón 3+ veces
               → prioridad alta en L05", deriva_objetivo: "N/A",
               tiempo_excesivo: ">80% de 120s → truncar, continuar con lo procesado",
               tokens_excesivos: "N/A", degradacion: "N/A"}
  escalada: {1: "N/A", 2: "N/A", 3: "N/A", 4: "N/A",
             5: "patrón crítico repetido (ej. una fuente falla siempre en
                 SECRET_SCAN) → reportar al Director"}
  eventos: [loop.enter, loop.exit]
  metricas_salida: [patrones_detectados, nodos_afectados, alimenta_L05]
```

```yaml
loop:
  id: "L08-consenso"
  proposito: "NO es consenso de generaciones LLM (LLM_CONTROL=DENY). Es
              VERIFICACIÓN REDUNDANTE — resolver 3 veces, de forma
              independiente, la determinación más crítica y ambigua de
              Discovery (ref→commit, o el equivalente en HF: ref→revision)
              y exigir coincidencia exacta antes de aceptarla como pin final."
  entrada: "candidato de pin resuelto en G1/G4 de T-005"
  salida: "pin confirmado por 3 resoluciones independientes coincidentes, o ASK_COUNCIL"
  max_iteraciones: 3
  presupuesto: {tokens: 0, tiempo_seg: 90, adaptativo: "no aplica"}
  estrategias:
    pool: ["fuente_directa (ej. git ls-remote / HF API revision)",
           "fuente_alternativa_1 (ej. GitHub Git Database API / HF hub_download metadata)",
           "fuente_alternativa_2 (ej. GitHub REST API /commits / HF web scrape de la página del modelo)"]
    activa: "las 3 se ejecutan SIEMPRE — es verificación cruzada, no selección"
    mutacion: "N/A — no hay mutación, hay comparación"
  delta: {definicion: "N/A — mide coincidencia exacta entre 3 fuentes",
          score: "100 si las 3 coinciden, 0 si alguna difiere", minimo_aceptable: 100}
  checkpoint: "las 3 resoluciones + su coincidencia quedan en provenance"
  rollback: "si no coinciden 3/3 → NO se acepta el pin → ASK_COUNCIL"
  detectores: {estancamiento: "N/A", repeticion: "N/A", deriva_objetivo: "N/A",
               tiempo_excesivo: ">80% de 90s → escalar", tokens_excesivos: "N/A", degradacion: "N/A"}
  escalada: {1: "N/A", 2: "N/A", 3: "ASK_COUNCIL con las 3 resoluciones
             discrepantes", 4: "N/A", 5: "Director si el Council no resuelve"}
  eventos: [loop.enter, loop.iter, loop.exit]
  metricas_salida: [coincidencia_3_de_3, pin_confirmado]
```

```yaml
loop:
  id: "L09-memoria"
  proposito: "Leer/escribir SOLO los campos memory.lee/memory.escribe
              declarados por contrato de cada nodo (A3) — nunca contexto de nodos ajenos."
  entrada: "RT-13 (memoria_in) o RT-43 (memoria_out) del nodo activo"
  salida: "state.json actualizado exactamente en las claves declaradas"
  max_iteraciones: 1
  presupuesto: {tokens: 0, tiempo_seg: 10, adaptativo: "no aplica"}
  estrategias: {pool: ["N/A"], activa: "N/A", mutacion: "N/A"}
  delta: {definicion: "N/A", score: "N/A", minimo_aceptable: "N/A"}
  checkpoint: "cada lectura/escritura es en sí misma un checkpoint atómico"
  rollback: "escritura fuera de las claves declaradas = veto SHERIFF inmediato, se revierte"
  detectores: {estancamiento: "N/A", repeticion: "N/A",
               deriva_objetivo: "escritura fuera de memory.escribe → veto",
               tiempo_excesivo: "N/A", tokens_excesivos: "N/A", degradacion: "N/A"}
  escalada: {1: "N/A", 2: "N/A", 3: "N/A", 4: "N/A", 5: "veto SHERIFF → RT-80 inmediato"}
  eventos: [context.compressed, context.cleared]
  metricas_salida: [claves_leidas, claves_escritas]
```

```yaml
loop:
  id: "L10-recuperacion"
  proposito: "Ejecutar el protocolo de 7 pasos de A8 cuando RT-80 clasifica
              un fallo — puente entre L04 (nodo) y recuperación de misión completa."
  entrada: "RT-80 activado (fallo no resuelto por L04 en sus 3 ciclos con L03)"
  salida: "misión reanudada desde checkpoint limpio, o escalada al Director"
  max_iteraciones: 1
  presupuesto: {tokens: 0, tiempo_seg: 300, adaptativo: "no aplica"}
  estrategias:
    pool: ["auto_recuperable: input_invalido_upstream, dependencia_
            instalable, timeout_con_checkpoint, estancamiento_con_pool",
           "requiere_Director: ley_violada, contradiccion, contrato_
            incumplible, 2do_recovery_mismo_nodo, presupuesto_agotado"]
    activa: "según clasificación de RT-80"
    mutacion: "N/A — clasificación binaria, no pool rotativo"
  delta: {definicion: "diferencia entre estado antes/después del protocolo", score: "N/A", minimo_aceptable: "N/A"}
  checkpoint: "protocolo completo registrado en journal + state.json"
  rollback: "el protocolo de 7 pasos ES el rollback"
  detectores: {estancamiento: "N/A", repeticion: "N/A", deriva_objetivo: "N/A",
               tiempo_excesivo: ">80% de 300s → forzar clasificación requiere_Director",
               tokens_excesivos: "N/A", degradacion: "N/A"}
  escalada: {1: "N/A", 2: "N/A", 3: "N/A", 4: "N/A",
             5: "siempre disponible — Director recibe: nodo, causa raíz, qué se intentó, 2-3 opciones"}
  eventos: [recovery.start, recovery.classified, recovery.done]
  metricas_salida: [clasificacion, pasos_aplicados, resultado]
```

```yaml
loop:
  id: "L11-cierre"
  proposito: "Cerrar la misión SOLO si Tribunal pasó en los 3 puntos de
              L03, evidencia completa, y state.json consistente."
  entrada: "T-010 (FICHA_REGISTRAR) en done"
  salida: "mission.completed + lock liberado (T-011)"
  max_iteraciones: 1
  presupuesto: {tokens: 0, tiempo_seg: 60, adaptativo: "no aplica"}
  estrategias: {pool: ["N/A"], activa: "N/A", mutacion: "N/A"}
  delta: {definicion: "N/A", score: "N/A", minimo_aceptable: "N/A"}
  checkpoint: "cierre final persistido, state.json marcado completed"
  rollback: "si falta algún done → PROHIBIDO cerrar, reportar cuáles y por qué"
  detectores: {estancamiento: "N/A", repeticion: "N/A",
               deriva_objetivo: "algún T-XXX no está done → bloquear cierre",
               tiempo_excesivo: "N/A", tokens_excesivos: "N/A", degradacion: "N/A"}
  escalada: {1: "N/A", 2: "N/A", 3: "N/A", 4: "N/A", 5: "cierre bloqueado persistente → Director"}
  eventos: [project.completed, mission.lock.released]
  metricas_salida: [nodos_done, duracion_total, coste_total, recoveries_totales]
```
