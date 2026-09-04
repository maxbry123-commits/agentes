# ARQUITECTURA YAIWES — X-RAY ACTUALIZADA

Fecha de corte: 2026-09-03
Estado: AUDITORÍA FORENSE EN CURSO — NO VERIFIED_CLOSED

## 1. Fuentes canónicas cruzadas
- Código real del repositorio `agentes/main`.
- `Documentos arquitectura Yaiwes lote 1/`.
- `Documentos proyectos Yaiwes instrucciones de Claude/`.
- Crazy Wall/estado/checkpoints dentro de esta raíz.

Regla: documento ≠ implementación. Toda capacidad declarada debe localizarse en código y validarse antes de marcar REAL.

## 2. Hallazgo nuevo — prioridad de cierre del Kernel
Los documentos nuevos de Claude `08_protocolo_cierre_kernel_simple.md` y `09_guia_decision_integrar_codigo_kernel.md` están presentes.

El cierre inmediato se divide en:
- NIVEL A: una tarea entra → sistema decide → ejecuta → guarda evidencia → termina sin intervención manual.
- NIVEL B: Mythos 40 pasos, pool paralelo, memoria multinivel, multi-API y gobernanza ampliada.

Gate arquitectónico: NIVEL A antes de ampliar NIVEL B.

Bloqueadores Nivel A declarados por Claude y pendientes de verificación línea-a-línea en fuente:
1. cinco imports rotos: `entrypoint.py`, `entrypoint_v1.py`, `bootstrap.py`, `execution_facade.py`, `orchestrator_v1.py`;
2. `mission.py`;
3. `goal_lock.py`;
4. `execution-orchestration/bootstrap.py`;
5. `recovery.py`, reutilizando `checkpoint.py` cuando sea posible;
6. prueba E2E mínima desde `python -m agente` hasta evidencia final.

## 3. Arquitectura de integración de componentes
Todo componente encontrado dentro del repositorio pero fuera de su destino final pasa por INTake antes de moverse:

`COMPONENTE_ORIGEN -> XRAY -> FICHA/CONTRATO -> DECISIÓN TOTAL|PARCIAL|ADAPTADOR|RECHAZAR -> DESTINO_YAIWES -> MOVIMIENTO -> VERIFICACIÓN_DESTINO -> CODEX_WIRING -> TEST -> AUDITORÍA`

Tabla obligatoria por componente:
| ID | Componente origen | Capacidad | Estado fuente | Integración | Destino YAIWES | Adaptador | Riesgo | Tests | Estado |
|---|---|---|---|---|---|---|---|---|---|
| pendiente | inventario en curso | — | XRAY | — | — | — | — | — | PENDING |

## 4. Enchufe Universal — hipótesis documental a verificar
Claude declara ya construidos `ficha_contract_v2.py`, `validator_v2.py`, `UniversalPluginBus.enchufar()`, `ContractGenerator.generate()`, `AdapterFactory.create()` y `PluginRegistry`.

Hasta localizar cada símbolo/archivo en el código fuente, su estado arquitectónico es `DECLARADO_NO_VERIFICADO`, no REAL.

Si se verifica, se reutiliza como carril canónico de integración y queda prohibido rediseñarlo desde cero.

## 5. Contrato determinista para Codex
Codex solo recibe tareas después de verificar físicamente el destino. Cada tarea tendrá ID único y:
- DSL de acciones permitidas;
- DAG de dependencias;
- schema cerrado de entrada/salida;
- Sheriff de límites de modificación;
- Validator de precondiciones;
- Verifier de resultados;
- Sentinel de archivos fuera de alcance;
- Supervisor de secuencia;
- Judge de aceptación objetiva;
- Guardian de rollback/integridad.

Codex cablea, conecta y añade únicamente código quirúrgico imprescindible. No reescribe módulos completos ni decide arquitectura.

## 6. Flujo Director → Sol GitHub Action → Codex
1. Sol Orquestador audita y mapea componente → destino.
2. Director aprueba.
3. Se entrega prompt determinista a Sol GPT/GitHub Action para mover/copiar archivos y emitir comprobante.
4. Sol Orquestador verifica destino real.
5. Se abre ID de Crazy Wall para Codex.
6. Codex cablea quirúrgicamente.
7. Sol Orquestador ejecuta auditoría post-Codex y solo entonces cierra.

## 7. Código aportado posteriormente por el Director
Cada lote listo de código sigue el mismo flujo: análisis estático → ubicación arquitectónica → prompt de movimiento → comprobante → verificación de destino → ID Codex → cableado quirúrgico → tests → X-Ray final.

## 8. Ruta de cierre Tareas 1–3
Paso 1 — Cerrar X-Ray documentos ↔ código y fijar arquitectura REAL/PARCIAL/FALTANTE. Logro esperado: fuente de verdad única y blockers verificables.

Paso 2 — Inventariar todos los componentes existentes del repo y mapear total/parcial/adaptador hacia destinos YAIWES. Logro esperado: matriz de integración aprobable.

Paso 3 — Mover por GitHub Action solo componentes aprobados y verificar destinos. Logro esperado: archivos físicamente correctos sin cableado invasivo.

Paso 4 — Cablear por IDs Codex deterministas, mínimo código nuevo y tests por integración. Logro esperado: componentes conectados sin reescritura.

Paso 5 — Auditar gaps restantes contra todos los documentos Claude; buscar primero en `Agentes-motores-Wordflow-YAIWES`, luego OSS cuando falte. Logro esperado: cada gap con fuente de solución concreta.

Paso 6 — Auditoría documento por documento contra código final, tests y evidencia. Logro esperado: actualizar lista Claude y cerrar únicamente ítems con `VERIFIED_CLOSED`.

## 9. Estado actual
- Nuevos documentos Claude: PRESENTES.
- Input del Director: almacenado literalmente en `Crazy Wall Orquestador/ESTADO.json`.
- Árbol del repositorio: contiene numerosos workflows de descarga, extracción, reparación, organización y relocalización; por tanto existe material de componentes que requiere inventario forense antes de nuevas descargas.
- Integración física: NO iniciada por esta pasada.
- Próximo gate: terminar inventario de componentes y cross-check de símbolos/código antes de emitir el primer prompt de movimiento.
