PARTE 5 - UEK (Enchufe Universal) + Agent Fleet (formato Glimmer)

## 1. Capacidad
UEK decide como se conecta cualquier plugin/componente nuevo al sistema sin
romper lo que ya existe (version en caliente con slot sombra). Agent Fleet
decide cual worker externo (OpenCode, OpenHands, Codex, etc.) ejecuta una
tarea que necesita capacidad de codigo real, nunca por "inteligencia" del
LLM sino por capability/role exacto.

## 2. Patron - Microflujo transversal horizontal
COMPONENTE NUEVO -> FICHA_CONTRACT -> UNIVERSAL_PLUGIN_BUS -> SHADOW_LOAD
-> RUN_SHADOW_TESTS -> SWAP ATOMICO o RECHAZO
TAREA CON CAPABILITY -> AGENT_FLEET_ADAPTER -> agent_id exacto o role exacto
-> SLOT DETERMINISTA -> FAIL_CLOSED si no hay match

## 3. LOOP (detallado, Enchufe Universal)
COMPONENTE_NUEVO -> UEK/FICHA_CONTRACT_V2.py (valida la ficha del componente
contra el schema v2)
-> UEK/UNIVERSAL_PLUGIN_BUS_V2_INTEGRATED.py (30KB, el archivo mas grande de
   todo el kernel - registra el plugin con un slot propio)
-> UEK/SANDBOX_MANAGER.py (aisla el componente antes de activarlo)
-> UEK/SBOM_ADAPTER_FACTORY.py (genera el inventario de que trae el componente)
-> shadow_load + run_shadow_tests (segun lo que ya documentamos antes en
   esta conversacion: prueba en un slot sombra antes del swap real)
-> SI PASA: swap atomico, el componente queda activo
-> SI NO EXISTE MAS Y OTROS DEPENDEN: DEPRECATED, no se borra
-> UEK/UEK_CLUSTER.py (coordina si hay varios UEK en paralelo)
-> UEK/BOOT_ENGINE.py (arranque del sistema completo)

## 3b. LOOP (detallado, Agent Fleet)
TAREA_CON_CAPABILITY_REQUERIDA
-> AGENT_FLEET_ADAPTER.py (7KB, real, confirmado)
-> busca agent_id exacto en AGENT_FLEET_REGISTRY.json (15.9KB, 18 slots)
-> si no hay agent_id exacto: busca por role exacto
-> si hay match: slot determinista, se despacha
-> si NO hay match: FAIL_CLOSED (nunca elige "el primero de la lista")
-> AGENT_FLEET_HEALTH.json (verifica que el worker esta vivo)
-> AGENT_FLEET_PLUGIN_REGISTRATION.json (registro de plugins del fleet)
-> AGENT_FLEET_READY_FOR_TEST.json (bandera: registrado pero sin prueba
   real de runtime todavia - confirmado, coincide con lo que ya sabiamos)

## 4. Aporta
UEK aporta que agregar un componente nuevo nunca rompe lo que ya funciona
(version en paralelo, swap solo si pasa pruebas). Agent Fleet aporta que
nunca se elige un worker "porque si" - o hay match exacto o se rechaza.

## 5. Usa
uek/{ficha_contract_v2,universal_plugin_bus_v2_integrated,sandbox_manager,
sbom_adapter_factory,uek_cluster,boot_engine}.py,
agent_fleet/{agent_fleet_adapter.py, agent_fleet_registry.json,
agent_fleet_health.json, agent_fleet_plugin_registration.json,
AGENT_FLEET_READY_FOR_TEST.json}.

## 6. Reglas
- Nunca reemplazar un componente en caliente sin probarlo primero en sombra.
- Nunca seleccionar un agente del Fleet "por defecto" si no hay match exacto.
- Un componente deprecado no se borra si otros dependen de el.

## 7. Fallos
NO_MATCH_EN_FLEET -> FAIL_CLOSED, nunca cae al agent_router.py debil (que
sigue existiendo en runtime/src/agent/, PENDIENTE DE DEPRECAR segun decision
ya tomada en los documentos VERBATIM).
SHADOW_TEST_FALLA -> el componente nuevo NUNCA reemplaza al anterior.

## 8. Test
AGENT_FLEET_READY_FOR_TEST.json confirma textualmente que el fleet de 18
agentes esta REGISTRADO pero sin prueba de runtime real todavia - esto no
es un hallazgo mio, es una bandera que el propio sistema ya declara.

GAP PRINCIPAL DE ESTA FASE: existen DOS routers de agentes (agent_router.py
en runtime/src/agent/, debil; agent_fleet_adapter.py en wordflow_loop/
wordflow_loop/agent_fleet/, robusto) coexistiendo. La decision de deprecar
el primero (ya tomada en los documentos VERBATIM guardados) TODAVIA NO SE
HA EJECUTADO - ambos archivos siguen presentes en el repo.
