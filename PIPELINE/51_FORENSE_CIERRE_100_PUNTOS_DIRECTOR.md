# PIPELINE 51 — Forense cierre 100% puntos Director (Opción 1)

**HEAD base:** aa572717… (pre-cierre)  
**Regla:** no COMPLETED sin path+blob+tests; GitHub = verdad; 0% sandbox storage.  
**Rechazo Director:** PARCIAL / MVP / “casi” = NO aceptable en estos puntos.

---

## 0. Veredicto forense por punto (estado REAL antes de C100)

| Punto | Claim previo | Estado forense | Gap crítico para 100% |
|-------|--------------|----------------|------------------------|
| **P0** PIPELINE residual audit | Doc 50 existe | **DOC OK / cierre operativo NO** | Trazabilidad doc→módulo→test por cada residual R2; bitácora viva |
| **P1** docs→code→loop→deploy | code_path + loop + deploy | **NO 100%** | `code_path_runner` NO invoca maxbry_loop ni GitDataAPIPort; cognitive_loop corta el path |
| **P2** multi GH + HF nativo | accounts + resources | **NO 100%** | publish_path no usa AccountResolver de forma obligatoria; HF FETCH_ENABLED=false sin dry-run index completo |
| **P3** download agentes/software | acquire_os OFF | **NO 100%** | Recipe runner no ejecuta pipeline verify/build/promote en modo dry-run cerrado; OpenClaw solo example yaml |
| **P4** README + auto-conexión | README_V1 | **NO 100%** | Wordflow runtime no expone `connect_catalog` legible por el propio motor; README no enlaza tests E2E |
| **P5a** Router + Osquestador memoria | slots | **NO 100%** | MemoryGateway unificado ausente en wordflow/engine; solo adapter aislado |
| **P5b** cualquier agente como motor | EnginePort stubs | **NO 100%** | Registry no carga fichas motor desde disco; no attach policy enforced en code_path |
| **P6** lo necesario para funcionar esta semana | núcleo disperso | **NO 100%** | Falta bootstrap canónico único + E2E Fake |
| **P7** UI plugin webui/chat | ui_gateway ACK | **NO 100%** | handle() no arranca GoalLock→code_path |

**Conclusión:** existencia de piezas = SÍ. Cadena integrada 100% = NO. El error fue marcar “operativo V1” sin cableado E2E demostrable.

---

## 1. Ask council (síntesis 12 pasos) — aplica a cada punto

1. ¿Qué exige el INPUT_BLOCK literal?  
2. ¿Qué path de código lo materializa hoy?  
3. ¿Hay test Fake que demuestre el flujo extremo a extremo?  
4. ¿Hay bypass LLM (openai/anthropic/direct key)?  
5. ¿Deploy/token solo credential_ref?  
6. ¿Loop usa GatewayModel no vendor?  
7. ¿EvidencePacket con claim≠evidence?  
8. ¿Enchufe ficha.v2 con llm_control DENY?  
9. ¿Documentado en PIPELINE + README con enlaces?  
10. ¿Un solo bootstrap canónico?  
11. ¿CI o unittest invocable offline?  
12. ¿Criterio de cierre binario (PASS/FAIL) sin PARCIAL?

---

## 2. Criterio 100% (binario)

Un punto está **100%** solo si:

- Código en GitHub en path declarado  
- Test offline que ejecuta el flujo del punto con FakePort  
- Sin vendor LLM directo en ese path  
- PIPELINE actualizado con sha/commit  
- README o connect_catalog apunta al path

---

## 3. Lista de tareas cierre C100 (orden estricto)

| ID | Tarea | Punto | Criterio cierre |
|----|-------|-------|-----------------|
| **C100-01** | Bootstrap canónico `wordflow_kernel/bootstrap_v1.py`: GoalLockView→stages→maxbry_loop→code_path→deploy Fake | P1 P6 | test E2E Fake PASS |
| **C100-02** | Extender `code_path_runner`: tras cognitive → optional maxbry_loop iteration bridge → publish_path Fake | P1 | test_code_path_full PASS |
| **C100-03** | `publish_path` **requiere** AccountResolver; multi-account matrix test | P2 | test multi account PASS |
| **C100-04** | HF `ResourceIndex` dry-run completo (skills/datasets/adapters) sin FETCH real | P2 | test index PASS |
| **C100-05** | Acquire dry-run: load recipe → verify/build/promote **simulado** + state.json + fail si FAILED | P3 | test recipe dry-run PASS |
| **C100-06** | `connect_catalog.json` + API `list_connections()` en kernel | P4 P5 | test catalog PASS |
| **C100-07** | `MemoryGateway` unificado (local | router HTTP) cableado en bootstrap | P5a | test memory path PASS |
| **C100-08** | `EngineRegistry` load from ficha dir + attach policy fail_closed | P5b | test attach PASS |
| **C100-09** | UI plugin: message → GoalLock → code_path (Fake) → response | P7 | test UI path PASS |
| **C100-10** | LLM ban gate: scan engine paths; test fails if openai/anthropic raw | P1 P6 | test ban PASS |
| **C100-11** | CI workflow matrix kernel+loop+deploy+accounts | P6 | workflow file + unittest |
| **C100-12** | PIPELINE 52 claim final + README_V1 actualizado con E2E | P0 P4 | docs + links |

**Total salidas C100:** 12  
**Kimi/Minimax full fusion code:** sigue R2 (fuera del 100% Opción1 Director; solo slot plugin si hace falta en C100-08).

---

## 4. Trazabilidad documentos → cierre

| Doc / origen | Tareas |
|---------------|--------|
| INPUT_BLOCK 6 puntos Director | C100-01…12 |
| maxbry_loop / continuous | C100-01 C100-02 |
| Gateway Router FastAPI | C100-07 C100-10 |
| Acquire Recipe (no OS) | C100-05 |
| Forensic claim≠evidence | C100-02 evidence |
| Enchufe v2 | C100-06 C100-08 C100-09 |
| GitHub multi-account + deploy | C100-03 |
| HF resources | C100-04 |

---

## 5. Orden de ejecución

```text
C100-01 → C100-02 → C100-10 → C100-03 → C100-04
  → C100-05 → C100-07 → C100-08 → C100-09 → C100-06
  → C100-11 → C100-12
```

Una tarea = una salida = commit GitHub.  
Al terminar C100-12: re-auditoría 4 pasadas; solo entonces claim 100% por punto.

---

## 6. Enlaces

- Repo: https://github.com/maxbry123-commits/agentes  
- Kernel: https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow_kernel  
- Loop: https://github.com/maxbry123-commits/agentes/tree/main/extensions/maxbry_loop  
- code_path: https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py  

**Estado lista C100:** 0/12  
**Siguiente:** C100-01 bootstrap canónico
