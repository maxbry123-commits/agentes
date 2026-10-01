SCHEMA REFACTORIZACION v2 corregido 2026-09-17
Correccion: version anterior omitia las 15 reglas con fuente. Anadidas aqui.

LAS 15 REGLAS CON FUENTE REAL:
1. Nunca refactorizar sin tests que ya pasan primero - Kent Beck TDD
2. Metodo no supera 4 niveles de anidacion - Clean Code Robert C Martin
3. Extract Method si un bloque necesita comentario - Fowler Refactoring
4. Refactorizar en pasos que nunca rompan el build - Fowler Refactoring
5. Complejidad ciclomatica maxima 10 por funcion - Thomas McCabe 1976
6. DRY nunca 3a repeticion sin extraer - The Pragmatic Programmer
7. YAGNI no construir lo que no se necesita - Kent Beck XP
8. Boy Scout Rule dejar codigo mas limpio - Robert C Martin
9. Un metodo hace una sola cosa - Clean Code
10. Guard Clauses en vez de condicional anidado - Fowler Refactoring
11. Nombrar por intencion nunca abreviar - Clean Code
12. Characterization tests antes de tocar codigo legado sin tests - Michael Feathers
13. Nunca mezclar refactor con cambio de comportamiento en el mismo commit - Fowler
14. Composicion sobre herencia profunda - Gang of Four
15. Code review nunca aprueba PR sin tests del cambio - practica estandar

CICLO OBLIGATORIO: VERIFY_BEHAVIOR - WRITE_TEST - RUN_BASELINE - ANALYZE - REFACTOR_SMALL_STEPS - RUN_TEST_AGAIN - REPEAT_ON_NEW_CODE

SCHEMA: max_nesting_level 4, max_cyclomatic_complexity 10, forbidden refactor_without_test y mix_refactor_and_behavior_change, on_test_change REVERT_LAST_STEP

Se integra en Wordflow antes de STRUCTURED_ACTION_GATE, en Seals Team antes de declarar PASS.
