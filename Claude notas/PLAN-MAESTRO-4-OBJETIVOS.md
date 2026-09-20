# PLAN MAESTRO - 4 OBJETIVOS YAIWES
Creado 2026-09-19 por Claude Opus 5. Version 1.

NOTA DE NOTACION: en este archivo `<E>` representa el prefijo de emoji flecha+carpeta
que usa el Director para marcar destino en la raiz del main.
URL-encoded: `%E2%9E%A1%EF%B8%8F%F0%9F%93%82`
(No se escriben emojis literales: la API de escritura devuelve HTTP 500 con ellos.)

## Contexto

El Director (Hy) tiene 4 objetivos concretos y poco presupuesto de plan restante.
Sesiones anteriores se desviaron a trabajo no pedido. Este plan existe para cerrar
los 4 objetivos sin desviacion, y para que CUALQUIER OTRO CHAT DE CLAUDE pueda
retomarlo sin perder contexto.

Repo unico de trabajo: `maxbry123-commits/agentes` (rama `main`, PUBLICO, 16.4GB).

---

## ESTADO REAL VERIFICADO 2026-09-19 (no de documentos - verificado por API)

Los documentos previos mentian en varios puntos. Esto es lo que hay FISICAMENTE:

| Componente | Ruta real | Estado real |
|---|---|---|
| 12 submodules MiniMax/Kimi | `<E> wordflow loop code Yaiwes/wordflow_loop/agent_sources/` | MONTADOS REALES (gitlinks a repos externos) - incluidos `kimi_code` y `kimi_cli` que las notas daban por GAP |
| `mcode` (@minimax-ai/code) | - | UNICO QUE FALTA de los 13 |
| Orca | `agent_sources/orca/` | DESCARGADO COMPLETO (src/, skills/, native/, mobile/, cloud/, orca.yaml, package.json, pnpm-lock 529KB). Las notas decian "ausente" - era FALSO |
| muse_glimmer | `agent_sources/muse_glimmer/` | Real (`code/`, `_archives/`, DOWNLOAD_EXTRACT_MANIFEST.json) |
| opencode | `agent_sources/opencode/` | Real y completo (packages/, sdks/, specs/, infra/) |
| meta_muse_code_sdk, metacua, cua_mcp, meta_agent_cookbook | `agent_sources/` | Presentes - contenido por verificar en Salida 1 |
| 18 slots de agentes (aider, cline, codex, goose, hermes, openhands, qwen_code, smolagents, agent_zero, claude_code, mimo_code, mirothinker, openclaw, opendev, research_agent_lab) | `agent_sources/` | Presentes como carpetas - contenido por verificar |

CONCLUSION: la mayoria del objetivo 1 YA ESTA DESCARGADO. El trabajo real no es
descargar, es VERIFICAR, PODAR, CABLEAR.

### ALERTA DE SEGURIDAD - ACCION DEL DIRECTOR
Las 5 API keys de NVIDIA estan en texto plano en `Claude notas/instrucciones 1 a 1 director.md`,
en un repo PUBLICO. Estan comprometidas. Regenerarlas en NVIDIA.
El plan las usa como secrets encriptados mientras tanto.

---

## REGLAS DURAS (no negociables, del Director)

1. PROHIBIDO ESCRIBIR CODIGO DESDE CERO. Todo sale del codigo ya descargado:
   podar -> editar quirurgicamente -> refactorizar -> cablear. REUSE > PATCH > ADAPT > GENERATE.
2. Maximo 500 LOC por bloque de codigo. Si no cabe, se divide en mas salidas.
3. NUNCA BORRAR ARCHIVOS. Editar quirurgicamente o crear version nueva.
4. No PASS sin evidencia real: CODE + TEST + EVIDENCE(sha256) + READ-BACK.
   Un LLM diciendo "CORRECTO" no es PASS.
5. SPARSE-CHECKOUT OBLIGATORIO en todo GitHub Action (repo 16.4GB; checkout completo
   tarda 13min o muere - comprobado en runs 35467245568 y 35468506302).
6. Cada paso se anota en `Claude notas/` + Crazy Wall bitacora stated JSON + handoff,
   ANTES de pasar al siguiente.
7. Escritura al repo via API (`create_or_update_file`). Sin emojis literales en el
   contenido (HTTP 500). En codigo Python usar escapes `➡️\U0001f4c2`.
8. Si algo se bloquea: FLAG + se anota + se sigue con lo siguiente. Nunca parar el ciclo.

---

## OBJETIVO 1 - COMPONENTES + SKILLS->SCHEMA + AGENTES FALTANTES

### SALIDA 1 - Inventario forense real de agent_sources/
- Recorrer las ~35 entradas de `agent_sources/` via `GET /git/trees/<sha>` (1 llamada por carpeta).
- Clasificar cada una: SUBMODULE REAL / CODIGO REAL / CARPETA VACIA / STUB.
- Escribir `Claude notas/INVENTARIO-FORENSE-agent_sources.md` con tabla + sha de cada arbol.
- PASS: tabla con las 35 entradas, ninguna marcada "supuesto".
- PARCHE DE RECUPERACION: si se corta, el archivo parcial ya tiene las verificadas;
  retomar desde la ultima fila escrita.

### SALIDA 2 - Cerrar el unico GAP de descarga (mcode) + keys NVIDIA
- Montar `mcode` como gitlink igual que los otros 12: Git Data API
  `POST /git/trees` con `mode=160000`, `type=commit`, sha pineado ->
  `POST /git/commits` -> `PATCH /git/refs/heads/main`.
  Metodo ya probado en commit f13f8f9.
- Subir las 5 keys NVIDIA como secrets `NVIDIA_API_KEY_1..5` del repo `agentes`,
  sellado libsodium via ctypes sobre libsodium.so.23 (metodo ya probado con las 7 GROQ,
  memoria.md seccion 11).
- PASS: `GET agent_sources/mcode` devuelve html_url a repo externo +
  `GET /actions/secrets` lista las 5 NVIDIA.
- PARCHE: si el mount falla, queda FLAG y se sigue - mcode no bloquea nada mas.

### SALIDA 3 - Skills -> DSL DAG Schema
Decision ya tomada por el Director (y Fables): los skills no sirven de adorno;
se convierten en contratos -> DSL DAG schema.
- Fuente: los 3 skills frontend (frontend-design, impeccable, skill-creator)
  + los skills nativos dentro de `agent_sources/orca/skills/` y `orca/skill-guides/`.
- REUTILIZAR el schema ya existente en el repo como plantilla - NO inventar formato nuevo:
  `Core kernel Yaiwes/control-layer/schemas/output_contract.yaml`
  y `Seals team YAIWES/dag_schema.yaml`.
- Producir `skills_schema/<nombre>.dag.yaml` por skill con:
  objective, acceptance[], tools[], evidence[], work_surface.
- PASS: cada schema valida contra el validador del DAG ya existente; 1 test por schema.
- PARCHE: schemas independientes entre si - si uno falla, los demas siguen.

---

## OBJETIVO 2 - CERRAR WORDFLOW LOOP CODE YAIWES

### SALIDA 4 - Resolver la doble raiz
- Carpeta 1 = `<E> wordflow loop code Yaiwes` (kernel Python real, minuscula).
- Carpeta 2 = `Wordflow loop code Yaiwes` (SIN emoji, W mayuscula) = proyecto ajeno
  big-AGI (Electron+Next.js) con los 3 skills frontend dentro de su `skills/`.
- Auditoria X-Ray cruzada: listar ambas raices, tabla de que hay en cada una.
- Mover SOLO los 3 skills a `Skills agente/` usando el motor de copia existente
  (motor_3_copy_batches.py), sin borrar el origen.
- Renombrar Carpeta 2 a `big-AGI-descargado/` SOLO si el Director lo confirma;
  si no, FLAG y seguir.
- PASS: los 3 skills accesibles en `Skills agente/` con contenido real;
  tabla de doble raiz escrita.
- PARCHE: nada se borra; el origen queda intacto, revertir = ignorar la copia.

### SALIDA 5 - Gaps del kernel Wordflow (orden del propio analisis)
Orden fijo, quirurgico sobre archivos existentes:
1. CheckpointManager guarda en memoria (`self._checkpoints={}`) -> persistencia durable.
   PRIORIDAD NUMERO UNO.
2. Deprecar `runtime/src/agent/agent_router.py` (debil, puede fallar sin cerrar) ->
   autoridad unica `AgentFleetAdapter` (fail-closed real). Decision tomada, nunca ejecutada.
3. Recovery Engine generico (ESCALATE_TO_DIRECTOR) -> estados tipados
   (RETRYABLE/DEPENDENCY/AUTH/STUCK/CRASH/IRREVERSIBLE/NO_SOLUTION).
4. Stuck detector (mismo tool+args+error x3 -> BLOCKED_STUCK).
5. 1 path = 1 writer + lease.
- PASS por item: test que falla ANTES del fix y pasa DESPUES.
- PARCHE: cada item es un commit independiente; revertible por separado.

### SALIDA 6 - Frontend visualizable
Peticion literal del Director: "revisa en wordflow la parte de frontend para que
visualice el frontend".
- REUTILIZAR el capability/adapter de navegador que Wordflow YA TIENE -
  NO crear otro navegador-kernel dentro de Seals.
- Cablear el gate CODE PASS + BROWSER PASS + VISUAL PASS
  (ya especificado en `arquitectura wordflow loop code Yaiwes/SCHEMA-frontend-browser-verified.md`).
- Tool loop Meta/Glimmer DENTRO de cada worker (no en el kernel).
- Screenshot recurrente en CADA paso visual relevante, no solo al cierre.
- PASS: un componente frontend real -> build -> navegador -> screenshot ->
  comparacion con acceptance.
- PARCHE: si el navegador no esta disponible en CI, FLAG y se deja el gate cableado
  pero marcado NO_VERIFICADO.

---

## OBJETIVO 3 - TERMINAR SEALS TEAM YAIWES (Salida 8 del cierre)

Ya cerrados (Salidas 1-7, memoria.md seccion 6):
P0-01..P0-15, P0-17, P1-18..P1-23, P1-25, P1-26, P1-29.

### SALIDA 7 - Gaps restantes
- P1-27 crash/resume: integrar con CrazyWallAdapter.checkpoint (depende de Salida 5.1).
- P1-28 sandbox/rollback del instalador: workspace aislado -> acquisition -> inspect ->
  dependency policy -> install -> local test -> promote; FAIL -> descartar workspace.
- P0-16 completar ToolRegistry Glimmer (quedo parcial) - extraer de
  `agent_sources/muse_glimmer/code/`.
- P1-24 MetaCua/CUA-MCP: LEER la implementacion real en `agent_sources/metacua/` y
  `agent_sources/cua_mcp/` ANTES de declarar nada. Detras de Sheriff + sandbox.
  NUNCA autoridad de PASS.
- P2-31 handoff drift: regenerar la seccion de estado desde el inventario runtime
  (dice 229 componentes, real 248).
- P1-30 tests faltantes: crash/recovery y wrong-source-commit.

### SALIDA 8 - Grupo 1 + Grupo 2 + cierre verificado
GRUPO 1 (7 requisitos nativos del agente, verbatim del Director):
1. Saber donde va cada cosa en el kernel (pool/rol del Wordflow) y como determinarlo,
   sin confundirse con un subagente (evitar 2 cerebros).
2. Radiografia nativa de la raiz de YAIWES - donde va cada archivo y por que,
   usando el motor de mover archivos.
3. Como convertir un skill en un schema - criterios + varios modelos de ejemplo.
4. Como usar UNICAMENTE el plugin universal Enchufe Universal Fables para cablear.
5. Como podar, que podar, como decapitar/convertir el wordflow.
6. Partes criticas del kernel: solo Claude las toca; otros preparan, Claude revisa.
7. Como descargar componentes con los motores: reciben URL + nombre y estudian su ubicacion.

GRUPO 2 (pool de agentes / equipo 2):
1. Hacen codigo puro - no integran.
2. Bajo consenso reciben lote de codigo ya creado y deciden donde va en la arquitectura.
3. Revisan lo realizado, refactorizan, auditoria forense X-Ray con verificacion cruzada
   carpeta por carpeta, usando la plantilla EXACTA de los agentes de Meta - nunca generica.

Las 4 simulaciones SIM-01..04 como regression tests obligatorios.

PASS = condicion completa del Director:
DAG_REAL + TASK_CONTRACT_REAL + CLAIM/LEASE + WRITE_SCOPE + STRUCTURED_ACTIONS +
SHERIFF + IDEMPOTENCY + DURABLE_QUEUE + OBJECTIVE+ACCEPTANCE + ORACLE + TESTS +
EVIDENCE_SHA256 + WATCHDOG/REENQUEUE + CRASH_RESUME + BACKEND/FRONTEND ROUTING +
BROWSER LOOP + REGRESSION + COMPLETION_AUDIT = SEALS WORKER VERIFIED.

PARCHE: si un item no cierra -> GAP explicito, nunca cierre fingido.

---

## OBJETIVO 4 - ORQUESTADOR COMAND CENTER

Arquitectura YA APROBADA por el Director (verbatim):
"Opcion 1 como capa de control y Opcion 2 como motor de ejecucion durable -
Omniroute/Orca gobiernan keys, mirrors y visibilidad; Dagu/DBOS aporta la durabilidad
que hoy falta. Lo unico que escribiria de cero son los adapters entre ambos y el
kernel Python. Cero componentes nuevos por descargar."

### SALIDA 9 - Adapters (capa de control)
- Extraer de `agent_sources/orca/` (YA DESCARGADO, codigo real):
  worktree aislado por agente + rotacion/hot-swap de keys con usage tracking +
  CLI scriptable como contrato de automatizacion.
- Extraer de Omniroute: gobierno de keys/mirrors.
- DESTINO: funciones Python dentro de `isolation.py` y `router_modelos.py` YA EXISTENTES
  en seals_core - no app Electron, no carpeta nueva.
- El Comand Center orquesta WORDFLOW (el kernel central), NO Seals
  (Seals dejo de ser el orquestador principal).
- PASS: test real de rotacion de keys + aislamiento de 2 workers sin colision de scope.

### SALIDA 10 - Motor durable + 50 mundos
- Dagu/DBOS como motor de ejecucion durable. VERIFICAR PRIMERO cual esta ya en el repo
  (`Core kernel Yaiwes/` tiene Dagster, Temporal, Prefect, APScheduler, Celery;
  hay TASK-GAPS/N21-DAGU-PASO1-XRAY.md). Si ninguno esta -> FLAG al Director,
  no se descarga sin su OK (regla suya: cero componentes nuevos).
- Router que llama al Router Inteligente Universal (50+ API keys en paralelo)
  y manda senal al Comand Center + todos los mirrors.
- Cada wordflow = su propio mundo (Readme + Handoff + Crazy Wall + System prompt).
  Mas de 50 wordflows previstos.
- Cerebras = SOLO PRUEBAS. En produccion todo va por el Router Inteligente Universal.
- PASS: un ciclo end-to-end: goal -> DAG -> worker -> evidencia -> completion audit,
  sobreviviendo a un crash del worker.

---

## WATCHDOG + BITACORA

- Tarea programada cada 1 hora, nombre "Motor de descarga", sesion nueva por disparo.
- Prompt del watchdog: leer este archivo -> localizar la primera salida no cerrada ->
  ejecutarla -> anotar -> siguiente.
- AVISO: puede requerir que el Director active "aprobacion automatica" en los ajustes
  de la tarea, o cada disparo se quedara esperando permiso.
- Tras CADA salida: actualizar `memoria.md` (anadiendo, nunca resumiendo) +
  Crazy Wall bitacora stated JSON + handoff.

---

## VERIFICACION END-TO-END

1. `GET /actions/secrets` -> 5 NVIDIA presentes.
2. Test real contra NVIDIA (`https://integrate.api.nvidia.com/v1`,
   modelo `minimaxai/minimax-m2.7`) DESDE GITHUB ACTIONS con sparse-checkout.
   El sandbox de Claude tiene la red bloqueada hacia NVIDIA (CONNECT tunnel 403);
   Actions no.
3. SIM-01..04 en verde.
4. Un componente frontend real pasando CODE+BROWSER+VISUAL.
5. Crash de worker -> lease expira -> mision recuperada sin duplicar side effect.
6. Read-back por API de cada archivo escrito (nunca confiar en el resultado del write).

---

## ORDEN DE EJECUCION

S1 -> S2 -> S3 -> S4 -> S5 -> S6 -> S7 -> S8 -> S9 -> S10

Dependencias reales:
- S7 depende de S5.1 (checkpoint durable).
- S9 depende de S1 (saber exactamente que hay dentro de orca).
El resto es secuencial pero independiente - si una se bloquea, FLAG y se salta
a la siguiente.

---

## ESTADO DE LAS SALIDAS (actualizar en cada ciclo)

| Salida | Objetivo | Estado | Evidencia |
|---|---|---|---|
| S1 | 1 | PENDIENTE | - |
| S2 | 1 | PENDIENTE | - |
| S3 | 1 | PENDIENTE | - |
| S4 | 2 | PENDIENTE | - |
| S5 | 2 | PENDIENTE | - |
| S6 | 2 | PENDIENTE | - |
| S7 | 3 | PENDIENTE | - |
| S8 | 3 | PENDIENTE | - |
| S9 | 4 | PENDIENTE | - |
| S10 | 4 | PENDIENTE | - |
