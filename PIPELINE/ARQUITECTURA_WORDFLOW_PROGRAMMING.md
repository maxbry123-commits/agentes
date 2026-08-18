# ARQUITECTURA WORDFLOW — PROGRAMACIÓN DE CODE (REAL)

**Fuente:** `PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`  
**Fecha:** 2026-08-18  
**Regla:** solo arquitectura demostrada + gaps explícitos. No idealizar.

---

## 1. Propósito

Orquestar un path de programación **determinista** (`run_code_path`) con:
- pre-gate (context/handoff + COPY-FIRST)
- quality + goal lock + cognitive loop
- evidence engine
- post-verify forense medido + VerdictAuthority

El runner **no** es el escritor de git; modifica repo el agente/CI externo. El runner **mide, bloquea y veredicta**.

---

## 2. Capas

```
┌─────────────────────────────────────────────┐
│  Caller (bootstrap_v1 / smoke / UNKNOWN)    │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  code_path_runner.run_code_path             │
│  hot path C-19                              │
└──────┬───────────────┬──────────────────────┘
       │               │
       ▼               ▼
┌──────────────┐  ┌──────────────────────────┐
│ Engine       │  │ standards/               │
│ quality_bar  │  │ pre_gate / COPY-FIRST    │
│ goal_lock    │  │ contract / verdict       │
│ cognitive    │  │ smoke / wiring / scope   │
│ evidence eng │  │ mission_edges            │
└──────────────┘  └──────────────────────────┘
       │               │
       └───────┬───────┘
               ▼
        dict resultado
        llm_control=DENY
```

---

## 3. Componentes canónicos (paths)

| Rol | Path |
|-----|------|
| Hot path | `extensions/wordflow/engine/code_path_runner.py` |
| Pipeline | `extensions/wordflow/engine/programming_pipeline.py` |
| Gates | `extensions/wordflow/standards/executor_gates.py` |
| COPY-FIRST | `extensions/wordflow/standards/copy_first.py` |
| Symbols AST | `extensions/wordflow/standards/symbol_index.py` |
| Contract | `extensions/wordflow/standards/forensic_contract.py` |
| Verdict | `extensions/wordflow/standards/verdict_authority.py` |
| Smoke | `extensions/wordflow/standards/test_runner.py` |
| Wiring | `extensions/wordflow/standards/wiring_graph.py` |
| Scope/REQ | `extensions/wordflow/standards/scope_measure.py` |
| Mission edges | `extensions/wordflow/standards/mission_edges.py` |
| Catalogs | `extensions/wordflow/component_catalog.json`, `connect_catalog.json` |
| CI | `.github/workflows/forensic-gates.yml` |
| Agent rules | `.cursor/rules/wordflow-programming.mdc`, `AGENTS.md` |

---

## 4. Flujo de control (arquitectura de secuencia)

1. **Pre-authorization:** context_verified + handoff_verified (default True — riesgo documentado).
2. **Reuse policy:** ExistingCodeScanner (name + catalog + AST) → ADAPT/COPY preferido; GENERATE last.
3. **Admit:** input quality bar.
4. **Lock:** goal_lock.
5. **Cognitive:** cognitive_loop (interior LLM = UNKNOWN).
6. **Optional compile:** skill_native_compiler.
7. **Evidence engine:** build + verify packet.
8. **Post forensic:** mediciones reales → ForensicCodeContract → VerdictAuthority.
9. **Return:** ok acoplado a verdict si post_verify on; llm_control DENY.

---

## 5. Contratos de arquitectura

| Contrato | Enforcement point |
|----------|-------------------|
| ForensicCodeContract | post_verify |
| EvidencePacket (standards) | VerdictAuthority |
| evidence_packet (engine) | verify en path |
| Catalog connectivity | WiringGraph load |

PIPELINE MD = política humana; **no** sustituye enforcement en hot path.

---

## 6. Límites explícitos de la arquitectura actual

| Límite | Impacto |
|--------|---------|
| Runner no escribe git | Code gen/adapt es externo al path |
| Context flags default True | BLOCK de handoff poco ejercido |
| Scope/REQ listas fijas | No git-diff scope aún |
| 4-pass global | Solo booleanos medidos en C-19 |
| GapRegistry runtime | Ausente |
| OPEN→CLOSED global SM | No verificado |
| cognitive_loop interior | UNKNOWN |

---

## 7. Relación con arquitectura multi-instancia

`bootstrap_multi` configura flags `copy_first` / `forensic_post_verify` / path pipeline en config de instancia.  
Instance store es estado de instancia, **no** gap store de programación.

---

## 8. Diagrama de enforcement

```
Policy (PIPELINE + Forensic MD)
        │
        ▼
code_path_runner (único hot path verificado)
        │
   ┌────┴────┐
   pre       post
   │         │
 scanner   measure→contract→VerdictAuthority
   │
 BLOCK solo si !context/handoff
```

---

## 9. Referencias

- Mapa forense completo: `PIPELINE/WORDFLOW_PROGRAMMING_FORENSIC_MAP.md`
- Método: `PIPELINE/00_METODO_TRABAJO_Y_ARQUITECTURA.md`
- Gaps: `PIPELINE/GAPS_PROGRAMMING_WORDFLOW.md`
- Forense checklist: `PIPELINE/FORENSIC_CODE_AUDIT.md`
