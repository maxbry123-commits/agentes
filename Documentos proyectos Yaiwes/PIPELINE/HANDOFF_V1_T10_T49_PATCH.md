# HANDOFF PATCH — gaps + detalle extra (NO reemplaza el handoff)
**Ancla:** leer primero `PIPELINE/HANDOFF_V1_T10_T49.md` (NO borrar / NO editar ese archivo).  
**Este archivo:** solo información adicional detectada en auditoría.  
**Fecha:** 2026-08-18  
**Original:** https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/HANDOFF_V1_T10_T49.md

---

## AUDITORÍA 4 PASADAS (resultado)

### Pasada 1 — Cobertura de IDs
| Check | Resultado |
|-------|-----------|
| T10–T49 presentes (40) | PASS |
| Extras T2/T2.1/T2.2/T2.3/CG/ARCH/DEL/AUDIT-5 | PASS |
| T01–T09 marcados DONE | PASS |
| Orden ejecución | PASS (alineado 52) |

### Pasada 2 — Autocontención “qué programar”
| Check | Resultado |
|-------|-----------|
| T10–T12 firmas de funciones | PASS (detallado) |
| T13–T40 | **PARTIAL** — hay objetivo/path/función única pero faltan firmas mínimas y path de salida exacto en varias |
| T41–T49 | PARTIAL — paths OK; T41 necesita contrato CSS/bloques más literal |
| Criterio DONE / NO hacer | PASS en casi todas |

### Pasada 3 — Simulación “otra instancia ejecuta” (3 sims por bloque)
**Sim A (T10):** encuentra ficha_loader + ficha.v2 → ADAPT. Riesgo: no sabe campos exactos del JSON existente.  
**Sim B (T13):** paths genéricos bajo engine/; riesgo: crea archivos paralelos si no lista árbol real primero.  
**Sim C (T41):** spec resumida; riesgo: HTML incompleto vs SPEC_HTML_MAPA_MENTAL.md.  
**Mitigación en este PATCH:** reglas de inventario + firmas mínimas + contrato T41 + template forense.

### Pasada 4 — Método / leyes
| Check | Resultado |
|-------|-----------|
| 3 pasos sandbox→GH→forense | PASS en handoff |
| COPY-FIRST | PASS |
| LOC por archivo (≤300 diseño / review 800) | **FALTABA** → aquí |
| Forense code template | **FALTABA** → aquí |
| Update TAREAS_ACTUAL cada DONE | **FALTABA** → aquí |
| Inventariar árbol antes de GENERATE | **FALTABA** → aquí |

---

## GAPS CERRADOS EN ESTE PARCHE

### G-H1 — Inventario obligatorio antes de code
Antes de PASO 1 de cualquier T13+:
1. Listar paths existentes bajo `extensions/wordflow/`, `extensions/wordflow_kernel/`, `extensions/maxbry_loop/`, `extensions/github_deploy/`.
2. Si el módulo ya existe → **ADAPT/WIRE** (no crear `*_v2.py` paralelo).
3. Solo GENERATE si path MISSING real.

### G-H2 — Regla de tamaño de archivo
- Preferido: ≤800 LOC/archivo; diseño orientativo 300; si >1000 → partir módulos.
- No significa “hacer MVP”: calidad profesional, alcance completo de la ficha.

### G-H3 — Tras cada DONE
Actualizar `PIPELINE/TAREAS_ACTUAL.md`:
- TERMINADAS += 1
- SIGUIENTE = siguiente ID
- Commit separado o mismo commit de la tarea.

### G-H4 — Template forense paso 3 (code)
```
METHOD | TASK_REQ | TRACE | SANDBOX | LOCAL_VERIFY | GH_PUBLISH | REMOTE_VERIFY |
CONTENT | NO_UNAUTHORIZED | ARCH | CONNECT | CONTRACT | BEHAVIOR | TESTS | AI_NOT_PROOF
Gaps bloqueantes: 0 → DONE
LLM no declara PASS sin evidencia GH/smoke
```

### G-H5 — Firmas mínimas extra (C100 / residual)

**T13** `run_bootstrap_fake(instance_id: str = "v1") -> dict`  
keys: `stages: list[str]`, `ok: bool`, `instance_id: str`  
Salida sugerida: `extensions/wordflow_kernel/bootstrap_fake.py` o función en `bootstrap_multi.py`.

**T14** `bridge_run_fake(payload: dict) -> dict`  
keys: `status`, `stages`, `evidence`  
Preferir ADAPT `loop_bridge.py` / `code_path_runner.py`.

**T15** `resolve_account(account_id: str) -> dict`  
raise si missing; `publish_path` exige `account_id`.

**T16** `plan_index(resources: list) -> dict`  
**T17** `acquire_dry_run(recipe: dict) -> dict` con keys verify/build/promote  
**T18** `kernel_list_connections() -> list` wrapper a T06  
**T19** `class MemoryGateway: get(k)/set(k,v)`  
**T20** `class EngineRegistry: load(ficha)/attach(name, policy)/list()`  
**T21** `handle_message(msg: dict) -> dict`  
**T22** `scan_paths_for_llm_ban(roots: list[str]) -> list[dict]`  
**T23** archivo `.github/workflows/wordflow_smoke.yml`  
**T25** `run_stage(instance_id: str, n: int) -> dict`  
**T26** `IntelligenceGateway.complete(prompt: str) -> str`  
**T27** `GatewayModel.generate(prompt: str) -> str`  
**T28** `sync_goals(instance_id: str) -> dict`  
**T29** `enqueue_gap(gap: dict) -> str`  # task_id  
**T30** `validate_claim(claim: dict, evidence: dict) -> str`  # pass|fail  
**T31** `class FakeRepoTruth: get_file(path) -> str`  
**T32** `plan_push(..., force: bool=False)` → error si force  
**T33** paths: `extensions/github_deploy/` o publisher; `PROTECTED_PATTERNS: list[str]`; conflicto → `"HOLD"`  
**T34** `write_evidence(path_result: dict) -> dict`  
**T35** `validate_resource(obj: dict) -> list[str]`  
**T36** `build_plan_only(src) -> dict`  
**T37** `discover/map/select/load` 4 callables  
**T38** `AccountRegistry.register/get/list`  
**T39** path `deploy_config` / github_deploy; `token_ref: str` only  
**T40** archivo ficha `extensions/wordflow_kernel/slots/kimi_minimax_slot.json` status PLACEHOLDER

### G-H6 — Contrato T41 (completar spec)
Archivo único HTML+CSS inline. Secciones en orden: Visión → Kernel → Instance → WF.01 → WF.02 → WF.03 → hot path → loop → recursos → UI → PIPELINE.  
Cada nodo: id, title, status class, para_qué, sin_esto, link GH si existe.  
Colores: IMPLEMENTED verde / PARTIAL ámbar / MISSING rojo / PENDING gris.  
Fuente status: XRAY_SEED + ROOT_MAP (no inventar).  
Ver `PIPELINE/SPEC_HTML_MAPA_MENTAL.md`.

### G-H7 — Imports de paquete
Kernel se importa como paquete bajo `extensions/`:  
`PYTHONPATH=extensions python -m wordflow_kernel.spawn`  
Asegurar `extensions/wordflow_kernel/__init__.py` existe (crear vacío si MISSING).

### G-H8 — Explicación simple (opcional Director)
Si el Director pide lenguaje básico: en cada PASO 1/2/3 una tabla “Objetivo / Función” en 1–2 frases no jerga.

### G-H9 — Enlaces ancla adicionales
- Spec HTML: https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/SPEC_HTML_MAPA_MENTAL.md
- Forense 51: https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/51_FORENSE_CIERRE_100_PUNTOS_DIRECTOR.md
- LEY AUDIT-5: https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/54_LEY_AUDIT_5_Y_TRAZABILIDAD.md
- TAREAS_ACTUAL: https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/TAREAS_ACTUAL.md
- Este PATCH: https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/HANDOFF_V1_T10_T49_PATCH.md

---

## 3 SIMULACIONES RESUMEN (por tipo de tarea)

| Tipo | Sim1 | Sim2 | Sim3 | Gap residual |
|------|------|------|------|--------------|
| Kernel T10–12 | ADAPT loader | bootstrap 2 ids | fail_closed raise | Campos ficha: leer JSON real primero |
| C100 T13–24 | WIRE fake E2E | account fail | CI yaml | Listar árbol antes de crear path |
| Residual T25–34 | hooks aislados | gateway stub | claim≠evidence | No vendor LLM |
| Recursos T35–40 | schema fail | plan_only | token_ref | PLACEHOLDER slot |
| Cierre T41–49 | HTML spec | matriz honest | claim gated | T49 solo si T48 PASS |

---

## Instrucción final a la otra instancia
1. Abrir **HANDOFF** original.  
2. Abrir **este PATCH**.  
3. Ejecutar **T10** con 3 pasos.  
4. No modificar el archivo HANDOFF original; si aparece gap nuevo → crear `HANDOFF_V1_T10_T49_PATCH2.md`.

**Original intacto. Parche solo aditivo.**
