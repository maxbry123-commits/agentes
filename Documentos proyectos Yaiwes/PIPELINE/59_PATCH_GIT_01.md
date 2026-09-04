PATCH-GIT-01

PROTOCOLO DE COPIA, MOVIMIENTO Y REUTILIZACIÓN DE CÓDIGO

Este parche complementa el método de trabajo.
Su finalidad es impedir que un agente reescriba código existente cuando la estrategia exige reutilizarlo.

1. REGLA SUPREMA
Cuando exista código funcional o reutilizable, está PROHIBIDO regenerarlo desde cero si la decisión es REUSE | COPY_FIRST | MOVE_FIRST | ADAPT_EXISTING.

No debe: volver a escribirlo; reconstruirlo desde memoria; generar versión equivalente; renombrar innecesario; reformatear; traducir; simplificar sin autorización; crear implementación paralela.

LOCATE → READ → COPY/MOVE → VERIFY → TEST → ADAPT ONLY IF AUTHORIZED

2. MODOS
COPY_FIRST: SOURCE → COPY → VERIFY → TEST → ADAPT LATER IF NEEDED. Predeterminado.
MOVE_FIRST: SOURCE → MOVE → VERIFY → TEST. Cambia ubicación, no contenido.
REUSE: usar tal cual.
ADAPT_EXISTING: IDENTIFY → DOCUMENT GAP → CREATE TASK → MODIFY → TEST.
GENERATE_LAST: solo si no existe, se verificó, ADAPT no resuelve, y hay autorización.

3. JERARQUÍA: REUSE → COPY_FIRST → MOVE_FIRST → ADAPT_EXISTING → GENERATE_LAST

4-8. Mismo repo: cp + cmp/sha256. Directorio: cp -a + diff -qr. Entre repos: clone + cp -a + diff -qr + commit + push + verify remote. git mv solo dentro del mismo repo.

9. COPY: origen permanece. MOVE: origen desaparece. Nunca git mv si hay que conservar. Nunca cp si hay que eliminar origen.

10-11. Durante COPY/MOVE: no rewrite, no refactor, no rename, no cleanup, no optimize, no arch change, no style, no import change. IMPROVEMENT_FOUND → GAP → WAIT.

12. SOURCE_HASH = DESTINATION_HASH o COPY_INTEGRITY FAIL y detener.
13. Si hash no comparable: INTEGRITY_MODE STRUCTURAL. Registrar excepción.
14-15. git status/diff. EXPECTED_CHANGE vs ACTUAL_CHANGE. Si hay cambio interno inesperado: BLOCKED.
16. Un commit = una intención. No mezclar refactor/features.
17. Push + verificar remoto. No declarar DONE solo porque push no falló.
18. Registrar TRANSFER_ID, SOURCE/DEST repo+path, METHOD, CONTENT_POLICY, commits, INTEGRITY, TEST.
19. DISCOVER → COMPARE → SELECT → COPY_FIRST → VERIFY → TEST → PROMOTE. Nunca ASK_LLM_TO_REWRITE.
20. Conflicto: GAP + DECISION_GATE. No reescribir.
21. SOURCE = IMMUTABLE_REFERENCE durante la transferencia.
22. No copiar secretos. credential_ref / environment_secret / secret_manager.
23. Memoria: CLASSIFY antes de copiar.
24. Matriz: idéntico=REUSE; otro lugar=COPY_FIRST; cambiar ubicación=MOVE_FIRST; incompat=ADAPT; no existe=GENERATE_LAST; duda=BLOCK; conflicto=GAP; secreto=NO COPY.
25. Prohibido: rewrite en COPY; regenerate; refactor en transfer; force push; borrar origen en COPY; conservar origen en MOVE; sustituir por LLM.
26. FIND → READ → UNDERSTAND → COMPARE → SELECT → REUSE/COPY/MOVE → VERIFY → TEST → ADAPT IF REQUIRED → GENERATE ONLY IF NECESSARY
27. MODE COPY_FIRST: PRESERVE, REWRITE=DENY, VERIFY_AFTER_COPY=REQUIRED.
28. GENERATE es último recurso.

Texto de origen del operador: adjunto 2026-08-19. Este archivo es el contrato operativo publicado.
