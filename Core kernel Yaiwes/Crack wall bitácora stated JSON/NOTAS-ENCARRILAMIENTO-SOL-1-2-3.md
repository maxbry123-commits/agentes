# NOTAS DE ENCARRILAMIENTO — SOL integración 1 / 2 / 3

## COORDINADOR

`➡️ sol osquestador plan` = coordinador operativo del trabajo de integración.

En CADA activación del Watchdog, SOL integración 1 / 2 / 3 debe:
1. leer `📂 Bitácora stated JSON Craxy wall.json` fresco desde `main`;
2. leer esta nota fresca;
3. ejecutar únicamente `current_step/next_action` del nodo asignado abajo si sigue `FREE`;
4. si ese nodo aparece `CLAIMED` por otro owner, NO tocarlo: pasar únicamente al fallback asignado si también está `FREE`.

Crazy Wall fresco manda sobre esta nota. No reinterpretar ni inventar trabajo.

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
- Estado fresco: `GAP`, `current_step=2`, `owner=null`, `lock=FREE`.
- STEP1 ya decidido: `B`; destino `Agente Yaiwes principal/execution-orchestration/state-machine-executor/dagu/`.
- GAP exacto: fuente residual `schemas/` contiene dos symlinks relativos rotos; Motor4 canónico usa `rglob(...).is_file()` y no los incluye.
- `next_action` literal: `STEP_2_REQUIRES_AUTHORIZED_SYMLINK_AWARE_EXECUTION_WITH_CANONICAL_MOTOR4; FLAG_AND_CONTINUE_SAFE_FREE_NODE`.
- Instrucción mínima: read-back físico primero; NO repetir STEP1 ni el MOVE ya verificado del resto; reparar únicamente la frontera symlink mediante ejecución autorizada del Motor4. Si no existe esa ejecución autorizada, persistir FLAG y soltar el nodo.
- Fallback seguro asignado: N25 Workalendar, solo si sigue `FREE`.

## SOL integración 2

### Nodo primario: N25 Workalendar
- Estado fresco: `GAP`, `current_step=2`, `owner=null`, `lock=FREE`.
- STEP1 ya decidido: `C`; destino `Agente Yaiwes principal/execution-orchestration/classifier-scheduler/workalendar/`.
- GAP exacto: no existe runner N25 ni runner Motor4 genérico reutilizable autorizado.
- `next_action` literal: `STEP_2_MOVE_WITH_CANONICAL_MOTOR_REQUIRES_EXISTING_AUTHORIZED_RUNNER_OR_DISPATCH`.
- Instrucción mínima: verificar read-back y disponibilidad de runner/dispatch autorizado; si sigue ausente, FLAG y liberar, sin crear workflow/motor alternativo.
- Fallback 1: N26 gVisor, solo si `FREE`.
- Fallback 2: N27 pgvector, solo si `FREE`.

### N26 gVisor
- `GAP/STEP2/FREE`, `C`, destino `Agente Yaiwes principal/execution-orchestration/container-pod-isolation/gvisor/`.
- GAP: no existe runner N26 ni Motor4 genérico reutilizable; `other_write_scope_authorized=false`.
- Acción: comprobar solo runner/dispatch autorizado; si no existe, FLAG + release.

### N27 pgvector
- `GAP/STEP2/FREE`, `C`, destino `Agente Yaiwes principal/tools-models-memory-knowledge/memory-microservices/pgvector/`.
- GAP: runners N21/N22 son hard-coded y `yaiwes-3step-move.yml` usa `git mv`, no Motor4 canónico.
- Acción: comprobar solo runner/dispatch autorizado; si no existe, FLAG + release.

## SOL integración 3

### Nodo primario: N23 PostgreSQL
- Estado fresco: `GAP`, `current_step=2`, `owner=null`, `lock=FREE`.
- STEP1 ya decidido: `C`; destino `Agente Yaiwes principal/state-events-durability/run-state-store/postgresql/`.
- Read-back vigente: source poblado; target exacto ausente/404.
- Motor4 HF procesó 7682 archivos y produjo aggregate SHA `4078b790994f4fc80470a5a3e5528a2bdc3d8f223b25af20c942b6089a4ae8b8`, pero no pudo persistir a `main` por ausencia de credencial GitHub.
- `next_action` literal: `WAIT_EXISTING_AUTHORIZED_N23_MOTOR4_RUNNER_OR_DISPATCH; FLAG_AND_CONTINUE_SAFE_FREE_NODE`.
- Instrucción mínima: NO repetir STEP1 ni declarar MOVE; comprobar si apareció runner/dispatch N23 autorizado. Si no, persistir FLAG y liberar.
- Fallback seguro: ninguno reservado; no invadir N21/N25/N26/N27 mientras estén asignados a SOL1/SOL2.

## NODOS CERRADOS — NO REABRIR

- N1–N20 = `VERIFIED_CLOSED`; no tocar.
- N22 Hatchet = `PASS`, owner=null, lock=FREE; COMPLETE; no tocar.
- N24 Redis = `PASS`, owner=null, lock=FREE; COMPLETE; no tocar.

## FAST PATH

1. Read-back físico fresco primero.
2. No repetir STEP1/STEP2 ya verificados.
3. Reparar solo el GAP exacto de `current_step`.
4. STEP3: microtest mínimo de la frontera real.
5. Separar `COMPONENT_FAIL` de `PUBLISH/WORKFLOW_FAIL`.
6. Si un GAP sigue bloqueado: FLAG + release + fallback seguro asignado; nunca invadir otro lane.

## INVENTARIO ACTUAL

N21–N27: 7 nodos.
Cerrados: 2 — N22 Hatchet, N24 Redis.
GAP STEP2: 5 — N21 Dagu, N23 PostgreSQL, N25 Workalendar, N26 gVisor, N27 pgvector.
Claims frescos observados al coordinar: ninguno; los cinco GAP estaban `owner=null`, `lock=FREE`.

## SINCRONIZACIÓN

`Crazy Wall fresco -> lane de esta nota -> owner/lock/current_step/next_action -> claim solo si FREE -> checkpoint.before -> ejecutar un paso -> verificar/refutar -> checkpoint.after/evidence -> PASS/GAP -> release`.
