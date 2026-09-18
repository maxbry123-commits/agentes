ARQUITECTURA WORDFLOW LOOP CODE YAIWES - INDICE MAESTRO
Auditoria forense X-Ray, 3 pasadas, verificacion cruzada con codigo fuente real.
Fecha: 2026-09-16/17. Autor: Claude (orquestador).
NOTA TECNICA: esta carpeta no lleva el emoji del nombre original porque el
conector de escritura falla al crear archivos nuevos en rutas con emoji al
inicio (confirmado con test). El contenido es identico a lo pedido.

ESTE ES EL ARCHIVO PRINCIPAL. Diagrama general, raiz completa, indice a partes.

## RAIZ REAL CONFIRMADA (leida en vivo, no de memoria)

Wordflow Loops Yaiwes/
- GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md
- HANDOFF.md
- PLAN-PROGRAMACION-11-OBJETIVOS-Y-AGENTES.md
- README arquitectura Wordflow LOOP Yaiwes.md
- readme indice agentes.md
- readme wordflow loop Yaiwes.md (69KB)
- Crazy Wall Orquestador/
- runtime/ (plugin-manifest.yaml, docs/, schemas/, tests/, src/)
  - src/ es EL KERNEL REAL, 17 subcarpetas (ver Parte 1)
- wordflow_loop/ (paquete Python, pyproject.toml)
  - wordflow_loop/ codigo real anidado:
    - contracts.py, ledger.py, llm_gate.py, model_api_router_mvp.py
    - agent_fleet/ (agent_fleet_adapter.py + registry, ver Parte 5)
    - governance/ (sheriff/sentinel/judge/guardian/supervisor, ver Parte 3)
    - contracts/ VACIA (gap confirmado)
    - evidence/ VACIA (gap confirmado)
    - adapters/, agent_sources/, code_graph/, intake/, plugins/, prompts/,
      research/, skills/, templates/, workflows/ (sin abrir aun)
- workspace/
- Capa de persistencia open mythos/
- Capa workflow GitHub Action/ (OBSOLETA, prohibido GitHub Actions)
- Capa workflow evolucion/
- archivos download/
- notas auditoria Claude/

## INDICE DE PARTES (cada una su propio archivo, no resumido)

- Parte 1: Estructura completa de runtime/src (17 carpetas, todos los archivos)
- Parte 2: Fase INTAKE + DAG (microflujo Glimmer-style)
- Parte 3: Fase EXECUTION + GOVERNANCE CHAIN (microflujo Glimmer-style)
- Parte 4: Fase RECOVERY + LEDGER/MERKLE (microflujo Glimmer-style)
- Parte 5: UEK (Enchufe Universal) + Agent Fleet (microflujo Glimmer-style)
- Anexo: Lista completa de GAPS y mejoras pendientes (mapa mental de Claude)

## DIAGRAMA GENERAL DEL FLUJO TOTAL (texto, sin imagenes)

INPUT (tarea/commit)
-> INTAKE (component_intake.py, existing_code_intake.py, project_intake_pipeline.py)
-> PLACEMENT (placement_classifier.py, reuse_selector.py: REUSE mayor PATCH mayor ADAPT mayor GENERATE)
-> DAG (dag_engine.py: dependencias, ciclos, orden topologico)
-> CLAIM+LEASE (crazywall_claim_gate.py, crazy_wall_concurrency.py)
-> SCHEDULER (parallel_scheduler.py, mavis_parallel.py)
-> LLM BOUNDARY (llm_boundary.py: LLM propone, nunca autoriza)
-> AGENT FLEET (agent_fleet_adapter.py: selecciona worker por capability)
-> EJECUCION (kernel.py: handler + idempotency + state)
-> GOBERNANZA (sheriff.py, sentinel.py, judge.py, guardian.py, supervisor.py,
  validator.py, verifier.py - archivos reales pero MUY PEQUENOS, 400-800 bytes)
-> ORACULO (tribunal.py: veredicto real, no status:ok)
-> EVIDENCIA (ledger.py + merkle_governance_core.py: cadena de hash)
-> CHECKPOINT (recovery/checkpoint.py)
-> SI FALLA: recovery/classifier.py -> recovery/engine.py -> circuit_breaker_sla.py
-> STATE_MACHINE (state_machine.py: PENDING/RUNNING/DONE/FAILED/BLOCKED/CANCELLED)
-> EVENT_BUS (event_bus.py: InMemory/Redis/NATS)
-> SIGUIENTE NODO o WATCHDOG si cola vacia

Estado real medido: nucleo determinista SI existe con nombre y tamano
verificado. Governance chain existe pero con archivos sospechosamente
pequenos. Contracts/ y evidence/ (JSON Schema real, Evidence Manifest)
estan VACIAS - gap confirmado, no de memoria.


## COMPONENT-OPS — Animation/Video Skills — 2026-09-17
- `manim-skill` — https://github.com/vumichien/manim-skill @ `70ccd68cf4dea135973f899b25fb408ddf5946c5` — destino: `Wordflow loop code Yaiwes/manim-skill/` — DOWNLOAD/EXTRACT=VERIFIED_CLOSED; INTEGRATION=PENDING.
- `skill-canvas-video` — https://github.com/siegerts/skill-canvas-video @ `6419a14d9fddb5003c66e0567d927ad57f1e4f06` — destino: `Wordflow loop code Yaiwes/skill-canvas-video/` — DOWNLOAD/EXTRACT=VERIFIED_CLOSED; INTEGRATION=PENDING.
- `chat-animation` — https://github.com/xue-xiaobao/chat-animation @ `d114e627833e2461efcc233d7a63a18cf85b149a` — destino: `Wordflow loop code Yaiwes/chat-animation/` — DOWNLOAD/EXTRACT=VERIFIED_CLOSED; INTEGRATION=PENDING.
- `taste-skill` — https://github.com/Leonxlnx/taste-skill @ `e79ca9ec7e071eb3a3b623c4fb752e853fc3ed58` — destino: `Wordflow loop code Yaiwes/taste-skill/` — DOWNLOAD/EXTRACT=VERIFIED_CLOSED; INTEGRATION=PENDING.
- Regla: read-back/hash obligatorio; integración se deja pendiente para wiring/test real Wordflow.


## COMPONENT-OPS — Animation/Video Skills — MATERIALIZED
- Motor canónico download/extract: 4/4 `VERIFIED_CLOSED`.
- Materialización Wordflow: submódulos/gitlinks fijados a commits exactos; read-back HF `6aacc3f55c02253cfb1463cb` = `AGENTES_4_OF_4_OK`.
- `manim-skill` @ `70ccd68cf4dea135973f899b25fb408ddf5946c5` — 123 archivos upstream; motor `6aacc2c95c02253cfb146381` COMPLETED.
- `skill-canvas-video` @ `6419a14d9fddb5003c66e0567d927ad57f1e4f06` — 10 archivos upstream; motor `6aacc2d05c02253cfb146383` COMPLETED.
- `chat-animation` @ `d114e627833e2461efcc233d7a63a18cf85b149a` — 25 archivos upstream; motor `6aacc2d7b1dc2b62dc590818` COMPLETED.
- `taste-skill` @ `e79ca9ec7e071eb3a3b623c4fb752e853fc3ed58` — 65 archivos upstream; motor `6aacc2de5c02253cfb146385` COMPLETED.
- Integración funcional Wordflow: `PENDING` hasta wiring/test real.

- Gitlinks no autorizados eliminados de ambos destinos; `.gitmodules` ausente. Continuar únicamente con motores canónicos.
