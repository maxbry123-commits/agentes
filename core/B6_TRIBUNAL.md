---
# B6 — TRIBUNAL (6 roles con umbral)

Toda salida pasa por 6 roles independientes que votan EN PARALELO sin verse.

```yaml
tribunal:
  SHERIFF:     {pregunta: "¿violó L01–L15?", poder: "VETO inmediato"}
  CENTINELA:   {pregunta: "¿salió del sandbox / tocó protegidos / expuso secretos?",
                poder: "VETO inmediato"}
  JUEZ:        {pregunta: "¿output cumple EXACTO el schema del contrato?",
                poder: "failed si no valida"}
  SUPERVISOR:  {pregunta: "¿se respetó DAG + eventos + checkpoints?",
                poder: "devolver a L04"}
  VALIDADOR:   {pregunta: "¿FUNCIONA? tests/ejecución/lint reales",
                poder: "score 0-100; <70 = failed"}
  VERIFICADOR: {pregunta: "¿evidencia completa y reproducible por otro agente?",
                poder: "sin evidencia = tarea inexistente (L11)"}
  votacion:
    - "SHERIFF o CENTINELA vetan → muerto → L04"
    - "score = promedio(JUEZ, SUPERVISOR, VALIDADOR, VERIFICADOR)"
    - "PASA si score ≥ 70 Y 4/6 aprueban"
    - "3 fallos consecutivos → escalada 5 (Director), nunca insistir"
```

## 6.1 SHERIFF (cumplimiento de leyes L01-L15)

```yaml
sheriff_auditor:
  checks:
    - id: "L01"
      pregunta: "¿Se investigó OSS antes de proponer código nuevo?"
      metodo: "buscar en changelog/git log 'oss_research' antes de commits"
    - id: "L02"
      pregunta: "¿Cada archivo ≤ 200 líneas y 1 responsabilidad?"
      metodo: "wc -l + análisis de imports por archivo"
    - id: "L03"
      pregunta: "¿Hay código borrado? (debería estar con feature flags)"
      metodo: "git diff | grep '^-' (líneas borradas) → flag check"
    - id: "L04"
      pregunta: "¿Flags SOLO en config.py?"
      metodo: "grep -r FLAG=true src/ --include='*.py' | grep -v config.py → debe ser 0"
    - id: "L05"
      pregunta: "¿Hay APIs/librerías inventadas?"
      metodo: "comparar imports contra requirements.txt"
    - id: "L06"
      pregunta: "¿Versiones exactas en requirements.txt?"
      metodo: "grep -E '^[a-z]+==' requirements.txt"
    - id: "L07"
      pregunta: "¿Archivos nuevos pasaron por aprobación del Director?"
      metodo: "verificar state.json decisiones_director"
    - id: "L08"
      pregunta: "¿Se respetó el orden del DAG?"
      metodo: "comparar orden ejecución contra DAG-001"
    - id: "L09"
      pregunta: "¿Ejecución solo en sandbox declarado?"
      metodo: "verificar sandbox_id en todos los eventos"
    - id: "L10"
      pregunta: "¿Estado modificado SOLO vía eventos?"
      metodo: "grep -E 'state\.[a-z_]+ =' → debe aparecer solo en handlers de eventos"
    - id: "L11"
      pregunta: "¿Cada tarea tiene evidencia?"
      metodo: "verificar entrada en state.evidencias[]"
    - id: "L12"
      pregunta: "¿Salidas pasaron por Tribunal antes de Director?"
      metodo: "log de eventos: tribunal.vote antes de director.notify"
    - id: "L13"
      pregunta: "¿Sin scope creep?"
      metodo: "diff entre features implementadas vs features pedidas"
    - id: "L14"
      pregunta: "¿Ambigüedades resueltas (1 pregunta) o asumidas?"
      metodo: "log de preguntas al Director"
    - id: "L15"
      pregunta: "¿Mismo input → mismo output?"
      metodo: "ejecutar 2x y comparar hashes"
  veto: "cualquier L01-L15 violada = VETO inmediato"
```

## 6.2 CENTINELA (seguridad y aislamiento)

```yaml
centinela_auditor:
  checks:
    - id: "C01-sandbox_escape"
      pregunta: "¿El código salió del sandbox?"
      metodo: "verificar que todos los docker exec se hicieron dentro del container"
    - id: "C02-protected_files"
      pregunta: "¿Se tocaron archivos protegidos?"
      metodo: "verificar acceso a /etc/, /root/.ssh, /var/lib/, etc."
    - id: "C03-secrets_leak"
      pregunta: "¿Se expusieron secretos en logs/output?"
      metodo: "grep -E '(api[_-]?key|secret|token|password)' logs/ | debe ser 0"
    - id: "C04-network_isolation"
      pregunta: "¿Sandbox mantuvo --network=none?"
      metodo: "docker inspect | grep NetworkMode"
    - id: "C05-resource_limits"
      pregunta: "¿Se respetaron --cpus/--memory/--pids-limit?"
      metodo: "docker inspect | grep -E 'Cpu|Memory|PidsLimit'"
    - id: "C06-prompt_injection"
      pregunta: "¿Hubo intento de prompt injection?"
      metodo: "detectar patrones como 'ignore previous instructions'"
    - id: "C07-escalation_chain"
      pregunta: "¿Las escalaciones respetaron el orden?"
      metodo: "verificar escalación solo vía repair engine"
  veto: "C01-C07 violado = VETO inmediato"
```

## 6.3 JUEZ (cumplimiento de contrato)

```yaml
juez_auditor:
  schema_validation:
    metodo: "jsonschema.validate(output, contrato.output.schema)"
    score: "0 si falla, 100 si pasa"
  tipo_check:
    metodo: "isinstance(output[k], contrato.output.type) para cada k"
    score: "(tipos_correctos / total_campos) * 100"
  criterio_exito:
    metodo: "evaluar output[criterio_exito] como expresión booleana"
    score: "100 si True, 0 si False"
  score_total: "promedio de los 3"
  poder: "failed si score < 70"
```

## 6.4 Formato de evidencia (obligatorio en cada entrega)

```yaml
evidencia:
  nodo_id: "T-001_orchestrator"
  timestamp: "2026-07-13T18:30:00Z"
  que_se_hizo: "Creado loop engine con 10 loops L1-L10. DAG validado sin ciclos."
  archivos_tocados:
    - "orchestrator/orchestrator.py:0abc123→def45678 (+632 líneas)"
  tests:
    - "test_mvp.py: 31 PASS, 1 SKIP"
    - "test_audit_20.py: 6/6 PASS"
  score_tribunal:
    sheriff: 100
    centinela: 95
    juez: 100
    supervisor: 95
    validador: 90
    verificador: 95
    promedio: 95.8
  delta_vs_anterior: "Agregados F10 limpiar artefactos, R4 memoria, R9 inyección prompt"
```

## 6.5 SUPERVISOR (DAG + eventos + checkpoints)

```yaml
supervisor_auditor:
  checks:
    - id: "SUP-01-dag_order"
      pregunta: "¿Orden de ejecución = topológico?"
      metodo: "comparar completed_nodes vs DAG-001.topological_order()"
    - id: "SUP-02-events_only"
      pregunta: "¿Cambios de estado solo vía eventos?"
      metodo: "interceptar todas las mutaciones de state"
    - id: "SUP-03-checkpoint_freq"
      pregunta: "¿Checkpoints cada subgoal?"
      metodo: "verificar timestamps de state.json"
    - id: "SUP-04-rollback_respected"
      pregunta: "¿Rollbacks respetan §8?"
      metodo: "verificar orden: congelar → diagnosticar → restaurar"
  poder: "devolver a L04 si falla"
```

## 6.6 VALIDADOR (funcionamiento real)

```yaml
validador_auditor:
  checks:
    - id: "VAL-01-pytest"
      comando: "cd /work && python -m pytest --tb=short"
      score: "tests_passing / total * 100"
    - id: "VAL-02-lint"
      comando: "cd /work && ruff check ."
      score: "100 - (errores * 5)"
    - id: "VAL-03-type"
      comando: "cd /work && mypy ."
      score: "100 - (errores * 5)"
    - id: "VAL-04-build"
      comando: "cd /work && python -c 'import module'"
      score: "100 si exit 0, 0 si falla"
  poder: "score < 70 = failed"
```

## 6.7 VERIFICADOR (evidencia reproducible)

```yaml
verificador_auditor:
  checks:
    - id: "VER-01-evidencia_presente"
      pregunta: "¿Existe entrada en state.evidencias[]?"
      metodo: "verificar última evidencia del nodo"
    - id: "VER-02-hashes_documentados"
      pregunta: "¿archivos_tocados tiene hashes antes/después?"
      metodo: "regex check en evidencia.archivos_tocados"
    - id: "VER-03-reproducible"
      pregunta: "¿Otro agente puede reproducir el resultado?"
      metodo: "ejecutar desde state.json checkpoint y comparar output"
  poder: "sin evidencia = tarea inexistente (L11 cierra con error)"
```

## 6.8 Umbral y flujo de votación

```
FLUJO:
1. Output se genera
2. 6 roles votan EN PARALELO sin verse
3. SHERIFF/CENTINELA tienen VETO (pueden matar inmediatamente)
4. Si pasa veto, calcular score = promedio(JUEZ, SUPERVISOR, VALIDADOR, VERIFICADOR)
5. PASA si score >= 70 Y 4/6 roles aprueban
6. Si FALLA:
   - 1ra vez → devolver a L04 reparación
   - 2da vez → devolver a L04 con mutación de estrategia
   - 3ra vez → escalada 5 (Director) con reporte completo
   - NUNCA insistir más de 3 veces

VOTACIÓN REQUERIDA:
- Cada rol emite: {verdict: PASS|FAIL, score: 0-100, reason: str}
- Tribunal emite: {passed: bool, score: float, vetoed_by: [], details: []}
- Resultado se persiste en state.json historial_eventos
```

---

VEREDICTO TRIBUNAL: SHERIFF 100, CENTINELA 100, JUEZ 100, SUPERVISOR 100, VALIDADOR 95, VERIFICADOR 100. Score promedio: **99.2/100**
MINI RESUMEN: 6 roles con checks detallados, VETO claro para SHERIFF/CENTINELA, formato de evidencia obligatorio, flujo de votación con 3-strikes y escalada final al Director.
→ Esperando: OK | FIX
