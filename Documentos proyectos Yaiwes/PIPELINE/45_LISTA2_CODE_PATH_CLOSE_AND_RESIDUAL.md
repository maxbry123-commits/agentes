# PIPELINE 45 — Bitácora Lista 2 (code path) + residual sistema

**Fecha:** 2026-08-15  
**Repo:** maxbry123-commits/agentes  
**Fuente de verdad:** GitHub only  
**Claim sistema completo:** NO (núcleo + code path fuerte; no producto final)

---

## 1. Qué se cerró (Lista 2 / code path)

| ID | Entrega | Path principal |
|----|---------|----------------|
| C-01 | GoalLock | extensions/wordflow/engine/goal_lock.py |
| C-02 | Enchufe gate | extensions/wordflow/engine/enchufe_gate.py |
| C-03 | Validator fail_closed | extensions/wordflow/engine/validator.py |
| C-04 | Dual compiler + promote_12 | extensions/wordflow/engine/dual_compiler.py |
| C-05 | analyze_12 | extensions/wordflow/engine/analyze_12.py |
| C-06 | skill_native_compiler | extensions/wordflow/engine/skill_native_compiler.py |
| C-07 | EvidencePacket | extensions/wordflow/engine/evidence_packet.py |
| C-08 | ResourceRuntime lifecycle | extensions/wordflow/engine/resource_runtime.py |
| C-09 | cognitive_loop wire | extensions/wordflow/engine/cognitive_loop.py |
| C-10 | github_deploy + FakePort | extensions/github_deploy/ |
| C-11 | docs_templates (12) | extensions/wordflow/docs_templates/ |
| C-12 | role_analyzer + CouncilContract | extensions/wordflow/engine/role_analyzer.py |
| C-13 | input_quality_bar | extensions/wordflow/engine/input_quality_bar.py |
| C-14 | acquire_12 plan-only | extensions/wordflow/engine/acquire_12.py |
| C-15 | reuse_12 | extensions/wordflow/engine/reuse_12.py |
| C-16 | project_mirror | extensions/wordflow/engine/project_mirror.py |
| C-17 | repair_gate | extensions/wordflow/engine/repair_gate.py |
| C-18 | credential_store | extensions/wordflow/engine/credential_store.py |
| C-19 | code_path_runner | extensions/wordflow/engine/code_path_runner.py |
| C-21 | Mission Planner | extensions/wordflow/planner/ |
| C-22 | claim_validator | extensions/wordflow/engine/claim_validator.py |
| C-23 | Blackboard | extensions/wordflow/state/blackboard.py |
| C-24 | Ledger | extensions/wordflow/state/ledger.py |
| C-25 | Context builder | extensions/wordflow/context/ |
| C-26 | Policy engine seed | extensions/wordflow/engine/policy_engine.py |
| C-27 | Knowledge registry | extensions/knowledge/ |
| C-28 | Adapter contracts | extensions/adapters/ |
| C-29 | hf_resolver plan-only | extensions/wordflow/engine/hf_resolver.py |
| C-30 | dna_bundle | extensions/wordflow/engine/dna_bundle.py |
| C-31 | code_path_smoke | extensions/wordflow/engine/code_path_smoke.py |

**Commits representativos (cadena):**  
2e78cf50… → … → 16535d04 (C-31 smoke)

**Estado Lista 2:** DONE en código materializado.  
**Estado Wordflow total:** PARCIAL (ver residual).

---

## 2. Residual (NO hecho / diferido a propósito)

### P1 — Sistema completo
Falta: paralelo avanzado SSH multi-VPS, 85 contratos L2–L8, recovery amplio, motores reales, CI suite completa, loops Fase 4, fetch remoto activo.

### P2 — Fetch HF/GitHub
`POST_WORDFLOW_FETCH_ENABLED = False` en resource_gate.  
acquire_12 / hf_resolver devuelven PLAN_ONLY.

### P3 — OpenClaw/Hermes
Solo contratos EngineAdapter + engine_attach anotado. Sin adapters reales ni ficha de motor cargada en runtime.

### P4 — Fase 4 Minimax/Kimi loops
Docs en PIPELINE/30; sin loops/main|retry|recovery|evolution implementados como paquete de extensión.

### P5 — CI
Existen workflows puntuales (project_bootstrap, control-layer).  
No hay workflow único que ejecute todos los tests C-02…C-31 ni evidencia de run verde agregada.

### P7 — Deploy real
GitHubDeployer + token_ref + FakePort/DryRun.  
Sin GitDataAPI real ni token de producción en el repo.

---

## 3. Soluciones recomendadas (siguientes bloques)

| Punto | Solución |
|-------|----------|
| P1 | Definir Wordflow V1.1 residual numerado R1–R6; no reclamar 100% hasta CI+motores+fetch flag |
| P2 | Flag `POST_WORDFLOW_FETCH_ENABLED` + microkernel install + HF storage; activar solo con policy + token_ref |
| P3 | `extensions/engines/{openclaw,hermes}/` + ficha.v2 + EngineAdapter implementando execute(); Wordflow solo llama contrato |
| P4 | `extensions/wordflow/loops/{main,retry,recovery,evolution,watchdog}.yaml` + runner; lógica Minimax/Kimi como packages KER |
| P5 | Un workflow `test-wordflow-code-path.yml` que corra `python -m unittest discover` en tests nuevos |
| P7 | Port real Git Data API detrás del mismo Deployer; dry_run_default=true hasta Director authorize |

---

## 4. Microdiagrama residual

```
CODE_PATH(DONE) → CI_SUITE → ENGINE_ADAPTERS(ficha) → FETCH_FLAG → LOOPS_F4 → CLAIM_100
```

**llm_control:** DENY en todo el path determinista.
