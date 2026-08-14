# PIPELINE/34 — Auditoría progreso vs plan (T0a→T23)

**Fecha:** 2026-08-14  
**HEAD verificado:** `4a4b50406036f0b80627b3754dae742de5ba877a`  
**Repo:** maxbry123-commits/agentes  
**Supersede contadores de:** PIPELINE/33 (obsoleto en §6–7; aún útil como reglas §0)

---

## 1 · Veredicto auditoría

```
DESVIACIÓN ARQUITECTÓNICA: NO
T3 OC/Hermes reales: NO tocado (correcto PIPELINE/32)
HF/SSH real / Docker real: NO (stubs only)
PIPELINE/33 como memoria: DESFASADO → usar este 34
Siguiente código: T24 (cierre WAVE-3 tests integración)
```

---

## 2 · Cumplimiento por wave

| Wave | Plan (33) | Código real | Estado |
|------|-----------|-------------|--------|
| WAVE-0 T0a–T0q | Anclas + ports fake | Completo en commits | **CERRADO** |
| WAVE-1 T1–T7 | Bus+Manifest+Handoff; T3 diferido | T1,T2,T4–T7 hechos; T3 skip | **CERRADO** (T3 diferido) |
| WAVE-2 T8–T13 | Pin+Catalog+Gate+Passport+Broker | Completo | **CERRADO** |
| WAVE-3 T14–T24 | Scheduler…parallel N07 base | T14–T23 hechos; **T24 falta** | **~95%** |
| WAVE-4+ T25+ | Sheriff/Panel/… | No iniciado | Pendiente |
| POST Wordflow | microkernel+HF+T3 real | No iniciado | Correcto diferir |

---

## 3 · Hecho (resumen IDs)

**WAVE-0:** T0a Input · T0b Q · T0c Trace · T0d Goals · T0e Lock · T0f Ping · T0g Focus · T0h Bitácora · T0i Echo · T0j Registers · T0k Classifier · T0l Ledger · T0m tests · T0n Proposal · T0o PlanningPort fake · T0p MemoryPort fake · T0q Ping hooks  

**WAVE-1:** T1 ABI · T2 Bus · T4 FakeEngine · T5 Manifest · T6 Handoff · T7 tests  
**T3:** diferido explícito  

**WAVE-2:** T8 Pin · T9 Catalog · T10 Gate · T11 Passport · T12 Broker · T13 tests  

**WAVE-3:** T14 Scheduler · T15 Queue/Pool · T16 Sandbox logical · T17 Lease · T18 Checkpoint · T19 CircuitBreaker · T20 SSH **stub** · T21 Retry · T22 ParallelRuntime · T23 Guarded (retry+circuit)  

**HEAD:** https://github.com/maxbry123-commits/agentes/commit/4a4b50406036f0b80627b3754dae742de5ba877a

---

## 4 · Alineación con reglas (sin desvío)

| Regla | ¿Respetada? |
|-------|-------------|
| 0% LLM en core anchors/bus/resources/parallel base | SÍ |
| 1 tarea ≈ 1 commit GitHub | SÍ (algunos commits duplicados T0k/T9/T20 por re-push; mismo contenido) |
| No OC/Hermes reales | SÍ |
| No fetch HF remoto | SÍ (`REMOTE_FETCH_DENIED_PRE_POST_WORDFLOW`) |
| SSH real disabled | SÍ (`REAL_SSH_DISABLED`) |
| Sandbox backend efectivo logical | SÍ |
| Parallel = slots lógicos no 50 workers reales | SÍ (base N07; full scale post) |

---

## 5 · Gaps / riesgos (no bloquean T24)

1. **PIPELINE/33 desfasado** — cualquier Grok que lea solo 33 cree que falta T0l. **Mitigación:** este 34.
2. **T24 pendiente** — falta suite integración WAVE-3 formal.
3. **Tests no corridos en CI** — evidencia = código+unittest locales claim; T40 CI sigue pendiente.
4. **No integración main_loop Wordflow legacy** — anchors viven en `extensions/wordflow/engine/`; cableado al loop 12 pasos = wave posterior.
5. **N07 “10–50 workers / SSH migrate real”** — solo modelo + stubs; no es gap de plan si se lee “base then full”.
6. **Search API lag** — a veces code search no indexa al instante; commits list es fuente de verdad.

---

## 6 · Próximos pasos ordenados

1. **T24** — `tests/test_wave3_parallel_integration.py` (Scheduler→Pool→Sandbox→Lease→Retry→Circuit→SSH stub)  
2. **PIPELINE refresh** tras T24 (cerrar WAVE-3 en bitácora)  
3. **WAVE-4 T25** Sheriff 5 estados (si control-layer ya tiene sheriff, **adaptar/conectar**, no from-scratch si existe)  
4. No abrir T3/HF/microkernel hasta cierre Wordflow core acordado  

---

## 7 · Contadores reales

| Métrica | Valor |
|---------|-------|
| Tareas código cerradas | T0a–T0q + T1–T2 + T4–T23 ≈ **40** IDs |
| Siguiente | **T24** |
| Diferidos | T3, HF fetch, SSH real, Docker real, CI T40 |
| HEAD | 4a4b5040… |

**SIGUIENTE CÓDIGO:** T24  
