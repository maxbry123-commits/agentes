# README — Arquitectura fusionada YAIWES · X-Ray

**Repositorio:** `maxbry123-commits/agentes`  
**Rama:** `main`  
**Arquitectura base:** `README-ARQUITECTURA-FUSIONADA-YAIWES-XRAY-2026-09-01.md`  
**Actualización X-Ray:** 2026-09-03  
**Regla:** GitHub y el código ejecutable son la verdad. Documento ≠ implementación.

> Esta es la única arquitectura canónica que Sol Orquestador actualizará. La bitácora, notas, instrucciones literales, checkpoints y tareas viven fuera de este documento, dentro de `Crazy Wall Orquestador/`.

## 1. Fuentes fusionadas
La arquitectura conserva como base la arquitectura fusionada X-Ray del 2026-09-01 y se cruza con:
- `agente-yaiwes/PLAN_100_ESTRUCTURA_DEFINITIVA.md`
- `agente-yaiwes/STRUCTURE.md`
- `agente-yaiwes/README.md`
- `PIPELINE/Agente_YAIWES_v.1_en_PRODUCCION.md`
- `PIPELINE/PASO3_ORGANIZACION_CODIGO_REAL_YAIWES.md`
- `PIPELINE/ARQUITECTURA_WORDFLOW_PROGRAMACION_CONSOLIDADA.md`
- las cuatro pasadas forenses de PIPELINE
- `Documentos arquitectura Yaiwes lote 1/`
- `Documentos proyectos Yaiwes instrucciones de Claude/`
- código fuente real de `main`.

## 2. Leyenda X-Ray
- **REAL:** código ejecutable localizado y demostrable.
- **PARCIAL:** existe código/capacidad, pero integración o evidencia incompleta.
- **ESQ:** scaffold/placeholder.
- **REF:** referencia a fuente canónica.
- **DECLARADO_NO_VERIFICADO:** documento afirma que existe, pero falta localizar/verificar en fuente.
- **FALTANTE:** requerido y no demostrado por código/pruebas.
- **VERIFIED_CLOSED:** código + cableado + pruebas + evidencia + auditoría destino.

## 3. Gate arquitectónico de cierre
Claude añade una distinción obligatoria:

### NIVEL A — Kernel simple
`Tarea → decisión → ejecución → evidencia → fin`, sin reparación manual.

Antes de ampliar el sistema, el X-Ray debe verificar/cerrar:
1. imports declarados rotos en `entrypoint.py`, `entrypoint_v1.py`, `bootstrap.py`, `execution_facade.py`, `orchestrator_v1.py`;
2. `mission.py`;
3. `goal_lock.py`;
4. `execution-orchestration/bootstrap.py`;
5. `recovery.py`, reutilizando `checkpoint.py` si corresponde;
6. una ejecución E2E mínima desde el entrypoint real.

Estado: **PENDIENTE DE VERIFICACIÓN FORENSE EN CÓDIGO; no se acepta el documento como prueba.**

### NIVEL B — Arquitectura ampliada
Mythos 40 pasos, EURS/DRE, pool paralelo, memoria multinivel, multi-API, reasoning/governance y observabilidad. Se mantiene en arquitectura, pero no puede ocultar un fallo del camino mínimo Nivel A.

## 4. Roadmap Claude incorporado
### Bloque 1 — Fundamentos/kernel, tareas 1–15
Objetivo conservado: eliminar duplicación real, dejar `kernel-principal` como fachada delegante, establecer 8 primitivas, manifest y regresión sobre los 27 tests heredados.

Primitivas objetivo: Event Loop, DSL Engine, Scheduler, Runtime, Registry, Router, Policy Engine, State Manager.

### Bloque 2 — Reasoning/governance, tareas 16–35
Incluye goal-dual-driver, decision-on-demand, prompts Mythos/EURS/DRE versionados, score de complejidad, expert-panel-router, consensus-trigger, workflow-capacity, schema-contracts, validator, timeout, idempotencia, concurrencia, sheriff, judge, forensic, deny rules y tests.

### Bloques 3–4
Workflows/pool/memoria y observabilidad/cierre continúan como dependencias de Nivel B. Sus tareas se mantienen pendientes hasta completar cross-check 1:1 contra fuente.

## 5. Lote 1 — arquitectura/capacidades a fusionar
El Lote 1 contiene material de Mythos/Fables, Muse, Rufo y documentos de integración/código. Su uso arquitectónico es:
- extraer capacidades y contratos;
- localizar si ya existe implementación en `main`;
- detectar duplicación;
- decidir reutilización total, parcial, adaptador o rechazo;
- nunca copiar lógica documental como si fuera código verificado.

## 6. Enchufe Universal — estado de verificación
Claude declara existentes:
- `ficha_contract_v2.py` / schema;
- `validator_v2.py` con reglas de validación;
- `UniversalPluginBus.enchufar()`;
- `ContractGenerator.generate()`;
- `AdapterFactory.create()`;
- `PluginRegistry` con slots/shadow-test/swap.

Estado X-Ray actual: **DECLARADO_NO_VERIFICADO** hasta localizar cada archivo/símbolo en fuente. Si se verifica, será el carril preferente para integrar componentes sin modificar originales.

## 7. Arquitectura de integración de componentes
Flujo canónico:

`ORIGEN → XRAY → CONTRATO/FICHA → TOTAL|PARCIAL|ADAPTADOR|RECHAZAR → DESTINO → GITHUB ACTION → VERIFICACIÓN DESTINO → ID CODEX → CABLEADO QUIRÚRGICO → TEST → AUDITORÍA → VERIFIED_CLOSED`

Matriz obligatoria:
| ID | Componente origen | Capacidad | Fuente | Decisión | Destino YAIWES | Cableado | Tests | Estado |
|---|---|---|---|---|---|---|---|---|
| POR_INVENTARIAR | componentes existentes en repo | pendiente | código real | pendiente | pendiente | pendiente | pendiente | XRAY |

No se mueve un componente hasta aprobación del Director.

## 8. Contrato determinista de Codex
Cada tarea Codex nace de un ID del Crazy Wall después de verificar el movimiento. Debe contener DSL + DAG + schema cerrado + Sheriff + Validator + Verifier + Sentinel + Supervisor + Judge + Guardian.

Codex ejecuta; no rediseña. Puede cablear/conectar y escribir únicamente el código mínimo quirúrgico requerido. Prohibida la reescritura amplia de módulos fuera del alcance del ID.

## 9. Orden operativo actualizado
1. X-Ray completo documentos Lote 1 + Claude ↔ fuente real.
2. Inventario de componentes existentes en `agentes` y clasificación total/parcial/adaptador/rechazo.
3. Presentar primera integración al Director.
4. Tras aprobación, prompt a Sol GPT/GitHub Action para movimiento y comprobante.
5. Verificar destino físicamente.
6. Crear ID Codex determinista y ejecutar cableado quirúrgico.
7. Auditar Codex y actualizar estado.
8. Para gaps restantes: buscar primero en `Agentes-motores-Wordflow-YAIWES`; después OSS si no existe solución interna.
9. Repetir hasta auditoría documento por documento y `VERIFIED_CLOSED`.

## 10. Regla de cierre
Ninguna tarea de Claude ni capacidad del Lote 1 se marca cerrada por presencia de archivo/documento. El cierre requiere localización en fuente, integración correcta, prueba relevante, evidencia y cross-check contra su requisito original.
