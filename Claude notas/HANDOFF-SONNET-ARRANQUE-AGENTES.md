# HANDOFF PARA SONNET - ARRANQUE DEL EQUIPO DE AGENTES (2026-09-21)

Lee SOLO este archivo primero. Donde CABLEADO-EQUIPO-AGENTES.md lo contradiga, manda este.

## 1. Estado real (verificado leyendo cada archivo)

1. Existe: 8 handoffs en Claude notas/handoffs/ + CABLEADO-EQUIPO-AGENTES.md. Son documentos de asignacion (nodo, acceptance, contrato JSON vacio).
2. NO existe: ningun agente ha corrido. Todos los contratos estan en WAITING_SIGNAL con steps_done vacio. No hay workflow ni script que lance a los agentes. No existe la bitacora Crazy Wall JSON que exige R06.
3. El cierre anterior decia "listo para arrancar". Era exagerado: estaba la asignacion en papel, no la ejecucion.

## 2. Contradicciones a ignorar

1. CABLEADO dice que Claude Code ejecuta el Objetivo 1. FALSO: HANDOFF-claude_code.md esta SUPERSEDED (agent_sources/claude_code es solo changelog, no CLI instalable).
2. CABLEADO dice que Codex audita el Objetivo 1. HANDOFF-codex.md esta SUPERSEDED (codex-rs exige compilar Rust).
3. CABLEADO dice que Opencode ejecuta Objetivos 2-4. HANDOFF-opencode.md esta SUPERSEDED (monorepo Bun con dependencias nativas).
4. HANDOFF-smolagents.md dice que mcode falta. FALSO: ya montado, commit 336d6a9e35d0f49e09e1a48849937f68f330b367.
5. HANDOFF-smolagents.md nodo N-1.4 (claves NVIDIA como GitHub Secrets): anulado por el Director. Se usa el banco por credential_ref.

## 3. Equipo que SI se puede instalar y correr

1. aider (pip install). Nodos N-1.1 (submodules en CI con sparse-checkout) y N-2.8 (leer los 7 archivos de gobernanza de control-layer: REAL o STUB). Handoff: handoffs/HANDOFF-aider.md
2. smolagents (pip install). Nodo N-2.11 (biblioteca RAG). N-1.3 ya hecho, N-1.4 anulado. Handoff: handoffs/HANDOFF-smolagents.md
3. openhands: AUDITOR, nunca declara PASS. Handoff: handoffs/HANDOFF-openhands.md
4. muse_code: revisa y repara con las recipes de 04_muse_code. Handoff: handoffs/HANDOFF-muse_code.md
5. muse_glimmer: primero leer agent_loop.py, response_parser.py, run_agent.py (aun no leidos). Handoff: handoffs/HANDOFF-muse_glimmer.md
6. Ejecutor de Objetivos 2-4: VACANTE (Opencode quedo fuera). Proponer al Director aider o smolagents. No decidirlo solo.

## 4. Orden de arranque

1. Crear Claude notas/CRAZY-WALL-BITACORA.json (entradas: fecha, agente, nodo, accion, evidencia, estado). Cada paso se anota antes de avanzar.
2. aider: N-1.1 primero (desbloquea N-1.2 y N-3.1). En GitHub Actions con sparse-checkout (R05). Evidencia: run_id + listado real de un submodule.
3. aider: N-2.8.
4. smolagents: N-2.11.
5. Tras cada nodo: actualizar el contrato JSON del handoff (status, steps_done, evidence_hash) + bitacora + memoria.md.

## 5. Modelo

Director: solo NVIDIA. Modelo nvidia/nemotron-3-super-120b-a12b por el banco (credential_ref nvidia/digi-maxbry, nvidia/movistar-briseida, nvidia/wow-maxbry, nvidia/wow-brisa).
BLOQUEO REAL: banco-nvidia-equipo.b64 no esta en ningun repo y la contrasena la da el Director por su canal. Sin eso ningun agente llama a NVIDIA. Pedirlo al Director. Nunca pedir ni escribir claves.

## 6. Donde se reporta

1. Contrato JSON dentro del handoff de cada agente.
2. Claude notas/CRAZY-WALL-BITACORA.json
3. Claude notas/memoria.md (solo anadir, nunca resumir).

## 7. Reglas

R01 nada desde cero, R02 max 500 LOC, R03 nunca borrar, R04 no PASS sin evidencia real, R05 sparse-checkout, R06 anotar antes de avanzar, R08 gap ladder y bandera.
