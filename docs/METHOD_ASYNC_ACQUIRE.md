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
