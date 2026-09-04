# PIPELINE 00 — MÉTODO DE TRABAJO + ARQUITECTURA

**Arquitectura REAL programación:** `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMMING.md`  
**Mapa forense:** `PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`  
**Forense checklist:** `PIPELINE/FORENSIC_CODE_AUDIT.md`  
**Gaps:** `PIPELINE/GAPS_PROGRAMMING_WORDFLOW.md`  
**Pipeline code:** `extensions/wordflow/engine/programming_pipeline.py`  
**Hot path:** `extensions/wordflow/engine/code_path_runner.py`

## Cadena obligatoria (política)
CONTEXT/HANDOFF → COPY-FIRST SCAN → IMPLEMENT(COPY|ADAPT|GENERATE) → WIRE → FORENSIC VERIFY → VERDICT AUTHORITY → CLOSED | FIX LOOP

## Cadena REAL en code_path (arquitectura)
pre_gate → quality_bar → goal_lock → cognitive_loop → evidence → post_verify(VerdictAuthority)

## COPY-FIRST
name + catalog + AST → COPY/ADAPT; GENERATE last. Evidence SOURCE→DEST+SHA si copy_file_deterministic.

## CONTROL DE TRABAJO
1 TOTAL · 2 TERMINADAS · 3 PENDIENTES · 4 SIGUIENTE · 5 PLAN · 6 MÉTODO · 7 NO sandbox / GitHub=verdad

---

# APPEND V3 — PROTOCOLO OPERATIVO SANDBOX → GITHUB → FORENSE
**Origen:** METHOD_WORK_UPDATE_V3_SANDBOX_GITHUB_FORENSIC  
**Tipo:** APPEND_ONLY · NO sustituye reglas anteriores · COPY-FIRST · deterministic-first · VERDICT AUTHORITY · CONTROL DE TRABAJO · GitHub=verdad · STAGNATION BREAKER · trazabilidad se CONSERVAN

## Autoridad
- Método de trabajo = reglas operativas
- GitHub = fuente persistente de verdad
- Sandbox = workspace temporal (build/test/verify) · NO memoria persistente · NO = DONE
- Usuario = aprueba cierre
- Auditoría forense = veredicto técnico con evidencia (no afirmación LLM)

## Modelo operativo (no saltar a DONE)
TASK_INTAKE → SALIDA_1_SANDBOX_BUILD → LOCAL_VERIFY → READY_FOR_PUBLISH → SALIDA_2_GITHUB_PUBLISH → REMOTE_VERIFY → PUBLISHED_AND_VERIFIED → SALIDA_3_FORENSIC_AUDIT → DONE

## TASK_INTAKE (antes de ejecutar)
Leer: README · Método · PIPELINE · tarea + trazabilidad · chat si hace falta.  
Definir: TASK_ID · OBJECTIVE · SOURCES · INPUTS · OUTPUTS · DEPENDENCIES · ACCEPTANCE · TRACEABILITY · STATUS=READY

## SALIDA 1 — SANDBOX_BUILD
- Construir en Sandbox primero; no publicar aún.
- Preferir cp/cat/sed/awk/git; no transportar bytes grandes por LLM; no regenerar fuente existente.
- Registrar comandos reales.
- Manifest obligatorio: `task_build/ARTIFACT_MANIFEST.json` (task_id, path, sources, size, lines, sha256, anchors, tests, diff_status, build_status).
- Éxito: READY_FOR_PUBLISH · Nunca: DONE desde build.
- **Permiso de usar sandbox en paso 1.** Al final de la salida de este paso: **confirmar con verdad si se usó sandbox o no** (no mentir).

## LOCAL_VERIFY
test -f · wc -c/-l · sha256sum · grep anchors · (code: git diff --check + tests).  
Gate: LOCAL_VERIFY_PASS. Sin PASS → no publicar.

## PUBLISH_GATE
Solo si LOCAL_VERIFY_PASS. Publicar el artefacto del manifest; sin regenerar/resumir/reescribir desde LLM.

## SALIDA 2 — GITHUB_PUBLISH
Persistir exactamente el artefacto verificado. Registrar repo/path/branch/commit. HTTP 200 ≠ prueba suficiente → READ-BACK obligatorio.
- **Enlaces GitHub:** mostrar **solo en paso 2**, uno por cada documento **nuevo o editado** (para auditar). Si no hubo publish a GitHub → **no mostrar enlaces**.

## REMOTE_VERIFY
Releer GitHub: size, lines, anchors, content, commit; comparar con local (sha256 si aplica).  
Fallo: PERSISTENCE_FAILURE → REPAIR · no DONE · no cleanup · no siguiente tarea.  
Éxito: PUBLISHED_AND_VERIFIED.

## SALIDA 3 — FORENSIC_AUDIT
- **Solo si la tarea produjo code** (auditoría forense de programación / FORENSIC_CODE_AUDIT). Si solo docs → forense documental ligero o N/A code.
- Si **no pasa** auditoría → **repetir paso 2 con reparación** (no DONE).
- Dominios: METHOD · REQUIREMENTS · TRACEABILITY · SANDBOX_BUILD · LOCAL_VERIFY · PUBLISH · REMOTE · INTEGRITY · NO_UNAUTHORIZED · TESTS · DOCS.
- Veredictos: DONE | REPAIR_REQUIRED | BLOCKED.
- Afirmación LLM ≠ evidencia.

## TASK_COMPLETION_GATE
DONE solo si: INTAKE + LOCAL_VERIFY + GITHUB_PUBLISHED + REMOTE_VERIFY + FORENSIC_AUDIT_DONE (o N/A code documentado).

## Trazabilidad post-DONE
Persistir en GitHub `TASK_COMPLETION_RECORD` (task_id, objective, sources, outputs, paths, commit, local/remote sha, verdict, next_task).

## Arquitectura en avance
Al avanzar y tocar archivos: actualizar arquitectura/trazabilidad según impacto; no regenerar fuentes; append/doc de lo tocado con evidencia.

## Recuperación de contexto
Orden: README → MÉTODO · PIPELINE · LISTA TAREAS · COMPLETION RECORDS · TRACE · DOCS REQUERIDOS · chat audit si hace falta.  
No depender solo del Sandbox ni solo de memoria de chat.

## Siguiente tarea
Solo con CURRENT_TASK=DONE y autorización usuario. No auto-iniciar.

## CLEANUP
Solo tras FORENSIC_DONE + aprobación usuario. Proteger: método, GitHub, fuentes, trazabilidad, completion records.

## STAGNATION (refuerzo)
Mismo fallo ×2 → cambiar mecanismo. Fallo publish → no regenerar documento completo. Fallo verify → reparar, no declarar éxito.

---

# APPEND V4 — SISTEMA DE TRABAJO Y CAPACIDADES INTEGRADAS

Los contratos operativos ampliados están definidos en:

- `PIPELINE/61_SISTEMA_TRABAJO_ROLES_ROUTER_COMMAND_CENTER_ORQUESTACION.md`
- `PIPELINE/62_ACR_RECICLAJE_TRIGGER_CUENTA_B.md`

Estos documentos formalizan, sin sustituir las reglas anteriores:

```text
ROUTER
→ COMMAND CENTER
→ AGENT REGISTRY / CAPABILITY RESOLUTION
→ ORCHESTRATOR
→ WORDflow KERNEL
→ EVIDENCE
→ SHERIFF
→ VERDICT AUTHORITY
```

Y añaden al método:

```text
ACR / CAPABILITY RESOLUTION
REUSE-FIRST / COPY-FIRST
TRIGGER + IDEMPOTENCY
CUENTA B REPOSITORY PROVISIONING
REMOTE READ-BACK
```

### Regla de integración

Toda nueva capacidad debe conectarse a las autoridades existentes. No se permite crear una segunda autoridad de credenciales, deployment, verificación o veredicto.
