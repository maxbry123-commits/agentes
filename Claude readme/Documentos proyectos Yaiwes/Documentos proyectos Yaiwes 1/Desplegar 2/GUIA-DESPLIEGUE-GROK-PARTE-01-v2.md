# GUÍA DE DESPLIEGUE PARA GROK — PARTE 1 (v2, corregida)
**v1 citaba una regla "E14" que no existe — UOOS Parte 2 solo llega hasta E12. Esta versión sí sigue el runtime real: RT-00→RT-90, nodos con contrato, paralelismo donde el DAG lo permite.**

---

## Paquete de nodos (equivalente simplificado a B3+B4, para esta entrega)

```yaml
nodos:
  T-001:
    goal: "Desplegar el núcleo determinista (A1) en agentes/control-layer/workflow_core/"
    dependencies: []
    skills_requeridas: [python, pytest, git]
    contrato_input: null
    contrato_output:
      artefactos: [pyproject.toml, "workflow_core/*.py (9 archivos)", test_state_machine.py]
    criterio_exito: >
      test_workflow_transition, test_node_transition,
      test_invalid_transition_is_rejected — los 3 pasan
    risk: bajo
    timeout_seg: 900

  T-002:
    goal: "Desplegar Research Engine (A2) en workflow_core/research.py"
    dependencies: [T-001]
    skills_requeridas: [python, git]
    contrato_input: "workflow_core/errors.py debe existir (de T-001)"
    contrato_output:
      artefactos: ["research.py (o research.py+research_contracts.py si >200 líneas)"]
    criterio_exito: "módulo importable sin error"
    risk: bajo
    timeout_seg: 600

  T-003:
    goal: "Desplegar DAG y Sheriff (A3) en workflow_core/"
    dependencies: [T-001]
    skills_requeridas: [python, pytest, git]
    contrato_input: "workflow_core/contracts.py y errors.py deben existir (de T-001)"
    contrato_output:
      artefactos: [dag.py, sheriff.py, policies.py, dag_patch.py, test_dag.py, test_sheriff.py, test_dag_patch.py]
    criterio_exito: >
      DAG válido pasa validación · DAG con ciclo lanza ContractViolationError ·
      Sheriff aprueba política válida y rechaza rol no permitido
    risk: bajo
    timeout_seg: 900

  T-004:
    goal: "Commit + push + PR de T-001..T-003 en un solo bloque al repo agentes"
    dependencies: [T-001, T-002, T-003]
    skills_requeridas: [git, github]
    contrato_input: "T-001, T-002, T-003 en estado done"
    contrato_output: "PR abierto contra agentes, branch workflow/A1-A3-nucleo-dag-sheriff"
    criterio_exito: "PR creado, CI corriendo, ningún push directo a main"
    risk: medio
    timeout_seg: 600

paralelo_max: 2
regla_paralelo: "T-002 y T-003 pueden ejecutarse en paralelo — ambos dependen solo de T-001, no entre sí. T-002 no importa nada de T-003 ni viceversa."
```

---

## Arranque — sigue el runtime real, no te lo explico distinto

1. **RT-00→RT-04** (boot): verifica que tienes los 4 nodos arriba, revisa preflight (git configurado, Python disponible, permisos de escritura, el binario de Temporal descargado y verificado — sin conectar todavía), carga solo las skills declaradas (python/pytest/git/github), y determina modo INICIO o REANUDACIÓN leyendo tu `state.json`.
2. Reporta el boot y **espera `GO` del Director** — no ejecutes nada antes de eso.
3. **Ciclo por nodo** (RT-10→RT-45), para cada uno de T-001 a T-004: selecciona por dependencias resueltas → verifica idempotencia (¿ya corriste este nodo con este mismo input?) → verifica capability → carga solo la memoria de ese nodo → valida input contra el contrato → ejecuta con las herramientas de la whitelist → pasa por Tribunal → **verifica el goal completo, no solo que Tribunal haya dado OK** → registra artefactos con hash → verifica consistencia → audita → entrega en el formato `NODO T-XXX DONE` y espera el siguiente `GO` si el riesgo lo pide (T-004 es riesgo medio — no lo hagas automático).
4. Cualquier fallo → `RT-80`: clasifica si es auto-recuperable o si necesita al Director antes de seguir. No improvises una solución fuera de eso.

---

## Recordatorio de alcance (sin cambios de la v1)

```
1º GitHub (esto)
2º HF (Parte 3 de esta guía, más adelante)
3º Documentos MD para el Director (al final)
```
No conectes Temporal a ningún workflow todavía — solo confirma que el binario existe. No avances a G4 por tu cuenta — sigue en construcción.

---

*Fin de la Guía de Despliegue — Parte 1, v2. Repositorio: `agentes`. 4 nodos, paralelismo real en T-002/T-003.*
