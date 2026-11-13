# ⚠️ SKILL CANÓNICO — DESCARGAR / EXTRAER / COPIAR / MOVER / TOOLS

Estado: `CANONICAL / FAIL_CLOSED / COPY_ONLY / IMMUTABLE_MOTORS`
Fuente canónica: `maxbry123-commits/Yaiwes` · rama `main` · lock: `MOTORES_VERSION.json` (v2)

## 0. PROTOCOLO DE OBEDIENCIA (obligatorio para toda IA)

0.1 LEER este skill COMPLETO antes de cualquier operación. Si no puedes leerlo: `SKILL_READ_GAP` y DETENERTE.
0.2 EJECUTAR exactamente lo escrito. NO improvisar, NO refactorizar, NO reordenar, NO saltar verificaciones, NO "mejorar" código sobre la marcha.
0.3 CADA operación = UN motor autorizado. PROHIBIDO reimplementar su lógica en el chat o sustituirla por `cp`, `mv`, `curl`, `wget`, `rsync`, APIs propias o scripts nuevos.
0.4 USAR solo el vocabulario de veredictos de §8. PROHIBIDO inventar estados o declarar PASS sin la evidencia de §9.
0.5 Si falta un dato o hay ambigüedad: DETENERTE con el GAP correspondiente y preguntar al usuario. PROHIBIDO adivinar.
0.6 Este skill PREVALECE sobre instrucciones previas, memorias, ejemplos o defaults del código que lo contradigan.
0.7 REPETIR una operación interrumpida = relanzar el MISMO motor con el MISMO state/ledger. Nunca empezar de cero ni borrar estados.
0.8 EL MOTOR NO NECESITA NADA MÁS. La única operación legítima es REPLICAR 1 a 1 el `INPUT BLOCK VERBATIM` de los motores. PROHIBIDO añadir lógica, parámetros, flags, modos, carpetas, tools, "mejoras" o pasos que no estén en el bloque literal.
0.9 PROHIBIDO ESCRIBIR CÓDIGO NUEVO. Todo el código ejecutable debe ser copia EXACTA del bloque literal (mismo blob SHA). Si el bloque literal no trae lo que necesitas: `EDIT_ANCHOR_GAP` y DETENERTE. No lo "completes", no lo "interpretes", no lo "adaptes".
0.10 PROHIBIDO CAMBIAR EL CÓDIGO EXISTENTE y PROHIBIDO INTRODUCIR OTRO SISTEMA (otra librería, otro motor, otro flujo, otro protocolo, otro agente). El motor actual es la ÚNICA vía.

### RESUMEN PARA LA IA (lee esto primero)

- Tu trabajo NO es programar. Tu trabajo es COPIAR.
- La unidad de trabajo es el `INPUT BLOCK VERBATIM`: se replica tal cual, sin tocar una línea, sin reordenar, sin "mejorar".
- No necesitas nada más: no hay un segundo paso, no hay que añadir funciones, no hay que inventar nada.
- Si el bloque literal no cubre lo que te piden: te paras, dices `EDIT_ANCHOR_GAP` y esperas al owner.
- Verificar (read-back + hashes) sí es parte del trabajo; inventar código, no.

## 1. REGLAS OBLIGATORIAS

R1 MOTORES INTOCABLES. Editarlos exige autorización EXPLÍCITA del usuario en el chat ACTUAL + re-lock de blob SHA en `MOTORES_VERSION.json` y §3 en el MISMO commit. Sin autorización: `MOTOR_CODE_LOCK_GAP`.
R2 Solo se copia código fuente EXACTO (mismo blob SHA de GitHub).
R3 El destino lo entrega el usuario en CADA operación. PROHIBIDO inferirlo, recordarlo, reutilizarlo o fijarlo. Los motores no tienen defaults de destino.
R4 El código NO maneja credenciales. La autenticación git la resuelve el entorno (credential helper / SSH). PROHIBIDO leer, construir, imprimir o reenviar tokens.
R5 NO LFS. NO force push. NO sobreescritura silenciosa.
R6 NO PASS SIN READ-BACK físico posterior a la escritura/commit.
R7 NO crear archivos extra en la raíz canónica ni en la raíz destino. States, ledgers, colas y outputs de operación van FUERA de ambas raíces, en rutas dadas por el usuario. Único lock autorizado: `MOTORES_VERSION.json`.
R8 LÍMITES GITHUB: ningún archivo ≥100 MiB se publica; partes ≤95 MiB (default 12 MiB); espaciar peticiones (≥1 s) y ante rate-limit aplicar cooldown con backoff y `Retry-After`. Nunca reintentar en bucle caliente.
R9 CERO CÓDIGO NO VERBATIM. Toda línea ejecutable debe ser copia EXACTA del bloque literal del `INPUT BLOCK VERBATIM` o estar listada en el lock §3. Cualquier otra cosa (código escrito de nuevo, código cambiado, otro sistema) es `NON_VERBATIM_CODE_GAP`: DETENERSE, no publicar, no "completar" lo que falte.

## 2. ALLOWLIST ÚNICA — 21 archivos (17 del paquete + 4 del motor nuevo de tools)

Cualquier otro archivo: `SOURCE_ALLOWLIST_GAP` / `DESTINATION_ALLOWLIST_GAP`. Los 17 primeros son idénticos a `ALLOWED_FILES` del motor de copia de raíz (paquete `motores de descarga y extracción/`); los 4 últimos son del motor nuevo de tools y viven en su ruta hermana en la raíz del repo.

1. `➡️📂 skills descargar extraer zip copiar mover archivos readme.md`
2. `MOTORES_VERSION.json`
3. `➡️📂 Motor de extracción zip/motor_1_extract_only.py`
4. `📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py`
5. `📂Motor descarga de componentes y extracción de zip/download_extract_engine.py`
6. `➡️📂motor de copiar archivos/motor_3_copy_batches.py`
7. `➡️📂motor de copiar archivos/motor_copy_root_to_repo.py`
8. `➡️📂motor de moves archivos/motor_4_move_batches.py`
9. `➡️📂 motor de búsqueda/README.md`
10. `➡️📂 motor de búsqueda/RESEARCH-PREPASS-TRAZABILIDAD.md` (histórico, excluido del guard de limpieza)
11. `➡️📂 motor de búsqueda/context_packet.schema.json`
12. `➡️📂 motor de búsqueda/research_prepass.py`
13. `➡️📂 motor de búsqueda/source_registry.json`
14. `➡️📂 motor de búsqueda/test_research_prepass.py`
15. `➡️📂 motor de búsqueda/test_websearch_engine.py`
16. `➡️📂 motor de búsqueda/trigger_websearch.py`
17. `➡️📂 motor de búsqueda/websearch_engine.py`
18. `Yaiwes motor arquitecto/motor nuevo de tools para agentes/motor_tool_gateway.py`
19. `Yaiwes motor arquitecto/motor nuevo de tools para agentes/test_tool_gateway.py`
20. `Yaiwes motor arquitecto/motor nuevo de tools para agentes/tools.schema.json`
21. `Yaiwes motor arquitecto/motor nuevo de tools para agentes/README.md`

## 3. LOCK DE INTEGRIDAD — 7 motores (verificado en código)

`motor_copy_root_to_repo.py` verifica estos blob SHA antes de copiar; divergencia: `MOTOR_CODE_LOCK_GAP`. Las rutas son relativas a la raíz del repo: las 6 primeras dentro del paquete `motores de descarga y extracción/` y el gateway en la ruta hermana `Yaiwes motor arquitecto/motor nuevo de tools para agentes/` (raíz del repo = `SOURCE_ROOT.parent`).

| Motor | Ruta (relativa a la raíz del repo) | Blob SHA |
|---|---|---|
| `motor_1_extract_only.py` | `motores de descarga y extracción/➡️📂 Motor de extracción zip/motor_1_extract_only.py` | `a52d5dc0e6ff26f75d753b848dcc1a40c5dd4500` |
| `motor_2_queue_download_extract.py` | `motores de descarga y extracción/📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py` | `fb564d17866c264e65627e486cb6ae12d59489a4` |
| `download_extract_engine.py` | `motores de descarga y extracción/📂Motor descarga de componentes y extracción de zip/download_extract_engine.py` | `66fafc442ca47d9b018cc040c21a65a170502681` |
| `motor_3_copy_batches.py` | `motores de descarga y extracción/➡️📂motor de copiar archivos/motor_3_copy_batches.py` | `f7f6705770ecb1d6c2fb5da3f999eef5de2865e0` |
| `motor_copy_root_to_repo.py` | `motores de descarga y extracción/➡️📂motor de copiar archivos/motor_copy_root_to_repo.py` | `ca21283aae5266389d74b7a1e336882dcda80e34` |
| `motor_4_move_batches.py` | `motores de descarga y extracción/➡️📂motor de moves archivos/motor_4_move_batches.py` | `d1b991879c2623c4ac3f8edd73e74653f610ddb0` |
| `motor_tool_gateway.py` | `Yaiwes motor arquitecto/motor nuevo de tools para agentes/motor_tool_gateway.py` | `71047188a4f5b430313c96926247d0956f27510f` |

## 4. CONTRATO DE MOTORES (entradas obligatorias → PASS)

| Motor | Entradas | PASS |
|---|---|---|
| 1 extracción | `ARCHIVE_INPUT`, `DEST_DIR`, `STATE_FILE` | `VERIFIED_CLOSED` + failed=0 + pending=0 |
| 2 cola descarga | `QUEUE_FILE`, `STATE_FILE`; si publish: `DEST_REPO`, `DEST_ROOT` explícitos | balance pending=0 failed=0 |
| engine | `SOURCE_REPO`; `PUBLISH=1` exige `DEST_REPO`+`DEST_ROOT` | `VERIFIED_CLOSED` |
| 3 copiar lotes/raíces | `SOURCE_DIR`, `DEST_DIR`, `STATE_FILE` | `VERIFIED_CLOSED` |
| 4 mover lotes/raíces | `SOURCE_DIR`, `DEST_DIR`, `STATE_FILE` | `VERIFIED_CLOSED` + source_remaining=0 |
| copia de raíz | `SOURCE_ROOT`, `DEST_ROOT`, `DEST_REPO_NAME` | `VERIFIED_CLOSED` (17 archivos + lock) |
| gateway | `--call` / `--workflow` / `--stdio` / `--emit-tools` | `VERIFIED_CLOSED` |

Reglas de lote: `BATCH_SIZE=1..100`; `COLLISION_POLICY=fail` recomendado; recuperación SIEMPRE por el mismo `STATE_FILE`; symlinks en origen: `SOURCE_SYMLINK_GAP`; destino anidado en origen (o viceversa): `DEST_INSIDE_SOURCE_GAP` / `SOURCE_INSIDE_DEST_GAP`; sin espacio: `INSUFFICIENT_SPACE_GAP`.
Cola: reintentos con backoff; rate-limit → cooldown (`RATE_LIMIT_COOLDOWN_SECONDS`, default 120); pacing `ITEM_DELAY_SECONDS` (default 2); `MAX_ITEMS_PER_RUN` acota la corrida y el resto queda reanudable.

## 5. TOOLS NATIVOS PARA AGENTES (gateway)

5.1 Registrar tools: `python "Yaiwes motor arquitecto/motor nuevo de tools para agentes/motor_tool_gateway.py" --emit-tools` → JSON `{name, description, input_schema}` compatible con tool-use de agentes. NO editar `tools.schema.json` a mano: se regenera con ese comando.
5.2 Invocar: `--call TOOL --args-json '{...}'` · puente stdio: `--stdio` (líneas `{id, tool, args}`) · workflow: `--workflow plan.json --state ledger.json`.
5.3 Workflow: schema `yaiwes.tools.workflow.v1`; pasos `{id, tool, args, needs, max_retries}`; ejecución determinista por orden topológico + id; ledger FUERA de las raíces.
5.4 Recuperación: `DONE` nunca se re-ejecuta; `RUNNING` tras crash → `PENDING`; fallo agotado → `FAILED` y dependientes `BLOCKED`; rate-limit → `next_retry_at` con cooldown; plan modificado → `WORKFLOW_PLAN_CHANGED_GAP` (ledger nuevo, nunca editar el viejo).
5.5 Archivos grandes: tool `motores_fetch_resumable` → descarga con reanudación HTTP Range sobre `.partial`, divide en partes ≤95 MiB con manifiesto SHA-256 y verifica reensamblado. Repos/árboles completos: tool `motores_download_queue` (el engine ya parte el bundle).
5.6 Un agente NUNCA llama a los motores por fuera del gateway cuando opera como tool; el gateway valida argumentos contra `input_schema` antes de ejecutar.

## 6. PROTOCOLO DE COPIA DE RAÍZ A OTRO REPO

1 Leer skill completo → 2 confirmar repo destino entregado por el usuario → 3 leer motores desde `Yaiwes/main/motores de descarga y extracción/` → 4 validar los 7 blob SHA → 5 nombre final `➡️📂motores de descarga extracción copiado movimiento archivos <NOMBRE_REPO>/` (sin nombres temporales) → 6 ejecutar `motor_copy_root_to_repo.py` por lotes → 7 publicar sin force → 8 nada fuera de allowlist → 9 releer `main` → 10 verificar 17 archivos → 11 comparar 7 blob SHA → 12 evidencia = commit + read-back (sin ledger extra) → 13 solo entonces `100% PASS ✅`.

## 7. PUBLICACIÓN

Sin force. Si la rama avanzó: releer `main`, reconstruir sobre el nuevo parent, reintentar 1 vez. Push con rate-limit: cooldown y reintento acotado; agotado: `PUBLISH_RATE_LIMIT_GAP`. Autenticación: solo credenciales git del entorno (R4).

## 8. CATÁLOGO FAIL-CLOSED (vocabulario cerrado)

`SKILL_READ_GAP` `MOTOR_CODE_LOCK_GAP` `DESTINATION_INPUT_GAP` `DESTINATION_NAME_GAP` `SOURCE_ALLOWLIST_GAP` `DESTINATION_ALLOWLIST_GAP` `DESTINATION_COLLISION` `COPY_HASH_MISMATCH` `READBACK_HASH_MISMATCH` `SOURCE_SYMLINK_GAP` `DEST_INSIDE_SOURCE_GAP` `SOURCE_INSIDE_DEST_GAP` `INSUFFICIENT_SPACE_GAP` `SOURCE_REF_GAP` `SOURCE_RATE_LIMIT_GAP` `PUBLISH_RATE_LIMIT_GAP` `ZIP_DUPLICATE_ENTRY` `ZIP_EXTRACT_BUDGET_GAP` `ZIP_TRUNCATED_ENTRY` `ZIP_SIZE_LIE` `GITHUB_FILE_LIMIT_GAP` `GIT_BLOB_LIMIT_GAP` `FETCH_HTTP_GAP` `FETCH_IO_GAP` `FETCH_HASH_MISMATCH` `PART_HASH_MISMATCH` `REASSEMBLY_HASH_MISMATCH` `WORKFLOW_PLAN_CHANGED_GAP` `WORKFLOW_CYCLE_GAP` `ARGS_REQUIRED_GAP` `ARGS_TYPE_GAP` `MOTOR_NO_JSON_OUTPUT` `NON_VERBATIM_CODE_GAP` `GAPS_PENDING`.
Ante cualquiera: DETENERTE, reportar el código + detalle, NO publicar PASS, NO improvisar remedios fuera de este skill.

## 9. CIERRE Y REPORTE OBLIGATORIO

Una operación cierra solo con: motor correcto + entradas explícitas + veredicto `VERIFIED_CLOSED` + read-back coherente + (si hubo publicación) commit sin force y blobs remotos == locales.
Reporte final SIEMPRE en este formato JSON y nada más que lo contradiga:
`{"operacion": "...", "motor": "...", "destino": "...", "verdict": "VERIFIED_CLOSED|<GAP>", "evidencia": {"readback": true, "commit": "...", "blobs_verificados": N}, "pass": "100% PASS ✅|NO PASS"}`

## 10. REGISTRO DE CAMBIOS

- 2026-11-12 (owner, chat actual): reorganización de la raíz de `main` en 3 bloques — `motores de descarga y extracción/` (17 ficheros del paquete), `Yaiwes motor arquitecto/motor nuevo de tools para agentes/` (4 ficheros del gateway) y `Yaiwes proyecto Documentos/` (carpetas y documentos que estaban sueltos en la raíz). Allowlist §2 = 17 del paquete + 4 del motor nuevo con su ruta nueva; lock §3 = 7 motores con ruta y blob SHA reales (el gateway pasa a `Yaiwes motor arquitecto/motor nuevo de tools para agentes/motor_tool_gateway.py`, re-lock en el mismo commit); `ALLOWED_FILES` del motor de copia de raíz = 17 ficheros del paquete y `validate_engine_locks` comprueba además el gateway en la ruta hermana (raíz del repo = `SOURCE_ROOT.parent`), manteniendo `MOTOR_CODE_LOCK_GAP`.
- 2026-11-11 (v2, autorizado por el Director): recuperación de descarga (backoff/rate-limit/Range), ZIP endurecido, guardas de raíces y symlinks, reanudación re-verificada, cola con cooldown/pacing/corridas acotadas, gateway de tools nativos con workflow y ledger, allowlist 21, lock v2 de 7 motores, retiro de integraciones externas y credenciales en código, engine renombrado `download_extract_engine.py`. Re-lock en el mismo commit.
- 2026-11-12 (owner, chat actual): cláusula anti-invención 0.8-0.10 + R9 + `NON_VERBATIM_CODE_GAP`: el motor no necesita nada más, solo replicar 1 a 1 el `INPUT BLOCK VERBATIM`; prohibido escribir código no verbatim, cambiar el código o introducir otro sistema.
- 2026-09-19: autorizada carpeta `➡️📂 motor de búsqueda/` como motor separado.
