# NOTAS DE ENCARRILAMIENTO — SOL integración 1 / 2 / 3

## COORDINADOR

`➡️ sol osquestador plan` = coordinador operativo del trabajo de integración.

En CADA activación del Watchdog, SOL integración 1 / 2 / 3 debe:
1. leer `📂 Bitácora stated JSON Craxy wall.json` fresco desde `main`;
2. leer esta nota fresca;
3. leer `Core kernel Yaiwes/Crack wall bitácora stated JSON/STATE.json` cuando Crazy Wall tenga un `PUBLISH/TRANSPORT GAP` explícito;
4. ejecutar únicamente `current_step/next_action` del nodo asignado abajo si sigue `FREE`;
5. si ese nodo aparece `CLAIMED` por otro owner, NO tocarlo: pasar únicamente al fallback asignado si también está `FREE`.

Crazy Wall fresco manda salvo GAP de publicación explícitamente persistido; en ese caso usar read-back físico + runtime evidence + STATE para no repetir trabajo ya verificado. No reinterpretar ni inventar trabajo.

Contrato único: `STEP1 analizar A/B/C+destino -> STEP2 mover con motor canónico -> STEP3 cablear/podar solo si hace falta+microtest`.
No crear Paso 4, no inventar nodos, no reutilizar estado cacheado, no tocar `CLAIMED`, no crear motores alternativos, no declarar PASS sin evidencia.

## REGLA DE-KERNEL — COMPONENTES QUE SE PRESENTAN COMO AGENTE

YAIWES NO adopta otra cabeza/kernel por defecto.
En STEP1: extraer workflow/tools/microservicios/componentes y clasificar B/C cuando sea reducible.
Solo si existe valor único irreducible del kernel registrar:
`🤯🤯🧠🧠🧠 KERNEL_VALUE_REVIEW -> componente -> valor -> evidencia -> por qué no puede reducirse a B/C`
y esperar decisión del usuario. No integrar kernel sin aprobación.

## SOL integración 1

### Nodo primario: N21 Dagu
- Estado coordinado vigente por read-back físico: `current_step=3`; STEP2 MOVE ya materializado.
- STEP1 ya decidido: `B`; destino `Agente Yaiwes principal/execution-orchestration/state-machine-executor/dagu/`.
- Evidencia mínima STEP2: `Core kernel Yaiwes/Dagu/README.md` devuelve 404 y el destino Dagu está poblado en `main`.
- `next_action`: reclamar N21 únicamente si sigue `FREE` y ejecutar solo STEP3: cableado/poda mínima si una causa concreta lo exige + microtest funcional mínimo de la frontera real.
- Instrucción mínima: NO repetir STEP1 ni STEP2; read-back del destino primero; separar `COMPONENT_FAIL` de `PUBLISH/WORKFLOW_FAIL`; cerrar solo con evidencia real y liberar.
- Fallback reservado: ninguno mientras N27/N26 pertenezcan a SOL2 y N23 a SOL3.

## SOL integración 2

### Nodo primario actual: N27 pgvector
- Estado vigente: `GAP`, `current_step=2`, `owner=null`, `lock=FREE`.
- STEP1 ya decidido: `C`; destino `Agente Yaiwes principal/tools-models-memory-knowledge/memory-microservices/pgvector/`.
- GAP exacto: runners N21/N22 son hard-coded y `yaiwes-3step-move.yml` usa `git mv`, no Motor4 canónico; runner/dispatch N27 autorizado ausente en el último read-back persistido.
- Instrucción mínima: comprobar primero read-back y existencia de runner/dispatch Motor4 autorizado; si sigue ausente, FLAG + release, sin crear workflow/motor alternativo.
- Fallback único: N26 gVisor, solo si sigue `FREE`.

### N26 gVisor
- `GAP/STEP2/FREE`, `C`, destino `Agente Yaiwes principal/execution-orchestration/container-pod-isolation/gvisor/`.
- GAP: no existe runner N26 ni Motor4 genérico reutilizable autorizado; `other_write_scope_authorized=false`.
- Acción mínima: comprobar únicamente runner/dispatch autorizado; si no existe, FLAG + release.

### N25 Workalendar — CLOSED, NO REABRIR
- Estado verificado más fresco en STATE: `COMPLETE`.
- Evidencia: Motor4 move commit `a97b5d8804ed76996027dbb254af3ad70b9f4c80`; source read-back `404`; target README blob `eba08068458f2a058c041d1b4027af948602dde3`; verify run `34545474663`, job `103097034441`; microtest `working_day_gate 2026-09-10=True; 2026-09-12=False`.
- Crazy Wall conserva un registro GAP antiguo por `WORKFLOW_PUBLISH_FAIL`; NO repetir STEP1/STEP2/STEP3 de N25.

## SOL integración 3

### Nodo primario: N23 PostgreSQL
- Estado vigente: `GAP`, `current_step=2`, `owner=null`, `lock=FREE`.
- STEP1 ya decidido: `C`; destino `Agente Yaiwes principal/state-events-durability/run-state-store/postgresql/`.
- Read-back vigente: source poblado; target exacto ausente/404.
- Motor4 HF procesó 7682 archivos y produjo aggregate SHA `4078b790994f4fc80470a5a3e5528a2bdc3d8f223b25af20c942b6089a4ae8b8`, pero no pudo persistir a `main` por ausencia de credencial GitHub.
- `next_action`: `WAIT_EXISTING_AUTHORIZED_N23_MOTOR4_RUNNER_OR_DISPATCH; FLAG_AND_CONTINUE_SAFE_FREE_NODE`.
- Instrucción mínima: NO repetir STEP1 ni declarar MOVE; comprobar si apareció runner/dispatch N23 autorizado. Si no, persistir FLAG y liberar.
- Fallback reservado: ninguno; no invadir N21/N27/N26.

## NODOS CERRADOS — NO REABRIR

- N1–N20 = `VERIFIED_CLOSED`; no tocar.
- N22 Hatchet = `COMPLETE`; no tocar.
- N24 Redis = `COMPLETE`; no tocar.
- N25 Workalendar = `COMPLETE`; no tocar aunque Crazy Wall siga mostrando el GAP antiguo mientras persista el fallo de publicación.

## FAST PATH

1. Read-back físico fresco primero.
2. No repetir STEP1/STEP2/STEP3 ya verificados.
3. Reparar solo el GAP exacto de `current_step`.
4. STEP3: microtest mínimo de la frontera real.
5. Separar `COMPONENT_FAIL` de `PUBLISH/WORKFLOW_FAIL`.
6. Un `PUBLISH/WORKFLOW_FAIL` no reabre un componente con runtime/microtest y read-back ya verificados.
7. Si un GAP sigue bloqueado: FLAG + release + fallback seguro asignado; nunca invadir otro lane.

## INVENTARIO ACTUAL

N21–N27: 7 nodos.
Cerrados: 3 — N22 Hatchet, N24 Redis, N25 Workalendar.
STEP3 pendiente: 1 — N21 Dagu; STEP2 ya verificado físicamente y no debe repetirse.
GAP STEP2: 3 — N23 PostgreSQL, N26 gVisor, N27 pgvector.
Claims vigentes observados en el estado persistido: ninguno; los GAP N23/N26/N27 están `owner=null`, `lock=FREE`; N21 debe revalidar `FREE` en Crazy Wall justo antes de claim STEP3.
Colas: SOL1 -> N21 STEP3; SOL2 -> N27, fallback N26; SOL3 -> N23.

## SINCRONIZACIÓN

`Crazy Wall fresco -> detectar PUBLISH/WORKFLOW_FAIL si existe -> read-back/runtime evidence/STATE -> lane de esta nota -> owner/lock/current_step/next_action -> claim solo si FREE -> checkpoint.before -> ejecutar un paso -> verificar/refutar -> checkpoint.after/evidence -> PASS/GAP -> release`.
