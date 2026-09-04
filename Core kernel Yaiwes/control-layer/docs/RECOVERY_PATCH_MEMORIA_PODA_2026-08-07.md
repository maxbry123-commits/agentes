# RECOVERY PATCH · Memoria + Poda Agentes
**Fecha:** 2026-08-07  
**Repo:** `maxbry123-commits/agentes`  
**Rama:** main  
**Uso:** pegar este doc en un **nuevo plan Grok** para continuar sin re-explicar el chat.

---

## 0. PARCHE DE ARRANQUE (copiar al nuevo plan)

```text
CONTEXTO FIJO — NO reinventar

Repo: maxbry123-commits/agentes
- control-layer/  = Wordflow (autoridad de control) — W01–W17 + memory parcial hechos
- agents/         = sources: OpenClaw, Hermes, Claude-Code, Codex, Mimo-Code, Kimi, OpenClaw-headless

Autoridad:
  OpenClaw = UI + capabilities (podar agent-loop libre)
  Hermes   = workers + cola + memoria ejecución (podar planner libre)
  Wordflow/ControlBus = mando (goals, budget, sheriff, events)
  KER extensions = parallel/swarm/harness/connectivity/evolution (NO dentro del núcleo)

Cadenas code confirmadas:
  Backend:  OpenCode → OpenHands → Codex CLI → Claude Code CLI
  Frontend: Cline → OpenHands → OpenCode → Codex → Kimi Code CLI → Mimo

Regla dura:
  300 capabilities registradas ≠ 300 jobs concurrentes
  Concurrente = ResourceGovernor + Budget + ModelSlots
  No tocar código existente salvo mejora clara (preguntar antes)

Orden pendiente:
  G0 contratos → DUAL → G1 inventario/fusión → G2 groups → G3 code runtime
  → G4 governors → EVO → DOC → IO → G5 extensions → G8 gateway → DEP → G7 HF → G9

Memoria: Control Plane nativo; Tencent = provider oculto; Graphiti/Grapify/OCR Baidu
  = capabilities nativas vía Evolution (modo OS→extension), NUNCA apps externas obligatorias.
Osquestador auditor + temporal: diferido hasta docs completos; integrar como kernel memoria.
```

---

## 1. MEMORIA — Qué tenemos en GitHub (estado real)

### 1.1 Árbol en repo

```text
control-layer/memory/
├── MEMORY.md              # índice parcial 0.1.0
├── router.py              # MemoryRouter
├── guard.py               # aislamiento namespaces
├── policy.py
├── classifier.py          # discard / temporal / fact
├── versioning.py
├── session_store.py
├── doc_registry.py
├── integridad.py
├── ondemand.py
├── api.py
├── cache_stub.py
├── providers/
│   ├── base.py
│   ├── local_provider.py  # Local-first
│   └── tencent/           # adapter (hidden provider)
├── schemas/
└── tests/
```

### 1.2 Diseño acordado (chat)

| Capa | Rol |
|------|-----|
| **Memory Control Plane** | Qué guardar, dónde, cuándo recuperar, cuánto contexto, caché |
| **MemoryRouter** | Enruta por scope (tenant/project/agent/mission) |
| **LocalProvider** | Primero siempre (sin dependencia externa visible) |
| **TencentAdapter** | Provider oculto bajo el plane (no arquitectura completa) |
| **MemoryGuard** | Aislamiento entre proyectos/agentes |
| **Classifier** | discard / temporal / fact |

**Tiers (S12 + MEMORY.md parcial):**

| Tier | Nombre | TTL / vida | Estado en repo |
|------|--------|------------|----------------|
| 0 | RAW | fin de turno | parcial (inputblock) |
| 1 | SESSION | fin sesión | session store |
| 2 | STRATEGIC | destila diario | stubs |
| 3 | PROJECT | permanente | doc_registry |

**KG lateral (diseño, no full code):** aristas `version_de / contradice / refina / depende_de / cita_a / autoridad_sobre`; conflictos → C60 CONFLICT (no auto-elige ganador).

**Dream loop / Distill loop:** diseñados; no cerrados en código.

### 1.3 Decisión de producto (usuario)

> El agente debe tener memoria **nativa**. No obligar Obsidian / Graphiti / Grapify / n8n / OCR Baidu como sistemas independientes visibles.

Integración correcta:

1. **TencentDB-Agent-Memory** → solo **provider** bajo adapter (ya en `providers/tencent/`).
2. **Graphiti / Grapify** → **no** como servicio externo obligatorio.  
   - Descargar **source OS** de forma determinista.  
   - Compilar vía **Evolution modo 4** a `extensions/memory_graph/` (capability nativa).  
   - El agente “sabe hacer grafos” sin conectar app aparte.
3. **OCR Baidu** → igual: capability OCR nativa (código adaptado o API detrás de CredentialBroker), no UI Baidu obligatoria.
4. **Osquestador de memoria / auditor** (docs del usuario: extensión kernel + ley OpenClaw+Hermes + temporal) →  
   - Es el **kernel especializado de memoria** (microservicios) que da superpoderes.  
   - Estado: **diferido** hasta docs completos del osquestador.  
   - Slot de integración: `extensions/osquestador_memory/` + hooks al Memory Control Plane.  
   - Auditor: validación integridad tiers, no-regresión scopes, sheriff de memoria.

### 1.4 Qué falta de memoria (pendiente)

- [ ] Cerrar tiers 2–3 + Dream/Distill
- [ ] Knowledge Graph nativo (tras destilar Graphiti/Grapify o diseño propio)
- [ ] Osquestador memoria + auditor (cuando pasen docs)
- [ ] OCR capability nativa
- [ ] Namespaces formales G0.11 alineados a Mission/Task/Job
- [ ] Tests aislamiento multi-proyecto bajo swarm

**No reabrir MC01–MC08 desde cero** — extender sobre `control-layer/memory/`.

---

## 2. PODA DE AGENTES + BINARIOS

### 2.1 Qué hay YA en `agents/` (sources, no hace falta re-clonar base)

| Carpeta | Tipo | Acción |
|---------|------|--------|
| `agents/OpenClaw` | source completo | **Base TEAM SEALS** — podar agent-loop libre |
| `agents/OpenClaw-headless` | variante | referencia |
| `agents/Hermes` | source completo | **Músculo** — podar planner/dispatcher LLM |
| `agents/Claude-Code` | source | code worker (cadena) |
| `agents/Codex` | source | code worker |
| `agents/Mimo-Code` | source | code worker |
| `agents/Kimi` | source | code / research |

**Faltan pinnear (si entran en cadena confirmada):** OpenHands, OpenCode, Cline — download determinista a `agents/sources/` o `agents/<Name>/` con SHA en manifest.

### 2.2 Qué se poda (sin mermar capacidades)

#### OpenClaw
| Se poda / bypasea | Se conserva |
|-------------------|-------------|
| agent-loop que decide tools libremente | tools, skills, plugins, MCP, gateway, sessions, UI |
| planner CoT continuo sin contrato | runtime de ejecución de tools |

**Reemplazo:** TEAM Entrypoint → ControlBus (classify → plan/approve → dispatch extension).

#### Hermes
| Se poda | Se conserva |
|---------|-------------|
| planner/dispatcher que razona el flujo | cola, workers, memory útil, tools, recovery |

**Reemplazo:** scheduler determinista + DAG + ResourceGovernor.  
Si una capability cae → **Evolution EVO.08** crea capa D o **BLOCK** merge.

### 2.3 Dónde viven los binarios / sources (layout objetivo)

```text
agentes/
├── agents/                    # canónicos (UNA copia física)
│   ├── OpenClaw/
│   ├── Hermes/
│   ├── Claude-Code/
│   ├── Codex/
│   ├── Mimo-Code/
│   ├── Kimi/
│   └── sources/               # pins OS adicionales (OpenHands, OpenCode, Cline…)
├── groups/
│   ├── backend.yaml           # cadena + max instances + isolation
│   ├── frontend.yaml
│   ├── fromted.yaml
│   ├── nav.yaml
│   └── mobile.yaml
├── control-layer/             # Wordflow
└── manifests/
    ├── AGENTS_SOURCE_MANIFEST.yaml   # repo URL + ref/SHA + license
    └── MODELS_MANIFEST.yaml          # GGUF (HF buckets, NO git LFS masivo)
```

**Regla:** mismo source, **instancias** por grupo con workspace/creds/memoria/branch **aislados**. No clonar OpenClaw 5 veces.

### 2.4 Descarga determinista (cómo)

1. Entrada en `manifests/AGENTS_SOURCE_MANIFEST.yaml`:
   ```yaml
   - id: openhands
     repo: https://github.com/.../OpenHands
     ref: vX.Y.Z          # tag o commit
     sha256: <commit tree o tarball>
     path: agents/sources/OpenHands
     method: git-sparse | release-asset
   ```
2. Script `scripts/pull_deterministic.sh`:
   - `git clone --depth 1 --branch <ref>` **o** curl release asset
   - verificar `sha256sum`
   - escribir `SOURCE_RECEIPT.json` (url, ref, sha, fecha)
3. **Prohibido** `main` flotante sin pin.
4. Modelos GGUF → storage HF Bucket / volumen; **no** al monorepo git.
5. Binario “temporal” osquestador → carpeta dedicada + manifest; **diferido** hasta docs.

### 2.5 Cadenas de code (confirmadas por usuario)

**Backend:** OpenCode → OpenHands → Codex CLI → Claude Code CLI  
**Frontend:** Cline → OpenHands → OpenCode → Codex → Kimi Code CLI → Mimo  

Code agents = **runtimes con razonamiento** (plan→edit→test→observe).  
Modelos locales (Seed/Nemotron/Gemma/Nanbeige) = **workers de tokens**, no sustituyen al code agent.

---

## 3. TEAM SEALS · Fusión (recordatorio)

```text
Usuario → OpenClaw UI (no se detiene; events)
       → TEAM Entrypoint
       → ControlBus (goals, budget, preview, sheriff)
       → KER extensions (parallel, swarm, harness, connectivity, evolution)
       → Adapters: OpenClaw tools | Hermes workers | Code agents
```

UI continua tipo MiniMax/Kimi: misión daemon + event stream; hot-input no mata jobs.

---

## 4. LISTA DE TAREAS PENDIENTES (orden)

### G0 Contratos
G0.01 Authority · G0.02 Mission SM · G0.03 MTJ · G0.04 Event · G0.05 Artifact  
G0.06 Lease/Idempotency · G0.07 Recovery · G0.08 Capability Manifest  
G0.09 Governors · G0.10 Model+Provider Router · G0.11 Namespace  
G0.12 Secrets · G0.13 Telemetry · G0.14 Concurrency formula

### DUAL
DUAL.01 Doc dual-mode · DUAL.02 ABI package · DUAL.03 Enchufe · DUAL.04 85 schemas/Sentinela

### G1 Fusión
G1.01 INV OpenClaw · G1.02 INV Hermes · G1.03 Gap matrix · G1.04 Fusion doc  
G1.05 Entrypoint · G1.06 Event→UI · G1.07 Hot-input

### G2 Groups
G2.01 sources+groups layout · G2.02 backend.yaml · G2.03 frontend.yaml  
G2.04 fromted · G2.05 nav · G2.06 mobile · G2.07 AGENTS_CATALOG · G2.08 isolation

### G3 Code runtime
G3.01 CodeAgentRuntime contract · G3.02 adapters existentes · G3.03 pin OpenHands/OpenCode/Cline · G3.04 sheriff anti-single-completion

### G4 Concurrency
G4.01 ResourceGovernor · G4.02 Budget · G4.03 ModelSlots · G4.04 Scheduler  
G4.05 max_parallel tests · G4.06 Circuit breaker · G4.07 Latency P0–P3

### EVO Evolución
EVO.01 Recipes · EVO.02–06 cinco modos · EVO.07 templates · EVO.08 gap→D  
EVO.09 sandbox→canary · EVO.10 Source Reuse Contract

### DOC / IO / DEP
DOC.01–05 schemas D1–D10 + discovery + pipeline guía + anchors  
IO.01–04 input/output + durable + council  
DEP.01–03 deterministic deploy + OUSS + github migrate

### G5 Extensions / G8 Gateway / G7 HF / G9 Audit
Parallel, swarm, harness, connectivity, API router, consensus  
Gateway, ChangeEngine, Council, sessions  
HF map 5 spaces (al final) · tests · AUDIT_FINAL

### Diferidos
- Osquestador memoria full + auditor (esperar docs usuario)
- Binario temporal
- SKYNER 17 obligatorio
- Multi-sandbox 100x / Hatchet como núcleo
- Pull GGUF masivo hasta OK explícito

---

## 5. REGLAS INMUTABLES (para el otro plan)

1. No segundo orquestador dentro de ControlBus.
2. No modificar archivos existentes sin mejora clara → **preguntar**.
3. Nunca from-scratch si hay source OS en manifest.
4. Secrets solo CredentialBroker; nunca en events/logs/prompts.
5. 300 capabilities ≠ 300 concurrent jobs.
6. Code agent reasoning se conserva; modelos locales no lo reemplazan.
7. Graphiti/Grapify/OCR/n8n → nativos vía Evolution, no SaaS obligatorios.
8. HF = infra de ejecución; Wordflow = autoridad.
9. Una salida = una tarea pequeña; audit cada 3.
10. Repo `agentes` es fuente de verdad de código; este MD es puente de contexto.

---

## 6. PRÓXIMA ACCIÓN RECOMENDADA

```text
1) G0.01 Authority map (contrato nuevo, no toca código viejo)
2) G0.02 Mission State Machine
3) G1.01 + G1.02 inventarios (solo docs de lectura sobre agents/OpenClaw y agents/Hermes)
```

Tras G0+G1 docs → G2 manifests groups → no poda de código hasta Gap Matrix aprobada.

---

*Fin recovery patch. Generado para continuidad inter-plan Grok · 2026-08-07*
