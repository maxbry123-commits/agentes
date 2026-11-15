# README ÍNDICE COMPONENTES 17 — YAIWES CORE KERNEL

Repositorio: `maxbry123-commits/agentes` · Rama: `main` · Raíz: `Core kernel Yaiwes/` · Bloque documental: **YAIWES 81–85** · Inventario físico fresh: **245**.

Continuidad fresh: `readme índice componentes 16 .md` cerró en YAIWES 80 (`Instructor`). El inventario fresh de `main` coloca a continuación los componentes físicos `Interlat`, `ipyhop`, `ISEK`, `json-logic-py`, `JSON-Schema`. Todo detalle que las fuentes físicas seleccionadas no demuestran se marca `NO VERIFICADO`.

## YAIWES 81 — Interlat ➡️ Comunicación multiagente enteramente en espacio latente
**URL raíz / ubicación:** `Core kernel Yaiwes/Interlat/` · código: `Core kernel Yaiwes/Interlat/code/` · origen registrado: `XiaoDu-flying/Interlat`.  
**Handoff:** inventario físico `84`; Crazy Wall nodo `222`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Interlat/code/README.md` + `Core kernel Yaiwes/Interlat/DOWNLOAD_EXTRACT_MANIFEST.json`; manifiesto: `source_commit=66a89cb4d4097b2f86cbe48ed9851d6e8578f821`, 147 archivos, extracción y reconstrucción verificadas.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; la fuente demuestra comunicación mediante hidden states y entrenamiento/benchmarks, pero no garantiza determinismo global de inferencia multiagente.  
**¿Es agente?:** No como agente individual; es un framework de comunicación **multi-agent**.  
**Cómo funciona el kernel/core para tomar decisiones:** kernel decisor autónomo propio: **NO VERIFICADO**. El mecanismo demostrado transmite directamente hidden states de última capa entre agentes, con alineación temporal, entrenamiento supervisado, separación condicional y regularización alineada al plan; las decisiones finales siguen dependiendo de los agentes/modelos participantes.  
**Microflujo horizontal:** `agente A procesa estado → hidden states finales → alineación/compresión latente → transmisión latente → agente B consume representación → razonamiento/acción`.  
**Contexto estructural:** `core_training/`, `compression_training/`, `data_collection/`, `eval/`, `scripts/`; comunicación language-free, modelos heterogéneos, sin parameter sharing obligatorio y compresión latente declarada hasta 24×.  
**Nivel seleccionado:** multi-agent latent-communication layer.  
**Qué aporta a un agente:** canal de contexto/razonamiento entre agentes sin decode–re-encode a lenguaje natural, útil para cooperación multiagente eficiente; integración concreta con el kernel YAIWES: **NO VERIFICADO**.

## YAIWES 82 — ipyhop ➡️ Planificador GTN totalmente ordenado con replanning reentrante
**URL raíz / ubicación:** `Core kernel Yaiwes/ipyhop/` · código: `Core kernel Yaiwes/ipyhop/code/` · origen registrado: `https://github.com/YashBansod/IPyHOP.git`.  
**Handoff:** inventario físico `85`; Crazy Wall: sin nodo registrado todavía. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/ipyhop/code/README.md` + `Core kernel Yaiwes/ipyhop/DOWNLOAD_EXTRACT_MANIFEST.json`; manifiesto: `source_commit=bdda21012b2396aed9a91980af8fbb71dbcb7075`, 53 archivos, extracción y reconstrucción verificadas.  
**Determinista:** **Sí para la simulación declarada; % global NO VERIFICADO**. El README afirma explícitamente que `planner.simulate(state)` puede simular determinísticamente el plan; no demuestra un porcentaje de determinismo global de todo el planner.  
**¿Es agente?:** No; es un planificador.  
**Cómo funciona el kernel/core para tomar decisiones:** recibe estado y una lista ordenada de acciones/tareas/metas, aplica métodos de descomposición GTN y construye un `solution tree`; el plan se obtiene recorriendo sus acciones en preorden DFS. Puede reentrar en un nodo fallido, hacer `replan` y bloquear un fallo determinista mediante `blacklist_command`.  
**Microflujo horizontal:** `estado + to-do GTN → métodos/acciones → descomposición jerárquica → solution tree → DFS preorden → plan → fallo → replan desde nodo`.  
**Contexto estructural:** `State`, `Methods`, `Actions`, `IPyHOP`, task/goal/multigoal methods, solution tree, replanning y simulación.  
**Nivel seleccionado:** symbolic planning/replanning layer.  
**Qué aporta a un agente:** planificación jerárquica explícita, trazabilidad de la descomposición y recuperación localizada cuando una acción/tarea/meta falla.

## YAIWES 83 — ISEK ➡️ Red descentralizada Agent-to-Agent para descubrimiento, identidad y cooperación
**URL raíz / ubicación:** `Core kernel Yaiwes/ISEK/` · código: `Core kernel Yaiwes/ISEK/code/` · origen registrado: `isekOS/ISEK`.  
**Handoff:** inventario físico `86`; Crazy Wall nodo `223`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/ISEK/code/README.md` + `Core kernel Yaiwes/ISEK/DOWNLOAD_EXTRACT_MANIFEST.json`; manifiesto: `source_commit=e2959f3c5209c396510b567faabe22982a231ad5`, 82 archivos, extracción y reconstrucción verificadas.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; la fuente no demuestra determinismo global de red, agentes ni razonamiento.  
**¿Es agente?:** No como agente único; es un framework/red para agentes AI.  
**Cómo funciona el kernel/core para tomar decisiones:** kernel central decisor: **NO VERIFICADO**. La arquitectura demostrada evita control central: agentes locales se conectan peer-to-peer, descubren otros agentes, forman comunidades y cooperan; A2A habilita intercambio y ERC-8004 se declara para identidad, reputación y cooperación. La política interna de decisión de cada agente permanece externa.  
**Microflujo horizontal:** `agente local → Node/A2A → conexión P2P/relay → descubrir agente → enviar mensaje/tarea → cooperación/servicio → respuesta`.  
**Contexto estructural:** Node server/client, `A2AProtocolV2`, P2P relay, agent card, red descentralizada, identidad/reputación ERC-8004 y componentes reemplazables del ecosistema.  
**Nivel seleccionado:** decentralized agent-network/coordination layer.  
**Qué aporta a un agente:** conectividad A2A/P2P, descubrimiento y cooperación descentralizada; decisión colectiva específica o integración con YAIWES: **NO VERIFICADO**.

## YAIWES 84 — json-logic-py ➡️ Ejecución de reglas JsonLogic en Python
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados A/json-logic-py/`.  
**Handoff:** inventario físico `87`; Crazy Wall nodo `77`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados A/json-logic-py/README.md`; implementación presente bajo `json_logic/`, junto con `setup.py`, `setup.cfg` y tests.  
**Determinista:** **Sí para una regla y datos fijos según semántica demostrada — % NO VERIFICADO**; la fuente muestra evaluación directa de reglas sin componente probabilístico declarado, pero no publica porcentaje formal.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no posee kernel autónomo; recibe un objeto de regla JsonLogic y opcionalmente datos, interpreta el operador situado en la clave y evalúa valores/reglas anidadas. `var` recupera datos y operadores lógicos/comparativos producen el resultado.  
**Microflujo horizontal:** `regla JSON + datos → parsear operador/operandos → resolver var/subreglas → evaluar lógica → resultado`.  
**Contexto estructural:** reglas serializables, operadores en clave, arrays de operandos, nesting, acceso `var`, lógica compartible entre frontend/backend y almacenable con datos.  
**Nivel seleccionado:** deterministic rules/policy-evaluation layer.  
**Qué aporta a un agente:** una capa de políticas explícitas y portables para gates, condiciones y decisiones basadas en datos sin delegarlas al LLM.

## YAIWES 85 — JSON-Schema ➡️ Vocabulario para validar, anotar y manipular documentos JSON
**URL raíz / ubicación:** `Core kernel Yaiwes/Componentes recuperados B/JSON-Schema/`.  
**Handoff:** inventario físico `88`; Crazy Wall nodo `170`, paso `1`, `PENDING_STEP1`, destino `NO REGISTRADO`. Handoff independiente adicional: **NO VERIFICADO**.  
**Fuente seleccionada exacta:** `Core kernel Yaiwes/Componentes recuperados B/JSON-Schema/README.md`; el repositorio contiene las fuentes work-in-progress de los siguientes IETF Internet Drafts de JSON Schema.  
**Determinista:** **NO VERIFICADO — % NO VERIFICADO**; la especificación define vocabulario/semántica, pero la fuente seleccionada no establece un porcentaje ni una garantía global de determinismo de todas las implementaciones.  
**¿Es agente?:** No.  
**Cómo funciona el kernel/core para tomar decisiones:** no es un kernel decisor. Proporciona vocabulario/esquemas contra los que un validador puede comprobar estructura y restricciones de documentos JSON, además de anotarlos/manipularlos; algoritmo de un validador concreto: **NO VERIFICADO** en esta fuente.  
**Microflujo horizontal:** `JSON + schema → interpretar vocabulario/restricciones → validar/anotar → válido/errores/metadatos`.  
**Contexto estructural:** especificación JSON Schema, drafts IETF, fuentes `specs/`, pipeline de construcción Markdown→HTML y tooling Remark para documentación de la especificación.  
**Nivel seleccionado:** schema/contract-validation layer.  
**Qué aporta a un agente:** contratos estructurales para entradas, salidas, mensajes y configuraciones JSON; reduce ambigüedad antes de ejecutar herramientas o políticas.

---
**COMPONENTES_DOCUMENTADOS = 85**  
**TOTAL_COMPONENTES_INVENTARIO_FRESH = 245**  
**SIGUIENTE_SECUENCIA_DOCUMENTAL = YAIWES 86–90**  
**SIGUIENTES FÍSICOS SEGÚN INVENTARIO = k3s, Kata-Containers, Kestra, Kimi-K2.5, Kubernetes**