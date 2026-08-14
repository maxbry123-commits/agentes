# PIPELINE/32 — Diferir engines · HF compute · micro-kernel install

**Fecha:** 2026-08-14  
**Estado:** DECISIÓN DIRECTOR (anotada)

---

## 1 · Auditoría OpenClaw / Hermes (resumen cerrado)

Ver detalle chat + PIPELINE/31.

| Motor | Rol TEAM | En Wordflow ahora |
|-------|----------|-------------------|
| OpenClaw | tools/skills/MCP/UI edge · PlanningPort futuro | **NO conectar aún** |
| Hermes | workers/cola/memoria · MemoryPort futuro | **NO conectar aún** |
| YAIWES/Wordflow | mando GoalLock, Sheriff, Manifest, Ping | **Construir hasta cierre** |

Adapters (T0n–T0q, T3) quedan **planificados** pero **no se implementan ni se cablean** hasta Wordflow core COMPLETED.

---

## 2 · Decisión de secuencia (obligatoria)

```
1. Terminar Wordflow (WAVE-0 → waves planificadas, sin adapters reales OC/Hermes)
2. Micro-kernel de instalación/descarga determinista
   - descarga agentes/repos → GitHub (control plane / tree)
3. Conectar repos a HuggingFace como procesador de cómputo
   - HF = storage + compute para skills/datasets/adapters + installs
4. Solo entonces: cablear OpenClaw/Hermes vía EnginePort / MemoryPort
```

**Sin HF compute + micro-kernel install, la descarga determinista se corta.**  
Por eso **no** se abre T3 real ni clone de agentes en esta fase.

---

## 3 · Qué sigue en código ahora

- T0e GoalLock (inmutable)
- T0f–T0m anclas cognitivas / classifier (fakes only)
- Resto Wordflow determinista
- T0n–T0q = schemas/fakes opcionales solo si no bloquean cierre
- **T3 real + download agents + HF wire = POST Wordflow**

---

## 4 · Trazabilidad

| Doc | Uso |
|-----|-----|
| PIPELINE/31 | Attach points Input + Ping (diseño) |
| PIPELINE/32 | Este archivo — defer + HF |
| docs/PRUNE_OPENCLAW_HERMES.md | Podar planner libre; conservar tools/workers |
| DESPLIEGUE-DETERMINISTA / HF pins | Post-cierre Wordflow |

---

**SIGUIENTE:** T0e GoalLock.
