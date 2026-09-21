# Handoff - agente openhands (agent_sources/openhands, contenido real verificado)

Fuente de verdad: Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml y
Claude notas/CABLEADO-EQUIPO-AGENTES.md

Verificacion real (2026-09-20, Git Data API, sha de arbol 5598f214c8cdfdd7d62e0fae4f4bd9764694a935):
app completa Electron + web. package-lock.json 789445B, src/, electron/, docker/,
helm/, specs/, tests/, playwright configs, AGENTS.md 119896B. No es carpeta vacia.

## Rol en el loop

AUDITOR Y REVISOR de los Objetivos 2, 3 y 4.
No es el ejecutor: ejecuta Opencode. Openhands entra despues, revisa lo que Opencode
produjo, y pasa el resultado a Meta Code (Muse Code + Muse Glimmer) para refactor y
reparacion.

Openhands NO declara PASS por si mismo. Su salida es un informe con evidencia; el
PASS lo decide el consenso (Ask Consul) con evidencia real.

## Que revisa en cada objetivo

1. Que el codigo que entrego Opencode existe de verdad (ruta + sha), no descrito.
2. Que el test que se dice que paso, corrio de verdad (run id o salida real).
3. Que no se escribio codigo desde cero donde habia codigo ya descargado (R01).
4. Que ningun bloque supera 500 LOC (R02).
5. Que no se borro ningun archivo (R03).
6. Que el objetivo cumple su acceptance, literal, no parecido.

## Acceptance de su propio trabajo

1. Un informe por objetivo, con una linea por hallazgo y su evidencia.
2. Cada hallazgo marcado OK o GAP. Nada de "parece correcto".
3. Si encuentra un GAP: bandera, se anota, y el ciclo sigue con la siguiente tarea.

## Evidence que debe dejar

ruta_revisada, sha_leido, test_run_id, veredicto, gaps

## Contrato de salida esperado (JSON, mismo formato que los demas handoffs)

  mission_id: N-OBJ2-openhands-AAAA-MM-DD
  status: WAITING_SIGNAL
  summary: ""
  goal_restated: "Auditar lo entregado por Opencode en el Objetivo 2 y devolver
  informe con evidencia real por hallazgo, sin declarar PASS"
  steps_done: []
  steps_pending: ["auditar objetivo 2"]
  artifacts: []
  contracts_active: ["Claude notas/PLAN-DSL-DAG-00-CONTRATO.yaml"]
  sheriff_state: YELLOW
  risk_score: 3
  evidence_hash: null
  errors: []
  warnings: ["Openhands nunca es autoridad de PASS"]
  next_action: "Leer entrega de Opencode y verificar ruta+sha+test real"
  signals_pending: 0
  mode: wordflow
  chef_pass: collect
  raw_refs: ["Claude notas/CABLEADO-EQUIPO-AGENTES.md"]

## Claves

Openhands nunca recibe una clave. Si necesita un modelo, lo pide al router con el
credential_ref (nvidia/digi-maxbry, nvidia/movistar-briseida, nvidia/wow-maxbry,
nvidia/wow-brisa). El broker resuelve por dentro.

## Reglas heredadas

R01 no codigo desde cero, R02 max 500 LOC, R03 nunca borrar, R04 no PASS sin
evidencia real, R05 sparse-checkout obligatorio en Actions, R06 anotar antes de
avanzar, R08 gap ladder 1..20 y luego bandera + siguiente nodo.
