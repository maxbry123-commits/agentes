# Handoff - agente Muse Glimmer (mitad 2 de "Meta Code")

Aclaracion del Director: "Meta Code" son DOS agentes. Este es el segundo.
El primero es Muse Code (handoffs/HANDOFF-muse_code.md).

Fuente real verificada (2026-09-20, Git Data API):
agent_sources/muse_glimmer, sha a3cd2b19a6c79b517b1017c314508ddafaf74762.
code/ es el cookbook real de Muse Glimmer: modelo denso de 30B, contexto 128K,
pensado para correr local en una sola GPU y totalmente offline (principios
local-first y agentic-first). Carpetas: quickstart/, agentic-fundamentals/,
recipes/, inference-server/, platform/, hosted/.

El loop real esta en code/agentic-fundamentals/, sha e0951464b3fa02753b7bb842f33f9acad9a730c1:
1. agent_loop.py (6986B)
2. response_parser.py (7587B)
3. run_agent.py (7412B)
4. README.md (8991B)

## Rol en el loop

Palabras del Director: "cerebro de decisiones: plan, tool, result, self-correct,
next. Su loop ejecuta herramientas, devuelve el resultado al modelo y corrige en la
siguiente iteracion".

Entra junto a Muse Code en los Objetivos 2, 3 y 4. Muse Code programa; Muse Glimmer
decide el siguiente paso y corrige cuando un paso sale mal.

## Donde encaja dentro de YAIWES

El loop de Muse Glimmer va DENTRO de cada worker, nunca en el kernel. Esta es una
decision ya tomada en el plan (Salida 6): "Tool loop Meta/Glimmer DENTRO de cada
worker, no en el kernel". Si se mete en el kernel se crean dos cerebros, que es
justo lo que el Director prohibio.

Tambien alimenta el gap P0-16 (ToolRegistry Glimmer, quedo parcial en Seals Team):
el registro de herramientas se extrae de este codigo, no se reinventa.

## Antes de usarlo: leer el codigo real

Los 3 archivos de arriba estan localizados pero aun NO leidos linea por linea en
este repo. Primer paso de este agente: leerlos y anotar que hace cada uno, antes de
cablear nada. Sin eso, cualquier integracion seria supuesta, y eso viola R04.

## Acceptance de su propio trabajo

1. El loop cableado en un worker real, no en el kernel.
2. Un ciclo completo demostrado: plan, tool, result, correccion, siguiente paso.
3. La correccion se prueba con un fallo provocado de verdad, no simulado en texto.
4. ToolRegistry extraido del codigo real, con la ruta de origen citada.

## Evidence que debe dejar

ruta_origen, sha_leido, worker_donde_se_cableo, traza_del_ciclo, test_de_correccion

## Contrato de salida esperado (JSON)

  mission_id: N-OBJ2-muse_glimmer-AAAA-MM-DD
  status: WAITING_SIGNAL
  summary: ""
  goal_restated: "Leer agent_loop.py, response_parser.py y run_agent.py y cablear el
  loop plan-tool-result-self_correct-next dentro de un worker, nunca en el kernel"
  steps_done: []
  steps_pending: ["leer los 3 archivos", "cablear en worker", "probar correccion"]
  artifacts: []
  contracts_active: ["Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml"]
  sheriff_state: YELLOW
  risk_score: 4
  evidence_hash: null
  errors: []
  warnings: ["el loop va en el worker, no en el kernel: dos cerebros esta prohibido"]
  next_action: "Leer code/agentic-fundamentals/agent_loop.py y anotar que hace"
  signals_pending: 0
  mode: wordflow
  chef_pass: collect
  raw_refs: ["agent_sources/muse_glimmer/code/agentic-fundamentals"]

## Claves

Nunca recibe una clave. Pide al router por credential_ref. El broker resuelve dentro.
Si se corre el modelo local (30B, 1 GPU, offline) no hace falta ninguna clave.

## Reglas heredadas

R01 no codigo desde cero, R02 max 500 LOC, R03 nunca borrar, R04 no PASS sin
evidencia real, R05 sparse-checkout obligatorio, R06 anotar antes de avanzar,
R08 gap ladder y luego bandera + siguiente nodo.
