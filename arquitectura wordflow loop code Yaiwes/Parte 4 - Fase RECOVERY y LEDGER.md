PARTE 4 - Fase RECOVERY + LEDGER/MERKLE (formato Glimmer)

## 1. Capacidad
Cuando algo falla, clasifica el fallo, decide si reintentar con backoff o
cortar circuito, y deja un registro encadenado (Merkle) de cada decision
para que nada se pueda alterar despues sin que se note.

## 2. Patron - Microflujo transversal horizontal
FALLO -> CLASIFICAR -> CHECKPOINT -> REINTENTAR o CIRCUIT_BREAK -> LEDGER
(hash encadenado) -> RECONCILIAR -> CONTINUAR o BLOCKED

## 3. LOOP (detallado)
FALLO_DETECTADO
-> RECOVERY/CLASSIFIER.py (clasifica: transitorio/dependencia/auth/stuck/crash)
-> RECOVERY/CHECKPOINT.py (guarda el ultimo estado valido)
-> SI transitorio: RECOVERY/CIRCUIT_BREAKER_SLA.py (backoff, o corta si hay
   demasiados fallos seguidos al mismo proveedor)
-> RECOVERY/ENGINE.py (el motor de recuperacion, decide la ruta)
-> RECOVERY/RECONCILIATION.py (concilia estado esperado vs estado real)
-> LEDGER.py (registra el evento en la cadena)
-> GOVERNANCE/MERKLE_GOVERNANCE_CORE.py (calcula el hash encadenado,
   seq + prev_hash + evento + hash)
-> SI PASS: siguiente nodo / SI FALLA DE NUEVO: BLOCKED_WITH_TRACE

## 4. Aporta
Aporta la diferencia entre "reintentar a ciegas" y "reintentar con criterio":
el CLASSIFIER decide si vale la pena reintentar o si es un problema de fondo
que reintentar no va a resolver. El LEDGER con Merkle aporta que el
historial no se puede alterar sin que la cadena de hashes lo delate.

## 5. Usa
recovery/{checkpoint,circuit_breaker_sla,classifier,engine,reconciliation}.py,
ledger.py (wordflow_loop/wordflow_loop/), governance/merkle_governance_core.py
(runtime/src/governance/, distinto del governance de sheriff/sentinel/etc).

## 6. Reglas
- Nunca reintentar el mismo fallo exacto sin un delta nuevo (regla anti-loop
  ya definida en los documentos VERBATIM guardados).
- El Ledger nunca se reescribe - solo se anexa (append-only).
- Circuit breaker corta el circuito si un proveedor falla repetidamente,
  no sigue insistiendo indefinidamente.

## 7. Fallos
STUCK (mismo GAP + mismo intento + mismo resultado repetido) -> BLOCKED_STUCK,
pasa a otro nodo independiente, no se queda atascado.
CIRCUITO_ABIERTO (demasiados fallos seguidos) -> pausa ese proveedor
especifico, no todo el sistema.

## 8. Test
Pendiente de verificar: no hay evidencia de un test que simule un crash real
(matar el proceso a mitad de ejecucion) y confirme que checkpoint.py permite
retomar exactamente donde quedo. Esto es precisamente el gap que los
documentos VERBATIM (analisis de Muse Code SDK) senalaron como "prioridad
numero uno" - crash recovery real, no solo teorico.

GAP PRINCIPAL DE ESTA FASE: checkpoint.py existe (2KB, confirmado) pero es
un archivo pequeno - falta confirmar si de verdad persiste en disco/SQLite
o si sigue siendo una estructura en memoria del proceso (como sospechaba el
analisis original antes de esta auditoria). Pendiente de lectura linea por
linea del contenido real.
