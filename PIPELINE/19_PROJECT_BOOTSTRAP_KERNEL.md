# PIPELINE 19 — PROJECT BOOTSTRAP (Kernel Auto-conocimiento)

**Fecha:** 2026-08-10  
**Estado:** COMPLETED (CI 16/16)  
**Módulo:** `extensions/project_bootstrap/`  
**Enchufe:** `wordflow.kernel.project_bootstrap`  
**Commit final módulo:** `0587a4e6eb6a05cf3ef49c04841b41e6ff42e6a8`  
**CI run:** https://github.com/maxbry123-commits/agentes/actions/runs/31352462001 → success

---

## 1. Qué es

Capa nativa del kernel que gestiona **auto-conocimiento** del sistema:
- plantillas de documentos de proyecto
- Kernel Thought Protocol (KTP / emoji FSM)
- Input Handler (chat/documento → tareas)
- actualización incremental
- Resource Brain (capacidades AVAILABLE)

Es la base del Objetivo 1 (extensión kernel + Wordflow conectable a cualquier agente).

---

## 2. Estructura materializada

```
extensions/project_bootstrap/
├── manifest.yaml              # Enchufe Universal v2
├── schema_module.json
├── __init__.py
├── entrypoint.py              # run(raw_input) → goal + tasks + profile
├── input_handler.py           # InputBlock + classify + pause
├── updater.py                 # hash + impacto + re-ejecución parcial
├── ktp/
│   ├── states.yaml            # 13 estados + transiciones
│   └── engine.py              # KTPEngine determinista
├── microflows/
│   ├── microflows.yaml
│   ├── runner.py              # extract_goal, decompose_tasks, build_*
│   └── __init__.py
├── resource_brain/
│   ├── registry.py            # DISCOVERED→AVAILABLE
│   └── __init__.py
└── tests/
    └── test_core.py           # 16 tests
```

CI: `.github/workflows/test-project-bootstrap.yml`

---

## 3. Tareas A1–A8 (trazabilidad)

| ID | Entrega | Commit |
|----|---------|--------|
| A1 | manifest + schema | 34b3af9c |
| A2 | KTP states + engine | 9c1d786c / f18b3ce3 |
| A3 | microflows | db38e2e8 |
| A4 | input_handler | cce4ebca |
| A5 | updater | b0b8c69e |
| A6 | resource_brain | 953bde97 |
| A7 | tests 16/16 | 053a0a0b |
| A8 | entrypoint + __init__ | 52e236d7 |
| CI | workflow | b9f12ba4 |
| FIX | extract_goal tokens | 0587a4e6 |

LOC net (A1–A8): **+1735** (suma stats commits)

---

## 4. Flujo ejecutable

```
raw_input
  → InputHandler (kind, priority, pause?)
  → ResourceBrain.select_ready
  → KTP: OBJETIVO → TAREA → PLANIFICAR
  → microflows: extract_goal + decompose_tasks + build_profile
  → Updater.register / apply_update
  → {status, goal, tasks, profile, ktp, resources}
```

---

## 5. Invariantes

- `llm_ratio ≤ 0.10` (manifest)
- Solo capacidades **AVAILABLE** se usan
- Transiciones KTP validadas (no saltos ilegales)
- Update: hash igual → ignore; distinto → solo dependientes
- Tests obligatorios en CI (push paths project_bootstrap)

---

## 6. Bugs cerrados

| Bug | Causa | Fix |
|-----|-------|-----|
| CI 2 FAIL extract_goal | `\\b` doble-escaped en push | token matching `re.findall` + set verbs |

---

## 7. Próximo

Parte B / Objetivo 1 resto del kernel (cuando Director entregue código kernel + paso 2).

**Fuente:** PIPELINE 12 FULL + 13 + 14 MVP + Enchufe v2 + auditoría CHAT_B.
