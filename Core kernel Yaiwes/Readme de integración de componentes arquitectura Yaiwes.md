# README — Método de integración de componentes en arquitectura YAIWES

**Repositorio:** `maxbry123-commits/agentes`  
**Raíz de auditoría:** `Core kernel Yaiwes/`  
**Arquitectura canónica:** `Readme arquitectura Yaiwes/README.md`  
**Destino físico:** `Agente Yaiwes principal/`  
**Contrato:** `tel.workflow/v3`  
**Modo:** `FAIL_CLOSED_LOOP`

## 1. Qué cuenta como componente
Un componente real es un proyecto/agente/software open source descargado con código ejecutable propio. No cuentan como componentes separados los ZIP, README, docs, ejemplos, `.keep`, manifests, carpetas contenedoras ni artefactos auxiliares. Si el mismo upstream aparece en varias carpetas, se deduplica por identidad canónica del repositorio/proyecto.

## 2. Orden de búsqueda de componentes
1. Leer primero chat/historial, plan, checkpoint, state y bitácora para no repetir trabajo.
2. Recorrer `Core kernel Yaiwes/` y, en especial, `Componentes recuperados A/`, `Componentes recuperados B/`, `Download code Yaiwes/` y `Download code/`.
3. Identificar proyecto real por código y metadatos; no decidir por nombre de carpeta solamente.
4. Revisar fuente oficial del proyecto en GitHub/repositorio oficial y registrar URL + SHA/commit cuando exista.
5. Usar comunidad de desarrolladores solo como señal secundaria para errores/build/runtime.
6. Filtrar resultados sin URL/evidencia, deduplicar y rankear: código oficial > código local/skills > comunidad.

## 3. Paso 1 — X-Ray del componente antes de integrar
La decisión se toma desde **código fuente real**, no desde el README upstream.

### Tres puntos de análisis obligatorios
1. **Función real:** qué ejecuta el código, qué clases/módulos/entrypoints usa y qué entradas/salidas maneja.
2. **Objetivo real:** qué problema resuelve dentro de su proyecto original y qué capacidad concreta aporta a YAIWES.
3. **Microflujo real:** cadena horizontal desde entrada hasta salida, por ejemplo `Input ➡️ validator/router/scheduler ➡️ executor/state ➡️ result/evidence`.

### Opciones A / B / C
- **A — agente/subagente autónomo:** tiene objetivo propio, estado, herramientas/acciones y ciclo de ejecución relativamente autónomo.
- **B — workflow/orquestador/pool:** organiza secuencias, DAG/FSM, routing, scheduling, ejecución o pools de workers/executores.
- **C — capacidad modular determinista/híbrida:** unidad del kernel o servicio enchufable; código primero, LLM solo cuando esté justificado. Ejemplos: validadores, gateways, policies, registries, parsers, adapters.
- Si la evidencia no permite clasificar: `GAP / NO_DETERMINABLE`; no se fuerza A/B/C.

## 4. Formato de salida de cada componente estudiado
Se entrega **un componente por bloque** con este formato fijo:

1. **Nombre**
2. **Función real**
3. **Objetivo**
4. **Microflujo horizontal** con `➡️`
5. **Opción validada A/B/C**
6. **Justificación** basada en archivos/clases/entrypoints reales y evidencia de repositorio

No se añaden campos que cambien la decisión sin autorización del Director.

## 5. Paso 2 — Decidir ubicación arquitectónica
1. Leer siempre `Readme arquitectura Yaiwes/README.md` antes de mover código.
2. Mapear la capacidad al árbol real de `Agente Yaiwes principal/`.
3. Elegir un destino modular existente cuando encaje: `definition-registry/`, `execution-orchestration/`, `mesh-routing-collaboration/`, `control-governance/`, `state-events-durability/`, `kernel-principal/extension-kernel/`, etc.
4. Prohibido crear un monolito. Separar contrato, adapter, ficha/descriptor, wiring/registry, guards, tests y runtime por responsabilidad.

## 6. Paso 2 — MOVE físico, no COPY
1. Mover solo código útil necesario para la capacidad aprobada.
2. No mover README upstream, docs, ejemplos, benchmarks, ZIP ni basura auxiliar salvo dependencia de build demostrada.
3. Preservar trazabilidad: origen local, upstream oficial, SHA/commit, destino y diff.
4. El destino recibe un **README Yaiwes nuevo**, que explica cómo se integra la capacidad; no reutiliza el README upstream como documento de arquitectura.
5. El MOVE se valida por origen ausente/destino presente o por diff reconocido como rename/move; una copia duplicada no se llama MOVE.

## 7. Enchufe universal obligatorio
Toda capacidad integrada se conecta mediante el patrón YAIWES de enchufe universal:

`Componente ➡️ adapter ➡️ contrato/Ficha v2 ➡️ WIRING/registry ➡️ Universal Plugin Bus ➡️ destino arquitectónico ➡️ health/evidence`

Elementos esperados según el componente:
- `adapter.py` o adapter equivalente del lenguaje;
- `ficha.<componente>.v2.json`;
- `WIRING.json`/registro equivalente;
- contrato de I/O;
- fail-closed, timeouts, health/evidence y observabilidad cuando aplique.

**Seguridad:** el bus v2 contiene rutas de inspección dinámica; código no confiable se revisa estáticamente y/o se aísla antes de cualquier ejecución dinámica.

## 8. Diez pasadas X-Ray post-movimiento
Después del MOVE se audita el código en su destino final en estas 10 dimensiones:
1. corrección;
2. determinismo;
3. contratos I/O;
4. concurrencia;
5. errores/retries;
6. rendimiento;
7. recursos;
8. seguridad;
9. observabilidad;
10. tests.

Solo se aplican mejoras sustentadas por evidencia. Cada GAP vuelve al LOOP con StrategyDelta materialmente distinto al intento fallido.

## 9. Verificación y cierre
1. Verificar estructura destino y ausencia de duplicación accidental.
2. Verificar imports/build/runtime del código movido.
3. Verificar adapter, Ficha v2, WIRING y targets del bus.
4. Ejecutar prueba real en el runtime correspondiente al proyecto.
5. Checks potencialmente inestables: repetir hasta 10×; checks puros/deterministas: una ejecución basta.
6. Auditar instrucciones 3 veces + 3 refutaciones + cross-check global.
7. Persistir evidencia en bitácora/state/checkpoint/plan/recovery cuando corresponda.
8. Actualizar `Readme arquitectura Yaiwes/README.md` **solo quirúrgicamente** con qué se incorporó, dónde vive y qué hace.
9. Cierre permitido: `VERIFIED_CLOSED`; si falta evidencia: `GAP`, `ACTIVE_LOOP`, `CLOSED_UNVERIFIED` o `INCONCLUSIVE` según corresponda.

## 10. Trabajo por lotes de 5
Se pueden investigar/integrar cinco componentes por lote para acelerar, pero cada uno conserva nodo, clasificación, destino, MOVE, tests, evidencia y estado independientes. Un GAP en un componente no autoriza falsear PASS en los demás. El lote solo se declara `5/5 VERIFIED_CLOSED` cuando los cinco tienen evidencia propia.

## 11. Evidencia mínima por componente
- ruta de origen local;
- upstream oficial + URL real;
- commit/SHA de MOVE o integración;
- destino exacto bajo `Agente Yaiwes principal/`;
- clasificación A/B/C;
- archivo de cableado/Ficha/adapter;
- test/run/log verificable;
- veredicto final.

## 12. LOOP operacional resumido
`INPUT literal ➡️ GOALS 12/12 ➡️ prioridades ➡️ plan ➡️ cola 1×1 ➡️ X-Ray ➡️ clasificación ➡️ arquitectura ➡️ MOVE ➡️ enchufe universal ➡️ X-Ray 10× ➡️ verify/refute ➡️ GAP? research/StrategyDelta ➡️ tests ➡️ persistencia ➡️ 3 refutaciones ➡️ cross-check ➡️ CODA ➡️ verify_final`.
