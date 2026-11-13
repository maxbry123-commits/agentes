# README - MINI LOOP CODA BUCLE (como funciona y como repetirlo)

Esto explica el PROCESO DE TRABAJO, no el plan. El plan esta en PLAN-MAESTRO-4-OBJETIVOS.md
y en PROMPT-DSL-DAG-PLAN-OPUS.yaml. Este archivo sirve para repetir el ciclo, revisarlo y
corregirlo sin depender de ningun chat.

## 1. Las piezas (todo en Claude notas/PLAN-OPUS/)

1. PROMPT-DSL-DAG-PLAN-OPUS.yaml - el DAG: 4 objetivos, nodos, quien ejecuta/audita/repara, grupos, router.
2. runner/plan_opus_loop.py - el loop. Usa la cola durable de Fables (coda workflow persistencias, SQLiteDurableStore).
3. runner/sonda_apis.py - el mini router: prueba que las APIs responden y que modelo usar.
4. CENTRO-DE-CONTROL.yaml - donde Sonnet, Sol o el Director dan ordenes.
5. CRAZY-WALL-BITACORA-PLAN-OPUS.json - donde queda anotado todo (solo se anade).
6. agentes/README-AGENTE-<nombre>.md - memoria e instrucciones de cada agente.
7. estado/SALUD-APIS.json - resultado de la sonda de APIs de la ultima vuelta.
8. estado/plan_opus_queue.db - la cola durable (que nodo esta hecho, en cola o fallido).
9. evidencia/<nodo>-<fecha>/ - logs de cada agente, ask_consul.json, EVIDENCIA.json con sha256.
10. Boton: .github/workflows/plan-opus-loop.yml (Actions > "Plan Opus - loop de agentes").

## 2. Una vuelta del bucle, paso a paso

1. Centro de control: se aplican las ordenes PENDIENTE (REACTIVAR, INSTRUCCION, PAUSAR, NUEVO_NODO, REVISION).
2. Cola: se siembra desde el DAG. Lo que ya es DONE no se repite.
3. Sonda de APIs (mini router): por cada proveedor con clave (NVIDIA por banco, Cerebras, Groq):
   GET /models con cada clave (valida o invalida), busca qwen y gpt-oss en el catalogo real, manda
   "Responde solo con la palabra OK" y mide HTTP, tiempo y respuesta. Recomienda el modelo mas rapido que paso.
   Se guarda en estado/SALUD-APIS.json y queda una entrada SONDA-APIS en la bitacora.
4. Router: el proveedor de los agentes lo dicta el DAG (router.proveedor_agentes). Si es NVIDIA, cada
   grupo usa su credential_ref; si es otro, se usa el modelo recomendado por la sonda.
5. Por grupo (G1..G4 = objetivos 1..4) se toma el siguiente nodo con dependencias en PASS:
   a. Ask Consul: los modelos de la cascada analizan la arquitectura antes de ejecutar; consenso.
   b. Ejecuta el agente de ese objetivo (Obj 1 Claude Code; Obj 2-4 Open Code).
   c. Audita (Obj 1 Codex; Obj 2-4 Open Hands). Ultima linea: VEREDICTO: OK o VEREDICTO: GAP.
   d. Si GAP: repara (Obj 1 Codex; Obj 2-4 Meta Code) y se re-audita.
   e. PASS solo si: ejecutor sin error + VEREDICTO OK + archivo de salida real o cambio real de codigo
      dentro de las rutas del grupo. Evidencia con sha256.
6. Bitacora + memoria de cada agente actualizadas. Segunda pasada = bucle de banderas.
7. La vuelta termina en una rama plan-opus/<grupo>-<run>. Se abre el PR y el Director decide el merge.

## 3. Como repetirlo (ciclo de trabajo)

1. Revisar: bitacora, estado/SALUD-APIS.json, evidencia/ y el PR de la ultima vuelta.
2. Ordenar: escribir ordenes en CENTRO-DE-CONTROL.yaml (estado PENDIENTE).
3. Lanzar: Actions > "Plan Opus - loop de agentes" > grupo (all o G1..G4) y nodos por vuelta.
4. Aprobar: revisar el PR de la vuelta y hacer merge. Sin merge, main no cuenta ese avance.
5. Volver a 1.

## 4. Saber si las APIs funcionan

- Archivo: estado/SALUD-APIS.json (tambien en la rama/PR de cada vuelta).
- Por proveedor: estado OK / SIN_CLAVES / CLAVES_INVALIDAS / SIN_MODELO_OK, lista de claves por NOMBRE
  con su HTTP, modelos qwen y gpt-oss del catalogo, prueba por modelo (HTTP, ms, PASS) y modelo recomendado.
- Nunca contiene una clave, solo el nombre.
- Claves que lee: NVIDIA por el banco (RIU_TEAM_BANK_B64 + RIU_TEAM_BANK_PASSPHRASE);
  Cerebras CEREBRAS_API_KEY*; Groq GROQ_API_KEY*.

## 5. Corregir fallos (mirar bandera_motivo en la bitacora)

1. "B-001: sin clave valida" -> faltan claves o son invalidas. Ver SALUD-APIS.json. Cargar el banco o cambiar
   router.proveedor_agentes a un proveedor en estado OK.
2. "sin consenso: menos de 2 modelos respondieron" -> la cascada tiene modelos caidos. Dejar en
   router.cascada_ask_consul solo modelos que pasaron en SALUD-APIS.json.
3. "dependencia pendiente: X" -> normal; se desbloquea cuando X pase. Si X esta atascado, darle una
   INSTRUCCION o REACTIVAR desde el centro de control.
4. "rc_ejecutor=127" -> el agente no se instalo. Ver evidencia/instalacion-<run>.txt.
5. "rc_ejecutor=124" -> timeout. Partir el nodo en nodos mas pequenos (NUEVO_NODO) o subir PLAN_OPUS_AGENT_TIMEOUT.
6. "veredicto=SIN_VEREDICTO" -> el auditor no escribio la ultima linea. Dar INSTRUCCION al nodo recordando
   el formato "VEREDICTO: OK|GAP".
7. "archivos_salida_ok=False" -> el agente dijo que termino pero no dejo el archivo o no cambio codigo.
   INSTRUCCION con la ruta exacta del archivo a crear o del codigo a tocar.
8. "error del runner: ..." -> fallo del loop, no del agente. Leer el mensaje y corregir el runner.
9. Nodo con 20 intentos -> ya no entra solo (R08). Revisar y REACTIVAR a mano con instrucciones nuevas.

## 6. Como mejorarlo

1. Nodos mas pequenos = mas PASS. Un nodo = una entrega verificable con archivo o test.
2. Cada nodo deberia traer "archivo" o "rutas" claros; sin eso el PASS depende solo de cambios de git.
3. Poner en el DAG un test por nodo (comando pytest) y exigirlo en el acceptance.
4. Anadir token de Hugging Face para Kimi K2 y MiniMax M3 en la cascada.
5. Cuando la sonda muestre un modelo estable, fijarlo en router.modelo_agentes.
6. Leer agent_loop.py de Muse Glimmer y llevar su ToolRegistry al worker (pendiente del plan).

## 7. Salvaguardas (no quitar)

- Los agentes corren con sus protecciones: sin saltarse permisos ni sandbox, sin shell libre.
- Cada agente solo recibe la clave de su grupo; nunca el banco ni otras claves.
- Las claves no quedan en logs (se reemplazan por ***).
- Nada entra a main sin PR aprobado por el Director.
