# A1 · NÚCLEO DETERMINISTA — Documento 1/4
**Bloques B1 (Manifest) + B2 (State) · UOOS Parte 1**
Fuente: `arquitectura_Wordflow.md`, Salida 1/13, líneas 1-791 · Modo A (código existente → paquete de despliegue)

---

## B1 · PROJECT_MANIFEST

```yaml
salida: A1 - Núcleo Determinista
serie: 1 de 19
modo: A
objetivo: >
  Base sobre la que se conecta todo lo demás. Contratos + estado +
  máquina de estados + eventos + store. Nada más.
alcance_explicito:
  no_conoce: [OpenCode, Cline, Claude, Temporal, Graphiti, GitHub, LLM, HTTP]
  solo_conoce: [contratos, estados, eventos]
regla_diseño: >
  "Workflow Core no conoce nada externo — evita convertir el núcleo
  en otro orquestador pesado" (fuente, línea 18)
dependencias_externas: []
python_version: ">=3.11"
propiedad_fundamental: "mismo estado + misma transición = mismo resultado"
grupos_que_dependen_de_este: [A3, G4, G5, G6, G7, G8, G9, G10, G11, G12, G13]
```

## B2 · state.json (estado de esta salida)

```yaml
grupo: A1
documento_actual: 1 de 4
estado: en_construcción
archivos_a_producir:
  - pyproject.toml
  - src/workflow_core/__init__.py
  - src/workflow_core/errors.py
  - src/workflow_core/enums.py
  - src/workflow_core/contracts.py
  - src/workflow_core/events.py
  - src/workflow_core/state.py
  - src/workflow_core/state_machine.py
  - src/workflow_core/store.py
  - tests/test_state_machine.py
loc_por_archivo:
  enums.py: 44
  errors.py: 20
  contracts.py: 88
  events.py: 33
  state.py: 51
  state_machine.py: 148
  store.py: 62
  init.py: 39
  test_state_machine.py: 67
archivos_que_exceden_200_loc: ninguno
verificación_l02: PASA
```

---

## Estructura del paquete

```
workflow/
├── pyproject.toml
├── src/workflow_core/
│   ├── __init__.py · errors.py · enums.py
│   ├── contracts.py · events.py
│   ├── state.py · state_machine.py
│   └── store.py
└── tests/
    └── test_state_machine.py
```

## pyproject.toml (literal)

```toml
[project]
name = "deterministic-workflow-core"
version = "0.1.0"
description = "Deterministic workflow control core"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "mypy>=1.10",
    "ruff>=0.5"
]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

El núcleo tiene deliberadamente cero dependencias externas.

---

*Siguiente: Documento 2/4 — B3 (Nodos/Contratos) + B4 (Máquina de estados).*
