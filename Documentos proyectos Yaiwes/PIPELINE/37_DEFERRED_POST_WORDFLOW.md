# PIPELINE/37 — Backlog post plan numerado (diferidos)

**Fecha:** 2026-08-14  
**Estado Wordflow numerado:** T0–T48 cerrados (salvo T3) · ver PIPELINE/36  
**HEAD ref:** https://github.com/maxbry123-commits/agentes/blob/main/PIPELINE/36_WORDFLOW_T25_T48_CLOSE.md

---

## Hecho (no reabrir sin gap)

- extensions/wordflow engine completo (mission, sheriff, bus, parallel, DNA, publish dry_run, HF index, orchestrator)
- control-layer/sheriff canónico 5 estados
- CI workflow test-wordflow.yml
- G1–G9 gaps cerrados (PIPELINE/35)

---

## Diferidos — lista de tareas

| ID | Tarea | Dependencia | Pri |
|----|-------|-------------|-----|
| D1 | Evidencia CI run verde (Actions) + claim run_id | T40 workflow | P1 |
| D2 | T3: wire PlanningPort/MemoryPort → engines reales OC/Hermes | HF compute + install | P0 post |
| D3 | Microkernel fetch real (git/HF) enable fetchable | D2 infra | P0 post |
| D4 | GitHubPublisher executor real (Git Data API) no dry_run | token store prod | P1 |
| D5 | SSH/Docker workers reales (hoy logical sandbox) | infra | P2 |
| D6 | Wordflow → control-layer Sheriff gate(CompilePlan+C00) | control package path | P1 |
| D7 | Fase 2 contratos B0–B8 (13 tipos routing) | PIPELINE/26 | P1 |
| D8 | Kimi cognitive runtime (PIPELINE/30) solo 10% gaps | policy | P2 |

---

## Política

1. No instalar OC/Hermes hasta Wordflow + HF compute (PIPELINE/32).  
2. No token en código / contratos.  
3. 1 tarea = 1 salida · commit real · claim.  

**SIGUIENTE al Ok del Director:** D1 (CI evidencia) o la ID que indique.
