# Agente YAIWES — Guía maestra (yaiwes-omega) + reglas de despliegue

**Repo:** maxbry123-commits/agentes · **rama:** `main`

**Guía completa (secciones 0–7: estructura, I/O C-19, catálogos):**  
https://github.com/maxbry123-commits/agentes/blob/a082104e76247c79539b675b129c582bb9b00837/agente-yaiwes/README.md

**Raíz nueva de despliegue:**  
https://github.com/maxbry123-commits/agentes/tree/main/despliegue

**Wordflow programming operativo:**  
https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/engine/code_path_runner.py

**PIPELINE (docs / CURSOR puntos):**  
https://github.com/maxbry123-commits/agentes/tree/main/PIPELINE

---

## §8 — Dónde van los YAML de despliegue

Separar artefactos de despliegue en `despliegue/` evita contaminar `wordflow/` y permite auditoría forense.

### Tres conceptos separados

```text
REPO/
├── .github/workflows/     ← SOLO lo que GitHub ejecuta (obligatorio físico aquí)
├── despliegue/            ← contratos, manifiestos, validadores, evidencia
│   ├── github/workflows/  ← índice/punteros (NO ejecutable solo)
│   ├── schemas/
│   ├── manifests/
│   ├── validators/
│   └── auditoria/
└── wordflow / extensions / agente-yaiwes/  ← sistema / ingeniería
```

### Limitación GitHub Actions

Workflows ejecutables **deben** vivir en `.github/workflows/`.  
Poner solo `despliegue/github/workflows/deploy_c0.yml` **no** hace que GitHub los ejecute.

### Regla

| Ubicación | Rol |
|-----------|-----|
| wordflow / agente-yaiwes / extensions | el **sistema** |
| **despliegue/** | mecanismo declarativo, contratos y **evidencia** |
| **.github/workflows/** | puente mínimo que GitHub detecta y ejecuta |

### Auditoría en `despliegue/auditoria/`

versión desplegada · commit SHA · checksums · manifiesto · schema · resultado validación · correspondencia YAML↔código · qué se ejecutó · fecha/versión.

### Enlaces despliegue

- https://github.com/maxbry123-commits/agentes/tree/main/despliegue
- https://github.com/maxbry123-commits/agentes/blob/main/despliegue/README.md
- https://github.com/maxbry123-commits/agentes/blob/main/despliegue/github/workflows/INDEX.md
- https://github.com/maxbry123-commits/agentes/tree/main/.github/workflows
- https://github.com/maxbry123-commits/agentes/blob/main/despliegue/schemas/deployment.schema.yaml
- https://github.com/maxbry123-commits/agentes/tree/main/despliegue/auditoria

**Hecho en main:** raíz `despliegue/` creada; **no** se movieron YAML fuera de `.github/workflows/` (seguirían sin correr).
