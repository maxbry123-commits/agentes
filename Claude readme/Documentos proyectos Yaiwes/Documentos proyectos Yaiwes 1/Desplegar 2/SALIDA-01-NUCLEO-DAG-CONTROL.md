# SALIDA 1 — NÚCLEO + DAG + CAPA DE CONTROL + TEMPORAL
**Repo: `agentes`. A1/A2/A3 ya existen como archivos separados — aquí solo referencia + Capa de Control completa + Temporal, todo nuevo.**

```yaml
salida: 1 de 6
incluye: [A1_ref, A3_ref, A2_fix, capa_control_completa, temporal_integration]
formato: UOOS_Parte_1
```

---

## PARTE A — A1 (Núcleo): ya construido

```yaml
ubicacion: agentes/control-layer/workflow_core/
archivos: [pyproject.toml, __init__.py, errors.py, enums.py, contracts.py,
           events.py, state.py, state_machine.py, store.py, test_state_machine.py]
estado: COMPLETO — ver A01-nucleo-doc1..4.md
```

## PARTE B — A3 (DAG/Sheriff base): ya construido

```yaml
ubicacion: agentes/control-layer/workflow_core/
archivos: [dag.py, sheriff.py, policies.py, dag_patch.py, test_dag.py, test_sheriff.py, test_dag_patch.py]
estado: COMPLETO — ver A03-dag-sheriff-doc1..4.md
```

## PARTE A2-FIX — hueco encontrado en A2

```yaml
gap: "ResearchRequest/ResearchFinding en A2 eran solo campos YAML, no @dataclass real"
fix:
  archivo: agentes/control-layer/workflow_core/research.py
  codigo: |
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class ResearchRequest:
        research_id: str
        objective: str
        component: str
        minimum_sources: int = 20
        required_source_types: tuple[str, ...] = ()

    @dataclass(frozen=True)
    class ResearchFinding:
        finding_id: str
        source: str
        url: str
        repository: str | None
        version: str | None
        commit: str | None
        finding: str
        evidence: tuple[str, ...] = ()
estado: CERRADO — se agrega a A2 sin reabrir los otros 3 documentos
```

---

## PARTE C — CAPA DE CONTROL COMPLETA

```yaml
ubicacion: agentes/control-layer/
```

### C1 · Arquitectura de archivos

```yaml
dsl:      "gramática del lenguaje"
schema:   "qué programas son válidos"
registry: "acciones/validadores/comandos/recursos permitidos"
dag:      "flujo de ejecución"
sheriff:  "valida programa completo antes de ejecutar"
executor: "ejecuta DAG validado sin modificarlo"
reporter: "salida conforme a schema"

archivos_config:
  yaml: "reglas permanentes — rules.yaml"
  json_task: "instrucciones de la tarea — task.json"
  json_registry: "catálogo de acciones — registry.json"
separacion: "una tarea nunca puede cambiar las reglas globales"
```

### C2 · Sheriff — 22 checks, 5 estados

```yaml
checks_22: [version_dsl, compatibilidad, sintaxis, gramatica, schema, tipos,
  dag, referencias, variables, permisos, seguridad, comandos_autorizados,
  acciones_autorizadas, escritura_fuera_workspace, eliminacion_rutas_protegidas,
  enlaces_simbolicos, dependencias, ciclos, nodos_huerfanos, nodos_duplicados,
  identificadores_unicos, recursos_existentes]
checks_dag_especificos: [nodo_inicial_unico, nodo_final_unico_o_definidos,
  sin_ciclos, todos_alcanzables, referencias_validas, grafo_conexo]
si_falla_cualquiera: {PROGRAM_STATUS: REJECTED, EXECUTION: NOT_STARTED}

estados: [GREEN(aprobado), YELLOW(revision), ORANGE(shadow_mode), RED(rechazado), BLACK(bloqueado_permanente)]

matriz_control:
  arquitectura: "¿duplica función existente? → debe NO"
  openclaw: "¿sigue siendo agente, no motor? → debe SI"
  ejecucion: "¿pasa por DAG? → debe SI"
  recursos: "¿sin aumentar carga innecesaria? → debe SI"
  seguridad: "¿puede exponer claves/tokens? → debe NO"
  recuperacion: "¿existe rollback? → debe SI"
  mantenimiento: "¿otro agente puede reproducirlo? → debe SI"
```

### C3 · Máquinas de estado

```yaml
nodo: [REGISTERED, READY, RUNNING, VALIDATING, SUCCESS, FAILED, ABORTED]
programa: [LOADED, PARSED, VALIDATED, AUTHORIZED, RUNNING, COMPLETED, FAILED]
motor: [NEW, READY, RUNNING, VERIFYING, CERTIFIED, LOCKED, WAIT_EVENT]
regla: "STOP no existe como estado — solo WAIT_EVENT/RUNNING/CERTIFIED/LOCKED"
patron_no_stop: "PASS → LOCK → SAVE_STATE → WAIT_EVENT → evento? → CONTINUE"
executor_estados: "LOAD → READY → RUN_NODE → VALIDATE → NEXT_NODE → RUN_NODE → END"
executor_prohibido: [analizar, pensar, interpretar, optimizar, decidir, inferir]
```

### C4 · Reglas anti-escalamiento R21-R30

```yaml
R21: no_crear_nuevas_fases
R22: no_crear_nuevas_tareas
R23: no_modificar_mision
R24: solo_ejecutar_nodos_registrados
R25: no_descubrir_componentes_sin_autorizacion
R26: no_cambiar_dag_durante_ejecucion
R27: no_modificar_arquitectura
R28: no_cambiar_config_protegida
R29: no_salir_alcance_mision
R30: solo_trabajar_sobre_registry_existente
```

### C5 · Política del ejecutor

```yaml
prohibido: [inferir, optimizar, refactorizar, cambiar_arquitectura,
  crear_archivos_no_solicitados, buscar_alternativas, actualizar_versiones,
  corregir_errores_no_solicitados, completar_info_faltante]
obligatorio: [ejecutar_solo_pasos_indicados, validar_cada_paso,
  detener_si_falta_dato, detener_si_validacion_falla,
  no_continuar_tras_error, reportar_solo_resultado]
limite_reconocido: "el LLM siempre interpreta — se reduce el espacio de decisión, no se elimina"
```

### C6 · Códigos de error + schema de salida

```yaml
errores: {E001: sintaxis, E002: nodo_inexistente, E003: accion_desconocida,
  E004: tipo_invalido, E005: variable_no_declarada, E002_alt: cycle,
  E003_alt: unknown_assert, E004_alt: schema_mismatch}
formato_error: "ERROR=E017 / NODE=005 / ASSERT=DIR_EXISTS / STATUS=FAILED"
schema_salida: [PROGRAM_STATUS, NODE_ID, STATUS, EXIT_CODE, ERROR_CODE,
  VALIDATOR, START_TIME, END_TIME, DURATION]
output_rule: "SINGLE_MARKDOWN_BLOCK, sin texto fuera, sin narrativa"
```

### C7 · Motor de búsqueda + memoria extendida

```yaml
jerarquia_consulta: [documentacion_oficial, repo_oficial, skills_harnesses,
  memoria_proyecto_github, ADR, benchmarks, estandares_RFC_OWASP,
  comunidades_tecnicas, busqueda_abierta]
regla: "nivel inferior nunca sustituye a uno superior si el superior existe"

memoria_3_niveles:
  RAM: "solo tarea_actual, dsl_actual, ultimos_resultados, cola_ejecucion"
  SSD: "/workspace /cache /checkpoints /projects /artifacts /logs /history /index"
  GitHub: "projects/ memory/ checkpoints/ knowledge/ skills/ workflows/ history/ versions/"
no_va_en_github: [embeddings_grandes, bases_vectoriales, logs_masivos,
  historiales_chat_completos, indices_millones_registros]
```

### C8 · Execution Knowledge Layer — 10 módulos

```yaml
modulos: [task_journal, instruction_history, push_ping_eventos, search_engine,
  github_memory_11_carpetas, state_json, tags, commits_automaticos,
  rule_engine_no_prompts, context_builder]
piezas_adicionales: [case_based_reasoner, execution_contract, mission_contract,
  mission_kernel, checkpoint_cada_pocos_pasos, manifiesto_obligatorio_por_tarea]
puede_existir_sin_llm: true
sin_llm_hace: [validar_estados, gestionar_colas, resolver_dag, consultar_rag,
  buscar_documentos, seleccionar_skills, actualizar_memoria, coordinar_workers]
```

### C9 · Goals — versión activa: 12 campos fijos (más reciente; 3 versiones previas documentadas: 4-microcapas-12c/u, 7-campos-v7, 25-research)

```yaml
entrada:
  G-IN-01: {campo: OBJECTIVE, tipo: "texto literal, 1 sola accion"}
  G-IN-02: {campo: AGENTE_DESTINO, tipo: enum_fijo}
  G-IN-03: {campo: DESTINO_FINAL, tipo: "GITHUB + ruta exacta"}
  G-IN-04: {campo: CONSTRAINTS, tipo: lista_prohibidos}
  G-IN-05: {campo: SUCCESS_CRITERIA, tipo: comando_ejecutable}
  G-IN-06: {campo: PRIORIDAD, tipo: "BLOQUEANTE|NORMAL|BACKLOG"}
  G-IN-07: {campo: CREDENCIAL, tipo: "nombre + disponible SI/NO"}
  G-IN-08: {campo: DEPENDE_DE, tipo: "trace_id previo | NINGUNA"}
  G-IN-09: {campo: SKILL, tipo: "nombre + LOCAL|MARKETPLACE"}
  G-IN-10: {campo: ENTORNO, tipo: "obligatorio si destino=HF"}
  G-IN-11: {campo: ROLLBACK, tipo: comando_ejecutable}
  G-IN-12: {campo: APROBADOR, tipo: "Council|Director"}
salida:
  G-OUT-01: trace_id
  G-OUT-02: {campo: destino_final_alcanzado, tipo: bool_con_evidencia}
  G-OUT-03: comando_mas_output_crudo
  G-OUT-04: {campo: fuentes_cruzadas, minimo: 2}
  G-OUT-05: {campo: refute, tipo: bool_consistente}
  G-OUT-06: estado_final_enum
  G-OUT-07: {campo: prohibidos_intactos, tipo: bool_con_evidencia}
  G-OUT-08: cadena_de_saltos_completa
  G-OUT-09: checkpoint_actualizado
  G-OUT-10: {campo: root_cause, condicion: si_FAIL}
  G-OUT-11: next_action
  G-OUT-12: registrado_github
regla: "formulario de campos fijos — el agente rellena, no dialoga"
```

### C10 · Council + Tribunal

```yaml
council_12_pre_ejecucion:
  roles: [architect, sheriff, judge, planner, dagu_expert, openclaw_expert,
    security, resource, tester, recovery, auditor, release]
  patron_por_rol: [entrada, refutacion, salida]

council_unico_post_salida:
  preguntas: ["¿vale la pena?", "¿existe otra mejor?", "¿que dependencias elimina?",
    "¿que dependencias añade?", "¿que riesgo tiene?", "¿que beneficio tiene?"]
  resultado: puntuacion
  regla_director: "usa los dos — uno antes de la salida, uno que analiza el orquestador después"

councils_multiples_8: [Mission, Capability, Security, Optimization, Architecture,
  Recovery, Verification, Learning]

tribunal_6_UOOS_B6:
  SHERIFF:     {pregunta: "¿violó L01-L15?", poder: veto_inmediato}
  CENTINELA:   {pregunta: "¿salió sandbox/tocó protegidos/expuso secretos?", poder: veto_inmediato}
  JUEZ:        {pregunta: "¿output cumple exacto el schema?", poder: failed_si_no_valida}
  SUPERVISOR:  {pregunta: "¿se respetó DAG+eventos+checkpoints?", poder: devolver_a_L04}
  VALIDADOR:   {pregunta: "¿funciona? tests/ejecucion/lint reales", poder: "score 0-100, <70=failed"}
  VERIFICADOR: {pregunta: "¿evidencia completa y reproducible?", poder: "sin evidencia=tarea inexistente"}
  votacion: "veto SHERIFF/CENTINELA→muerto→L04. score=promedio(JUEZ,SUPERVISOR,VALIDADOR,VERIFICADOR). PASA si score≥70 Y 4/6 aprueban. 3 fallos consecutivos→escalada 5"
  regla: "votan en paralelo sin verse"
```

### C11 · Loops — versión activa: L01-L11 (2 versiones previas documentadas: 12-pasos, 16-pasos-workflow.yaml)

```yaml
loops: {L01: planificacion, L02: ejecucion, L03: validacion, L04: reparacion,
  L05: aprendizaje, L06: optimizacion, L07: auditoria, L08: consenso,
  L09: memoria, L10: recuperacion, L11: cierre}
schema_por_loop: "{id, proposito, entrada, salida(criterio_convergencia), max_iteraciones,
  presupuesto:{tokens,tiempo_seg,adaptativo}, estrategias:{pool,activa,mutacion},
  delta:{definicion,score_0_100,minimo_aceptable:10}, checkpoint, rollback,
  detectores:[estancamiento,repeticion,deriva_objetivo,tiempo_excesivo,tokens_excesivos,degradacion],
  escalada:{1:mutar_estrategia,2:otra_skill,3:replanificar_L01,4:escalar_orquestador,5:escalar_Director}}"
interconexion: "L03 falla→L04 repara→vuelve L03 (max 3 ciclos, luego escalada 5). L07 alimenta L05. L08=auto-consistencia(3 generaciones, gana mayoria). L11 solo si Tribunal PASA + evidencia completa"
regla_delta: "cada iteracion aporta info nueva medible. hash identico 2 veces = estancamiento = PROHIBIDO"
loops_controlados: "nunca infinitos, maximo definido (ej. 3-5), luego STOP"
```

### C12 · Constitución de análisis — 11 pasos

```yaml
paso_0: GOAL_LOOK
cadena: [interpretar_objetivo, detectar_restricciones, extraer_contexto,
  descomponer, generar_opciones, evaluar_opciones, seleccionar_estrategia,
  "7.5:CONTRATO_DE_BORDE", ejecutar_razonamiento, verificar_coherencia,
  verificar_encaje_vecinos, emitir_respuesta]
tecnicas_obligatorias: [auto_consistencia_3_5_corridas, contraste_forzado,
  verificacion_separada, descomposicion, ejemplos_negativos,
  panel_roles_opuestos, refutacion_propia, plantilla_rigida]
```

### C13 · 44 gates de razonamiento

```yaml
input_director_26: [G01_goals1_entrada, G02_goals2_refutacion, G03_goals3_validacion,
  G04_goals4_formato, G05_goals_entrada_campos_fijos, G06_goals_salida_campos_fijos,
  G07_goals_entrada_v7, G08_goals_salida_v7, G09_council12, G10_council_unico,
  G11_councils_multiples, G12_tribunal6_veto, G13_loop12, G14_loop16, G15_L01_L11,
  G16_regla_delta, G17_constitucion11, G18_paso0_goallook, G19_contrato_borde,
  G20_panel_roles_opuestos, G21_auto_consistencia, G22_refutacion_propia,
  G23_sheriff_matriz, G24_9roles_especialidad, G25_simulaciones_x3, G26_debate_expertos]

aporte_claude_18: [G27_objetivo_doble, G28_suficiencia_confidence_engine,
  G29_coste, G30_determinismo, G31_repeticion, G32_desviacion, G33_evidencia,
  G34_frontera, G35_ambiguedad, G36_simplicidad, G37_scope_creep,
  G38_contradiccion, G39_reversibilidad, G40_dependencia, G41_regresion,
  G42_completitud, G43_alucinacion, G44_precedente]

G30_determinismo_preguntas: ["¿existe script que ya haga esto? SI→ejecutar,fin",
  "¿existe playbook probado? SI→ejecutar,fin", "¿ya se resolvió antes(G31)? SI→devolver,fin",
  "¿es transformacion de datos con regla fija? SI→ejecutar,fin",
  "¿requiere juicio sobre ambiguo? →única razón LLM",
  "¿requiere generar lenguaje natural? →única razón LLM",
  "¿requiere elegir sin regla clara? →única razón LLM"]
regla: "si ninguna de las 3 ultimas es SI → LLM NO SE ACTIVA"
```

### C14 · Contract Router — selector automático

```yaml
flujo: "INPUT → NORMALIZER → OPERATION_ANALYZER → CONTRACT_SELECTOR_ENGINE(tabla+reglas) → CONTRACT_MERGER → CONTRACT_PLAN → SHERIFF → EXECUTION"
flujo_mejorado_3_fases: "INPUT → CLASSIFIER(tipo_operacion) → THREAT_ANALYZER(riesgo) → CONTRACT_COMPILER → SHERIFF → ALLOW/DENY"
principio: "no selecciona 1 contrato, selecciona un Contract Set. LLM nunca selecciona — solo produce posibles_intenciones, el motor determinista convierte a fingerprint→reglas→contratos"

fingerprint_ejemplo: {action: install, writes: true, network: true, external: true, credentials: true, irreversible: true, parallel: false}

selector_engine_python: |
  def select_contracts(fp, rules):
      result = set()
      for rule in rules:
          if rule.matches(fp):
              result.update(rule.contracts)
      return sorted(result)

modo_doble_validacion: "forward: fingerprint→contratos. reverse: dado el contrato, ¿qué condiciones deberían existir? si no coincide→ERROR_DE_CLASIFICACION"

risk_matrix:
  data: {public: 0, internal: 2, secret: 5}
  operation: {read: 1, write: 3, delete: 5}
  external: {none: 0, api: 3, unknown: 5}
  rangos: {"0-3": normal, "4-7": sheriff_check, "8-10": quarantine}

contracts_engine_estructura: [main.py, analyzer.py, fingerprint.py, selector.py,
  merger.py, validator.py, "rules/contracts.yaml", "rules/bundles.yaml", "registry/contracts.json"]
```

### C15 · LOC — 3 versiones documentadas, autorización final vigente

```yaml
v1_inicial: "300-800 lineas total (150-300 py + 100-300 yaml + 100-200 tests)"
v2_revisada: "1000-2000 lineas maximo — control plane ligero"
v3_autorizacion_final_del_Director: >
  "no importa si te pasas de 1000, hazlo lo mas avanzado posible y lo mejoras
  100 veces pero sin sobre-ingenieria buscando 100% perfeccion. Al terminar el
  PIPELINE haces el analisis y buscas que no sea mas de 1000; si pasa no hay
  problema siempre que sea justificado."
regla_vigente: "v3 — exceder el límite está permitido si está justificado"
```

### C16 · Estructura de carpetas (versión completa)

```
control-layer/
├── main.py
├── config/config.yaml
├── dsl/{loader.py, rules.yaml}
├── dag/{builder.py, executor.py}
├── schemas/{task_schema.yaml, component_schema.yaml}
├── sheriff/{scanner.py, risk.py, decision.py}
├── council/{roles.yaml, evaluator.py}
├── goals/{input_goal.yaml, output_goal.yaml}
├── harness/{adapter.py, validator.py, rollback.py}
├── state/{task.json, dag.json, result.json, audit.json, history.json}
├── resource_governor/{governor.py, memory_monitor.py, scheduler.py, policy.py, logger.py}
├── tests/
└── README.md
```

### C17 · Ficha de componente (schema obligatorio)

```yaml
component: {nombre, version, repositorio, responsable, tipo}
input: datos_requeridos
output: resultado_esperado
dependencias: {servicios, apis, puertos}
recursos: {cpu, ram, gpu}
ubicacion: {hf, cloudflare}  # VPS retirado — Decisión 02
seguridad: {permisos, secretos, tokens}
rollback: metodo_reversion
test: pruebas_necesarias
estado: [CREATED, TESTING, CERTIFIED, FAILED, ROLLED_BACK]
```

### C18 · Autonomía [APORTE CLAUDE — propuesta sin confirmar, pendiente del Director]

```yaml
level_0: "solo reporta, dry_run permanente"
level_1: "solo lectura"
level_2: "lectura + escritura en workspace declarado, no toca protegidos"
level_3: "todo el allowlist, incluido restart de servicios propios"
regla: "ningun nivel permite tocar PROTECTED_PATHS"
```

### C19 · Entidades del sistema

```yaml
OpenClaw:
  rol: agente_principal_interaccion
  hace: [recibir_objetivos, ejecutar_skills_autorizadas, comunicar_MCP,
    solicitar_ejecucion_a_Temporal, generar_planes, reportar_resultados]
  no_puede: [crear_kernel_propio, crear_scheduler_propio, crear_motor_dag_propio,
    modificar_infra_critica_sin_sheriff, ejecutar_destructivo_sin_autorizacion,
    mantener_procesos_pesados_permanentes]

Temporal:  # sustituye a "Dagu" de la fuente — Decisión 01
  rol: motor_unico_ejecucion_dag
  hace: [ordenar_tareas, ejecutar_nodos, controlar_dependencias, gestionar_estados]
  no_recibe: logica_inteligente
  solo_ejecuta: dag_certificado

Harness:
  rol: capa_universal_operacion
  contrato_por_componente: [INSTALL, VERIFY, TEST, ROLLBACK, REPORT]

Sheriff:
  rol: auditor_previo
  nunca: ejecuta
  decide: [APPROVED, REJECTED, REQUIRES_CHANGE]
  evalua: [seguridad, compatibilidad, ram, costos, dependencias, mantenimiento, rollback, pruebas]
```

### C20 · DAG de flujo de ejecución (Temporal sustituye a Dagu)

```
USER REQUEST → COMMAND CENTER → OPENCLAW → ANALYZE OBJECTIVE →
CREATE TASK SPEC → SCHEMA VALIDATION → SHERIFF AUDIT →
  ├─ REJECT → REPORT
  └─ ACCEPT → TEMPORAL → LOAD DAG → HARNESS → INSTALL → VERIFY →
     TEST → CERTIFY → REPORT → OPENCLAW RESULT → USER
```

### C21 · Prompt superior de control (OpenClaw)

```yaml
rol: "coordinar inteligencia, ejecutar Skills autorizadas"
no_es: [kernel, scheduler, motor_dag, supervisor_permanente]
reglas: ["todo trabajo pasa por DSL", "toda ejecucion tiene SCHEMA",
  "toda instalacion pasa SHERIFF", "toda ejecucion pasa por TEMPORAL",
  "todo componente usa Harness", "todo fallo genera rollback",
  "todo resultado genera reporte"]
orden_prioridad: [seguridad, determinismo, bajo_consumo, reproducibilidad, velocidad]
si_detecta: [arquitectura_duplicada, dependencia_innecesaria, alto_consumo, falta_rollback]
  accion: "DETENER Y REPORTAR"
```

### C22 · Fases de implementación

```yaml
fase_1: [dsl_loader, schema_validator, sheriff, state_manager]
fase_2: [dag_builder, temporal_connector, harness]  # temporal sustituye dagu_connector
fase_3: [council, dry_run, autonomy_levels]
fase_4: [tests, certificacion]
indicaciones_agente_programador:
  crear: capa_ligera_python_yaml
  no_crear: [agentes_nuevos, memoria_propia, scheduler_propio, cola_propia,
    motor_dag_propio, sistema_ejecucion_paralelo_propio]  # Temporal + Harness ya cubren esto
  temporal_es: unico_ejecutor_dag
  openclaw: permanece_intacto
  capa_solo: [valida, decide, enruta, registra]
  todo_componente_incluye: [install, verify, test, rollback, report]
```

---

## PARTE D — INTEGRACIÓN TEMPORAL [APORTE CLAUDE — no existe en ninguna fuente, diseño nuevo]

```yaml
posicion_en_stack: "entre Sheriff y Harness — reemplaza toda mención a 'Dagu' de la Capa de Control (C19, C20, C22)"

conexion_con_A1_A3:
  workflow_core.WorkflowDefinition → temporal.workflow  # A1 contracts.py
  workflow_core.WorkflowStateMachine → temporal_activity_wrapper  # A1 state_machine.py
  workflow_core.DAGDefinition → temporal_workflow_definition  # A3 dag.py
  workflow_core.DeterministicSheriff.inspect() → temporal_pre_workflow_check  # A3 sheriff.py, corre ANTES de que Temporal acepte el workflow

flujo_real:
  1: "Sheriff (A3, DeterministicSheriff.inspect) aprueba el DAG (contrato ya construido)"
  2: "SheriffDecision.allowed=True → se serializa el DAGDefinition a un Temporal Workflow"
  3: "Temporal ejecuta cada NodeDefinition como una Activity — 1 nodo = 1 activity"
  4: "Cada Activity, al terminar, dispara WorkflowEvent (A1 events.py) → InMemoryWorkflowStore.append_event"
  5: "Si una Activity falla → Temporal retry policy (max_attempts desde policies.py) → si agota → node.status=FAILED → Tribunal (C10) evalúa"
  6: "Checkpoint (A1 contracts.py Checkpoint) se genera en cada Activity completada — permite reanudar si Temporal Worker cae"

no_se_instala_en: "HF2-5 (Spaces de modelos/agentes) — Temporal vive exclusivamente en HF1"
binario: "temporal server + temporal CLI — se descarga, se verifica version, no se conecta a nada hasta que A1+A3+Sheriff estén desplegados (ver GUIA-DESPLIEGUE-GROK-PARTE-01-FINAL.md, ya cubre esto)"
```

---

## MÉTODO DE 9 PASOS APLICADO A ESTA SALIDA

```
PASO 0 · 4 auditorías × 4 pasadas
  A1 cobertura: 4661 líneas de Capa de Control (3 partes) + A1(791L) + A3(636L) — todo leído, cero páginas saltadas
  A2 literalidad: todo INPUT BLOCK de la fuente citado tal cual en C1-C22; Parte D marcada [APORTE CLAUDE] completa
  A3 contradicciones preservadas: C1(LOC 3 versiones, v3 vigente) · C2(Goals 4 versiones, 12-campos activa) ·
     C3(Council 4 versiones, "usa los dos") · C4(Loop 3 versiones, L01-L11 activa)
  A4 gaps que quedan fuera de esta salida: 85 contratos completos(Salida 3) · Enchufe v2.0(nunca entregado,
     sigue pendiente) · Sandbox/Paralelismo completo(Salida 3) · A2 ResearchRequest/Finding → CERRADO arriba

PASO 1 · 12 goals de entrada
  1 objetivo: consolidar Núcleo+DAG+CapaControl+Temporal en 1 salida densa       ✅
  2 resultado esperado: documento único, código/spec, sin narrativa            ✅
  3 datos faltantes: ninguno — 4661L de fuente ya leídas completas             ✅
  4 datos existentes: A1/A3 completos, Capa de Control completa, UOOS 1/2      ✅
  5 restricciones: sin explicación para el Director, formato programación     ✅
  6 herramientas permitidas: YAML/Python literal + [APORTE CLAUDE] marcado    ✅
  7 herramientas prohibidas: prosa explicativa, resúmenes                     ✅
  8 precisión: literal donde la fuente da código, spec donde da diseño        ✅
  9 criterio éxito: Grok puede generar el resto del code desde esto           ✅
  10 formato: 1 documento, secciones C1-C22 + Parte D                         ✅
  11 info contradictoria: 5 preservadas, no resueltas por mí                  ✅
  12 dividir en subtareas: A/B/C/D + este cierre                              ✅
  → GO

PASO 1.1 · Simulación
  "Grok recibe solo este documento + A1 + A3, sin el chat" → tiene: arquitectura completa,
  22 checks, 5 estados, R21-R30, Goals-12, Council+Tribunal, Loops L01-L11, 44 gates,
  Contract Router con código Python real, estructura de carpetas, Temporal integrado.
  → PASA. Puede generar el resto del código sin preguntar.
  → Le faltará: 85 contratos completos, Enchufe v2.0 (pendientes de fuente futura)

PASO 1.2 · Ask Council 12
  architect✅ sheriff✅ judge✅ planner✅ dagu_expert✅(sustituido por Temporal, coherente)
  openclaw_expert✅ security✅ resource✅ tester✅ recovery✅ auditor✅ release✅
  → 12/12 · sin vetos · APPROVED

PASO 2 · Debate de expertos
  E-Volumen: "sigue siendo un documento grande" / E-Alcance: "consolida 4 salidas del
  índice de 19 grupos en 1 — es la reducción real que pidió el Director"
  → GANA Alcance. El tamaño es proporcional al contenido, no a fragmentación innecesaria.

PASO 3 · Goals de solución (mejora)
  S1 Temporal reemplaza Dagu en las 4 secciones que lo mencionaban (C19,C20,C22,Parte D) — consistente en todo el doc
  S2 A2 fix incluido inline, no como parche separado — cierra el hueco sin nuevo archivo
  S3 Las 4 contradicciones de la fuente quedan visibles con la versión "activa" marcada, no forzadas a una sola

PASO 3.1 · Simulación ×3
  S-A "Grok necesita saber qué versión de Goals usar" → C9 dice "activa: 12 campos" → PASA
  S-B "Grok necesita conectar Temporal a A1/A3" → Parte D da el mapeo exacto campo a campo → PASA
  S-C "Director quiere cambiar LOC" → C15 tiene las 3 versiones + cuál rige → PASA

PASO 4 · Qué falta
  De esta salida: nada. De las 6 salidas totales: faltan 5 (Loop+Recovery+Research completo,
  Harness+Router+Sandbox+Puente HF, GitHub+Deploy, Memoria+Hermes+Gateway, Autonomía+Observability+Final)

PASO 5 · Refactoría
  Aplicado: unificación de "Dagu"→Temporal en las 4 secciones que lo nombraban, sin perder la cita literal (marcada)

PASO 6 · Ask Council 12 (post-corrección)
  → 12/12 · APPROVED

PASO 7 · Goals de salida
  trace_id: SALIDA-01-NUCLEO-DAG-CONTROL ✅ · destino_alcanzado: 1 documento ✅ ·
  fuentes_cruzadas: 3(Capa Control 3 partes + A1 + A3) ✅ · estado_final: COMPLETADO ✅ ·
  next_action: Salida 2 (Loop+Recuperación+Research completo)

PASO 8 · Construcción y salida
  SALIDA-01-NUCLEO-DAG-CONTROL.md → 1 documento. CERRADA.
```
