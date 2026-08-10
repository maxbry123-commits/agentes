# PIPELINE 21 — STATUS + WORDFLOW CODE FASES

```
fecha: 2026-08-10
auditoria_fase1: PASS / CONFIRMADO 100%
commit_cierre_fase1: 5b216697f4e44d61c2bde73d13725f5bd1bdeb83
CI: run 31354290850 success
```

---

## 1. ESTADO 4 OBJETIVOS MVP

| Obj | Descripción | Estado | Path / evidencia |
|-----|-------------|--------|------------------|
| **1** | Extensión kernel + Wordflow a cualquier agente (Enchufe) | **PARCIAL código** | `control-layer/ficha.v2.json` + `manifest.yaml` + motor Sheriff; C82–C85 → B7 |
| **2** | Wordflow fusión Kimi/Minimax + sistema documentos/plantillas | **CÓDIGO base plantillas SÍ** | ver §2 |
| **3** | Acquire determinista (repos/binarios) | **SPEC en PIPELINE** | `PIPELINE/02_ACQUIRE_OS_MODULO.md` · código motor acquire pendiente |
| **4** | GitHub publish determinista | **SPEC** | contrato github_publish definido; módulo publisher pendiente |

---

## 2. SISTEMA DE PLANTILLAS — CONFIRMACIÓN

**SÍ existe** (código + docs PIPELINE):

```
extensions/project_bootstrap/
├── ktp/                 # Kernel Thought Protocol (emoji FSM)
├── microflows/          # extract_goal, decompose_tasks, …
├── input_handler.py     # input block → tareas
├── updater.py           # incremental hash+impacto
├── resource_brain/      # descubre→registra→mapea→…
├── entrypoint.py
├── manifest.yaml
└── tests/
```

Docs nativos (PIPELINE):

| Doc | Contenido |
|------|-----------|
| `10_KERNEL_THOUGHT_PROTOCOL.md` | KTP / emoji states |
| `11_PROJECT_DOCUMENT_SYSTEM.md` | sistema documentos proyecto |
| `12_PROJECT_DOCUMENTS_NATIVE_FULL.md` | plantillas nativas FULL |
| `13_PROJECT_DOCUMENTS_MISSING_PIECES.md` | gaps plantillas |
| `14_PERFIL_MVP_4_OBJETIVOS.md` | perfil 4 objetivos |
| `19_PROJECT_BOOTSTRAP_KERNEL.md` | bootstrap kernel resumen |

**Qué cubre:** plantilla nativa de docs de proyecto, KTP, microflows, input→tareas, resource brain, updater incremental.  
**Qué NO es aún:** fusión Minimax/Kimi loops completos (→ Fase 4 abajo) ni FROMTED builder (→ Fase 3).

---

## 3. CONTROL LAYER FASE 1 — CERRADA

```
motor: normalize→fingerprint→threat→rules→graph→reverse→compile→sheriff→gate
commits: e36eba91 → 4d9c112c · CI 31354290850 success
G-DOC-1..5: CERRADOS
pendiente contratos: B0–B8 (routing 13 tipos → L8 C82–C85)
```

---

## 4. WORDFLOW CODE — PLAN FASES (90% det / 10% LLM)

```
F0  Investigación fuentes (repos/guías)     → Acquire + sparse clone
F1  Arquitectura de programación           → schemas + capas código
F1.1 Sistema documentos/plantillas         → YA base en project_bootstrap
F2  Sistema diseño de código               → design contracts + generators
F3  Sistema construir FROMTED              → fromted builder determinista
F4  Bucles/loops + fusión Minimax/Kimi     → loops/*.yaml + fusion engine
```

### Microdiagrama

```
F0 research/acquire → F1 arch → F1.1 docs(plantillas)
                    → F2 design → F3 fromted → F4 loops+fusion
                    → (todo bajo Sheriff + Enchufe v2)
```

### Reglas
- 90% determinista / 10% LLM (solo puntos schema-in/out)
- ≤300 LOC/archivo · YAML contratos · Python runtime
- 1 tarea = 1 salida = 1 commit
- No tocar LEGACY control-layer sin autorización

### Orden propuesto de arranque
1. **F1.1** — consolidar plantillas ya existentes (project_bootstrap) como capacidad nativa Wordflow  
2. **F0** — Acquire-OS determinista (Obj 3)  
3. **F1 → F2 → F3 → F4** secuencial  
4. **Obj 4** publisher GitHub en paralelo cuando haya BUILD/

---

## 5. SIGUIENTE PUERTA

Director elige:
- **B0** (cerrar 13 tipos ruteo control-layer), o
- **F1.1 / F0** (Wordflow code según §4)
