# PIPELINE 53 — Método multi-cuenta: Sistema (A) + Software externo (B) + HF

**Fecha:** 2026-08-17  
**Repo sistema (Cuenta A):** maxbry123-commits/agentes  
**Regla:** Nunca token en código, YAML de workflow, journal ni chat. Solo `credential_ref` → env/secret store.

---

## 1. Arquitectura de almacenamiento

```
CUENTA A — SISTEMA VIVO (maxbry123-commits)
───────────────────────────────────────────
agentes          ← Wordflow / YAIWES / kernel / policies
maxbry-router    ← Router inteligente
osquestador-auditor ← Orquestador auditor
MEMORIA          ← Memoria / hub
        │
        │ AUTH (credential_ref → token Cuenta B)
        ▼
CUENTA B — ALMACÉN SOFTWARE (ej. abc1tienda-web)
───────────────────────────────────────────
REPO-SOFTWARE-01..N  (forks, libraries, agents, tools)
        │
        │ DOWNLOAD / CLONE / API file (NO ejecuta aquí)
        ▼
RUNTIME (VPS / HF Space / sandbox / container)
        │
        ▼
HF / STORAGE EXTERNO — datasets, models, skills grandes, adapters >100MB
```

| Qué | Dónde |
|-----|--------|
| Código propio Wordflow, schemas, policies | Cuenta A |
| Software externo, forks, tools reutilizables | Cuenta B (repos) |
| Datasets / models / skills grandes | HuggingFace |
| Metadata, hash, version, provenance | DB / state Wordflow |

**GitHub B no ejecuta código.** Solo almacena. El motor de YAIWES descarga → verifica hash → sandbox → ejecuta.

---

## 2. Flujo Resource Acquisition

```
MISIÓN
  → RESOURCE REGISTRY (recurso, repo B, version/tag, sha256, runtime)
  → AUTH MANAGER (credential_ref → token solo en memoria de proceso)
  → PREFLIGHT (size, license, checksum, límites)
  → DOWNLOAD / CLONE / get_contents (shallow si aplica)
  → ADAPTER / BRIDGE
  → SANDBOX
  → UNIVERSAL EXECUTION ENGINE
  → CAPABILITY (ficha.v2)
```

---

## 3. Conector (código en agentes)

- Path: `extensions/wordflow/connectors/github_external.py`
- Config: `extensions/wordflow/connectors/external_accounts.example.yaml`
- Integra con `AccountRegistry` (`credential_ref` only)

Variables de entorno (ejemplo):

```bash
export GITHUB_EXTERNAL_TOKEN_REF_VALUE="..."   # valor real solo en secret store / env local
# En registry: credential_ref: "env:GITHUB_EXTERNAL_TOKEN_REF_VALUE"
```

**Prohibido:** `GITHUB_EXTERNAL_TOKEN = "ghp_..."` en archivo versionado.

---

## 4. Repos sistema que deben documentar este método

| Repo | Rol |
|------|-----|
| agentes | Wordflow + conector + AccountRegistry |
| maxbry-router | Router pide recursos vía mismo contrato account_id |
| osquestador-auditor | Auditor/orquestador usa registry para software externo |
| MEMORIA | Documenta topología A/B/HF; no guarda tokens en markdown de secretos |

---

## 5. Policy engine (decisión de destino)

| Tipo recurso | Destino |
|--------------|--------|
| Código pequeño / library | GitHub B |
| Software completo reutilizable | GitHub B |
| Dataset / modelo / skill grande | HF |
| Artefacto temporal | Storage temporal runtime |
| Metadata / hash / versión | State Wordflow / DB |

---

## 6. Tareas relacionadas plan V1

- Amplía **T15 / T38** (AccountRegistry multi-cuenta) con account_id de tipo `external_software`.
- Amplía **T17** (Acquire) para resolver repo en Cuenta B.
- Nuevo residual si hace falta: wire real a owner `abc1tienda-web` cuando Director entregue `credential_ref` (no token en chat).

**Fin PIPELINE 53.**
