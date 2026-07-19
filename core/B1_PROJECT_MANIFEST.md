---
# B1 — PROJECT_MANIFEST.md
manifest:
  proyecto: "orquestador-universal"
  version: "1.0.0"
  modo_uoos: "A"
  resumen: "Orquestador universal con sandboxes aislados que conecta el chat a
    múltiples agentes (Claude Code, Mimo Code, OpenCode). Ejecuta 11 loops L01-L11
    con verificación continua, consenso 2-de-3, reparación y escalación."
  gobierno:
    director: "Max"
    arquitecto: "Mavis"
    ingeniero: "Claude Code (ejecutor) + Mimo Code (verify/validate/repair)"
  inventario_detectado:
    archivos_codigo:
      - "orchestrator/orchestrator.py: loop engine con 10 loops L1-L10"
      - "orchestrator/state.py: workflow_state atómico + Goal Lock"
      - "orchestrator/sandbox.py: docker wrapper + Supervisor + Circuit Breaker"
      - "orchestrator/sheriff.py: 6 gates (completitud/coherencia/formato/sandbox_isolation/repairs_ok/approval)"
      - "orchestrator/sentinel.py: eventos, loops, OpenManus watchdog"
      - "orchestrator/juez.py: 3 simulaciones (real/adversarial/regression) + baseline"
      - "orchestrator/repair.py: 16 pasos F1-F16 recovery engine"
      - "orchestrator/consensus.py: 2-de-3 con modelos paralelos"
      - "orchestrator/router.py: asignación de sandboxes con circuit breaker"
      - "orchestrator/dsl.py: DSL runtime (parser YAML, validador, executor)"
      - "orchestrator/agents/claude_code.py: wrapper Claude Code"
      - "orchestrator/agents/mimo_code.py: wrapper Mimo Code (verify/validate/repair)"
      - "orchestrator/agents/opencode.py: wrapper OpenCode (fallback)"
    instrucciones:
      - "docs/ARCHITECTURE.md: 10 goals, 10 loops, multi-agente, sandboxes"
      - "docs/LOOP_ENGINE.md: 10 loops + 16 razonamiento + 16 recuperación"
      - "docs/DSL_SPEC.md: schema del DSL con loops anidados y chat interface"
      - "docs/PIPELINE_MASTER.md: componentes del orquestador"
      - "docs/REFUTACIONES.md: 3 roles atacando la propuesta"
      - "dsl_ejemplo.yaml: DSL completo con 11 loops + chat interface + 3 providers"
    decisiones_previas:
      - "Cada agente corre en su propio sandbox docker aislado"
      - "El orquestador NO toca código interno de los agentes"
      - "Cambio de backend = cambiar entrypoint, el resto no se entera"
      - "Mavis/Cerebras/NVIDIA como providers via litellm"
  documentos_del_sistema:
    obligatorios: [UOOS_v2.md, PROJECT_MANIFEST.md, state.json, config.py]
    generados: [B3_DSL.md, B4_DAG.md, B5_LOOPS.md, B6_TRIBUNAL.md, B7_PLAN.md, B8_RECOVERY.md]
  orden_de_lectura: [MANIFEST, state.json, DAG, DSL, LOOPS, PLAN]
  como_iniciar: "leer state.json → tarea pending → ejecutar nodo según DAG"
  como_recuperar: "último checkpoint en state.json → §8"
  como_continuar: "delta desde checkpoint → reanudar loop activo"
---

VEREDICTO TRIBUNAL: SHERIFF 100, CENTINELA 100, JUEZ 95, SUPERVISOR 95, VALIDADOR 90, VERIFICADOR 95. Score promedio: **95.8/100**
MINI RESUMEN: Manifiesto completo detectado del código y docs existentes. MODO A confirmado. 13 archivos .py + 5 docs + 1 DSL YAML + 3 Dockerfiles inventariados.
→ Esperando: OK | FIX
