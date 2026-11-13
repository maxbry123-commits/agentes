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

## SOURCE DOWNLOAD DETERMINISTA (OBLIGATORIO)

Basado en documentación GitHub (archives estables) y práctica reproducible.

### Regla de oro
**Pin por commit SHA completo de 40 caracteres.**  
El tag solo es etiqueta humana; puede moverse. El commit no.

GitHub: un archive de un **commit ID** siempre tiene el mismo contenido de archivos.  
Un archive de un **tag/branch** puede cambiar si el tag se mueve a otro commit.

### Pin mínimo en el manifest
```yaml
repository: https://github.com/ORG/REPO
tag: vX.Y.Z                    # opcional, etiqueta
commit: <40-char-sha>          # OBLIGATORIO
url_archive_commit: https://github.com/ORG/REPO/archive/<commit>.tar.gz
# o:
url_archive_tag: https://github.com/ORG/REPO/archive/refs/tags/vX.Y.Z.tar.gz
expected_sha256: <sha256-del-artefacto>   # tras primera descarga exitosa
dest: sources/... o agents/<Id>/source/...
```

### Método A — Archive por COMMIT (preferido para reproducibilidad)
```bash
URL="https://github.com/ORG/REPO/archive/<COMMIT_SHA>.tar.gz"
curl -fsSL -o source.tar.gz "$URL"
sha256sum source.tar.gz   # guardar en SHA256SUMS
# opcional: gunzip -c source.tar.gz | git get-tar-commit-id
tar -xzf source.tar.gz -C dest/
```
- URL fija al commit → contenido del árbol estable.
- Guardar SHA-256 del `.tar.gz` en el repo.
- Preferir API/archives con `:ref` = commit ID si se usa la API de GitHub.

### Método B — Git clone + verificar HEAD (script estilo Wordflow/Tencent)
```bash
git clone --depth 1 --branch <TAG> https://github.com/ORG/REPO.git DEST
ACTUAL=$(git -C DEST rev-parse HEAD)
if [ "$ACTUAL" != "<COMMIT_SHA_ESPERADO>" ]; then
  echo "SHA mismatch: got $ACTUAL want <COMMIT>" >&2
  exit 1
fi
```
- Si no coincide → **FAILED**, no marcar VERIFIED.
- No editar archivos del vendor (modified: false).

### Método C — Tag archive + verificación obligatoria
Si solo hay URL de tag:
1. Descargar `.../archive/refs/tags/vX.Y.Z.tar.gz`
2. Registrar SHA-256 del archivo
3. **Obligatorio:** obtener el commit del tag en ese momento y comprobar que sigue siendo el pin
4. Sin paso 3 → **NO es determinista completo**

### Prohibido
- `main` / `master` / `latest` / `HEAD` flotante
- Solo tag sin commit en el manifest
- Marcar VERIFIED sin SHA-256 del artefacto
- Marcar SOURCE completo si el árbol extraído está incompleto
- Declarar 100% si solo existe el `.tar.gz` y el extract falló

### Vendor externo (ej. TencentDB-Agent-Memory)
```
control-layer/memory/providers/<vendor>/
  SOURCE_MANIFEST.yaml    # pin tag+commit+url
  download_deterministic.sh
  adapter.py              # solo nuestro código
sources/<vendor>/<repo>/  # árbol source NO modificado
```
- Nunca editar dentro de `sources/<vendor>/`
- Solo el adapter habla con el motor (HTTP)

### Estados SOURCE
| Estado | Significado |
|--------|-------------|
| FROZEN | pin escrito en manifest |
| ARCHIVE_DOWNLOADED | archivo bajado, size OK |
| ARCHIVE_VERIFIED | SHA-256 OK |
| HEAD_VERIFIED | git rev-parse == commit pin |
| EXTRACT_COMPLETE | árbol completo en dest |
| VERIFIED | archive/tree + hashes + path final OK |
| EXTRACT_PARTIAL | archive OK pero árbol incompleto → **no es 100%** |

### Checklist SOURCE 100%
- [ ] commit SHA 40 chars en manifest
- [ ] URL no flotante (commit o tag+verify)
- [ ] artefacto descargado
- [ ] SHA-256 registrado en SHA256SUMS
- [ ] HEAD o get-tar-commit-id == pin (si aplica)
- [ ] árbol completo en path de destino
- [ ] modified: false para vendor

---

## CASO TENCENT (estado + salidas para cerrar)

Pin: `TencentCloud/TencentDB-Agent-Memory` · tag `v2.0.0` · commit `0aff21a2d9f2b8a0354aaa80a2e586aab4054562`

| Hecho | Pendiente |
|-------|-----------|
| Archive tag ~33.8 MB SHA `6ab73fd3…` (local) | Verify HEAD / archive-by-commit |
| ~282 / 836 files extracted | 554 files remaining OR full re-extract |
| Adapter + SOURCE_MANIFEST en control-layer | Path `sources/tencent/TencentDB-Agent-Memory` completo |
| | SHA256SUMS + status VERIFIED en repo agentes |

### Conteo de salidas (método: 1 unidad → STOP)

**Camino A — cerrar verificación + metadata (sin árbol full en este entorno)**  
~**5 salidas**:
1. FREEZE manifest URL por commit + expected SHA  
2. Confirm archive SHA (no re-download si match)  
3. HEAD_VERIFIED (clone depth-1 branch tag + rev-parse)  
4. SHA256SUMS + MASTER VERIFIED local  
5. Push status/hashes a agentes (no subir 33MB si git limit)

**Camino B — extract completo aquí a 5 files/salida**  
554 restantes ÷ 5 ≈ **111 salidas** solo de extract (+5 de arriba) → **~116** total.  
**Inviable** en chat; usar Camino A o extract offline desde archive VERIFIED.

**Camino C — git clone depth-1 en 1–2 salidas si el entorno lo permite**  
Si clone completa y HEAD match → **3–6 salidas** total al path oficial + metadata.

Política: no declarar Tencent SOURCE 100% sin HEAD_VERIFIED + path completo o archive VERIFIED documentado como única forma de source con extract offline explícito.

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
