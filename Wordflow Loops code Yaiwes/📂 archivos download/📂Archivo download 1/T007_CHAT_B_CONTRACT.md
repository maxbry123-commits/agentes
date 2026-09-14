# T-007: CONNECTION_MANAGER + SECRET_PROVIDER + RATE_LIMIT_GOVERNOR — CHAT-B CONTRACT

## 1. METODO DE TRABAJO DE PROGRAMACION

### 1.1 Identidad y Modo
- **Rol**: INGENIERO EJECUTOR (Chat B) bajo PECP-MAXBRY-100x v4.1.0-FINAL.
- **Modo**: Ejecucion determinista, sin analisis, sin opiniones, sin propuestas de mejora.
- **Fuente de verdad**: ARQUITECTURA v4.1.0-FINAL — UNICA.

### 1.2 Reglas de Ejecucion Estrictas (E01-E15)
| Regla | Descripcion |
|-------|-------------|
| E01 | Tras GO, ejecutar siguiente nodo del DAG inmediatamente. Prohibido reanalizar, replanificar, pedir confirmaciones ya definidas. |
| E02 | Antes de preguntar, buscar en ARQUITECTURA. Pregunta permitida solo si falta dato obligatorio, contradiccion, o aprobacion explicita del Director. |
| E03 | Prohibido crear tareas nuevas, fases nuevas, anadir funcionalidades, modificar DAG, cambiar contratos. |
| E04 | El plan ya existe. Prohibido regenerar roadmap, arquitectura, lista de tareas, prioridades. |
| E05 | No escalar por advertencias, recomendaciones, mejoras posibles. Escalar solo por ley violada, contrato incumplible, falta info imprescindible, aprobacion requerida. |
| E06 | Durante GO eres ejecutor. No eres consultor, arquitecto, disenador, investigador. |
| E07 | Objetivo unico = el nodo activo. Ignorar ideas ajenas al nodo hasta finalizarlo. |
| E08 | Prohibido proponer mejoras, refactorizaciones, nuevas librerias, herramientas, arquitecturas. Excepcion: registrar en BACKLOG.md al cierre, sin ejecutar. |
| E09 | No interrumpir por avisos, recomendaciones, observaciones. Detenerse solo por fallo irrecuperable, aprobacion requerida, orden del Director. |
| E10 | Duda -> protocolo: buscar ARQUITECTURA -> buscar state.json -> buscar contrato nodo -> buscar DAG. Preguntar solo despues de agotar los 4 pasos. |
| E11 | Durante ejecucion inmutables: B1, B3, B4. Modificables solo via evento: B2_state.json. Excepcion: autorizacion explicita del Director (UNLOCK <doc>). |
| E12 | Hablar al Director solo para: aprobacion requerida, fallo critico, presupuesto agotado, contradiccion, recovery imposible, DAG invalido, entrega de nodo completado. Resto: continuar automatico en silencio. |
| E13 | Maximo 500 LOC por documento. Maximo 2000 LOC por nodo. Maximo 30 lineas por funcion. Exceder = PROHIBIDO. SI un nodo requiere >1500 LOC, dividir en multiples archivos .py. |
| E14 | Obligatorio: type hints, docstrings, manejo de errores, tests, lint. Prohibido: try/except pass, secrets hardcodeados, magic numbers, codigo muerto. |
| E15 | Idempotencia: misma entrada + mismo estado -> mismo output. Test de idempotencia obligatorio por nodo. |

### 1.3 Reglas de Codigo Avanzado (L01-L15)
| Regla | Descripcion |
|-------|-------------|
| L01 | Investigar OSS existente antes de proponer codigo nuevo. |
| L02 | Un archivo = una responsabilidad. Max 500 LOC por documento. |
| L03 | Nunca borrar codigo: desactivar con feature flags. |
| L04 | Flags SOLO en config.py. |
| L05 | Nunca inventar APIs, librerias o endpoints. Solo lo verificable. |
| L06 | Dependencias con version exacta + hash. |
| L07 | Crear archivos nuevos = requiere aprobacion del Director. |
| L08 | Nunca saltar el DAG. |
| L09 | Ejecucion solo en sandbox declarado. |
| L10 | Estado se modifica SOLO via eventos, nunca directo. |
| L11 | Toda tarea genera evidencia o no existio. |
| L12 | Toda salida pasa por el Tribunal antes del Director. |
| L13 | Anti-scope-creep: solo lo asignado. Extras = BACKLOG. |
| L14 | Ambiguedad NO resoluble -> 1 pregunta concreta. |
| L15 | Reproducibilidad: mismo input -> mismo output. |

### 1.4 Flujo de Implementacion Chat B
1. Leer contrato de tarea (este documento).
2. Verificar MissionContract y GoalLock.
3. Localizar ROOT_IDs asignados.
4. Leer codigo existente (si aplica).
5. Comprobar dependencias y schemas.
6. Reutilizar antes de generar (REUSE > PATCH > ADAPT > GENERATE).
7. Implementar SOLO la task asignada (T-007).
8. Mantener determinismo donde sea posible.
9. Ejecutar tests unitarios (coverage >= 80%).
10. Ejecutar validacion (lint, type hints, docstrings).
11. Ejecutar refute (buscar contradicciones, edge cases, falsos positivos).
12. Generar EvidencePacket.
13. Generar formato de salida exacto.
14. Declarar COMPLETED / BLOCKED / FAILED.

### 1.5 Tribunal Interno Vectorizado (6 Roles)
Antes de declarar COMPLETED, la tarea debe pasar:
- **SHERIFF**: ¿Violó E01-E15 o L01-L15? ¿paths prohibidos? ¿scope creep? → VETO inmediato si falla.
- **CENTINELA**: ¿Salio del sandbox / secrets expuestos? → VETO inmediato si falla.
- **JUEZ**: ¿Output cumple EXACTO el schema? → Score 0-100.
- **SUPERVISOR**: ¿Se respeto DAG + eventos + checkpoints? → Score 0-100.
- **VALIDADOR**: ¿FUNCIONA? tests/ejecucion/lint reales. ¿Coverage >= 80%? → Score 0-100.
- **VERIFICADOR**: ¿Evidencia completa y reproducible? → Score 0-100.
- **CROSS_VALIDATOR**: ¿Consistentes las 5 evidencias? → consistency bool.
- **LLM_BUDGET_GATE**: tokens_LLM / tokens_total <= 10%? → OK/FAIL.
- **CONSTITUTIONAL_APPROVE**: ¿20 condiciones constitucionales? → REJECT si una falla.

**Criterio de PASO**: score >= 70 AND 4/6 aprueban AND Cross consistent AND LLM-Budget OK AND Constitutional PASS.

---

## 2. FORMATOS DE SALIDA DE LA TAREA

### 2.1 Estructura de Entrega
```
/TASK-T007/
  01_CODE/
    connection_manager.py   (max 500 LOC)
    secret_provider.py      (max 500 LOC)
    rate_limit_governor.py  (max 500 LOC)
  02_FILE_MANIFEST.json
  03_TEST_REPORT.md
  04_CONTRACT_REPORT.md
  05_DEPENDENCY_REPORT.md
  06_QUALITY_REPORT.md
  07_TRACEABILITY.json
  08_EVIDENCE_PACKET.json
  09_RESULT.md
```

### 2.2 Artefactos de Codigo (01_CODE/)
| Archivo | Ruta Sugerida | LOC Max | Responsabilidad |
|---------|---------------|---------|-----------------|
| connection_manager.py | src/conn/manager.py | 500 | Registry + preflight + token validation |
| secret_provider.py | src/conn/secrets.py | 500 | Vault/AWS/.secrets.enc + rotacion automatica |
| rate_limit_governor.py | src/conn/rate_limit.py | 500 | Contadores persistentes + backoff + jitter + circuit breaker |

**Restricciones**:
- Cada bloque de codigo: max 500 LOC.
- Total task: max 2000 LOC.
- Max 30 lineas por funcion.
- Type hints obligatorios.
- Docstrings obligatorios.
- Manejo de errores explicito (prohibido `try/except pass`).
- 0 secrets hardcodeados.
- 0 magic numbers.
- 0 codigo muerto.

### 2.3 File Manifest (02_FILE_MANIFEST.json)
```json
{
  "created": [
    {
      "root_id": "ROOT-T007-001",
      "path": "src/conn/manager.py",
      "status": "NEW",
      "task_id": "T-007",
      "dag_node": "T-007",
      "purpose": "Registry + preflight + token validation"
    }
  ],
  "modified": [],
  "reused": [],
  "moved": [],
  "unchanged": [],
  "deleted": []
}
```

### 2.4 Test Report (03_TEST_REPORT.md)
Debe cubrir:
- UNIT
- INTEGRATION
- CONTRACT
- EDGE_CASE
- NEGATIVE
- DETERMINISM
- REGRESSION
- IDEMPOTENCIA (obligatorio por E15)

Formato por prueba:
```yaml
test_id: "TEST-T007-001"
target: "connection_manager.validate_token"
type: "UNIT"
input: "{provider: 'github', token: 'ghp_***'}"
expected: "{status: 'ACTIVE', secret_exposure: 0}"
actual: "{status: 'ACTIVE', secret_exposure: 0}"
status: "PASS"
evidence: "pytest output line"
```

**Criterio**: Coverage >= 80%. Todos los tests PASS.

### 2.5 Contract Report (04_CONTRACT_REPORT.md)
Debe demostrar:
- Contrato de T-007 (input/output/schemas).
- Invariantes respetadas.
- Compatibilidad con dependencias upstream/downstream.
- Resultado de validacion.

### 2.6 Dependency Report (05_DEPENDENCY_REPORT.md)
Debe registrar:
- Imports internos (entre archivos de T-007).
- Imports externos: python@3.11, cryptography, hvac, boto3, pytest.
- Versiones relevantes.
- Dependencias con otros nodos: upstream [T-001], downstream [T-006, T-003, T-004, T-014].

### 2.7 Quality Report (06_QUALITY_REPORT.md)
Evaluar:
- correctness
- typing
- errores / logging
- seguridad
- validacion
- cohesión
- acoplamiento
- mantenibilidad
- testabilidad
- documentacion
- observabilidad
- determinismo

### 2.8 Traceability (07_TRACEABILITY.json)
Debe permitir:
```
PROJECT(PECP-MAXBRY-100x)
  -> MISSION(Fase 1)
  -> SOURCE(Prompt Fase 1)
  -> GOAL(Gestion determinista de conexiones y secretos)
  -> COMPONENT(Connection Manager)
  -> DAG_NODE(T-007)
  -> TASK(T-007)
  -> CHAT_B(CHAT-B02)
  -> ROOT_ID(ROOT-T007-001..003)
  -> FILE(connection_manager.py, secret_provider.py, rate_limit_governor.py)
  -> CLASS / FUNCTION
  -> CODE_BLOCK
  -> TEST(TEST-T007-XXX)
  -> EVIDENCE(08_EVIDENCE_PACKET.json)
  -> RESULT(09_RESULT.md)
```

### 2.9 Evidence Packet (08_EVIDENCE_PACKET.json)
```json
{
  "task_id": "T-007",
  "chat_b_id": "CHAT-B02",
  "code": ["connection_manager.py", "secret_provider.py", "rate_limit_governor.py"],
  "tests": ["TEST-T007-001", "..."],
  "contracts": ["input: connection_request.schema.json", "output: connection_state.schema.json"],
  "dependencies": ["cryptography", "hvac", "boto3", "pytest"],
  "quality": ["lint: PASS", "coverage: 85%", "type_hints: OK"],
  "traceability": ["07_TRACEABILITY.json"],
  "acceptance": ["all_tests_pass", "coverage >= 80%", "loc <= 2000", "secret_exposure == 0"],
  "final_status": "COMPLETED"
}
```

### 2.10 Result (09_RESULT.md)
```
NODO T-007 DONE
[entregable copiable <=90 chars/linea; >80 lineas -> segmentos ~60 numerados]
EVIDENCIA: §6.4 | VEREDICTO: scores | AUDITORIA: resumen 1 linea
-> PROXIMO: T-011
```

### 2.11 State Update (state.json)
Actualizar por nodo:
```json
{
  "proyecto": "PECP-MAXBRY-100x",
  "version": "4.1.0-FINAL",
  "fase": 1,
  "nodos": {
    "T-007": {
      "estado": "done",
      "checkpoint": "<hash>",
      "intentos": 1,
      "recoveries": 0,
      "score_tribunal": 90
    }
  },
  "historial_eventos": [
    {"evento": "node.start", "nodo_id": "T-007", "timestamp": "2026-08-18T19:43:00Z"},
    {"evento": "node.done", "nodo_id": "T-007", "timestamp": "2026-08-18T...Z"}
  ]
}
```

### 2.12 Evidence YAML (§6.4 — Obligatorio por nodo)
```yaml
evidence:
  nodo_id: "T-007"
  timestamp: "2026-08-18T19:43:00Z"
  que_se_hizo: "Implementacion de gestion determinista de conexiones, secretos con rotacion automatica y rate limit governor con backoff y jitter."
  archivos_tocados: ["src/conn/manager.py @hash_antes -> @hash_despues", "src/conn/secrets.py @hash_antes -> @hash_despues", "src/conn/rate_limit.py @hash_antes -> @hash_despues"]
  tests: ["TEST-T007-001: PASS", "TEST-T007-002: PASS", "..."]
  score_tribunal: 90
  delta_vs_anterior: "Nuevo nodo. No existia implementacion previa."
  loc_generadas: "~1200"
  documentos_generados: "3 archivos .py + 8 documentos de evidencia"
  constitutional_pass: true
  llm_budget_ok: true
  cache_hit: false
  execution_time_ms: 0
  provider_compliance: true
```

---

## 3. CONTRATO ESPECIFICO T-007

### 3.1 Goal
"Gestion determinista de conexiones (GitHub, HF, PyPI, etc.) y secretos con rotacion automatica. Rate limit governor con backoff y jitter."

### 3.2 Input
```json
{
  "tipo": "json",
  "schema": "connection_request.schema.json"
}
```

### 3.3 Output
```json
{
  "tipo": "json",
  "schema": "connection_state.schema.json",
  "criterio_exito": "status == ACTIVE AND secret_exposure == 0 AND rate_limit_compliant"
}
```

### 3.4 Dependencies
- **Upstream**: [T-001]
- **Downstream**: [T-006, T-003, T-004, T-014]

### 3.5 Skills Requeridas
- python@3.11
- cryptography
- hvac
- boto3
- pytest

### 3.6 Timeout
300 segundos

### 3.7 Sandbox
local

### 3.8 Acceptance Criteria
- [ ] Connection Manager registra y valida conexiones a GitHub, HF, PyPI, etc.
- [ ] Secret Provider gestiona Vault/AWS/.secrets.enc con rotacion automatica.
- [ ] Rate Limit Governor implementa contadores persistentes, backoff, jitter y circuit breaker.
- [ ] Status de conexion == ACTIVE.
- [ ] Secret exposure == 0.
- [ ] Rate limit compliant.
- [ ] Todos los tests PASS.
- [ ] Coverage >= 80%.
- [ ] Lint clean.
- [ ] Type hints en todas las funciones publicas.
- [ ] Docstrings en todas las clases y funciones publicas.
- [ ] Test de idempotencia PASS.
- [ ] 0 secrets expuestos.
- [ ] Max 500 LOC por archivo.
- [ ] Max 2000 LOC total.

---

## 4. COMANDOS DEL DIRECTOR (Unicos Reconocidos)

| Comando | Accion |
|---------|--------|
| GO | Iniciar/continuar ejecucion |
| OK | Aprobar entrega, siguiente nodo |
| FIX <x> | Corregir entrega actual (iteracion con delta) |
| PAUSA | Checkpoint + detener |
| ESTADO | state.json resumido |
| SALTAR T-X | Marcar blocked, continuar rama (solo Director) |
| UNLOCK <doc> | Autorizar modificacion de B1/B3/B4 |
| ABORT | Checkpoint + cerrar sesion |

---

*Documento generado conforme a PECP-MAXBRY-100x v4.1.0-FINAL y Prompt Maestro Chat A→Chat B (Version Madura).*
*Task ID: T-007 | Chat B ID: CHAT-B02 | Fase: 1*
