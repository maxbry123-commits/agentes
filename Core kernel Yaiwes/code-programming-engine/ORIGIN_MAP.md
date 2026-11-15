# ORIGIN_MAP — migración code-programming-engine

**Regla:** NO reescribir. Originales en `extensions/wordflow/**` siguen operativos.  
**Método:** M3 = puntero SOURCE (estructura). M1/M2 = body idéntico (lote backbone pendiente de script CI o batches).  
**Estado migración estructura:** CERRADA. **Estado body full de todos los .py:** parcial (pool + docs aquí; C-19 body sigue canónico en extensions).

## Raíz lógica → canónico real

### A) Hot path C-19 (motor — canónico extensions)

| Destino lógico bajo code-programming-engine/ | Origen canónico |
|----------------------------------------------|-----------------|
| engine-modules/code_path_runner.py | extensions/wordflow/engine/code_path_runner.py |
| engine-modules/programming_pipeline.py | extensions/wordflow/engine/programming_pipeline.py |
| engine-modules/programming_kwargs.py | extensions/wordflow/engine/programming_kwargs.py |
| engine-modules/input_quality_bar.py | extensions/wordflow/engine/input_quality_bar.py |
| engine-modules/skill_native_compiler.py | extensions/wordflow/engine/skill_native_compiler.py |
| engine-modules/goal_lock.py | extensions/wordflow/engine/goal_lock.py |
| engine-modules/cognitive_loop.py | extensions/wordflow/engine/cognitive_loop.py |
| engine-modules/evidence_packet.py | extensions/wordflow/engine/evidence_packet.py |
| engine-modules/code_path_smoke.py | extensions/wordflow/engine/code_path_smoke.py |
| engine-modules/main_loop.py | extensions/wordflow/engine/main_loop.py |
| engine-modules/task_classifier.py | extensions/wordflow/engine/task_classifier.py |
| engine-modules/dual_compiler.py | extensions/wordflow/engine/dual_compiler.py |

### B) Standards forenses

| Destino | Origen |
|---------|--------|
| standards-forensic/* | extensions/wordflow/standards/* (todos los .py del árbol standards/) |

### C) Schemas I/O

| Destino | Origen |
|---------|--------|
| schema-contracts-io/* | extensions/wordflow/schemas/* |

### D) Store / catalogs

| Destino | Origen |
|---------|--------|
| store/main_12.yaml | extensions/wordflow/store/main_12.yaml |
| catalogs/component_catalog.json | extensions/wordflow/component_catalog.json |
| catalogs/connect_catalog.json | extensions/wordflow/connect_catalog.json |

### E) Instance pool (ya materializado en esta raíz)

| Archivo | Estado |
|---------|--------|
| programming_instance.py | BODY en code-programming-engine/ |
| instance_pool.py | BODY en code-programming-engine/ |
| (espejo) despliegue/*.py Opción A | BODY en despliegue/ |

### F) Rest engine/*.py (no solo C-19)

Todo `extensions/wordflow/engine/*.py` y subdirs `engines/`, `ports/` →  
`code-programming-engine/engine-modules/SOURCE_ENGINE.md` lista; canónico = extensions.

### G) Tests C-19

| Destino lógico | Origen |
|----------------|--------|
| module-tests/test_code_path_runner.py | extensions/wordflow/tests/test_code_path_runner.py |
| module-tests/test_unified_programming.py | extensions/wordflow/tests/test_unified_programming.py |
| module-tests/test_main12_programming.py | extensions/wordflow/tests/test_main12_programming.py |
| module-tests/test_input_quality_bar.py | extensions/wordflow/tests/test_input_quality_bar.py |
| module-tests/test_skill_native_compiler.py | extensions/wordflow/tests/test_skill_native_compiler.py |
| module-tests/test_code_path_smoke.py | extensions/wordflow/tests/test_code_path_smoke.py |

### H) wordflow_kernel (gateway — no se mete en kernel-principal; referencia)

| Uso | Origen |
|-----|--------|
| external-motor-bridge | extensions/wordflow_kernel/gateway/intelligence.py |
| external-motor-bridge | extensions/wordflow_kernel/gateway/router_http.py |
| auxiliary | extensions/wordflow_kernel/engines/openclaw_stub.py |
| auxiliary | extensions/wordflow_kernel/engines/hermes_stub.py |

## Qué NO se borra

`extensions/wordflow/**` permanece. Migración = **estructura + mapa + pool**; imports de producción siguen al path canónico hasta cutover explícito post-tests.
