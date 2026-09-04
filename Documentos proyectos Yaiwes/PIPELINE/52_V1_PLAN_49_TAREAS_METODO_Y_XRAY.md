# PIPELINE 52 — Plan V1 100% · 49 tareas · Método + Forensic X-Ray

**Fecha:** 2026-08-17  
**Repo verdad:** https://github.com/maxbry123-commits/agentes  
**Regla:** 0% sandbox como almacenamiento · GitHub = única fuente de verdad  
**Fuera de V1 (explícito):** fusión Minimax + Kimi k completa → **V1.1** (code del Director listo; COPY/MOVE tras V1)

---

## 1. Método de trabajo (LEY — ampliar PIPELINE 00)

### 1.1 Arquitectura canónica

```
KERNEL (estable, pequeño)
  │
  ├── WordflowInstance A  (aislado: goals, state, loops, evidence)
  ├── WordflowInstance B
  └── WordflowInstance N

EXTENSIONS / CAPABILITIES (enchufe ficha.v2)
  ├── engines / adapters / connectors
  ├── skills / datasets index (HF bajo demanda)
  └── plugins (UI, router slot, memory slot)
```

- **No monolítico:** un kernel, N instancias; crear instancia ≠ reescribir kernel.
- **Extensión capacidad ≠ instancia:** capability = paquete cargable; instancia = ejecución/proyecto.

### 1.2 Operación de código existente (ahorro tokens)

```
INGEST (md/py/zip en repo)
  → HASH
  → TYPE DETECT
  → DESTINATION RESOLVER (bajo kernel multi-instancia + extensions)
  → COPY / MOVE
  → IMPORT CHECK → CONTRACT CHECK → DEPENDENCY CHECK

OK  → REGISTER + VERIFY
FAIL → AGENT mínimo: PATCH → ADAPT → GENERATE LAST
```

Prioridad fija: **COPY/MOVE → LINK/CONNECT → PATCH → ADAPT → GENERATE**.
Nunca regenerar código reutilizable. SHA-256 antes/después en COPY.

### 1.3 Forensic X-Ray + mapa mental

Cada elemento del Wordflow lleva **ID único** estable:

`[WF.xx]` → `[FILE.xxx]` → path real → `[FN.x]` → `[CONN]` → `[TOOL]` → `[SCHEMA]`

Estados reales solo: `IMPLEMENTED | PARTIAL | MISSING | PENDING | PLACEHOLDER | DEPRECATED | EXTERNAL | UNKNOWN`

Mapa mental (estilo NCT/APEX cascada): cada bloque con `→ Para qué` / `→ Sin esto`.
Entrega HTML en GitHub + copia en chat al cerrar bloques.

### 1.4 Criterio 100% (binario)

- Código en path declarado en GitHub  
- Test Fake/offline del flujo  
- Sin vendor LLM directo en path  
- PIPELINE + enlace que abre el archivo  
- Sin claim PARCIAL/MVP en puntos de cierre V1

### 1.5 Formato de salida por tarea

```
# CONTROL DE TRABAJO
1. TOTAL DE TAREAS EN CURSO:
2. TOTAL DE TAREAS TERMINADAS:
3. TAREA FALTANTE / SIGUIENTE:
4. ENLACE GITHUB (abre archivo directo):
5. CONFIRMACIÓN: NO uso sandbox como almacenamiento
```

Una tarea = una salida = commit GitHub.

---

## 2. Inventario consolidado (chat + PIPELINE 00–51)

| Fuente | Qué aporta al plan |
|--------|--------------------|
| PIPELINE 51 C100 | 12 tareas cierre puntos Director |
| Chat 2026-08-17 | multi-instancia, COPY-FIRST, X-Ray, mapa HTML |
| PIPELINE 43–50 | code_path residual, loops gateway, punto0 |
| PIPELINE 37/39 | diferidos post-Wordflow (sin Kimi fusion en V1) |
| PIPELINE 00 | LOC≤300, loops YAML, 6 niveles |

**Sí: se ejecutan todas las postergadas de V1 listadas abajo (~49).**  
**No en V1:** fusión Minimax/Kimi runtime completa (V1.1).

---

## 3. Lista maestra de tareas V1 (49)

### BLOQUE A — Fundamento método + mapa (T01–T06)

| ID | Tarea | Criterio cierre |
|----|-------|-----------------|
| **T01** | Actualizar PIPELINE 00 + 52 (este doc) método multi-instancia + COPY-FIRST + X-Ray | commit + enlace |
| **T02** | README arquitectura: Kernel multi-instancia + extensions + diagrama texto | path README |
| **T03** | ROOT MAP IDs canónicos (kernel/, extensions/, instances/, connections/) | doc ID table |
| **T04** | X-Ray seed: matriz FILE existentes extensions/wordflow* status real | tabla STATUS |
| **T05** | Spec HTML mapa mental cascada (estructura NCT/APEX + IDs) | HTML en repo |
| **T06** | connect_catalog.json skeleton + list_connections API stub | test catalog |

### BLOQUE B — Kernel multi-instancia (T07–T12)

| ID | Tarea | Criterio cierre |
|----|-------|-----------------|
| **T07** | `WordflowInstance` dataclass + registry (create/get/list) | test instance |
| **T08** | Instance state isolation (state.json por instance_id) | test isolation |
| **T09** | spawn_wordflow(config/DNA) sin tocar código de otras instancias | test spawn |
| **T10** | Extension loader: ficha.v2 → register capability | test load |
| **T11** | Bootstrap multi-instance aware (default instance_id=v1) | test bootstrap |
| **T12** | Fail_closed si ficha inválida / llm_control no DENY donde aplique | test gate |

### BLOQUE C — C100 puntos Director (T13–T24) = C100-01…12

| ID | = C100 | Tarea | Punto |
|----|--------|-------|-------|
| **T13** | C100-01 | Bootstrap canónico GoalLock→loop→code_path→deploy Fake | P1 P6 |
| **T14** | C100-02 | code_path_runner → maxbry_loop bridge → publish Fake | P1 |
| **T15** | C100-03 | publish_path requiere AccountResolver multi-account | P2 |
| **T16** | C100-04 | HF ResourceIndex dry-run (skills/datasets/adapters) | P2 |
| **T17** | C100-05 | Acquire recipe dry-run verify/build/promote simulado | P3 |
| **T18** | C100-06 | connect_catalog + list_connections en kernel | P4 P5 |
| **T19** | C100-07 | MemoryGateway unificado cableado bootstrap | P5a |
| **T20** | C100-08 | EngineRegistry load fichas + attach policy | P5b |
| **T21** | C100-09 | UI plugin message→GoalLock→code_path Fake | P7 |
| **T22** | C100-10 | LLM ban gate scan paths | P1 P6 |
| **T23** | C100-11 | CI workflow matrix kernel+loop+deploy | P6 |
| **T24** | C100-12 | Claim final + README E2E links | P0 P4 |

### BLOQUE D — Code path / loops / gateway residual (T25–T34)

| ID | Tarea | Criterio cierre |
|----|-------|-----------------|
| **T25** | Continuous loop 12-stage hooks cableados a instance | test hooks |
| **T26** | IntelligenceGateway only path for LLM (RouterHTTP stub) | test gateway |
| **T27** | GatewayModel en maxbry_loop (no vendor directo) | test model |
| **T28** | GoalLock ↔ loop goals bridge | test bridge |
| **T29** | Gaps → gap_tasks → code_path_runner bridge | test gaps |
| **T30** | Forensic auditor Claim≠Evidence packet | test claim |
| **T31** | RepoTruthPort + FakePort | test repotruth |
| **T32** | GitDataAPIPort dry-run + no force_push | test gitdata |
| **T33** | Protected patterns deploy + CONFLICT HOLD | test protect |
| **T34** | Evidence/provenance write al cerrar path | test evidence |

### BLOQUE E — Recursos HF / skills / deploy nativo (T35–T40)

| ID | Tarea | Criterio cierre |
|----|-------|-----------------|
| **T35** | ResourceContract schema estricto skills/datasets/adapters | schema + test |
| **T36** | Índice remoto HF (PLAN_ONLY / dry-run) sin saturar GitHub | test index |
| **T37** | Router micro-kernel: discover→map→select→load bajo demanda | test router-res |
| **T38** | Multi-account GitHub AccountRegistry enforced | test accounts |
| **T39** | Deploy config + token_ref only (nunca token en log) | test secret |
| **T40** | Plugin slot Kimi/Minimax **solo conexión** (sin fusion code V1) | ficha slot |

### BLOQUE F — Mapa HTML + cierre V1 (T41–T49)

| ID | Tarea | Criterio cierre |
|----|-------|-----------------|
| **T41** | HTML mapa mental cascada completo (visión→ensamblaje) | HTML GitHub |
| **T42** | HTML X-Ray por WF bloques con IDs | HTML GitHub |
| **T43** | Matriz pendientes MISSING/PARTIAL actualizada post-code | tabla |
| **T44** | README_V1: cómo conectar motores (OpenClaw/Hermes slots) | README |
| **T45** | README_V1: cómo conectar Router + Memory orch | README |
| **T46** | Bitácora PIPELINE final V1 (qué cerrado / qué V1.1) | PIPELINE |
| **T47** | Suite tests offline documentada + comandos | docs/tests |
| **T48** | Re-auditoría 4 pasadas puntos P0–P7 | report PASS |
| **T49** | Claim V1 100% + enlaces archivo directo | claim YAML |

**Total tareas V1: 49**  
**Total salidas: 49** (1 tarea = 1 salida)

---

## 4. Orden de ejecución

```
T01 → T02 → T03 → T04
  → T07 → T08 → T09 → T10 → T11 → T12
  → T13 (C100-01) → T14 → T22 → T15 → T16 → T17
  → T19 → T20 → T21 → T18 → T23 → T24
  → T25…T34 (residual path)
  → T35…T40 (recursos)
  → T05 → T06 → T41…T49 (mapa + cierre)
```

Ajuste permitido: COPY/MOVE de code que el Director suba puede colapsar varias T en una salida si SHA verifica y solo hay relocate.

---

## 5. Fuera de V1 (V1.1 / residual punto 0)

- Fusión Minimax + Kimi k NCT continuous mode completo (code Director listo)
- Fetch real HF/GitHub post-PLAN_ONLY
- 85 contratos L2–L8 literales completos (semilla + plan B ya existe)
- DSL lexer/parser propio
- Auto-recovery 200 estrategias

---

## 6. Estado actual

| Métrica | Valor |
|---------|-------|
| Tareas V1 totales | **49** |
| Terminadas (este plan) | **0** (T01 se materializa con este commit de doc) |
| C100 previas en código | verificar en T13; no claim 100% sin re-audit |
| Siguiente | **T01** (este archivo) luego **T02** |

---

## 7. Enlaces base

- PIPELINE: https://github.com/maxbry123-commits/agentes/tree/main/PIPELINE  
- Este plan: https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md  
- Método 00: https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md  
- Forense 51: https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/51_FORENSE_CIERRE_100_PUNTOS_DIRECTOR.md  
