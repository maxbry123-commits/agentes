# PIPELINE/35 — Gaps G1–G9 CERRADOS · T25 desbloqueado

**Fecha:** 2026-08-14  
**Repo:** maxbry123-commits/agentes  
**HEAD gaps:** ver commits G1–G8 abajo  

---

## 1 · G1 Input canónico — DONE

| Artefacto | Rol |
|-----------|-----|
| **InputContract + input_compiler** | **CANÓNICO** |
| input_block | LEGACY — no código nuevo |

Gap **G-S1-01** → RESUELTO  
Commit G1: https://github.com/maxbry123-commits/agentes/commit/1d4d57bd4924bc66620cfb99b785ec7d9b92d6c7

---

## 2 · Salidas G2–G8 — DONE (commits)

| ID | Commit | Entrega |
|----|--------|--------|
| G2 | https://github.com/maxbry123-commits/agentes/commit/05a1c595ca5c394f8facb2023bb983735178c714 | `loop_bridge` → GoalLock |
| G3 | https://github.com/maxbry123-commits/agentes/commit/7466b818804fb69186ce195774cf0df0e59516a1 | `bridge_full` echo/registers/classify/ping |
| G4 | https://github.com/maxbry123-commits/agentes/commit/e38cfe06d48ca8d7a47f0f7cd3813360158cc8c3 | `execution_facade` resource vs Bus |
| G5 | https://github.com/maxbry123-commits/agentes/commit/3ff1e6275d8efda6341cf5e76bd6402bb8af681b | `parallel_facade` no bypass |
| G6 | https://github.com/maxbry123-commits/agentes/commit/05ae1e9c8efdb9b02e17d83bacfbd38fe0e4a6e6 | Guarded SCOPE Bus out |
| G7 | https://github.com/maxbry123-commits/agentes/commit/1bdfdb94ad5dac241d77cf5b9ca44b8492df758c | policy + ports exports |
| G8 | https://github.com/maxbry123-commits/agentes/commit/b379c6e7f9a7da894862b63d8ee67ed886c38469 | tests P0 integration |

---

## 3 · Mapa gap → estado

| Gap | Estado |
|-----|--------|
| G-S1-01 Input canónico | **CLOSED** G1 |
| G-S1-02 main_loop anchors | **MITIGATED** G2–G3 (`bridge_full` disponible; main_loop puede llamar) |
| G-S2-02 engine_attach.yaml | **CLOSED** G7 |
| G-S2-03 ports exports | **CLOSED** G7 |
| G-S3-05 / G-S4-02 dual path | **MITIGATED** G4–G5 facade |
| G-S4-03 Guarded scope | **CLOSED** G6 |
| G-S1-03 CI | **DEFERRED** T40 |
| G-S3-01/02/04 schemas opcionales | **SKIP** P2 |
| T3 / HF / SSH real | **DEFERRED** PIPELINE/32 |

---

## 4 · Flujo canónico post-gaps

```
InputContract
  → loop_bridge.bridge_full
  → GoalLock + Classifier
  → ExecutionFacade
       ├ resource → Broker (+ Gate/Passport)
       └ engine   → Manifest → RuntimeBus
  → ParallelFacadeRuntime (slots; no bypass_bus)
  → T25 Sheriff (NEXT)
```

---

## 5 · Desbloqueo

```
G1–G9: DONE
T25+:  UNLOCKED
SIGUIENTE CÓDIGO: T25 Sheriff 5 estados
  → Auditar primero control-layer/sheriff o extensions existentes
  → Adaptar/conectar, no from-scratch si ya hay código
```

**G9 DONE** — este documento.  
