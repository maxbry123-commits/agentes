# README — Integración de componentes en arquitectura YAIWES

**Repositorio:** `maxbry123-commits/agentes`  
**Raíz de auditoría:** `Core kernel Yaiwes/`  
**Arquitectura canónica:** `Readme arquitectura Yaiwes/README.md`  
**Destino físico:** `Agente Yaiwes principal/`  
**Modo:** `FAIL_CLOSED_LOOP`

## Método simple obligatorio

Cada componente se procesa únicamente con estos 3 pasos. No se agregan fases nuevas sin autorización del Director.

### Paso 1 — Auditoría forense X-Ray + análisis
1. Leer código fuente real; no decidir por README upstream ni por nombre de carpeta.
2. Verificar qué hace realmente: clases/funciones principales, dependencias, entradas/salidas, persistencia, ejecución y errores.
3. Cruzar el hallazgo con el chat y con `Readme arquitectura Yaiwes/README.md` para decidir encaje y destino.
4. Clasificar cuando la evidencia lo permita:
   - **A — agente/subagente autónomo:** mantiene ciclo propio, estado y capacidad de decidir/ejecutar.
   - **B — workflow/orquestador/pool:** coordina DAG/FSM, scheduler, colas, workers, retries, estados o procesos.
   - **C — capacidad modular:** aporta una función concreta al kernel/runtime sin convertirse en agente autónomo.
5. Si la evidencia no alcanza, registrar `GAP / NO_DETERMINABLE`; no forzar A/B/C.

### Formato simple de salida por componente
1. Nombre.
2. Función real.
3. Objetivo/aporte dentro de YAIWES.
4. Microflujo: entrada ➡️ procesamiento ➡️ estado/resultado.
5. Opción A/B/C.
6. Justificación basada en código real.
7. Destino exacto propuesto.

### Paso 2 — Integración física
1. Integrar/mover únicamente código útil y dependencias necesarias a la estructura raíz de YAIWES.
2. No crear monolitos; separar responsabilidades.
3. No mover ZIP, README upstream, docs, ejemplos, benchmarks ni packaging innecesario salvo dependencia demostrada.
4. Conectar exclusivamente mediante el carril Fables / Enchufe Universal:

`Componente ➡️ adapter/contrato ➡️ Ficha Contract v2 ➡️ WIRING/registry ➡️ Universal Plugin Bus ➡️ módulo YAIWES`

5. El código original no se reescribe si un adapter resuelve la integración.
6. Carpetas, manifests o documentación por sí solos no cuentan como integración.

### Paso 3 — Verificación + arquitectura
1. Verificar destino físico y código fuente real.
2. Verificar adapter + contrato/Ficha v2 + WIRING/registry + Enchufe Universal.
3. Verificar imports/build/runtime/tests reales según el componente.
4. Exigir evidencia verificable: ruta + diff/SHA + test/run/log + URL cuando aplique.
5. Solo después editar quirúrgicamente `Readme arquitectura Yaiwes/README.md`.
6. Prohibido reescribir el README arquitectura; solo añadir el delta real del componente preservando todo lo existente.
7. Resultado: `VERIFIED_CLOSED | CLOSED_UNVERIFIED | INCONCLUSIVE`; cualquier GAP vuelve al LOOP.

## Regla de lote
Los 20 componentes se trabajan en tandas. La tanda actual contiene 5 y se procesa en cola 1×1. Un componente no avanza a integración física hasta que el Director haya visto y aprobado su análisis/propuesta cuando así lo solicite.

## Tanda actual — primeros 5
1. APScheduler
2. AWS-Step-Functions-DS-SDK
3. Ajv
4. Apache-APISIX
5. Apache-Airflow

Secuencia por cada uno:

`X-Ray ➡️ mostrar integración propuesta al Director ➡️ aprobación ➡️ integración física ➡️ verificación ➡️ delta quirúrgico README arquitectura`.
