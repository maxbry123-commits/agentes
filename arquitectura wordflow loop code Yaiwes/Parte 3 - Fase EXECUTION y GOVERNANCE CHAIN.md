PARTE 3 - Fase EXECUTION + GOVERNANCE CHAIN (formato Glimmer)

## 1. Capacidad
Ejecuta el nodo ya autorizado, y antes de declarar exito, lo pasa por una
cadena de 7 guardianes (sheriff, sentinel, judge, guardian, supervisor,
validator, verifier) que en teoria nadie puede saltarse.

## 2. Patron - Microflujo transversal horizontal
NODO READY -> CLAIM+LEASE -> LLM_BOUNDARY (si aplica) -> KERNEL EJECUTA
-> SHERIFF -> SENTINEL -> VALIDATOR -> VERIFIER -> JUDGE -> GUARDIAN
-> SUPERVISOR -> TRIBUNAL (oraculo final) -> PASS/GAP

## 3. LOOP (detallado)
CRAZYWALL_CLAIM_GATE (reclama el nodo, fresh_sha + lease)
-> LLM_BOUNDARY (si el nodo necesita LLM: propone, nunca autoriza)
-> KERNEL._execute_and_track (handler + idempotency_check + state=RUNNING)
-> STRUCTURED_ACTION_GATE (valida que la accion tiene forma correcta)
-> UNSAFE_BEHAVIOR_GATE (bloquea acciones peligrosas)
-> SHERIFF.py (regla dura, fail-closed)
-> SENTINEL.py (vigila anomalias)
-> VALIDATOR.py (valida contra schema)
-> VERIFIER.py (verifica resultado)
-> JUDGE.py (decide entre alternativas si hay varias)
-> GUARDIAN.py (ultima compuerta antes de cerrar)
-> SUPERVISOR.py (reintenta si aplica)
-> TRIBUNAL.tribunal (el oraculo real, con budget_gate + constitutional +
   cross_validator + hmac_manager)
-> COMPLETION_GATE (cierre final)
-> PASS: STATE_MACHINE a DONE / GAP: STATE_MACHINE a FAILED o BLOCKED

## 4. Aporta
En teoria, aporta 7 capas de gobernanza independientes antes de que algo se
declare exitoso - nadie puede autoaprobar su propio trabajo.

## 5. Usa
crazywall_claim_gate.py, llm_boundary.py, kernel.py, structured_action_gate.py,
unsafe_behavior_gate.py, governance/{sheriff,sentinel,validator,verifier,judge,
guardian,supervisor}.py, tribunal/{tribunal,budget_gate,constitutional,
cross_validator,hmac_manager}.py, completion_gate.py, state_machine.py.

## 6. Reglas
- LLM propone, el runtime autoriza (llm_boundary.py lo fuerza).
- Ninguna accion pasa sin pasar por TODA la cadena, no solo una parte.
- El Tribunal es el oraculo final, no el propio handler del kernel.

## 7. Fallos - HALLAZGO CRITICO DE ESTA AUDITORIA
Los 7 archivos de gobernanza (governance/*.py dentro de wordflow_loop/wordflow_loop/,
distinto de runtime/src/governance/) son SOSPECHOSAMENTE PEQUENOS:
guardian.py=586 bytes, judge.py=441 bytes, sentinel.py=728 bytes,
sheriff.py=667 bytes, supervisor.py=804 bytes, validator.py=627 bytes,
verifier.py=389 bytes.
Un archivo de 389-800 bytes es apenas unas 15-25 lineas de Python. Esto
sugiere que son STUBS o wrappers minimos, no la implementacion completa de
36 invariantes o similar que se penso que tenian. NO CONFIRMADO SIN LEER EL
CONTENIDO LINEA POR LINEA - marcado como GAP A VERIFICAR, no como hecho.

## 8. Test
Pendiente: no hay evidencia de test que ejercite la cadena completa de 7
guardianes en un solo nodo. runtime/tests/ no fue abierto en detalle.

GAP PRINCIPAL DE ESTA FASE: verificar el contenido real de los 7 archivos
de gobernanza antes de asumir que la cadena esta completa - el tamano en
bytes sugiere lo contrario a lo que documentamos en los VERBATIM guardados.
