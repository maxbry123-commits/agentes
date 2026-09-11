# NOTAS DE ENCARRILAMIENTO — SOL integración 1 / 2 / 3

## COORDINADOR

`➡️ sol osquestador plan` = coordinador operativo del trabajo de integración.

En CADA activación del Watchdog, SOL integración 1 / 2 / 3 debe:
1. leer `📂 Bitácora stated JSON Craxy wall.json` fresco desde `main`;
2. leer esta nota fresca;
3. revisar la indicación más reciente de `➡️ sol osquestador plan`;
4. ejecutar únicamente `current_step/next_action` del nodo FREE reclamado.

Crazy Wall fresco manda sobre cualquier nota antigua. Si no existe indicación nueva del coordinador, NO esperar: continuar literalmente el `current_step/next_action` del nodo FREE. No reinterpretar ni inventar trabajo.

Contrato único: `STEP1 analizar A/B/C+destino -> STEP2 mover con motor canónico -> STEP3 cablear/podar solo si hace falta+microtest`.
No crear Paso 4, no inventar nodos, no reutilizar estado cacheado, no tocar `CLAIMED`, no crear motores alternativos, no declarar PASS sin evidencia.

## REGLA ESPECIAL — COMPONENTES QUE SE PRESENTAN COMO "AGENTE"

YAIWES NO quiere otra cabeza/kernel por defecto.

En STEP1, si el componente upstream es un agente:
- primero identificar qué valor real aporta: workflow determinista, tools, microservicio, adapter, scheduler, memoria, policy, runtime o componente;
- por defecto DESCAPITAR/PODAR la cabeza/kernel del agente y reutilizar solo ese valor como B o C;
- solo mantenerlo como candidato A si su kernel aporta una capacidad única que YAIWES no tiene y que no puede extraerse limpiamente como workflow/tool/microservicio.

Si aparece valor real del kernel, NO integrarlo automáticamente. Registrar:
`🤯🤯🧠🧠🧠 KERNEL_VALUE_REVIEW -> componente -> valor único -> evidencia -> por qué no puede reducirse a workflow/tool/microservicio`
y enviarlo a `➡️ sol osquestador plan` para presentarlo al usuario y esperar decisión.

## SOL integración 1
Estado observado: N22 Hatchet = PASS completo, owner=null, lock=FREE, evidencia runtime real + FABLES + read-back.
Nota: NO reabrir Hatchet. Leer Crazy Wall fresco y tomar solamente un nodo EXISTENTE `FREE` que no esté COMPLETE. Ejecutar solo su `current_step` y actualizar checkpoint/evidence antes de seguir.

## SOL integración 2
Estado observado: Redis N24 = PASS real. Dagu N21 = GAP STEP2; Workalendar N25 = GAP STEP2; gVisor N26 = GAP STEP2; pgvector N27 = GAP STEP2.
Nota: respetar `next_action` literal del Crazy Wall. Si el GAP no puede resolverse con motores autorizados ya existentes, persistir FLAG y continuar con otro nodo `FREE`; no inventar movimiento manual, workflow paralelo ni arquitectura lateral.

## SOL integración 3
Estado observado: nodos 1–20 = VERIFIED_CLOSED. PostgreSQL N23 sigue GAP STEP2: source poblado, target ausente; Motor4 procesó contenido fuera de GitHub pero no persistió a `main` y no existe runner N23 autorizado.
Nota: NO volver a nodos 1–20. Para N23, seguir solo STEP2 y `next_action`; no declarar destino poblado sin read-back real. Si continúa bloqueado, FLAG + siguiente nodo FREE.

## FAST PATH APRENDIDO DEL CIERRE 1–20

1. Leer estado físico fresco antes de actuar.
2. NO repetir STEP1/STEP2 ya verificados.
3. Trabajar solo el GAP exacto del `current_step`.
4. En STEP3 usar el microtest funcional mínimo de la capacidad real; NO construir/testear todo upstream si no es necesario.
5. Si falla, cambiar solo adapter/comando/configuración responsable y repetir el mismo microtest.
6. Separar `COMPONENT_FAIL` de `PUBLISH/WORKFLOW_FAIL`: si los microtests pasan y falla solo publicar evidencia, NO reabrir ni modificar el componente.

## INVENTARIO ACTUAL

Nuevos después de 1–20: **7 componentes (N21–N27)**.
Cerrados: **2** — N22 Hatchet, N24 Redis.
Pendientes/GAP: **5** — N21 Dagu, N23 PostgreSQL, N25 Workalendar, N26 gVisor, N27 pgvector.

## SINCRONIZACIÓN

`Crazy Wall fresco -> nota coordinador -> owner/lock/current_step/next_action -> checkpoint.before -> ejecutar un paso -> verificar/refutar -> checkpoint.after/evidence -> PASS/GAP -> release`.
