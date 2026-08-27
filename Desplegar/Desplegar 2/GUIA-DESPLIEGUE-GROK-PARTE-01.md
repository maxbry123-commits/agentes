# GUÍA DE DESPLIEGUE PARA GROK — PARTE 1
**Cubre: A1 (Núcleo) + A2 (Research Engine) + A3 (DAG/Sheriff). Objetivo de esta parte: código en GitHub, funcionando y probado. Nada de HF todavía. Nada de documentos explicativos para el Director todavía.**

---

## 0 · Quién eres y qué vas a hacer

Eres el ejecutor. No rediseñas, no reinterpretas, no mejoras nada de lo que viene en A1/A2/A3 — lo despliegas tal como está especificado. Si algo es ambiguo, lo marcas y sigues con lo que sí es claro — no lo resuelves por tu cuenta (regla E14 del runtime UOOS Parte 2 que ya tienes).

**Orden de prioridad de todo el proyecto, sin excepción:**
```
1º GitHub (código funcionando y probado)
2º HF (despliegue a los 5 Spaces)
3º Documentos MD explicativos para el Director
```
Esta Parte 1 de la guía es exclusivamente el paso 1º.

---

## 1 · Preparación — antes de tocar código

**Repositorio destino:** `agentes` (nunca `command-center` — nombre arrastrado de otro proyecto, ya corregido).

**Estructura raíz a crear si no existe:**
```
agentes/
├── control-layer/
│   └── workflow_core/
│       ├── __init__.py
│       ├── errors.py
│       ├── enums.py
│       ├── contracts.py
│       ├── events.py
│       ├── state.py
│       ├── state_machine.py
│       ├── store.py
│       ├── dag.py
│       ├── sheriff.py
│       ├── policies.py
│       ├── dag_patch.py
│       └── research.py
├── tests/
│   ├── test_state_machine.py
│   ├── test_dag.py
│   ├── test_sheriff.py
│   └── test_dag_patch.py
└── pyproject.toml
```

**Temporal:** descarga el binario oficial de Temporal (`temporal` CLI/server) — todavía no lo conectes a nada, solo verifica que existe y corre (`temporal --version`). Se conecta de verdad más adelante, cuando llegue el grupo de Recuperación/Loop. No lo instales dentro de ningún Space de HF — Temporal vive en HF1 exclusivamente, nunca en los HF2-5 (son Spaces ligeros de modelos/agentes).

---

## 2 · Desplegar A1 — Núcleo

Fuente: los 4 documentos `A01-nucleo-doc1..4`.

1. Extrae cada bloque de código Python de los 4 documentos hacia su archivo correspondiente (el nombre del archivo está indicado justo antes de cada bloque, ej. `# store.py`).
2. `pyproject.toml` va en la raíz del proyecto (documento 1).
3. `enums.py`, `errors.py`, `contracts.py`, `state.py`, `state_machine.py` van en `control-layer/workflow_core/` (documentos 1 y 2).
4. `events.py`, `store.py`, `__init__.py` van en el mismo directorio (documento 4).
5. `test_state_machine.py` va en `tests/` (documento 3).
6. Corre los 3 tests. Los 3 deben pasar antes de continuar — si alguno falla, no sigas a A2, repórtalo.

## 3 · Desplegar A2 — Research Engine

Fuente: los 4 documentos `A02-research-doc1..4`.

Nota: esta salida es mayormente contratos e interfaces (Protocol), no un paquete tan grande como A1. Une los bloques de código de `SkillRequirement`, `ResearchRequest`, `ResearchFinding`, `RepositoryResolver`, `SandboxProvider` (Protocol), `MemoryProvider` (Protocol) en un único archivo `control-layer/workflow_core/research.py`. Si al juntarlos supera 200 líneas, sepáralos en `research.py` + `research_contracts.py` — L02 es innegociable, la organización exacta dentro de esa regla queda a tu criterio.

No hay tests propios en esta salida — son solo contratos, se prueban indirectamente cuando algo los implemente (grupos futuros).

## 4 · Desplegar A3 — DAG y Sheriff

Fuente: los 4 documentos `A03-dag-sheriff-doc1..4`.

1. `dag.py`, `sheriff.py`, `policies.py`, `dag_patch.py` van en `control-layer/workflow_core/` (documentos 1, 2 y 4).
2. `test_dag.py`, `test_sheriff.py` (si no vino explícito, créalo con el mismo patrón de los otros tests) y `test_dag_patch.py` van en `tests/`.
3. Corre los tests: DAG válido pasa, DAG con ciclo se rechaza (`ContractViolationError`). Los dos casos deben comportarse exactamente así.

---

## 5 · Commit y push — sigue el Git Workflow ya especificado

No inventes el flujo de Git — ya está documentado completo (`plan-grock-despliegue-01/02/03`). En resumen para esta primera entrega:

```
branch: workflow/A1-A3-nucleo-dag-sheriff
commit: "workflow(a1-a3): núcleo determinista + dag + sheriff"
```
Un solo PR para A1+A2+A3 juntos (son la base indivisible — no tiene sentido fusionar A1 sin A3, ya que A3 importa de A1). Antes de abrir el PR: confirma que los 6+ tests pasan localmente. El PR debe poder mergear sin tocar `main` directamente en ningún momento del proceso.

---

## 6 · Qué NO hacer todavía

- No toques ningún HF (ni HF1 ni HF2-5) — eso es la Parte 3 de esta guía, más adelante.
- No generes documentación explicativa para el Director — eso es la Parte 4, al final.
- No conectes Temporal a ningún workflow real todavía — solo confirma que el binario existe.
- No avances a G4 (Capa de Control) por tu cuenta — esa salida sigue en construcción del lado del Director/Claude, todavía no está lista para desplegar.

---

## 7 · Qué sigue (Parte 2 de esta guía)

Cuando el Director confirme que A1-A3 quedaron desplegados y con los tests pasando en CI, llega la Parte 2 — cubrirá el siguiente bloque de salidas (Capa de Control completa) con el mismo formato: extracción de código, ubicación exacta, tests, commit/push.

---

*Fin de la Guía de Despliegue — Parte 1. Repositorio: `agentes`. Alcance: A1+A2+A3, solo GitHub.*
