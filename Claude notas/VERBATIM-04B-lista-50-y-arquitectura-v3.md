VERBATIM DOCUMENTO 4/4 PARTE B - Lista 50 mejoras + arquitectura SEALS TEAM
YAIWES V3 (Director+Sol, 2026-09-16)

LISTA COMPLETA DE 50 MEJORAS PRIORITARIAS ("100x" = salto de arquitectura,
no rendimiento literal):
1. Eliminar PASS auto-declarado - PASS solo puede proceder de un oracle
2. Un DAG unico autoritativo (YAML define, Python carga y ejecuta)
3. FSM explicita: PENDING-CLAIMED-RESEARCHING-READY-EXECUTING-OBSERVING-
   VALIDATING-VERIFIED_CLOSED
4. JSON Schema completo: NodeInput, ResearchEvidence, ExecutionPlan,
   ToolCall, ToolReceipt, ValidationResult, Evidence, NodeOutput
5. Tool Registry Glimmer-style sujeto a permissions YAIWES
6. Plan/Act/Observe/Correct de Glimmer
7. Read/Act/Observe/Evaluate de Cookbook
8. Oracle externo: test/build/hash/API assertion/postcondition
9. Idempotencia Muse Code: stable command ID + replay
10. Pending command state: SUBMITTED-ACKED-QUEUED-STARTED-MATERIALIZED-
    COMPLETED/REJECTED
11. Crash recovery Muse: checkpoint durable + resume
12. Session/mission isolation: nunca mezclar estado de dos tareas
13. Contract SHA256 + Input SHA256
14. Ledger hash-chain para todo el historial
15. Checkpoint despues de cada transicion, no solo tras terminar un nodo
16. Claim + lease para impedir doble worker
17. 1 path = 1 writer, mediante resource locks
18. Safe edit Meta: exact-match-before-patch
19. Diff obligatorio para cambios
20. Evidence manifest: path+sha256_before+sha256_after+operation+receipt+test
21. Research real, no preguntarle 20 veces al mismo modelo
22. Research funnel: sources->normalize->dedupe->cross-check->rank->evidence
23. No-new-evidence anti-loop
24. Stuck detector: mismo GAP + mismo delta + mismo resultado
25. Retry budget por nodo y mision
26. Circuit breaker para proveedores
27. Dead-letter queue para fallos terminales
28. Saga/compensation para mutaciones reversibles
29. Watchdog real: heartbeat -> lease expiry -> reclaim
30. Queue steer/reclaim estilo Muse
31. Cancellation segura
32. Durability profile: durable/ephemeral/unknown
33. Schema/protocol fingerprint al conectar tools/runtimes
34. Conformance transcripts para reproducir ejecuciones
35. Golden traces del workflow
36. Independent Final Verifier que no lea el PASS interno
37. Adversarial tests reales
38. Regression fixtures reales
39. Property tests de invariantes
40. LLM sin permisos directos de mutacion
41. Approval como politica opcional, no nodo obligatorio del DAG general
42. Configuracion externa (retries/timeouts/thresholds/sources) en YAML
43. Versionado del workflow: schema_version, engine_version, policy_version,
    tool_version
44. Plugin adapters: capability -> adapter -> tool (kernel no sabe de marcas)
45. Test suite del orquestador: unit, contract, replay, crash recovery,
    double-execution, corrupted-state, stale-lease, adversarial-input, integration
46. Golden traces para comparar nuevas versiones del engine
47. Property-based tests (ej: jamas EXECUTING sin AUTHZ_PASS)
48. Invariantes formales: NO PASS WITHOUT EVIDENCE, NO MUTATION WITHOUT
    AUTH, NO CLOSE WITHOUT ORACLE, NO REPLAY WITHOUT SAME INPUT HASH,
    NO TWO WRITERS SAME RESOURCE
49. Separar telemetry de reasoning
50. Una unica salida canonica JSON

REGLA CENTRAL SOBRE TODAS:
LLM = PROPONE
POLICY = AUTORIZA
TOOL = EJECUTA
RECEIPT = DEMUESTRA
ORACLE = DECIDE PASS

ARQUITECTURA FINAL "SEALS TEAM YAIWES V3":
VERBATIM INPUT -> INPUT SHA256 -> CONTRACT SHA256 -> JSON SCHEMA ->
OBJECTIVE LOCK -> SCOPE LOCK -> AUTHZ -> CLAIM NODE -> ACQUIRE LEASE ->
CHECKPOINT -> RESEARCH -> EVIDENCE -> CROSS-CHECK -> PLAN -> POLICY
VALIDATE PLAN -> TOOL CALL -> IDEMPOTENCY CHECK -> EXECUTE -> RECEIPT ->
OBSERVE -> EVALUATE -> REAL TEST ORACLE ->
  rama PASS: POSTCONDITIONS -> SUPERVISOR -> GUARDIAN -> CODA ->
    FINAL VERIFY -> VERIFIED_CLOSED -> RELEASE LEASE -> NEXT NODE -> QUEUE EMPTY
  rama FAIL: CLASSIFY GAP -> (NEW EVIDENCE->RESEARCH | FIX->RETEST)
    o STUCK -> BLOCKED_WITH_TRACE

LAS 3 HERENCIAS:
MUSE CODE SDK -> COMMAND ID, IDEMPOTENCY, QUEUE, DURABILITY, RESUME,
  REPLAY, CONFORMANCE
MUSE GLIMMER -> TOOL REGISTRY, JSON TOOL SCHEMA, PLAN, TOOL CALL,
  TOOL RESULT, SELF-CORRECT
META AGENT COOKBOOK -> READ, ACT, OBSERVE, EVALUATE, TEST ORACLE,
  SAFE EDIT, GUARDS

YAIWES ANADE ENCIMA: FAIL_CLOSED + DAG + FSM + OBJECTIVE LOCK + SCOPE
LOCK + AUTHZ + LEDGER + EVIDENCE + FINAL INDEPENDENT VERIFY

NOTA FINAL DEL ANALISIS ORIGINAL (cita textual):
"Esa seria para mi la direccion correcta: no convertir Seals en una
copia de Meta, sino usar las mejores primitivas de los tres proyectos
de Meta dentro de un kernel YAIWES mas estricto que cualquiera de ellos
por separado."

NOTA DE CLAUDE (no es verbatim, es mi anotacion propia):
Mi Seals Team actual (ejecutor.py, instalador_deterministico.py,
consultor_experto.py, verificador.py, watchdog.py, router_modelos.py)
NO implementa ninguno de estos 50 puntos, y tiene el defecto confirmado
de PASS auto-declarado sin oracle real. Modo recepcion activo, pendiente
instruccion del Director para proceder al rediseno V3.
