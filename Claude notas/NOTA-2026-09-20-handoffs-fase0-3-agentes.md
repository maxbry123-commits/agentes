# Nota 2026-09-20 - Pool de agentes verificado + handoffs fase_0

## 1. Verificacion del pool (los 4 agentes pedidos)
Verificado por listado directo del arbol de `agent_sources/` (no por busqueda, la busqueda de codigo de GitHub devolvio 0 resultados incluso para archivos que existen - no confiar en `/search/code` para este repo):

- `claude_code`: presente, contenido real (README.md, CHANGELOG.md, SECURITY.md, scripts/, plugins/, examples/)
- `codex`: presente, contenido real (listado extenso)
- `opencode`: presente, contenido real (listado extenso)
- `mcode`: AUSENTE. No aparece bajo ningun nombre. Coincide con el nodo N-1.3 del DAG, que ya lo tenia identificado como el unico gap de descarga.

## 2. Fuente real de dependencias
No se invento un analisis de bloqueos nuevo: `Claude notas/PLAN-DSL-DAG-01-NODOS.yaml` ya trae `depends_on` / `bloquea` por nodo y un `orden_ejecucion` con 9 fases precalculado. Se uso eso.

`fase_0_desbloqueo` (los unicos 5 nodos sin dependencias, ejecutables ya): N-1.1, N-1.3, N-1.4, N-2.8, N-2.11.

Nodos con mas impacto de desbloqueo dentro de fase_0:
- N-1.1 bloquea N-1.2 y N-3.1
- N-2.4 (fuera de fase_0, YA tiene depends_on:[] pero el estado real se contradice, ver seccion 3) bloquea N-3.1
- N-2.8 bloquea N-2.9 y N-2.12
- N-2.11 bloquea N-1.5

## 3. Discrepancia detectada (no resuelta, solo documentada)
`Claude notas/PLAN-DSL-DAG-01-NODOS.yaml` (fuente de verdad segun el propio contrato) tiene los 33 nodos en estado `PENDIENTE`, incluido `N-2.4` (CheckpointManager durable). Sin embargo hay un archivo local (`/home/claude/patch-checkpoint/memoria_current.md`, nunca subido al repo) que describe N-2.4/G06 como ya cerrado con PASS, test, sha256 y commits reales (`266ab97a...`, `fccac012...`). No se resolvio esta discrepancia hoy ni se toco `memoria.md` ni el estado del DAG - queda como FLAG para que el Director confirme cual es el estado real de N-2.4 antes de que algun agente lo vuelva a tocar.

## 4. Handoffs creados (fase_0, 3 de los 5 nodos asignados)
- `Claude notas/handoffs/HANDOFF-claude_code.md` -> N-1.3 (montar mcode) + N-1.4 (5 keys NVIDIA)
- `Claude notas/handoffs/HANDOFF-codex.md` -> N-1.1 (submodules en CI)
- `Claude notas/handoffs/HANDOFF-opencode.md` -> N-2.8 (7 archivos de gobernanza) + N-2.11 (biblioteca RAG)

Formato reutilizado, no inventado: campos de `Core kernel Yaiwes/control-layer/schemas/output_contract.yaml` (mission_id, status, sheriff_state, evidence_hash, etc.) + `id` de nodo del propio DAG para la traza.

## 5. Lo que esto NO es
Los 3 "agentes" verificados son copias de codigo fuente montadas en el repo (submodules/carpetas), no procesos vivos que este chat pueda invocar directamente. Los handoffs son el contrato de tarea listo para que ese CLI (instalado y ejecutado, por quien lo dispare) lo lea y ejecute - no hay, todavia, un dispatcher automatico corriendo esos 3 CLIs desde esta sesion. Eso no se armo hoy porque no estaba autorizado explicitamente y requiere credenciales propias de cada CLI.

## 6. Gap sin tocar
`dag_schema.yaml` referenciado en el plan bajo "Seals team YAIWES/dag_schema.yaml" no se verifico su existencia hoy (no se encontro por busqueda ni se listo esa carpeta especifica) - no se cito como si existiera en ningun handoff.
