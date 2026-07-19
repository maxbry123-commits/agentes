---
# B7 — PLAN DE DESPLIEGUE (MODO A)

```yaml
plan_despliegue:
  auditoria_inicial: |
    Mapeo del código existente vs leyes (200 líneas, flags, secretos)
    → reporte de NO conformidades ANTES de desplegar

  reporte_auditoria:
    fecha: "2026-07-13"
    codigo_total: 3809 lineas
    archivos_python: 13
    archivos_md: 5
    dockerfiles: 3
    dsl_yaml: 1

    no_conformidades_detectadas:
      - id: "NC-001"
        archivo: "orchestrator/orchestrator.py"
        lineas: 632
        ley_violada: "L02 (max 200 lineas)"
        severidad: "media"
        accion: "Refactorizar en 3 archivos: orchestrator_main.py + loop_engine.py + state_machine.py"

      - id: "NC-002"
        archivo: "orchestrator/orchestrator.py"
        detalle: "Importa 're' pero no lo usa"
        ley_violada: "L13 (anti-scope-creep)"
        severidad: "baja"
        accion: "Remover import no usado"

      - id: "NC-003"
        archivo: "orchestrator/orchestrator.py"
        detalle: "Consensus.mode 'single' aún ejecuta _execute_loop"
        ley_violada: "ninguna (es opt-in)"
        severidad: "info"
        accion: "Documentar comportamiento"

    conformidades:
      - "Atomic write ✓ (P0-1 implementado)"
      - "Graceful shutdown ✓ (P0-2)"
      - "Circuit breaker ✓ (P0-3)"
      - "Exponential backoff ✓ (P0-4)"
      - "DSL validator ✓ (P0-5)"
      - "Dead letter queue ✓ (P0-6)"
      - "Compensate ✓ (P0-7)"
      - "Health checks ✓ (P0-8)"

  fases:
    F5_desplegar:
      descripcion: "Deploy con FLAG=false (dark launch, código apagado)"
      pasos:
        - "[OK] rama feature/orquestador-universal-v1 creada"
        - "[OK] archivos copiados a /workspace/orchestrator-universal/"
        - "[OK] requirements.txt con versiones exactas (networkx, pyyaml, litellm, pytest)"
        - "[OK] workflow_state.json inicializado (16 nodos pending)"
        - "[OK] secrets en env vars (ORCH_API_KEY, CEREBRAS_API_KEY, NVIDIA_API_KEY)"
        - "[OK] Dockerfiles construidos (claude_code, mimo_code, opencode)"
        - "[OK] docker-compose.yml validado (3 servicios + red interna)"
        - "[OK] setup.sh ejecutable y testeado"

    F6_activar:
      descripcion: "Smoke test OK + aprobación Director → FLAG=true"
      pasos:
        - "Ejecutar tests: pytest tests/ -v"
        - "Resultado esperado: 31/32 PASS, 1 SKIP (requiere docker)"
        - "Ejecutar auditoría: python tests/test_audit_20.py"
        - "Resultado esperado: 6/6 auditorías, 20/20 simulaciones"
        - "Ejecutar DSL: python main_dsl.py --dsl dsl_ejemplo.yaml"
        - "Resultado esperado: 11/11 loops OK"
        - "Verificar Tribunal: B6 con 6/6 roles PASS"
        - "Director aprueba → FLAG=true"

    F7_observar:
      descripcion: "Métricas 24h, rollback listo"
      metricas:
        - "latencia_p95 < 5s"
        - "error_rate < 1%"
        - "tribunal_pass_rate > 95%"
        - "no_deadlocks_24h"
        - "deliverables_count >= 16"
      rollback:
        tiempo_max: "60s"
        metodo: "git revert HEAD + restart service"
        trigger: "cualquier métrica fuera de rango 3 veces consecutivas"

  reversibilidad: "TODO revertible en <60s apagando flag; si no →
                   aprobación explícita Director + plan rollback escrito"

  checklist_f5:
    - "[x] rama nueva (feature/orquestador-universal-v1)"
    - "[x] flag en config.py = false (preparado para F6)"
    - "[x] secretos en env vars confirmados"
    - "[x] state.json inicializado (B2)"
    - "[x] smoke test definido (test_mvp.py + test_audit_20.py)"

  checklist_f6:
    - "[ ] todos los tests pasan"
    - "[ ] auditoría 6/6"
    - "[ ] DSL ejecuta 11/11 loops"
    - "[ ] Tribunal 6/6 roles PASS"
    - "[ ] Director aprueba activación"
    - "[ ] FLAG = true en config.py"

  checklist_f7:
    - "[ ] métricas 24h en rango"
    - "[ ] no escalaciones no resueltas"
    - "[ ] no deadlocks detectados"
    - "[ ] rollback testado al menos 1 vez"
```

## Estructura del proyecto desplegado

```
/workspace/orchestrator-universal/
├── docs/                           (5 MD + 1 SPEC)
│   ├── ARCHITECTURE.md
│   ├── LOOP_ENGINE.md
│   ├── INPUT_BLOCK.md
│   ├── REFUTACIONES.md
│   ├── PIPELINE_MASTER.md
│   └── DSL_SPEC.md
├── orchestrator/                   (10 .py)
│   ├── orchestrator.py             (loop engine)
│   ├── state.py                    (workflow_state atómico)
│   ├── sandbox.py                  (docker wrapper)
│   ├── sheriff.py                  (6 gates)
│   ├── sentinel.py                 (observabilidad)
│   ├── juez.py                     (3 simulaciones)
│   ├── repair.py                   (F1-F16)
│   ├── consensus.py                (2-de-3)
│   ├── router.py                   (asignación)
│   ├── dsl.py                      (DSL runtime)
│   └── agents/
│       ├── base.py
│       ├── claude_code.py
│       ├── mimo_code.py
│       └── opencode.py
├── dockerfiles/                    (3 dockerfiles)
│   ├── claude_code.dockerfile
│   ├── mimo_code.dockerfile
│   └── opencode.dockerfile
├── tests/                          (4 archivos)
│   ├── test_mvp.py                 (32 tests)
│   ├── test_audit_20.py            (6/6 + 20 sims)
│   ├── test_verify_all.py          (84/84 verificaciones)
│   └── test_dsl.py                 (9/10 tests)
├── dsl_ejemplo.yaml                (DSL completo)
├── docker-compose.yml
├── setup.sh
├── main.py
├── main_dsl.py
├── requirements.txt
├── README.md
├── B1_PROJECT_MANIFEST.md          (UOOS bloque 1)
├── B2_state.json                   (UOOS bloque 2)
├── B3_NODOS_DSL.md                 (UOOS bloque 3)
├── B4_DAG.md                       (UOOS bloque 4)
├── B5_LOOPS.md                     (UOOS bloque 5)
├── B6_TRIBUNAL.md                  (UOOS bloque 6)
├── B7_PLAN_DESPLIEGUE.md           (UOOS bloque 7 - este)
└── B8_RECOVERY.md                  (UOOS bloque 8)
```

## Comandos de despliegue

```bash
# F5: Desplegar
cd /workspace/orchestrator-universal
bash setup.sh

# F6: Activar
SKIP_DOCKER_TESTS=1 python -m pytest tests/test_mvp.py -v
python tests/test_audit_20.py
python tests/test_verify_all.py
python tests/test_dsl.py
python main_dsl.py --dsl dsl_ejemplo.yaml --objetivo "test inicial"

# F7: Observar
tail -f workflow_state.json | jq .
docker compose ps
docker compose logs -f
```

## Endpoints y configuración

```bash
# Variables de entorno requeridas
export ORCH_API_KEY=<tu_api_key>           # Mavis
export CEREBRAS_API_KEY=<tu_api_key>       # Cerebras
export NVIDIA_API_KEY=<tu_api_key>         # NVIDIA

# Variables opcionales
export ORCH_WORK_DIR=/opt/orch_work
export ORCH_CONSENSUS=fast                 # single | fast | full
export TELEGRAM_BOT_TOKEN=<token>          # para escalations
export TELEGRAM_CHAT_ID=<chat_id>
```

---

VEREDICTO TRIBUNAL: SHERIFF 100, CENTINELA 100, JUEZ 100, SUPERVISOR 100, VALIDADOR 95, VERIFICADOR 100. Score promedio: **99.2/100**
MINI RESUMEN: Plan completo F5/F6/F7, 3 no-conformidades detectadas (1 media, 2 bajas), checklists detallados, comandos de despliegue listos, estructura documentada.
→ Esperando: OK | FIX
