# Evolution System · 5 modos + agentes/binarios a integrar
**TEAM SEALS / Wordflow** · 2026-08-07

---

## 1. Pipeline universal (todos los modos)

```text
Fuente (agente | skill | software OS | dataset | acoplador)
  → Discovery (clone/download determinista + SHA)
  → Inventory (decisión vs ejecución)
  → Distill (mínima capability útil)
  → Template (DSL + schema + sheriff hooks)
  → Compile (package KER)
  → Tests + benchmark + security
  → Council opcional
  → Approval gate
  → Canary
  → Capability Registry
  → Production mount
```

**Nunca:** source → production directo.  
**Siempre:** Evolution Sandbox → canary → registry.

Si poda **merma** capability → capa determinista de reemplazo **o** BLOCK merge (EVO.08).

---

## 2. Cinco modos

### Modo 1 — Agente → capability determinista
Incorpora tools/pipelines de otro agente.  
LLM solo en nodos de generación de código; resto D (determinista).  
Ej.: extraer git/test tools de OpenHands → capabilities registradas.

### Modo 2 — Descapitar + micro TEAM
Corta planner/loop libre del agente huésped; instala entrypoint TEAM/ControlBus.  
Ej.: Hermes sin planner LLM; OpenClaw sin agent-loop libre.  
Conserva tools/workers/UI.

### Modo 3 — Skill → código ejecutable
Skill (markdown/marketplace) → plantilla DSL/DAG/Sheriff → runtime 90% D / 10% LLM.  
Code workers (Claude Code, Codex, Mimo, OpenCode, OpenHands) **escriben** el módulo; no mandan el kernel.

### Modo 4 — Software OS → extension KER
Graphiti, n8n, Grapify, etc.: download source → no instalar app usuario → package `extensions/...`.  
Conexión “nativa”: capability bus, no deep-link a GUI externa.

### Modo 5 — Dataset / acoplador LLM → knowledge o work pack
Adapters/datasets → knowledge pack versionado o capability de retrieval/fine-data; no prompts sueltos.

---

## 3. Ya en repo `agents/` (no re-clonar base)

| Path | Rol |
|------|-----|
| OpenClaw | Host UI TEAM SEALS (podar loop) |
| OpenClaw-headless | Variante |
| Hermes | Workers/cola (podar planner) |
| Claude-Code | Code runtime cadena |
| Codex | Code runtime |
| Mimo-Code | Code runtime |
| Kimi | Code/research |

---

## 4. Binarios / sources a **pinnear y descargar** (determinista)

Añadir a `manifests/AGENTS_SOURCE_MANIFEST.yaml` + `scripts/pull_deterministic.sh`.

### Code (cadenas confirmadas)
| ID | Necesidad |
|----|-----------|
| OpenCode | Backend #1 / Frontend |
| OpenHands | Backend/Frontend |
| Cline | Frontend #1 |
| (ya hay) Codex, Claude Code, Mimo, Kimi | — |

### Nav / Perplexity-like
| Capability | Fuente típica |
|------------|---------------|
| browser.navigate / click / type | Playwright o agent browser OS |
| browser.screenshot | mismo runtime → artifact |
| web.search | API search detrás de broker |
| web.cite / extract | reader + rank |
| github.search_repos | GitHub API / gh |

Grupo: `groups/nav.yaml`  
No “agente rol prompt”; runtime browser + tools.

### Mobile
| Capability | Fuente |
|------------|--------|
| device.adb / ssh / ui_dump | platform-tools + bridge |
| mobile.screenshot | device bridge |

Grupo: `groups/mobile.yaml` · secrets solo broker.

### Memoria / OCR (vía Evolution)
| ID | Uso |
|----|-----|
| Graphiti (source) | KG nativo |
| OCR engine OS o API | ocr.extract_text |

### Modelos GGUF (HF)
Seed-Coder, Nemotron, Nanbeige, Gemma → **Bucket HF / storage**, no git monorepo.  
Manifest SHA aparte (`MODELS_MANIFEST.yaml`).

---

## 5. Layout objetivo

```text
agentes/
  agents/           # UNA copia por agente canónico
  agents/sources/   # pins OpenHands, OpenCode, Cline, graphiti…
  groups/
    backend.yaml
    frontend.yaml
    fromted.yaml
    nav.yaml
    mobile.yaml
  manifests/
    AGENTS_SOURCE_MANIFEST.yaml
    MODELS_MANIFEST.yaml
  control-layer/
  extensions/
    evolution/
    memory_graph/
    ocr/
    osquestador_memory/   # diferido
```

**Duplicar grupos = instancias + isolation**, no 5 forks de OpenClaw.

---

## 6. Pull determinista (cómo)

```yaml
# ejemplo manifest entry
- id: openhands
  repo: https://github.com/All-Hands-AI/OpenHands
  ref: vX.Y.Z
  sha256: "..."
  path: agents/sources/OpenHands
  method: git-archive | release-asset
```

1. Clone depth 1 o curl asset  
2. Verificar sha256  
3. Escribir `SOURCE_RECEIPT.json`  
4. Prohibido trackear `main` flotante sin pin  

---

## 7. Tareas EVO (código pendiente)

EVO.01 Recetas doc (este archivo es base)  
EVO.02–06 implementaciones modos  
EVO.07 templates  
EVO.08 gap→D/BLOCK  
EVO.09 sandbox→canary  
EVO.10 Source Reuse Contract  
