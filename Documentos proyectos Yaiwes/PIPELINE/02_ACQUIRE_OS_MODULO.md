# PIPELINE 02 — ACQUIRE-OS v1 (Sub-Sheriff de Adquisición)

**Fecha:** 2026-08-09  
**Estado:** PERFIL INCORPORADO  
**artifact_id:** `wordflow.subsheriff.acquire_os`  
**Formato de registro:** Enchufe Universal v2.0 (`ficha.v2.json`)

---

## 1. Qué es dentro del proyecto más grande

ACQUIRE-OS es **una extensión kernel** registrada en la Capa de Control de Wordflow.

No es el sistema completo.  
Es un módulo conectado al Sheriff general, Contract Router, Council of 12 y Tribunal.

Se registra con ficha JSON (Enchufe Universal v2.0) que contiene:  
`artifact_id`, `contrato`, `ejecucion`, `perfiles`, `tribunal`, `seguridad`, etc.

---

## 2. Qué hace

Motor **determinista** que adquiere CUALQUIER software:

- repo git
- modelo HuggingFace
- binario de release
- paquete de package manager

Flujo:  
adquiere → verifica integridad → construye/instala (si aplica) → publica en repo GitHub.

`LLM_CONTROL = DENY` en casi todo el pipeline.  
Único punto con lenguaje natural: extracción de la guía oficial de instalación (Discovery), y ahí opera en modo schema-in / schema-out. Nunca decide.

---

## 3. Arquitectura — 2 niveles de DAG

### NIVEL 1 — DAG maestro (12 nodos, lineal, paralelo_max=1)

```
T-000 GITHUB_AUTH
  → T-002 DESTINATION_VALIDATOR
  → T-003 MISSION_LOCK
  → T-004 CHECK_EXISTING_FICHA
  → T-005 DISCOVERY_GOAL_6
  → T-001 HF_AUTH (condicional)
  → T-006 SOURCE_ADAPTER
  → T-007 SIZE_ROUTER
  → T-008 SHERIFF (sub-DAG nivel 2)
  → T-009 PUBLISHER
  → T-010 FICHA_REGISTRAR
  → T-011 LOCK_RELEASE
```

### NIVEL 2 — sub-DAG interno de T-008 (28 nodos, genérico, dirigido por Recipe)

```
01_RECEIVE_CHECKOUT
→ 02_VERIFY_PIN_MATCH
→ 03-06 (condicional: solo git)
→ 07_VERIFY_CHECKSUM (condicional: release_binary | package_manager | hf_hub)
→ 08_VERIFY_TOOLCHAIN_PIN
→ 09-11 (dependencias)
→ 12-13 (build, condicional)
→ 14_INDEX_ARTIFACTS
→ 15-17 (install/verify, condicional)
→ 18_PROVENANCE
→ 19_MANIFEST_FROM_DISK
→ 20_SOURCE_HASH_BEFORE_PROMOTE
→ 21_AUDIT_DINAMICO
→ 22_LICENSE_GATE
→ 23_SECRET_SCAN
→ 24_PROMOTE
→ 25_SOURCE_HASH_AFTER_PROMOTE
→ 26_FINAL_IDENTITY
→ 27_FINAL_HASHES
→ 28_DONE
```

**Regla clave:**  
Nodos condicionales que no aplican al `source_type` actual **nunca** cuentan como PASS.  
Quedan en estado `SKIPPED_EXPECTED`.  
Solo `FAILED` detiene el pipeline (QUARANTINE + rollback).

---

## 4. Contrato de datos — la Recipe (input de T-008)

```python
recipe = {
  "source_type": "git_native" | "hf_hub" | "release_binary" | "package_manager",
  "pin": { ... },          # commit / revision / checksum según tipo
  "toolchain": { ... } | None,
  "dependencies": { ... } | None,
  "build": { ... } | None,
  "install": { ... },
  "verify": { ... }
}
```

La Recipe la produce **T-005 DISCOVERY_GOAL_6** (G1→G6).  
Ningún dato se infiere por analogía. Se extrae **literal** de la fuente oficial de ESE software.

---

## 5. Código — paquete `acquire_os_core/`

```
core.py      → orquestador + primitivas (run, sha, gate)
verify.py    → nodos 01-11
build.py     → nodos 12-17
promote.py   → nodos 18-28
```

Cada módulo ≤ 200 líneas.  
Ningún comando de instalación está hardcodeado — todo `run(...)` recibe argv desde `recipe`.

---

## 6. Estado y checkpoints

```
.acquire/{mission_id}/state.json
journal.jsonl          (append-only)
checkpoint.json        (por nodo)
```

Reanudación = leer último checkpoint. Nunca reiniciar desde el nodo 1.

---

## 7. Validación (Tribunal) — solo 3 puntos

- post-T-005 (Recipe compilada)
- pre-T-009 (antes de promover)
- post-T-009 (antes del PR)

Roles mapeados a mecanismos ya existentes:  
SHERIFF · CENTINELA · JUEZ · SUPERVISOR · VALIDADOR · VERIFICADOR  
Veto de SHERIFF/CENTINELA = absoluto.

---

## 8. Cómo un agente Wordflow debe invocarlo

1. Consulta Contract Router por `artifact_id: "wordflow.subsheriff.acquire_os"`
2. Pasa por Contract Router (nunca llama directo a `acquire_os_core`)
3. Router crea `mission_id`, inicializa state, dispara DAG maestro
4. Resultado se entrega vía schema `universal_acquisition_manifest`
5. El agente invocador **no** recibe el token de GitHub/HF

---

## 9. Invariantes (obligatorios si se toca este código)

- Nunca escribir comando de instalación literal en verify/build/promote
- Nunca convertir `SKIPPED_EXPECTED` en `PASS`
- Nunca promover si hay algún `FAILED`
- Nunca loggear token de auth en journal/provenance
- `install()` usa `${LOCAL_ARTIFACT}` ya verificado — nunca vuelve a pedirlo en vivo

---

## 10. Micro-diagrama horizontal

```
mission_request → GITHUB_AUTH → LOCK → DISCOVERY → SOURCE_ADAPTER → SHERIFF(sub-DAG) → PUBLISHER → FICHA → RELEASE
```

## 11. Micro-diagrama transversal (gobierno)

```
Contract Router · Sheriff · Centinela · Juez · Supervisor · Validador · Verificador · Tribunal
```

---

## 12. Trazabilidad de este documento

- Origen: input block del Director (2026-08-09) — documento “ACQUIRE-OS v1 — Resumen técnico”
- Incorporado al perfil del PIPELINE como módulo Sub-Sheriff
- Próximo: esperar más bloques del perfil principal (PIPELINE 0)

**Estado:** listo para auditoría.
