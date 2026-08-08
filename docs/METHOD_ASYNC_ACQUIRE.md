# METHOD — Deterministic Agent Snapshot (TEAM SEALS)

Para cualquier AI en `maxbry123-commits/agentes`.

## Objetivo
DESCARGAR → CONSERVAR → FIJAR → VERIFICAR → REPRODUCIR  
Snapshot por agente: SOURCE + DISTRIBUTION oficial + deps + build + provenance + hashes.

## Pipeline (genérico)
DISCOVER → PIN → DOWNLOAD → VERIFY → STORE → RECORD HASH → ACQUIRE BINARY → DEPS → BUILD ENV → PROVENANCE → REBUILD? → COMPARE HASH → SNAPSHOT

Pin solo con: `repo + tag/release + commit SHA`. Prohibido main/master/latest/HEAD.

## Qué adquirir (si el proyecto lo publica)
source completo · commit/tag · submódulos · binarios oficiales (todas arch) · modelos/pesos legales · plugins · tools · runtimes · configs ejemplo · manifests · lockfiles · scripts install/build · Dockerfiles · CI · release assets · checksums · firmas · attestations · docs reconstrucción

DISTRIBUTION = el paquete ejecutable oficial (no asumir un solo .exe): binary, AppImage, deb, rpm, tar/zip, Docker, npm/PyPI, standalone.

No inventar. Estados: `VERIFIED` | `NOT_PUBLISHED` | `NOT_VERIFIABLE` | `NOT_REPRODUCIBLE`.

## Búsqueda antes de NOT_PUBLISHED
1 releases/assets 2 npm/PyPI/crates 3 containers+digest 4 páginas oficiales 5 CI público

## Layout
```
agents/<Id>/{source,distribution/{official,rebuilt},models,dependencies,runtime,tools,plugins,build,provenance,hashes,manifest.json}
agents/_state/<Id>.json
```
Release grandes: `agent-<Id>-<ref>` (≤90MB git; >90MB Release + PIN.json).

Cada artefacto: URL + version/tag + commit + SHA256 + platform + arch.

## Async (ahorro tokens)
DISPATCH → STATE → STOP → RESUME (1 check/turno). Sin sleep-poll.  
status: QUEUED|RUNNING|NEED_*|DONE|FAILED. Solo DONE → siguiente agente.  
Workflows mínimos + scripts/*.sh. YAML largo rompe workflow_dispatch.

## Chat
8–12 líneas. Lista tareas: nº / tema+fuente / resultado / cómo. Audit cada 3. Ok=continuar. No tocar control-layer.

## Checklist 100%
[ ] pin inmutable  [ ] SOURCE (tree|archive+SHA)  [ ] DIST oficial o ausencia documentada  
[ ] deps/build si existen  [ ] manifest+SHA256SUMS  [ ] state DONE  [ ] control-layer OK

---

## BINARY DOWNLOAD — límites y anti-bloqueo (OBLIGATORIO)

### Máximo por archivo / chunk
| Tipo | Máximo por operación | Acción |
|------|----------------------|--------|
| Archivo completo | **≤ 32 MB** | Descargar entero en 1 salida, verificar SHA, STOP |
| Archivo **> 32 MB** | **chunks de 16 MB** | 1 chunk por salida (HTTP Range), verificar chunk, checkpoint, STOP |
| Archivo **> 100 MB** | **chunks de 16 MB** | Obligatorio chunked; nunca entero en una salida |
| Extracción de archive | **≤ 5 archivos** por salida | Nunca carpetas enteras grandes; checkpoint de índice; STOP |

### Regla de ejecución (sin quedarse pegado)
```
LOAD MANIFEST / CHECKPOINT
    ↓
SELECT next unit (1 archivo ≤32MB  OR  1 chunk 16MB  OR  ≤5 files extract)
    ↓
EXECUTE unit
    ↓
VERIFY (size + SHA si aplica)
    ↓
UPDATE CHECKPOINT
    ↓
STOP
```

**PROHIBIDO:**
- Esperar procesos largos en la misma salida
- Poll / sleep hasta que termine algo grande
- Extraer árboles completos (`src/`, `extensions/`, etc.) de una vez
- Descargar un binario >32 MB sin Range/chunks
- Re-descargar lo ya `VERIFIED`

**OBLIGATORIO:**
- Enviar la tarea → ejecutar la unidad → parar
- Siguiente salida lee checkpoint y continúa
- Determinismo: tag/commit/asset id/digest; nunca `latest`

### Chunked download (binarios grandes)
```
artifact/
├── chunks/
│   ├── 000000
│   ├── 000001
│   └── ...
├── reconstructed/
│   └── original-file
└── manifest.json
```
Todos los chunks VERIFIED → REASSEMBLE → verify full SHA256 → STORE → STOP.

### Binary ya adquirido
Si el binario oficial ya está en el repo / `A1/binary/` con SHA verificado: **NO volver a descargar**. Solo documentar ruta + SHA.
