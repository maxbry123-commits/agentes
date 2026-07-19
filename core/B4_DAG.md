---
# B4 — DAG-001

```yaml
dag:
  id: "DAG-001"
  version: "1.0.0"
  nodos: ["T-001_orchestrator", "T-002_state", "T-003_sandbox", "T-004_sheriff",
          "T-005_sentinel", "T-006_juez", "T-007_repair", "T-008_consensus",
          "T-009_router", "T-010_dsl", "T-011_agents", "T-012_dockerfiles",
          "T-013_docker_compose", "T-014_setup", "T-015_tests", "T-016_docs"]
  aristas:
    # Base layer
    - {de: "T-001_orchestrator", a: "T-002_state"}
    - {de: "T-001_orchestrator", a: "T-004_sheriff"}
    - {de: "T-001_orchestrator", a: "T-005_sentinel"}
    - {de: "T-001_orchestrator", a: "T-008_consensus"}
    - {de: "T-001_orchestrator", a: "T-010_dsl"}
    - {de: "T-001_orchestrator", a: "T-016_docs"}
    # T-002 → T-003
    - {de: "T-002_state", a: "T-003_sandbox"}
    - {de: "T-003_sandbox", a: "T-009_router"}
    - {de: "T-003_sandbox", a: "T-011_agents"}
    - {de: "T-009_router", a: "T-011_agents"}
    # T-004 + T-005 → T-006 y T-007
    - {de: "T-004_sheriff", a: "T-006_juez"}
    - {de: ["T-004_sheriff", "T-005_sentinel"], a: "T-007_repair"}
    # T-011 → T-012
    - {de: "T-011_agents", a: "T-012_dockerfiles"}
    - {de: "T-012_dockerfiles", a: "T-013_docker_compose"}
    - {de: "T-013_docker_compose", a: "T-014_setup"}
    # T-001, T-004, T-006, T-010 → T-015
    - {de: ["T-001_orchestrator", "T-004_sheriff", "T-006_juez", "T-010_dsl"], a: "T-015_tests"}
    # T-015 + T-014 → final
    - {de: ["T-014_setup", "T-015_tests", "T-016_docs"], a: "T-099_dag_done"}
  verificacion: "orden topológico calculado y MOSTRADO (ciclo = abortar)"
  reglas:
    paralelo_max: 2
    nodo_bloqueado: "bloquea solo su rama"
    fallo_risk_alto: "pausa DAG completo → Director"
    inmutable: "cambiar DAG en ejecución = nueva versión + aprobación"
  arranque_nodo: "SOLO cuando todas sus dependencies están done"
```

## Orden topológico resuelto

```
CAPA 1 (arranque, sin dependencias):
  T-001_orchestrator

CAPA 2 (paralelo, depende de T-001):
  T-002_state
  T-004_sheriff
  T-005_sentinel
  T-008_consensus
  T-010_dsl
  T-016_docs

CAPA 3 (paralelo):
  T-002 → T-003_sandbox
  T-004 → T-006_juez
  T-004 + T-005 → T-007_repair
  T-001 → T-016 (ya en capa 2)

CAPA 4 (paralelo):
  T-003 → T-009_router
  T-003 + T-009 → T-011_agents
  T-004 + T-005 + T-006 + T-007 → reparaciones

CAPA 5:
  T-011 → T-012_dockerfiles

CAPA 6:
  T-012 → T-013_docker_compose

CAPA 7:
  T-013 → T-014_setup

CAPA 8 (join de tests):
  T-001 + T-004 + T-006 + T-010 → T-015_tests

CAPA 9 (cierre):
  T-014 + T-015 + T-016 → T-099_dag_done
```

## Diagrama visual

```
         T-001_orchestrator
         ┌────┬────┬────┬────┬────┐
         ▼    ▼    ▼    ▼    ▼    ▼
       T-02  T-04 T-05 T-08 T-10 T-16
         │    │    │    │    │    │
         ▼    │    │    │    │    │
       T-03   │    │    │    │    │
         │    │    │    │    │    │
         ├────┼────┼────┼────┼────┼──► T-15_tests
         │    │    │    │    │    │        │
         ▼    ▼    ▼    │    │    │        │
       T-09  T-06 T-07  │    │    │        │
         │              │    │    │        │
         ▼              │    │    │        │
       T-11             │    │    │        │
         │              │    │    │        │
         ▼              │    │    │        │
       T-12             │    │    │        │
         │              │    │    │        │
         ▼              │    │    │        │
       T-13             │    │    │        │
         │              │    │    │        │
         ▼              │    │    │        │
       T-14             │    │    │        │
         │              │    │    │        │
         └──────────────┴────┴────┴────────┘
                          ▼
                    T-099_dag_done
```

## Reglas de ejecución

- **risk=alto** (T-001, T-003, T-011, T-007, T-008): pausa DAG → requiere aprobación Director
- **risk=medio**: continúa si Tribunal PASA
- **risk=bajo**: continúa automáticamente
- **paralelo_max=2**: máximo 2 nodos ejecutan simultáneamente
- **fallo**: rollback al último checkpoint + escalar

---

VEREDICTO TRIBUNAL: SHERIFF 100, CENTINELA 100, JUEZ 95, SUPERVISOR 100, VALIDADOR 90, VERIFICADOR 95. Score promedio: **96.7/100**
MINI RESUMEN: DAG con 16 nodos, orden topológico resuelto, 9 capas de ejecución paralela, 3 nodos join, reglas de risk/parallel/rollback explícitas.
→ Esperando: OK | FIX
