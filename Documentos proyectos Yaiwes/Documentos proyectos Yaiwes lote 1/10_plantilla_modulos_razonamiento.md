# Plantilla: cómo calificar e incorporar un módulo de razonamiento al kernel
**Extiende el Enchufe Universal v2.0 (Fables) — no lo reemplaza, agrega una 4ta categoría de ficha**

## 0. Qué es y qué NO es un "módulo de razonamiento" (la distinción que ya hiciste bien)

| | Módulo de CONOCIMIENTO (lo que rechazaste) | Módulo de RAZONAMIENTO (lo que buscas) |
|---|---|---|
| Contenido | Hechos de un dominio (precios, medicina, leyes) | Una forma genérica de mirar cualquier problema |
| Sirve para | Un tipo de tarea | Todos los tipos de tarea |
| Ejemplo | "El descuento del 20% sube ventas" | "¿Qué pasa si invierto el objetivo?" |
| Crece por | Investigación de dominio | Añadir una nueva LENTE de pensar |

## 1. Las 4 pruebas de calificación (antes de aceptar cualquier bloque nuevo)

Un bloque de código o una idea **solo** se convierte en módulo de razonamiento si pasa las 4:

### Prueba 1 — Independencia de dominio (la más importante)
Aplica el módulo, sin cambiar su estructura, a 3 problemas de dominios completamente distintos (ej. un problema de código, uno de logística, uno personal). Si en los 3 sigue teniendo sentido y genera una pregunta/instrucción útil, pasa. Si solo funciona en uno, **es conocimiento, no razonamiento — se rechaza.**

### Prueba 2 — No redundancia
Corre el módulo nuevo contra el mismo problema de prueba junto con 3 módulos ya existentes en el banco. Si su resultado es casi idéntico a uno que ya tienes, **se rechaza o se fusiona** con el existente — no se duplica.

### Prueba 3 — Es una instrucción accionable, no una idea vaga
Debe poder escribirse como una pregunta o instrucción concreta que el LLM puede seguir literalmente. "Piensa mejor" no pasa. "Antes de responder, identifica qué supuesto estás dando por sentado y pregúntate qué pasa si es falso" sí pasa.

### Prueba 4 — Costo declarado
Como correrá en paralelo junto a otros módulos (vía tu Multi-API Fabric), debe declarar un presupuesto estimado de tokens/tiempo, igual que cualquier otra ficha del Enchufe Universal.

Si falla cualquiera de las 4, no entra al banco — ni se adapta, ni se fuerza. Se descarta con el motivo anotado.

## 2. La ficha del módulo de razonamiento (extiende el schema v2.0 que ya tienes)

No es un tipo de ficha nuevo desde cero — es la misma ficha del Enchufe Universal, con estos valores fijos y un bloque adicional:

```yaml
categoria: transversal      # siempre, porque sirve a cualquier tarea
etapa: T                    # siempre
ejecucion:
  kind: llm                 # es un patrón de pensamiento, no código puro
  runtime_type: llm
  llm_ratio: 1.0

# --- Bloque nuevo, específico de razonamiento ---
cognicion:
  patron_generico: string        # nombre corto, ej. "inversion_objetivo"
  descripcion: string             # la instrucción/pregunta accionable (Prueba 3)
  dominios_prueba:                # evidencia de la Prueba 1 (mínimo 3, distintos)
    - dominio: string
      resultado_util: boolean
  prueba_no_redundancia:          # evidencia de la Prueba 2
    comparado_contra: [string]    # ids de módulos existentes usados en la comparación
    similitud_maxima: number      # 0.0-1.0, debe ser < 0.6 para pasar
  fase_uso:                       # en qué paso del ciclo SELECT/ADAPT/IMPLEMENT entra
    enum: [select, adapt, implement]
  presupuesto:
    max_tokens: integer
    max_ms: integer
```

Esto valida con el mismo `validator_v2.py` que ya tienes — solo agrega una función `validar_cognicion(ficha)` que revisa el bloque nuevo con las 4 pruebas como invariantes (`C01_independencia_dominio`, `C02_no_redundante`, `C03_accionable`, `C04_presupuesto`), siguiendo el mismo patrón `I01`, `I02`... que ya usa el validador.

## 3. Dónde vive (usando tu árbol existente, ninguna carpeta nueva rara)

```
reasoning-kernel/
└── decision-on-demand/
    ├── prompts/                    ← ya existe (Mythos, EURS, DRE)
    └── reasoning_modules/          ← NUEVO, un archivo = un módulo
        ├── inversion_objetivo.yaml
        ├── trabajar_hacia_atras.yaml
        ├── caso_extremo.yaml
        ├── cuestionar_supuestos.yaml
        └── ... (crece indefinidamente, nunca se edita uno viejo)
```

Cada archivo se registra en el `PluginRegistry` con su propio slot, exactamente como cualquier otro plugin del Enchufe Universal — la diferencia es que su "categoria" siempre es `transversal` y vive en esta subcarpeta en vez de en `capability-registry/`.

## 4. Quién decide cuáles usar en cada tarea (no construyas nada nuevo — reutiliza lo que ya tienes)

El componente que ya tienes llamado `expert-panel-router` es exactamente el que debe hacer el **SELECT**: en vez de solo enrutar entre workflows, ahora también recorre `reasoning_modules/` y elige cuáles N módulos aplican a la tarea entrante. El flujo completo:

```
Tarea entra
  → expert-panel-router hace SELECT sobre reasoning_modules/ (elige 4-8 módulos)
  → decision-on-demand hace ADAPT (reescribe cada módulo para esta tarea específica)
  → Multi-API Fabric en modo SPLIT corre los módulos adaptados en paralelo
  → verdict-authority (tu Judge) rankea o agrupa las respuestas resultantes
  → salida: no una respuesta, sino el abanico rankeado
```

No es una capa nueva del kernel — es el mismo `expert-panel-router` + `decision-on-demand` + `Multi-API Fabric` + `verdict-authority` que ya diseñaste, apuntando a una carpeta nueva de contenido. Cero componentes nuevos que inventar, solo esta ficha y esta carpeta.

## 5. Ejemplo completo de una ficha real, lista para usar como plantilla

```yaml
artifact_id: reasoning.inversion_objetivo
version: 1.0.0
estado: active
categoria: transversal
etapa: T
contrato:
  rol: service
ejecucion:
  kind: llm
  runtime_type: llm
  llm_ratio: 1.0
cognicion:
  patron_generico: inversion_objetivo
  descripcion: >
    Antes de proponer una solución, identifica el objetivo declarado e
    invierte su dirección por completo. Pregunta: "¿qué acciones concretas
    producirían exactamente lo OPUESTO de lo que quiero?" Luego pregunta
    cuáles de esas acciones ya está haciendo el sistema actual sin darse
    cuenta, y elimínalas primero.
  dominios_prueba:
    - dominio: ventas
      resultado_util: true
    - dominio: depuración_de_código
      resultado_util: true
    - dominio: planificación_personal
      resultado_util: true
  prueba_no_redundancia:
    comparado_contra: [reasoning.cuestionar_supuestos, reasoning.caso_extremo]
    similitud_maxima: 0.3
  fase_uso: implement
  presupuesto:
    max_tokens: 400
    max_ms: 8000
seguridad:
  sandbox: none
  limites:
    timeout_ms: 8000
firma:
  gpg_key_id: PENDIENTE
```

Con esta plantilla, cada vez que se te ocurra o encuentres una forma nueva de pensar (leyendo, viendo cómo resuelve algo un humano, o incluso extrayéndola de cómo Kimi K2 o Grok abordaron un problema distinto), solo llenas este mismo formulario, corre las 4 pruebas, y si pasa, se enchufa — sin tocar ni un solo módulo de los que ya existen.
