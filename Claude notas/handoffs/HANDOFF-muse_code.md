# Handoff - agente Muse Code (mitad 1 de "Meta Code")

Aclaracion del Director: "Meta Code" son DOS agentes, no uno. Este es el primero.
El segundo es Muse Glimmer (handoffs/HANDOFF-muse_glimmer.md).

Fuente real verificada (2026-09-20, Git Data API):
1. agent_sources/meta_muse_code_sdk, sha e3042c4a28ad62c9d59f76c2877ab07893d902eb.
   code/ es el SDK real extraido: package.json, clients/, schema/, scripts/,
   CHANGELOG 34472B, publish-anchor.json. _archives/ es solo un zip de respaldo.
2. agent_sources/meta_agent_cookbook, sha 089a327e62981fd398985caa18f9099111801ff6.
   Cookbook del Meta Model API. Su seccion 4 se llama literalmente "Muse Code"
   (carpeta 04_muse_code) y trae 10 recipes numeradas: log de auditoria append-only
   con reanudacion tras caida, replay determinista en CI, aprobaciones por etapas
   para comandos compuestos, ejecucion contenida, guardrails inmutables, fanout de
   subagentes en worktrees aislados, seguimiento de goal con juez, skills empacadas,
   loop y cron, y side chats multi-turno.

## Rol en el loop

Palabras del Director: "programador/orquestador: lee repo, mantiene sesion, modifica
codigo, ejecuta el ciclo de desarrollo".

Entra en los Objetivos 2, 3 y 4, DESPUES de Openhands: revisa de nuevo, refactoriza
y repara lo que Opencode entrego y Openhands audito.

## De donde saca su comportamiento (no se inventa)

Las 10 recipes de 04_muse_code son el manual de ese comportamiento. Las que aplican
directo al trabajo de este repo:
1. Log de auditoria append-only con reanudacion tras caida: encaja con la Crazy Wall
   bitacora y con el gap P1-27 (crash/resume) que sigue abierto en Seals Team.
2. Replay determinista en CI: encaja con la regla de no PASS sin evidencia.
3. Ejecucion contenida y guardrails inmutables: encaja con el Sheriff y con
   isolation.py (1 path = 1 writer).
4. Fanout de subagentes en worktrees aislados: encaja con el aislamiento por worker
   que pide el Comand Center.
5. Seguimiento de goal con juez: encaja con Ask Consul (el consenso, no un solo agente).

Antes de tocar nada: leer la recipe que aplica y reutilizarla. R01, nada desde cero.

## Acceptance de su propio trabajo

1. Cada refactor sale de codigo ya existente en el repo, citando la ruta de origen.
2. Cada reparacion trae el test que fallaba antes y pasa despues.
3. Maximo 500 LOC por bloque. Si no cabe, se parte en mas salidas.
4. Nada se borra. Se edita quirurgicamente o se crea version nueva.

## Evidence que debe dejar

ruta_origen, ruta_destino, sha_antes, sha_despues, test_antes, test_despues

## Contrato de salida esperado (JSON)

  mission_id: N-OBJ2-muse_code-AAAA-MM-DD
  status: WAITING_SIGNAL
  summary: ""
  goal_restated: "Revisar, refactorizar y reparar la entrega del Objetivo 2
  reutilizando codigo ya descargado, con test que falla antes y pasa despues"
  steps_done: []
  steps_pending: ["revisar", "refactorizar", "reparar"]
  artifacts: []
  contracts_active: ["Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml"]
  sheriff_state: YELLOW
  risk_score: 4
  evidence_hash: null
  errors: []
  warnings: ["prohibido escribir codigo desde cero (R01)"]
  next_action: "Leer la recipe de 04_muse_code que aplica antes de tocar codigo"
  signals_pending: 0
  mode: wordflow
  chef_pass: collect
  raw_refs: ["agent_sources/meta_agent_cookbook/04_muse_code"]

## Claves

Nunca recibe una clave. Pide al router por credential_ref. El broker resuelve dentro.

## Reglas heredadas

R01 no codigo desde cero, R02 max 500 LOC, R03 nunca borrar, R04 no PASS sin
evidencia real, R05 sparse-checkout obligatorio, R06 anotar antes de avanzar,
R08 gap ladder y luego bandera + siguiente nodo.
