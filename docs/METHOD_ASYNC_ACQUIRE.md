# METHOD_ASYNC_ACQUIRE — Adquisición determinista por capas (sin polling)

**Audience:** cualquier instancia de Grok / Claude / otra AI que trabaje en `maxbry123-commits/agentes`.

**Objetivo:** DESCARGAR → CONSERVAR → FIJAR → VERIFICAR → REPRODUCIR  
**sin** quedarse pegado esperando GitHub Actions ni quemar tokens en bucles de espera.

---

## 1. Regla de oro

1. **DISPATCH** el trabajo pesado (Actions / scripts largos).
2. **ESCRIBE STATE** en el repo.
3. **PARA** la conversación (no hagas `sleep` + poll en bucle).
4. En el siguiente mensaje del usuario ("Ok" / "sigue"): **RESUME** — lee state, consulta el run **una sola vez**, actúa, actualiza state, para otra vez si hace falta.

Nunca:
- `while true: sleep; check status`
- Esperar >1 consulta de estado por turno de chat
- Avanzar al siguiente agente si el actual no está `DONE`

---

## 2. Capas del pipeline

```
C0 DISPATCH     → lanza workflow / script  → escribe state QUEUED/RUNNING → STOP
C1 STATE        → agents/_state/<AgentId>.json (fuente de verdad)
C2 RESUME       → 1× get run → DONE | RUNNING | FAILED | NEED_*
C3 SPLIT JOBS   → jobs cortos, no un monstruo:
                  a) acquire-source     (source + locks + tree SHA)
                  b) acquire-dist-meta  (lista assets + SHA256SUMS)
                  c) acquire-dist-upload (Release assets grandes, async)
                  d) acquire-finalize   (pins + manifest + commit git)
```

### Layout físico del agente (protocolo v2.1)

```
agents/<AgentId>/
  source/complete-source/
  distribution/official/     # ≤90MB + *.PIN.json + SHA256SUMS + assets.json
  distribution/staging/      # solo en runner; NO commit; va a GitHub Release
  distribution/rebuilt/
  dependencies/ build/ models/ runtime/ tools/ plugins/ provenance/ hashes/
  manifest.json
```

Release tag de binarios grandes:
`agent-<AgentId>-<ref>` ejemplo: `agent-Codex-rust-v0.147.0`

Cada artefacto registra: `URL + version/tag + commit + SHA256 + platform + arch`.
Prohibido anclar a `main` / `master` / `latest` / `HEAD`.

---

## 3. Formato de state

Archivo: `agents/_state/<AgentId>.json`

```json
{
  "agent": "Codex",
  "task": "A5",
  "status": "RUNNING",
  "protocol": "TEAM-SEALS-ACQUIRE-v2.1",
  "identity": {
    "repository": "https://github.com/openai/codex",
    "ref": "rust-v0.147.0",
    "commit": "be6e8eac029b183056b7e4402879f15d2c85f61b"
  },
  "workflow": "a5-codex.yml",
  "run_id": 31222211773,
  "release_tag": "agent-Codex-rust-v0.147.0",
  "layers": {
    "source": "PENDING|CAPTURED|FAILED",
    "distribution_git": "PENDING|CAPTURED|N/A",
    "distribution_release": "PENDING|CAPTURED|N/A",
    "finalize": "PENDING|DONE|FAILED"
  },
  "updated_at": "ISO-8601",
  "notes": "una línea"
}
```

**status admitidos:**  
`QUEUED` | `RUNNING` | `NEED_RELEASE` | `NEED_COMMIT` | `DONE` | `FAILED`

Solo `DONE` permite pasar a la siguiente tarea de instalación de agente.

---

## 4. Protocolo de chat (salidas)

- Salidas de texto: máximo ~8–12 líneas salvo listas de tareas pedidas.
- Lista de tareas siempre en cascada (número, tema+fuente, resultado, cómo).
- Cada 3 salidas: AUDIT cruzado con el protocolo de binario/SOURCE.
- Al decir el usuario **Ok**: continuar la siguiente capa o RESUME del state, no re-explicar todo.

### Turno tipo RESUME

1. Leer `agents/_state/<id>.json`
2. Si `run_id`: `get_workflow_run` **una vez**
3. Actualizar state + reportar 4 líneas
4. Si RUNNING → STOP ("sigue en background; Ok para retomar")
5. Si DONE → auditar layout + hashes + marcar DONE
6. Si FAILED → leer logs (cola), proponer fix, no inventar artefactos

---

## 5. Script canónico

`scripts/acquire_agent.py` (v2.1+)

```bash
python scripts/acquire_agent.py \
  --id Codex \
  --repo https://github.com/openai/codex \
  --ref rust-v0.147.0 \
  --commit be6e8eac029b183056b7e4402879f15d2c85f61b
```

- SOURCE completo siempre a git.
- DISTRIBUTION: ≤ `GIT_MAX_BYTES` (90MB) → `distribution/official/`
- > 90MB → `distribution/staging/` + `.PIN.json` en official; workflow sube staging a Release.
- Búsqueda: GitHub releases → npm → PyPI → docker refs (sin inventar).

---

## 6. Control-layer

**NUNCA** borrar ni modificar la capa de control / Wordflow del repo excepto por petición explícita.

---

## 7. Checklist 100% de un agente

- [ ] `source/complete-source/` presente + `commit.txt` + tree/archive SHA256
- [ ] `manifest.json` con identity inmutable
- [ ] `distribution/official/SHA256SUMS` + `assets.json`
- [ ] Binarios grandes en Release `agent-<Id>-<ref>` **o** en git si ≤90MB
- [ ] Pins `*.PIN.json` con `conserved_url` si aplica
- [ ] `agents/_state/<Id>.json` → `status: DONE`
- [ ] control-layer intacto

---

## 8. Tareas actuales (referencia)

| Task | Agente | Estado esperado |
|------|--------|-----------------|
| A1 | pipeline acquire_agent | DONE (v2.1) |
| A2 | OpenClaw | DONE |
| A3 | OpenClaw-headless | DONE (alias A2) |
| A4 | Hermes | SOURCE DONE; dist buscada |
| A5 | Codex | RUNNING/RESUME hasta DONE |
| A6+ | Mimo-Code … | solo tras A5 DONE |

---

*TEAM SEALS / agentes — documento operativo para instancias AI.*
