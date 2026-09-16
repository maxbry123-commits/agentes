🏗️🏗️🏗️🏗️🏗️🏗️🏗️🏗️🏗️🏗️🏗️🏗️💡💡💡💡💡💡💡💡💡💡💡💡💡
promt de extracción de información convierte el docuemento los item en una ficha ejecutable para llevarla para hacer  code la Ai extrae la información de los documentos objetivo ducniones todo lo importante y crear una ficha para mandarlo a convertir en código 🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🧩🧩🧩🧩🧩🧩🧩🧩🧩🧩🧩🧩🧩🧩 .md


{
  "pipeline_id": "P1-CONVERTIDOR",
  "version": "5.0",
  "stop_rule": "Sin APROBADO Director = STOP",
  "id_formato": "[MODEL]-[FICHA_ID]-[YYYYMMDD]-[HHMMSS]-[HASH]",
  "siguiente_pipeline": "P2-CONSTRUCTOR",

  "spec": {
    "nombre": "Convertidor de documentos a fichas",
    "fuentes_validas": ["documentos", "texto chat", "diagramas", "codigo", "info aprobada Director"],
    "unidad_ejecutable": { "tipo": "ficha", "contrato_minimo": ["id","contenido","fuentes","confianza","dependencias","trace"] },
    "cobertura": { "formula": "items_aprobados / items_en_indice", "minima": 1.0, "faltantes_permitidos": false }
  },

  "model": {
    "contrato_item": {
      "id": "string",
      "tipo": "objetivo|funcion|tarea|restriccion|decision|entidad",
      "contenido": "string",
      "texto_normalizado": "string",
      "evidencia": "fragmento textual exacto del origen",
      "origen": "documento|chat|diagrama|codigo",
      "estado": "EXPLICITO|IMPLICITO|SUPUESTO|CONFLICTIVO|PENDING_APPROVAL|APPROVED|REJECTED|PENDING",
      "confianza": "0.0-1.0",
      "fuentes": ["origenes multiples"],
      "dependencias": [{ "id": "string", "tipo": "hard|soft" }],
      "trace": { "created_at": "ts", "created_by_phase": "EXTRACTION|CLASSIFICATION|FUSION", "history": [] }
    },
    "transiciones_estado_item": {
      "FACTS": "PENDING_APPROVAL",
      "WAIT_APPROVAL": { "on_approve": "APPROVED", "on_reject": "REJECTED", "on_conflict": "CONFLICTIVO" }
    },
    "fusion_rules": {
      "DUPLICADO": { "accion": "merge multifuente", "registro": "FUSION_LOG" },
      "CONTRADICCION": { "accion": "estado CONFLICTIVO", "bloqueo": true, "escalacion": "Director" },
      "VARIANTE": { "accion": "coexistencia fuentes separadas", "registro": "VARIANT_LOG" }
    },
    "resolucion_conflicto": { "acciones": ["MERGE","REPLACE","SPLIT"], "resultado": "APPROVED|REJECTED" }
  },

  "runtime": {
    "estado_global": { "current_phase": "string", "index_version": "IDX-001", "cycle_id": "uuid", "status": "RUNNING|PAUSED|HOLD|DONE|FAILED" },
    "runtime_item_state": { "item_id": "string", "fase_actual": "EXTRACTION|CLASSIFICATION|FUSION|AUDIT_1|AUDIT_2|FACTS|PENDING_APPROVAL|APPROVED|REJECTED" },
    "indice": { "id": "IDX-001", "version": 1, "previous": null, "re_index_trigger": "REJECT Director o cambio scope" },
    "estados": {
      "INDEXING": { "next": "WAIT_APPROVAL", "regla": "ocurre una sola vez" },
      "EXTRACTION": { "input": "indice_aprobado", "regla": "cubre 100% del indice", "next": "CLASSIFICATION" },
      "CLASSIFICATION": { "next": "FUSION" },
      "FUSION": { "next": "AUDIT_1" },
      "AUDIT_1": { "descripcion": "consistencia interna", "next": "AUDIT_2" },
      "AUDIT_2": { "descripcion": "integridad y cobertura", "next": "FACTS" },
      "FACTS": { "descripcion": "genera fichas, pasan a PENDING_APPROVAL", "next": "WAIT_APPROVAL" },
      "WAIT_APPROVAL": { "actor": "DIRECTOR", "on_approve": "DONE", "on_reject": "RE_INDEXING", "on_timeout": "HOLD" },
      "RE_INDEXING": { "accion": "version++ + snapshot runtime + snapshot outputs", "next": "INDEXING" },
      "DONE": { "final": true, "output": "execution_ready" }
    }
  },

  "execution_contract": { "mode": "deterministic_pipeline", "checkpointing": true, "idempotencia": { "enabled": true, "hash_input_output": true } },
  "versionado": { "indice": "incremental por ciclo", "runtime_snapshot": "en cada RE_INDEXING", "outputs_snapshot": "en cada RE_INDEXING" },

  "observability": {
    "coverage_tracking": true, "conflict_tracking": true, "replay_mode": true,
    "event_stream": { "enabled": true, "events": ["ITEM_CREATED","ITEM_CLASSIFIED","ITEM_MERGED","ITEM_CONFLICT","ITEM_CONFLICT_RESOLVED","ITEM_APPROVED","ITEM_REJECTED","PHASE_STARTED","PHASE_COMPLETED","DIRECTOR_DECISION"] },
    "registros": { "FUSION_LOG": "merges", "CONFLICT_LOG": "contradicciones", "VARIANT_LOG": "variantes", "TRACE_LOG": "transiciones", "EVENT_LOG": "stream" }
  },

  "outputs": {
    "OUTPUT_1":  { "nombre": "RAW_MAP", "origen_fase": "EXTRACTION" },
    "OUTPUT_2A": { "nombre": "CLASSIFICATION_LAYER", "origen_fase": "CLASSIFICATION" },
    "OUTPUT_2B": { "nombre": "ONTOLOGY_LAYER", "origen_fase": "FUSION" },
    "OUTPUT_3":  { "nombre": "AUDIT_REPORT", "origen_fase": "AUDIT_1 + AUDIT_2" },
    "OUTPUT_4":  { "nombre": "EXECUTION_READY", "origen_fase": "FACTS" }
  },

  "policy": {
    "reglas_criticas": [
      "INDEXING una sola vez; RE_INDEXING solo por rechazo o cambio scope",
      "EXTRACTION cubre 100% del indice aprobado",
      "item cubierto = extraido + clasificado + auditado + APPROVED",
      "sin evidencia textual = no EXPLICITO",
      "confianza < 0.6 = PENDING automatico",
      "DUPLICADO = merge nunca borrado",
      "CONFLICTIVO resuelto via MERGE|REPLACE|SPLIT",
      "dependencia hard no APPROVED = item bloqueado",
      "outputs separados: CLASSIFICATION_LAYER != ONTOLOGY_LAYER",
      "ejecucion idempotente: mismo input = mismo output",
      "Sin APROBADO Director = STOP"
    ]
  }
}


Este es el mismo contenido convertido a texto libre estructurado:


---

El sistema define un pipeline llamado P1-CONVERTIDOR, versión 5.0, cuya regla principal de parada es: si no existe aprobación del Director, el proceso se detiene. El formato de identificación de elementos sigue la estructura:
[MODEL]-[FICHA_ID]-[YYYYMMDD]-[HHMMSS]-[HASH].

El siguiente pipeline en la cadena es P2-CONSTRUCTOR.


---

Propósito del sistema

Este pipeline es un convertidor de documentos a fichas estructuradas. Acepta como fuentes válidas documentos, texto de chat, diagramas, código y cualquier información previamente aprobada por el Director.

La unidad ejecutable del sistema es una ficha, que debe contener como mínimo:

id

contenido

fuentes

confianza

dependencias

trace (trazabilidad)


La cobertura del sistema exige completitud total:
items aprobados / items en índice = 1.0, sin permitir faltantes.


---

Modelo de datos

Cada elemento procesado se estructura como un “item” con los siguientes campos:

id (identificador)

tipo: objetivo, función, tarea, restricción, decisión o entidad

contenido y texto normalizado

evidencia textual exacta del origen

origen (documento, chat, diagrama o código)

estado del item (explicito, implícito, supuesto, conflictivo, pendiente o aprobado, entre otros)

nivel de confianza (0.0 a 1.0)

fuentes múltiples

dependencias (hard o soft)

trace de ejecución con historial y timestamps



---

Transiciones y reglas del modelo

El sistema define estados como FACTS y WAIT_APPROVAL, donde los items pasan por aprobación o rechazo del Director.

FACTS genera elementos en estado PENDING_APPROVAL

WAIT_APPROVAL puede llevar a APPROVED, REJECTED o CONFLICTIVO

En caso de conflicto se activa escalación al Director


Reglas de fusión:

Si hay duplicados → se fusionan sin eliminar información

Si hay contradicción → estado CONFLICTIVO y bloqueo

Si hay variantes → pueden coexistir


Resolución de conflictos: MERGE, REPLACE o SPLIT, con resultado final aprobado o rechazado.


---

Runtime del sistema

El sistema mantiene un estado global con fase actual, versión de índice, ciclo y estado general (RUNNING, PAUSED, HOLD, DONE o FAILED).

El pipeline sigue estas fases:

1. INDEXING (solo una vez)


2. EXTRACTION (cubre 100% del índice aprobado)


3. CLASSIFICATION


4. FUSION


5. AUDIT_1 (consistencia interna)


6. AUDIT_2 (integridad y cobertura)


7. FACTS (generación de fichas)


8. WAIT_APPROVAL (decisión del Director)


9. DONE o RE_INDEXING en caso de rechazo



RE_INDEXING incrementa versiones y guarda snapshots del sistema.


---

Ejecución y control

El sistema es determinista, idempotente y con checkpointing activo.
El mismo input siempre produce el mismo output.

Se registran snapshots en cada reindexación y se mantiene trazabilidad completa.


---

Observabilidad

El sistema incluye:

tracking de cobertura

tracking de conflictos

modo replay

event stream con eventos como creación de items, clasificación, fusiones, conflictos, aprobaciones y decisiones del Director

logs específicos para fusiones, conflictos, variantes y trazas



---

Outputs generados

El pipeline produce:

RAW_MAP (desde extracción)

CLASSIFICATION_LAYER (clasificación)

ONTOLOGY_LAYER (fusión)

AUDIT_REPORT (auditorías)

EXECUTION_READY (fase final FACTS)



---

Políticas críticas del sistema

Reglas esenciales:

INDEXING ocurre solo una vez

EXTRACTION debe cubrir el 100% del índice

Sin evidencia textual no hay item explícito

Confianza menor a 0.6 pasa automáticamente a PENDING

duplicados nunca se eliminan, solo se fusionan

conflictos deben resolverse explícitamente

dependencias hard bloquean aprobación

ejecución completamente idempotente

sin aprobación del Director el sistema se detiene



---

