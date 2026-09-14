# README CLAUDE INSTRUCCIONES — INPUT BLOCK TEXTUAL DEL DIRECTOR
**Regla de este archivo: texto literal del Director, sin resumir, sin reinterpretar, sin reescribir. Cada bloque lleva fecha y hora de Colombia (America/Bogota).**

**NOTA DE HONESTIDAD DE CLAUDE (no es instrucción del Director, es mi propia anotación):** este archivo se abre en este momento (2026-09-13). No contiene, todavía, las instrucciones textuales de los turnos anteriores de esta conversación (hay más de 20 documentos y decenas de turnos previos sobre Yaiwes, Mythos, el Enchufe Universal, la ficha ADN, etc.). Reconstruir eso palabra por palabra ahora sería una tarea enorme y arriesgo transcribir mal algo — prefiero decírtelo claramente en vez de fingir que este archivo ya está completo. Lo que sí contiene, textual, son las 2 instrucciones más recientes que definen el método de trabajo actual. Iré añadiendo (nunca borrando) instrucciones anteriores por tema, a medida que las vayamos retomando en cada paso.

---

## BLOQUE 1 — 2026-09-13, ~19:30 hora de Colombia — Definición del ecosistema completo y los 9 pasos

Repos para iniciar por ahora como prioridad son
1. Agentes
2. Fromtend
3. Router universal inteligente

Dentro está la mayoría de lo que hay que trabajar en los 9 pasos los demás proyectos requieren terminar los 9 pasos para avanzar

Vas hace 1 por salida vamos hace1 paso una auditoría primero cerramos lo que venimos creando de Yaiwes la fichas los componentes y integración

Luego seguimos con el wordflow loops code

Empezamos del paso 1 al 4 porque la ventana de trabajo de antropy no te va dar para hacer todo por eso dividi en pasos según la prioridad
1 paso 1 salida si se puede solucionar ese paso hasta cerrarlo en una salida genial si no seguimos hasta cerrar el paso para seguir con el siguiente

P2 Yo dividi cada parte del proyecto en micro flujo de trabajo para no colapsar cada parte tiene su propio
Readme arquitectura
CRAZY WALL stated JSON y bitácora y handoff
Componente open soure para integrar
Motores en cada repo de descarga de componentes open soure y extracción y copiar y mover archivo

Gpt y grock que han trabajado pero alucinan solo trabajan en esos micro mundo sin mezclar otros trabajos ni proyecto y es una manera de controlar todo que tú me diseñas en otro chat además con 3 pasos máximo por tarea

Gpt sol resuelve un 60 % y grock el 1% no logra avanzar
Tengo Abstra Pero es muy limitado el plan no da para tanto
Por eso hice este nuevo plan de claude y otros plan para cerrar arquitectura y hacer lo que sol no puede y diseñar los wordflow loops de trabajo para usar varias api que tengo de otros proveedores

La idea es que tú orquestar y resolver lo que sol o el wordflow loops code no pueda

P3 son diferentes repo y diferente procesos Fables los diseño por separado osquestador auditor y memoria es el mismo maneja todo lo de la memoria pero cuando hicimos el proyecto con Fables el me dio el concepto aunque no quedó bien claro donde colocar 2 procesos 1 en el Imput yo le puse input sharck que controla el contexto es como un sistema de busque que prepare el contexto de la llm por ejemplo ayer en otro chat de Claude estaba instalando un sdk de la cuenta la fricción al máximo aunque tú Claude sabes mucho me toca decirte busca investiga en la comunidad de desarrolladores de antropy busca en la comunidad de desarrolladores de programación de code y pasa en todo lo que hago hay que mandar a buscar información porque si no caes en un bucle de pérdida de tiempo y eso es lo que hace que la gente abandone la IA los trabajos no porque la ai no sepa si no que piensa que ya sabe cómo resolverlo entonces Fables me dio esa idea para solucionar el problema y me dio otra para el formato de salida que no lo he creado
Pero como el osquestador auditor memoria mantiene la memoria del agente tiene varios sistme piense que debe ir en ese lugar más adelante vemos si lo conservamos hay o lo movemos por eso está en ese repo del osquestador auditor memoria

P4 el problema es que hay que estar pendiente que sol gpt no inventes no escriba archivos nuevos o cambie los existentes debe escribir solo en el Craxy wall bitácora stated JSON y handoff y en los archivos que ejecuta y en el readme de la arquitectura de cada proyecto los otros repo son parte del proyecto pero más adelante ahora los ignoras
En el repo tarea 1 metí la arquitectura de huggueface donde está todo lo relacionado a las llm locales el cómputo el almacenamiento hay puede revisar aunque tienes acceso total a huggueface en tu plugins para revisar cuando lleguemos a lo de el router inteligente universal
Por ahora lo ignoras

P5 si existe algunas cosas fuere de la raíz como documentos del proyecto y core kernel Yaiwes, Componentes, Bitácora stated JSON Craxy wall
Eso lo puedes organizar me das un promt para que gpt sol organice esos archivos dentro de la raíz de trabajo solo lo que tenga que ver con agente Yaiwes

Yo dejaria en main:
Componente open soure
Claude readme
Agente Yaiwes principal
Core kernel Yaiwes
Skills
Motores
Conecciones router inteligente universal
Wordflow Loops code Yaiwes

[Enlaces a Documentos proyectos Yaiwes, Lote 0 y Lote 1, en el commit bdf07f84ac4011a2ad2298893e643229be4a19a9]

P5 (continuación) hay en los enlaces está varios archivos y está los enchufes de Fables
Hay que actulizar todo el handoff y borrar archivos fantasma y organizar el trabajo

P6 el problema es que no confundir un Craxy wall bitácora stated JSON de una proyecto con otro

Si tú escribes en el Craxy wall bitácora stated JSON y me das un mini promt que le das el enlace del Craxy wall donde está su trabajo y el handoff ye. Dices que nodo tarea shema va a ejecutar y las normas

En algunos trabajos uso el wachdog en automático y se activan cada una hora para yo no estar pendiente reviso al final

[Ejemplo de prompt real que el Director usa con Sol GPT — ver BLOQUE 2 abajo, transcrito completo]

También activo cuando creas mucho trabajo hasta 10 a 20 chat en enjambre de sol para hacer tareas lo hago y voy revisando y coloco un chat como supervisor osquestador que va revisando el Craxy wall por mi y el progreso

Tu mandas la tareas y yo hago el enjambre y pongo un supervisor que tengo en cada proyecto luego que terminen que el osquestador me diga que ya terminaron algunas veces hay algunos Gaps y tareas que no logran avanzar tu revisas y me das el promt para que haiku o Sonnet ejecute le pones la tarea en el Craxy wall bitácora stated JSON y handoff y yo los mando a resolver ese será nuestro método de trabajo
Va escalando
1. Sol gpt
2. Claude Haiku
3. Claude Sonnet
4. Claude Opus
5. Gptn abstra aunque no ha resultó nada nunca
6. Fables 5.1

Ese será nuestro método de trabajo tu orquestas

---

## BLOQUE 2 — Ejemplo real de prompt que el Director usa con Sol GPT (transcrito completo, textual)

```
SOL GPT — UI YAIWES — EJECUTOR DINÁMICO DEL ENJAMBRE.

schema: "tel.workflow/v3"
mode: "FAIL_CLOSED_LOOP"
repo: "maxbry123-commits/frontend"
branch: "main"

Tu nombre será el que indique este chat: "SOL GPT <N>".

FUENTES OBLIGATORIAS — LEER FRESH ANTES DE ACTUAR

CRAZY WALL — cola autoritativa
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES/bit%C3%A1cora%20stated%20JSON%20Craxy%20wall%20plan%20checkpoint/CRAZY-WALL-TASK-NODES-DYNAMIC-V5-2026-09-12.json

HANDOFF dinámico V8
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES/readme%20arquitectura%20UI%20YAIWES/HANDOFF-DYNAMIC-NODES-UI-YAIWES-V8-2026-09-12.md

Arquitectura V7
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES/readme%20arquitectura%20UI%20YAIWES/ARQUITECTURA-WORDFLOW-PYTHON-DSL-DAG-96-4-V7-2026-09-12.md

OBJETIVO

Entrar al Crazy Wall fresco y ejecutar:

"READ FRESH → IDENTIFY FREE/GAP_RESOLVABLE → CLAIM → VERIFY_RESEARCH → EXECUTE_DELTA → TEST_REPORT → VERIFIED_CLOSED|GAP → READ FRESH → NEXT NODE"

REGLAS

1. Un chat = un solo nodo activo.
2. Nunca reclames "CLAIMED|EXECUTING" por otro SOL.
3. Reclama únicamente "FREE|GAP_RESOLVABLE".
4. Antes del claim relee "main" y registra:
   "fresh_main_sha + chat_id + node_id + write_scope + claimed_at".
5. Sigue exactamente los 3 pasos definidos por el nodo:
   "VERIFY_RESEARCH → EXECUTE_DELTA → TEST_REPORT".
6. No inventes tareas ni arquitectura nueva.
7. Prioridad:
   "REUSE_EXISTING > PATCH > ADAPT > GENERATE > NEW_DOWNLOAD".
8. No Git LFS, no force, no motor alternativo.
9. Respeta estrictamente "write_scope".
10. No declares PASS sin evidencia real:
    "path/blob/SHA + test + run/job/log cuando aplique + readback".
11. "SOURCE_PRESENT != IMPLEMENTED != WIRED != RUNTIME_TEST_PASS != VERIFIED_CLOSED".
12. Si el nodo queda bloqueado, registra GAP con evidencia y toma otro nodo independiente FREE.
13. Después de cada commit/test vuelve a leer Crazy Wall fresco porque hay otros SOL trabajando en paralelo.
14. No uses "11/33" como porcentaje global del producto; es sólo estado operativo de nodos.
15. No cierres el proyecto hasta N17 E2E + N31 UI FINAL + Final Judge y dependencias estén realmente PASS.

PRIORIDAD ACTUAL PARA LOS 10 SOL NUEVOS

Cada chat debe releer el Crazy Wall antes de usar esta lista porque puede cambiar.

Priorizar nodos "FREE|GAP_RESOLVABLE", especialmente:
"N03 evidence/auditor → N21 worker adapter → N32 guest installer → N33 mirror transport → GAPs N14/N16/N18/N22/N24/N26/N28 mediante reconciliación de código+CI antes de parchear".

No tocar nodos ya reclamados.

CÓMPUTO VISIBLE OBLIGATORIO

Mostrar durante el trabajo:

"[NODO] [PASO] [ACCIÓN] [RESULTADO] [GAP] [FIX] [TEST/EVIDENCIA] [SIGUIENTE]"

No mostrar razonamiento privado; mostrar únicamente operaciones, pruebas, resultados y evidencia verificable.

LOOP

No parar después de explicar.
Ejecuta el nodo.
Si falla → investiga causa → StrategyDelta distinto → prueba otra vez.
Si PASS → reporta/readback → relee Crazy Wall → reclama siguiente nodo permitido.

INICIA AHORA.
```

**Hallazgo importante de Claude sobre este bloque:** este prompt revela que el repo `frontend` YA TIENE su propia infraestructura de Crazy Wall (V5) y Handoff (V8) dentro de una carpeta `UI YAIWES/`, con nodos numerados (N03, N14, N16, N17, N18, N21, N22, N24, N26, N28, N31, N32, N33) — esto hay que leerlo fresco antes de asumir nada, en el Paso 1 de auditoría de `frontend`.

---

## BLOQUE 3 — 2026-09-13, ~20:10 hora de Colombia — Instrucción de crear esta memoria persistente

Tu memoria la resuleves de esta manera usas siempre y anotas en el repo de agente todo lo que vallas hacer y creas una raíz en main del repo de agentes ya hay un readme de prueba que dice readme Claude.md

Haces 2 cosas
1. Una raíz llamada Claude readme/
2. Creas 3 documentos
Readme Claude.md → tu memoria persistente
Readme Claude instrucciones.md → todas mis instrucciones 1 a 2 imput block sin reinterpretar ni reescribir con fecha y hora de colombia y todo textual
Craxy wall bitácora stated JSON → donde anotas haces tús planes de trabajo de las instrucciones que diste según cada proyecto que sea tu mapa mental
Handoff coneccion con todos los proyectos por separado por cada repo así sabes dónde está todo
Si necesitas un archivo adicional lo haces todos los que necesites

Todo siempre acrulizado nunca puedes en nada de lo que vallas a escribir hacer un resumen es prohibido todo debe ser bien detallado para que pueda funcionar como parche de recuperación detallado

La idea es sacar a sol gpt de la osquestador porque no le rinde no logra planificar bien y pierdo tiempo explicando cada proceso ahora tu te encargas y centralizado todo poseemos retomar en cualquier momento
