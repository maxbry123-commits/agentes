# METHOD_ASYNC_ACQUIRE — Adquisición determinista por capas

**Repo:** `maxbry123-commits/agentes`  
**Audience:** cualquier instancia Grok / Claude / otra AI.

---

## 0. Objetivo real

No es solo auditar ni etiquetar.  
Es **ADQUIRIR Y CONSERVAR** el agente completo que el proyecto distribuye:

```
DESCARGAR → CONSERVAR → FIJAR → VERIFICAR → REPRODUCIR
```

Resultado: **DETERMINISTIC AGENT SNAPSHOT** por agente.

---

## 1. Qué debe tener un agente al 100%

### CAPA 1 — SOURCE

- Árbol completo **o** archive `.tar.gz` completo del commit fijado
- Identidad inmutable: `repository + ref/tag + commit SHA`
- `archive.sha256` + `tree.sha256` (si árbol expandido)
- Nunca `main` / `master` / `latest` / `HEAD` como pin final

### CAPA 2 — DISTRIBUTION (oficial)

Conservar lo que el proyecto **realmente publica**, en el formato que sea:

- binary / executable / AppImage / deb / rpm / tar.gz / zip
- npm tarball / PyPI wheel-sdist
- Docker image (digest fijado)
- paquete con varios ejecutables, runtimes, plugins, resources

No inventar binarios. Si no hay distribución pública tras búsqueda sistemática → documentar; SOURCE igual se conserva.

### CAPA 3 — DEPENDENCIAS Y BUILD

Cuando existan: lockfiles, Dockerfile, CI workflows, toolchain notes, base image digest.

### CAPA 4 — PROVENANCE / HASHES

Cada artefacto: `URL + version/tag + commit + SHA256 + platform + arch`.

### CAPA 5 — REBUILD (cuando sea posible)

```
SOURCE + deps fijas + entorno fijo → REBUILT → comparar SHA256 vs oficial
```

Si no es reproducible: conservar oficial igual; marcar `NOT_REPRODUCIBLE`.

### Layout

```
agents/<AgentId>/
  source/          # complete-source/ y/o SOURCE_PIN + archive en Release
  distribution/
    official/      # ≤90MB en git; >90MB → Release + *.PIN.json
    rebuilt/
  dependencies/ build/ models/ runtime/ tools/ plugins/ provenance/ hashes/
  manifest.json
agents/_state/<AgentId>.json
```

Release tag: `agent-<AgentId>-<ref>`

---

## 2. Búsqueda antes de declarar ausencia

Orden obligatorio:

1. repo oficial + releases + assets  
2. package registries (npm, PyPI, crates, …)  
3. containers (ghcr, docker hub) con digest  
4. páginas de descarga oficiales  
5. CI artifacts públicos  

Solo entonces: artefacto específico no publicado.

---

## 3. Método async (sin quemar tokens)

```
C0 DISPATCH  → lanza workflow/script  → escribe state  → STOP
C1 STATE     → agents/_state/<id>.json
C2 RESUME    → 1 consulta de run por turno de chat
C3 SPLIT     → source | dist-meta | dist-upload | finalize
```

**Prohibido:** bucles `sleep` + poll en la misma conversación.

**status:** `QUEUED` | `RUNNING` | `NEED_RELEASE` | `NEED_COMMIT` | `DONE` | `FAILED`  
Solo `DONE` permite el siguiente agente.

### Si git no aguanta el árbol

1. SOURCE como `.tar.gz` en Release + SHA256 en git  
2. Binarios grandes en el mismo Release  
3. Git = pins + manifest + hashes  
Sigue siendo snapshot determinista (URL + SHA + commit).

### Workflows YAML

Scripts largos en `scripts/*.sh` / `scripts/*.py`.  
Workflows **mínimos** (`run: bash scripts/...`) — YAML complejo rompe el trigger `workflow_dispatch`.

---

## 4. Chat / salidas

- ~8–12 líneas salvo listas pedidas  
- Lista de tareas en cascada: número, tema+fuente, resultado, cómo  
- Cada 3 salidas: AUDIT cruzado  
- **Ok** del usuario = RESUME o siguiente capa  
- No tocar control-layer / Wordflow sin orden explícita  

---

## 5. Checklist 100%

- [ ] identity pin (repo + ref + commit)  
- [ ] SOURCE conservado (tree o archive + SHA256)  
- [ ] DISTRIBUTION oficial conservada (git y/o Release) o ausencia documentada tras búsqueda  
- [ ] `manifest.json` + `hashes/SHA256SUMS`  
- [ ] `agents/_state/<id>.json` → `DONE`  
- [ ] control-layer intacto  

---

## 6. Estado de tareas

| Task | Agente | Estado |
|------|--------|--------|
| A1 | pipeline | DONE |
| A2 | OpenClaw | DONE |
| A3 | OpenClaw-headless | DONE (alias A2) |
| A4 | Hermes | SOURCE OK |
| A5 | Codex | DONE (Release + pins) |
| A6+ | siguientes | tras A5 DONE |

---

*TEAM SEALS — documento operativo para instancias AI.*
