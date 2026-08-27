# GUÍA DE DESPLIEGUE PARA GROK — PARTE 1 (FINAL)
**Reemplaza v1 y v2. Consolida todo en un solo documento: nodos, DAG, Tribunal, comandos del Director, eventos obligatorios. Repositorio: `agentes`. Alcance: A1+A2+A3, solo GitHub.**

---

## Paquete de nodos (B3+B4 simplificado para esta entrega)

```yaml
nodos:
  T-001:
    goal: "Desplegar el núcleo determinista (A1) en agentes/control-layer/workflow_core/"
    dependencies: []
    skills_requeridas: [python, pytest, git]
    contrato_output:
      artefactos: [pyproject.toml, "workflow_core/*.py (9 archivos)", test_state_machine.py]
    criterio_exito: "test_workflow_transition, test_node_transition, test_invalid_transition_is_rejected — los 3 pasan"
    risk: bajo
    priority: 1
    timeout_seg: 900

  T-002:
    goal: "Desplegar Research Engine (A2) en workflow_core/research.py"
    dependencies: [T-001]
    contrato_input: "workflow_core/errors.py debe existir (de T-001)"
    contrato_output:
      artefactos: ["research.py (o +research_contracts.py si >200 líneas)"]
    fuente_obligatoria: "usa el código de SALIDA-01-NUCLEO-DAG-CONTROL.md, sección 'PARTE A2-FIX' para ResearchRequest/ResearchFinding — los 4 documentos A02-research-doc1..4 originales NO tienen el @dataclass real, solo describen los campos. Sin esta fuente, research.py queda incompleto."
    criterio_exito: "módulo importable sin error, incluye ResearchRequest y ResearchFinding como @dataclass funcionales"
    risk: bajo
    priority: 2
    timeout_seg: 600

  T-003:
    goal: "Desplegar DAG y Sheriff (A3) en workflow_core/"
    dependencies: [T-001]
    skills_requeridas: [python, pytest, git]
    contrato_input: "workflow_core/contracts.py y errors.py deben existir (de T-001)"
    contrato_output:
      artefactos: [dag.py, sheriff.py, policies.py, dag_patch.py, test_dag.py, test_sheriff.py, test_dag_patch.py]
    criterio_exito: "DAG válido pasa · DAG con ciclo lanza ContractViolationError · Sheriff aprueba/rechaza según política"
    risk: bajo
    priority: 2
    timeout_seg: 900

  T-004:
    goal: "Commit + push + PR de T-001..T-003 en un solo bloque al repo agentes"
    dependencies: [T-001, T-002, T-003]
    skills_requeridas: [git, github]
    contrato_input: "T-001, T-002, T-003 en estado done"
    contrato_output: "PR abierto contra agentes, branch workflow/A1-A3-nucleo-dag-sheriff"
    criterio_exito: "PR creado, CI corriendo, ningún push directo a main"
    risk: medio
    priority: 1
    timeout_seg: 600

paralelo_max: 2
regla_paralelo: "T-002 y T-003 corren en paralelo — ambos dependen solo de T-001, no se importan entre sí. Desempate si hiciera falta: priority menor primero, luego risk menor, luego timeout_seg menor."
```

## B6 · Tribunal para esta entrega

```yaml
tribunal:
  SHERIFF:     "¿el output respeta el DAG y las políticas declaradas? veto si no."
  CENTINELA:   "¿algo del cambio toca fuera del alcance de T-00X? veto si sí."
  JUEZ:        "¿el criterio_exito del nodo se cumple, literal?"
  SUPERVISOR:  "¿el archivo resultante respeta L02 (≤200 líneas, 1 responsabilidad)?"
  VALIDADOR:   "¿los tests declarados corren y pasan?"
  VERIFICADOR: "¿los hashes de los artefactos coinciden con lo registrado?"
veto_bloquea_todo: true
score_solo_si_cero_vetos: true
```

## Vocabulario del Director

```
GO             → iniciar/continuar          OK   → aprobar, siguiente nodo
FIX <x>        → corregir entrega actual    PAUSA → checkpoint + detener
ESTADO         → resumen de nodos           SALTAR T-X → marcar blocked, seguir otra rama
UNLOCK <doc>   → autorizar bloque congelado ABORT → checkpoint + cerrar sin completar
```

## Eventos obligatorios

```yaml
por_nodo_minimo: [node.selected, node.start, "node.checkpoint (≥1)", node.validate, "node.done | node.failed"]
regla: "cambio de estado sin evento asociado = modificación silenciosa = se rechaza"
```

---

## Arranque

1. **RT-00→RT-04:** confirma que tienes los 4 nodos de arriba · preflight (git configurado, Python disponible, permisos de escritura, binario de Temporal descargado y verificado — **sin conectar todavía**, Temporal va en HF1, nunca en HF2-5) · carga solo `python/pytest/git/github` · determina INICIO o REANUDACIÓN por tu registro de estado.
2. Reporta el boot y **espera `GO`** — nada se ejecuta antes.
3. **Por cada nodo (RT-10→RT-45):** selecciona por dependencias resueltas (T-002/T-003 en paralelo tras T-001) → verifica idempotencia → verifica capability → carga solo la memoria de ese nodo → valida input contra contrato → ejecuta (`orden_preferencia: OSS→local→MCP→API→LLM` — extraer código de los .md de A1/A2/A3, escribir archivos, correr `pytest`, hacer `git commit/push` es **todo determinista, cero LLM**: el nombre de archivo ya está indicado antes de cada bloque, es lectura literal) → Tribunal (6 roles arriba, vetos primero) → **verifica el goal completo, no solo que Tribunal dio OK** → registra artefactos con hash → verifica consistencia → audita → entrega en formato `NODO T-XXX DONE` y espera `GO` si el riesgo lo pide (T-004 es riesgo medio — no automático).
4. Fallo en cualquier paso → clasifica auto-recuperable vs. requiere Director, nunca improvises fuera de eso.
5. **RT-90 no se dispara todavía** — esta es la Parte 1 de varias. El cierre completo llega cuando todas las partes futuras estén en `done`.

---

## Alcance — sin excepción

```
1º GitHub (esto)
2º HF (Parte 2 de esta guía, más adelante)
3º Documentos MD para el Director (al final)
```
No conectes Temporal a ningún workflow todavía. No avances a G4 por tu cuenta — sigue en construcción.

---

*Guía de Despliegue — Parte 1, versión final. Repositorio: `agentes`. 4 nodos, paralelismo real en T-002/T-003, Tribunal + comandos + eventos completos.*
