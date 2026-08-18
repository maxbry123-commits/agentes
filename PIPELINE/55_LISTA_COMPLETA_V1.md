# PIPELINE 55 — LISTA COMPLETA V1 (1:1 con salidas)
**Fecha:** 2026-08-17 21:55  
**Fuente:** 52 + extras chat + formato Director

## Formato de lista (obligatorio)
Columnas: Salida | ID | Tarea | Trazabilidad docs | Objetivo | Estado
Agrupada por BLOQUE A–F + Extras chat.

### BLOQUE A — Método + mapa
| Salida | ID | Tarea | Trazabilidad docs | Objetivo | Estado |
|--------|-----|-------|-------------------|----------|--------|
| S01 | T01 | PIPELINE 00+52 método multi-instancia, COPY-FIRST, X-Ray | chat 17-ago · 00 · 52 | Ley de trabajo en repo | DONE |
| S02 | T02 | README arquitectura multi-instancia + diagrama texto | chat no-monolito · 00 §2 · 52 | Quién lee el repo entiende N instancias | PEND |
| S03 | T03 | ROOT MAP IDs canónicos | X-Ray spec · 52 | ID→path estable | PEND |
| S04 | T04 | X-Ray seed STATUS real extensions/* | árbol GitHub · 52 | No inventar IMPLEMENTED | PEND |
| S05 | T05 | Spec HTML mapa mental cascada | NCT/APEX · chat mapa | Contrato del HTML final | PEND |
| S06 | T06 | connect_catalog + list_connections stub | Punto 4 · 46 · 51 | Auto-conexión legible | PEND |

### BLOQUE B — Multi-instancia
| Salida | ID | Tarea | Trazabilidad | Objetivo | Estado |
|--------|-----|-------|--------------|----------|--------|
| S07 | T07 | WordflowInstance + registry | chat multi-instancia · 00 | N Wordflows sin reescribir kernel | PEND |
| S08 | T08 | state.json por instance_id | 00 · 52 | Aislamiento | PEND |
| S09 | T09 | spawn_wordflow(config/DNA) | Workflow DNA docs · 52 | Nueva instancia = config | PEND |
| S10 | T10 | Loader ficha.v2 → capability | Enchufe v2 · 07 | Extensions cargables | PEND |
| S11 | T11 | Bootstrap multi-instance aware | 51 C100-01 · bootstrap_v1 | Entry único | PEND |
| S12 | T12 | Fail_closed ficha / llm_control | 51 · invariantes 50 | Seguridad | PEND |

### BLOQUE C — C100
| Salida | ID | C100 | Tarea | Docs ancla | Punto | Estado |
|--------|-----|------|-------|------------|-------|--------|
| S13 | T13 | 01 | VERIFY bootstrap_v1 + E2E Fake | 51 · bootstrap_v1.py | P1 P6 | PEND |
| S14 | T14 | 02 | WIRE code_path→loop→publish + verify docs_templates | 51 · 47 · docs_templates/ | P1 | PEND |
| S15 | T15 | 03 | publish_path + AccountResolver enforced | 46 ACC · accounts/ | P2 | PEND |
| S16 | T16 | 04 | HF ResourceIndex dry-run | 46 HF · resources/ | P2 | PEND |
| S17 | T17 | 05 | Acquire recipe dry-run | 46 AQ · acquire_os | P3 | PEND |
| S18 | T18 | 06 | connect_catalog operativo en kernel | 46 P4 · component_catalog.json | P4 P5 | PEND |
| S19 | T19 | 07 | MemoryGateway unificado en bootstrap | 51 · memory_slot | P5a | PEND |
| S20 | T20 | 08 | EngineRegistry + attach policy | 51 · engines/ | P5b | PEND |
| S21 | T21 | 09 | UI plugin → GoalLock → code_path | 51 · ui_gateway · 46 GW | P7 | PEND |
| S22 | T22 | 10 | LLM ban gate scan | 51 · invariante loop | P1 P6 | PEND |
| S23 | T23 | 11 | CI matrix kernel+loop+deploy | 50 · workflows | P6 | PEND |
| S24 | T24 | 12 | Claim + README E2E links | 51 · 49 · README_V1 | P0 P4 | PEND |

### BLOQUE D — Path residual
| Salida | ID | Tarea | Trazabilidad | Objetivo | Estado |
|--------|-----|-------|--------------|----------|--------|
| S25 | T25 | Hooks 12-stage ↔ instance | 47 · stages/ · maxbry_loop | Loop continuo en instancia | PEND |
| S26 | T26 | IntelligenceGateway único LLM | 48 · gateway/ | Sin vendor directo | PEND |
| S27 | T27 | GatewayModel en maxbry_loop | 48 | Loop→Router | PEND |
| S28 | T28 | GoalLock ↔ loop goals | 47 · bridge/ | Marcadores→tareas | PEND |
| S29 | T29 | gaps → gap_tasks → code_path | 47 · gap_bridge | Gaps ejecutable | PEND |
| S30 | T30 | Claim≠Evidence packet | forensic · audit_forensic | Auditoría honesta | PEND |
| S31 | T31 | RepoTruthPort + Fake | 47 · repo_truth | Verdad repo | PEND |
| S32 | T32 | GitDataAPIPort dry-run no force_push | github_deploy · 46 DEP | Deploy seguro | PEND |
| S33 | T33 | Protected patterns + CONFLICT HOLD | deploy_config · 50 | No pisar protegidos | PEND |
| S34 | T34 | Evidence/provenance al cerrar | evidence_* · 50 | Trazabilidad fin path | PEND |

### BLOQUE E — Recursos / cuentas
| Salida | ID | Tarea | Trazabilidad | Objetivo | Estado |
|--------|-----|-------|--------------|----------|--------|
| S35 | T35 | ResourceContract schema estricto | 46 HF-01 · contract.py | Contrato skill/dataset | PEND |
| S36 | T36 | Índice HF PLAN_ONLY | chat HF · 50 | Índice sin fetch masivo | PEND |
| S37 | T37 | Router-res discover→load | Resource Brain · 52 | Bajo demanda | PEND |
| S38 | T38 | AccountRegistry enforced | 46 ACC · accounts/ | Multi-cuenta | PEND |
| S39 | T39 | token_ref only | 50 · credential | Secretos fuera del workflow | PEND |
| S40 | T40 | Slot plugin Kimi/Minimax solo conexión | 50 · chat | Preparar V1.1 sin fusion | PEND |

### BLOQUE F — Mapa + cierre
| Salida | ID | Tarea | Trazabilidad | Objetivo | Estado |
|--------|-----|-------|--------------|----------|--------|
| S41 | T41 | HTML mapa mental cascada | NCT/APEX · chat | Visión en 5 s | PEND |
| S42 | T42 | HTML X-Ray IDs | X-Ray spec | Radiografía | PEND |
| S43 | T43 | Matriz MISSING/PARTIAL post-code | Pasada 2 árbol | Estado real | PEND |
| S44 | T44 | README conectar motores OpenClaw/Hermes | 46 P5 · engines | Cómo attach | PEND |
| S45 | T45 | README Router + Memory | 46 · slots | Cómo conectar orch | PEND |
| S46 | T46 | Bitácora V1 vs V1.1 | 50 · 52 | Continuidad | PEND |
| S47 | T47 | Suite tests + comandos | tests/* · 50 | Reproducible | PEND |
| S48 | T48 | Re-audit 4 pasadas P0–P7 | 51 | Binario PASS | PEND |
| S49 | T49 | Claim V1 100% | 52 · CHAT_A yaml | Solo si S13–S48 PASS | PEND |

### Extras chat
| ID | Tarea | Trazabilidad | Estado |
|----|-------|--------------|--------|
| T0 | 4 motors + reception + knowledge | chat · motors/ · reception/ | DONE |
| T2 | Reception/conversion motor | chat · T0 | PEND |
| T2.1 | SDPA vía T2 | chat | PEND |
| T2.2 | MCR vía T2 | chat | PEND |
| T2.3 | 20M contexto vía T2 | chat | PEND |
| CG | Code-gen DSL/DAG/schema | chat | PEND |
| ARCH | Arquitectura final | chat · doc 🎯🔒 | PEND |
| DEL | Delete mavis-deploy-keys | chat | PEND |
| AUDIT-5 | Forense cada 5 tareas | PIPELINE/54 | RECURRENTE |
