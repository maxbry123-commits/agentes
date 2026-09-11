# NOTAS DE ENCARRILAMIENTO — SOL integración 1 / 2 / 3

Fuente obligatoria antes de actuar: `📂 Bitácora stated JSON Craxy wall.json` fresco desde `main`.
Contrato único: `STEP1 analizar A/B/C+destino -> STEP2 mover con motor canónico -> STEP3 cablear/podar solo si hace falta+microtest`.
No crear Paso 4, no inventar nodos, no reutilizar estado cacheado, no tocar `CLAIMED`, no crear motores alternativos, no declarar PASS sin evidencia.

## SOL integración 1
Estado observado: N22 Hatchet = PASS completo, owner=null, lock=FREE, evidencia runtime real + FABLES + read-back.
Nota: NO reabrir Hatchet. Leer Crazy Wall fresco y tomar solamente un nodo EXISTENTE `FREE` que no esté COMPLETE. Ejecutar solo su `current_step` y actualizar checkpoint/evidence antes de seguir.

## SOL integración 2
Estado observado: Redis N24 = PASS real. Dagu N21 = GAP STEP2 por limitación symlink/motor; Workalendar N25 = GAP STEP2; gVisor N26 = GAP STEP2; pgvector N27 = GAP STEP2. Los GAP de N25/N26/N27 indican ausencia de runner Motor4 reutilizable autorizado; no inventar mover manual ni workflow paralelo.
Nota: respetar `next_action` literal del Crazy Wall. Si el GAP no puede resolverse con los motores autorizados ya existentes, persistir FLAG y continuar con otro nodo `FREE`; no construir arquitectura lateral ni declarar MOVE hecho.

## SOL integración 3
Estado observado: trabajo anterior APScheduler ya está absorbido por cierre global 1–20 = VERIFIED_CLOSED. PostgreSQL N23 sigue GAP STEP2: source poblado, target 404; Motor4 en HF procesó contenido pero no pudo persistir a GitHub y no existe runner N23 autorizado.
Nota: NO volver a nodos 1–20. Para N23, seguir solo STEP2 y `next_action`; no usar movimiento manual ni declarar destino poblado sin read-back real. Si continúa bloqueado, FLAG + siguiente nodo FREE.

## Instrucción de sincronización para los 3 chats
Al reactivarse: 1) leer Crazy Wall fresco, 2) confirmar `owner/lock/current_step/next_action`, 3) escribir `checkpoint.before`, 4) ejecutar solo ese paso, 5) verificar/refutar con evidencia, 6) escribir `checkpoint.after` y liberar o dejar GAP demostrado.
Si el estado leído contradice este archivo, manda SIEMPRE Crazy Wall fresco.
