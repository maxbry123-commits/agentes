# PIPELINE 48 — Arquitectura V1: Loop → Gateway → Router

**Fecha:** 2026-08-15  
**Repo:** maxbry123-commits/agentes  
**Fuente de verdad:** GitHub only  
**Reemplaza decisiones de:** PIPELINE 47 §C en lo relativo a model.execute directo

---

## 1. Fronteras (inmutables V1)

```
LOOP CONTROLLER (maxbry_loop v2 fusionado + 12-stage hooks + code-path)
  Tasks / DAG / Gaps / Trace / Verify / Retry / Acquire Engine
        │
        │  necesita LLM o memoria
        ▼
INTELLIGENCE GATEWAY (contrato estable)
  task_id + trace_id + capability + policy + payload
        │
        ▼
ROUTER UNIVERSAL (otro repo / FastAPI) — HTTP client, NO código copiado
  routing / providers / failover / health / credentials
        │
   ┌────┴────┐
   ▼         ▼
LLM PROVIDERS    MEMORY ORCHESTRATOR → Extension Kernel → DB
(Grok, Claude…)     (no Xata directo desde Loop)
```

**Prohibido en producción:** Loop → OpenAI/Anthropic directo.  
**Permitido offline:** MockAdapter.  
**OpenClaw / Hermes:** motores de **razonamiento intermedio** (Wordflow ↔ LLM) vía EnginePort; no son el Loop ni el Router.

---

## 2. Fusión de loops (qué se monta)

| Pieza | Rol en V1 |
|-------|-----------|
| maxbry_loop v2 | Continuous work loop (gaps → tasks → completion) |
| 12-stage loop | Hooks por etapa (enter/exit/trace) sobre el mismo controller |
| code_path C-01…C-31 | Path determinista de code invocado como **tasks** del loop |
| cognitive_loop existente | Absorbedo: wire council/plan dentro de stages |
| Kimi/Minimax fusion | **Slot plugin** en extensión; code R2 |

Un solo controller; tres modos de trabajo, no tres kernels.

---

## 3. Contratos nuevos (código a materializar)

```python
# IntelligenceGateway — único punto LLM/memoria desde el Loop
class IntelligenceGateway(Protocol):
    def execute(
        self,
        task_id: str,
        trace_id: str,
        capability: str,  # llm.complete | memory.recall | memory.capture
        payload: dict,
        policy: dict | None = None,
    ) -> dict: ...

class MockIntelligenceGateway:  # offline tests
    ...

class RouterHTTPGateway:  # producción
    # POST {router_url}/api/router/execute
    ...

# EnginePort — OpenClaw / Hermes como razonamiento intermedio
class EnginePort(Protocol):
    def reason(self, ctx, messages, policy) -> dict: ...

# Acquire Engine — no "ACQUIRE-OS"
# Recipes/*.yaml → TaskGraph determinista → verifier
```

Request canónico al Router:

```json
{
  "request_id": "REQ-...",
  "task_id": "TASK-...",
  "trace_id": "TRACE-...",
  "operation": "llm.complete",
  "policy": {"max_cost": 0.05, "max_latency_ms": 30000, "required_capabilities": ["coding"]},
  "input": {"messages": []}
}
```

---

## 4. OpenClaw + Hermes (fusión de rol)

- **No** ejecutan el continuous loop.  
- **Sí** se registran como `EngineAdapter` bajo EnginePort.  
- Cuando una task del loop tiene `capability: reasoning` o el policy exige LLM:  
  Loop → Gateway → Router **o** Loop → EnginePort.reason (OpenClaw/Hermes) → resultado al Loop.  
- En V1: stubs + contrato; cableado real cuando Router FastAPI esté up (flag `ROUTER_URL`).

---

## 5. Lista de tareas V1 actualizada (~38 salidas)

### Bloque 0 — Base (3)
| ID | Tarea |
|----|-------|
| V0-01 | CI workflow test-wordflow-code-path |
| V0-02 | component_catalog.json |
| V0-03 | Bitácora PIPELINE 48 en README fragment |

### Bloque G — Gateway + Router client (4)
| ID | Tarea |
|----|-------|
| VG-01 | IntelligenceGateway Protocol + Mock |
| VG-02 | RouterHTTPGateway (FastAPI client) |
| VG-03 | EnginePort + stubs OpenClaw/Hermes |
| VG-04 | Tests offline Mock + contract shapes |

### Bloque K — Kernel extension zip (6)
| ID | Tarea |
|----|-------|
| VK-01 | Montar wordflow_kernel (runtime, workflow, models) sin pycache |
| VK-02 | repo_truth + forensic |
| VK-03 | gap_tasks |
| VK-04 | memory/checkpoint/ledger/trace |
| VK-05 | resources + validator |
| VK-06 | tests + ficha.v2 kernel |

### Bloque L — Continuous loop fusionado (6)
| ID | Tarea |
|----|-------|
| VL-01 | Montar maxbry_loop v2 (engine, gaps, persistence, convergence) |
| VL-02 | **Eliminar** model OpenAI directo; inyectar IntelligenceGateway |
| VL-03 | 12-stage hooks integrados al controller |
| VL-04 | Bridge GoalLock → loop goals/tasks |
| VL-05 | Bridge gaps → gap_tasks → mission_planner / code_path tasks |
| VL-06 | Tests mock gateway + completion_score |

### Bloque F — Forensic (3)
| ID | Tarea |
|----|-------|
| VF-01 | RepoTruthPort local/GitHub |
| VF-02 | CrossVerifier |
| VF-03 | forensic.audit → EvidencePacket + tasks |

### Bloque A — Accounts + Deploy (4)
| ID | Tarea |
|----|-------|
| VA-01 | AccountRegistry |
| VA-02 | Workspace→account DENY |
| VA-03 | GitDataAPIPort flag |
| VA-04 | Tests Fake |

### Bloque H — HF (4)
| ID | Tarea |
|----|-------|
| VH-01…04 | ResourceContract, Skill IR, Dataset/Space, Factory PLAN_ONLY |

### Bloque Q — Acquire Engine (5)
| ID | Tarea |
|----|-------|
| VQ-01 | acquire engine core/verify/build/promote |
| VQ-02 | ficha + config OFF |
| VQ-03 | Recipe Graphify |
| VQ-04 | Recipe OpenClaw-40 (instancia, no motor) |
| VQ-05 | Tests SKIPPED_EXPECTED |

### Bloque D — Docs/Gateway UI (3)
| ID | Tarea |
|----|-------|
| VD-01 | Wire loop + code_path + docs_templates |
| VD-02 | README mapa fronteras Loop/Gateway/Router |
| VD-03 | Gateway mission API UI |

**Total:** 3+4+6+6+3+4+4+5+3 = **38 salidas**

**Orden:** V0 → VG → VK → VL → VF → VA → VH → VQ → VD

---

## 6. Residual R2 (sin cambio de lista; anclas)

Router full, Osquestador real, Kimi/Minimax fusion code, FETCH ON, 85 contratos, parallel 50, post-deploy re-audit — ver PIPELINE 47 §D.

---

## 7. Criterio DONE V1

- Loop fusionado no llama LLM directo  
- Mock tests verdes  
- RouterHTTPGateway listo con `ROUTER_URL`  
- OpenClaw/Hermes stubs EnginePort  
- Acquire Engine + recipes  
- Forensic gap→task  
- README fronteras  
- Flags OFF por defecto  
