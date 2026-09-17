SCHEMA - REFACTORIZACION DETERMINISTA OBLIGATORIA

Ciclo obligatorio (Feathers + Fowler + Beck):
1. VERIFY_BEHAVIOR_FIRST - leer y entender el codigo antes de tocarlo
2. WRITE_CHARACTERIZATION_TEST - test que captura el comportamiento actual
3. RUN_TEST_BASELINE - confirmar que pasa, sin tocar nada
4. ANALYZE_FOR_REFACTOR - ahora si analizar necesidad de refactor
5. REFACTOR_SMALL_STEPS - cambios pequenos, nunca mezclar con cambio de comportamiento
6. RUN_TEST_AGAIN - correr el mismo test tras cada paso
7. REPEAT_ON_NEW_CODE - mismo ciclo al generar codigo o copiar componentes

Schema YAML:
refactor_gate:
  step_order: [VERIFY_BEHAVIOR, WRITE_TEST, RUN_BASELINE, ANALYZE, REFACTOR_STEP, RUN_TEST_AGAIN]
  max_nesting_level: 4
  max_cyclomatic_complexity: 10
  forbidden: [refactor_without_test, mix_refactor_and_behavior_change]
  on_test_change: REVERT_LAST_STEP

Se integra en Wordflow (antes de STRUCTURED_ACTION_GATE), en Seals Team
(antes de declarar PASS), y en cualquier agente futuro.
