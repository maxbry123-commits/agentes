# Agente YAIWES — Guía maestra de estructura (yaiwes-omega)

**Repo:** maxbry123-commits/agentes  
**Rama operativa:** `main`  
**Regla de trabajo:** NO reescribir código existente. Solo copiar (M1–M5) o crear PLACEHOLDER si el nodo no existe.  
**Wordflow de programación de code operativo (sigue vivo en main):**  
- Hot path: [`extensions/wordflow/engine/code_path_runner.py`](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py)  
- Pipeline: [`extensions/wordflow/engine/programming_pipeline.py`](https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/programming_pipeline.py)  
- Tests: [`extensions/wordflow/tests/`](https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow/tests)  
- Docs PIPELINE: [`PIPELINE/`](https://github.com/maxbry123-commits/agentes/tree/main/PIPELINE)

**Método de copia obligatorio:** [`METODO_ZIP_COPY_DETERMINISTA.md`](https://github.com/maxbry123-commits/agentes/blob/main/METODO_ZIP_COPY_DETERMINISTA.md)

**Raíz de despliegue (nueva):** [`despliegue/`](https://github.com/maxbry123-commits/agentes/tree/main/despliegue) — ver **§8**.

---

## 0. Propósito de esta raíz `agente-yaiwes/`

Esta raíz es la **arquitectura en cascada** del Agente YAIWES (estructura lógica **yaiwes-omega**):

1. Organiza lo ya construido en el repo sin apagar el monolito operativo.
2. Separa el **motor de programación de code** (`code-programming-engine`) como pieza única compartida.
3. Deja nodos ausentes como carpetas + `PLACEHOLDER.md` (escalable, sin inventar implementación).
4. Sirve de guía de verificación cruzada: esqueleto 1 + esqueleto 2 + raíces reales de wordflow.

**Intocable durante reorganización:** el monolito en `main` (`code_path_runner.py` tal como está) sigue siendo la única fuente operativa real hoy.

---

## 8. Dónde van los YAML de despliegue (organización obligatoria)

Separar los artefactos de despliegue en una raíz `despliegue/` es la solución canónica: evidencia forense y verificación cruzada **sin contaminar** `wordflow/` ni `agente-yaiwes/`.

### 8.1 Tres conceptos separados

```text
REPO/
│
├── .github/
│   └── workflows/
│       └── *.yml              ← puente/mecanismo que GitHub EJECUTA
│
├── despliegue/
│   ├── github/workflows/      ← solo ÍNDICE/punteros (NO ejecutable por sí solo)
│   ├── manifests/
│   ├── schemas/
│   ├── validators/
│   └── auditoria/
│
├── wordflow/ / extensions/wordflow / agente-yaiwes/
│   └── ...                    ← producto / ingeniería principal
│
└── PIPELINE/                  ← docs (incl. programming); no runtime Actions
```

### 8.2 Limitación de GitHub Actions

Un workflow que quieras que GitHub ejecute automáticamente debe estar **físicamente** en:

```text
.github/workflows/
```

**No** basta con:

```text
despliegue/github/workflows/deploy_c0.yml
```

GitHub **no** lo ejecutará como workflow normal si solo está ahí.

### 8.3 Regla de arquitectura

| Ubicación | Contiene |
|-----------|----------|
| **wordflow / agente-yaiwes / extensions** | el **sistema** (producto e ingeniería) |
| **despliegue/** | el **mecanismo declarativo**, contratos, validadores y **evidencia** de despliegue |
| **.github/workflows/** | **únicamente** lo que GitHub necesita detectar y ejecutar (puente mínimo) |

- `.github/workflows/*.yml` = entrada obligatoria de GitHub (lógica de disparo fina).
- `despliegue/` = repositorio técnico del despliegue y auditoría (manifiestos, schema, validadores, checksums, verification).
- La lógica declarativa, contratos y evidencias **permanecen** en `despliegue/`.

### 8.4 Qué debe conservar `despliegue/auditoria/` (forense)

1. versión exacta desplegada  
2. commit SHA  
3. hashes / checksums  
4. manifiesto del despliegue  
5. schema utilizado  
6. resultado de validación  
7. correspondencia entre YAML y código  
8. evidencia de qué se ejecutó  
9. fecha / versión de la ejecución  

### 8.5 Enlaces de esta organización

| Recurso | URL |
|---------|-----|
| Raíz `despliegue/` | https://github.com/maxbry123-commits/agentes/tree/main/despliegue |
| README despliegue | https://github.com/maxbry123-commits/agentes/blob/main/despliegue/README.md |
| Índice workflows (punteros) | https://github.com/maxbry123-commits/agentes/blob/main/despliegue/github/workflows/INDEX.md |
| Workflows ejecutables GitHub | https://github.com/maxbry123-commits/agentes/tree/main/.github/workflows |
| Schema deployment | https://github.com/maxbry123-commits/agentes/blob/main/despliegue/schemas/deployment.schema.yaml |
| Auditoría | https://github.com/maxbry123-commits/agentes/tree/main/despliegue/auditoria |

**Estado:** raíz `despliegue/` creada en `main`. Los YAML de Actions **no se movieron** de `.github/workflows/` (seguirían sin ejecutarse). Solo índice + contratos + placeholders de evidencia.

---

## 1–7 (resto de la guía)

El contenido detallado de secciones 1–7 (estructura yaiwes-omega, mapa I/O C-19, catálogos, tests, enlaces programming) permanece en el historial del archivo y en commits previos de este README. Resumen operativo:

- Motor de programming: **fuera del kernel**, pieza `code-programming-engine` compartida.
- Runtime: extensión / wordflow-agente / motor solo + pool de instancias.
- Copia sin reescribir; placeholders con `PENDIENTE_CODE`.
- Docs CURSOR / 500+ puntos: carpeta [`PIPELINE/`](https://github.com/maxbry123-commits/agentes/tree/main/PIPELINE).

**Este README (actualizado §8):** https://github.com/maxbry123-commits/agentes/blob/main/agente-yaiwes/README.md
