# despliegue/ — mecanismo, contratos y evidencia de despliegue

**Repo:** maxbry123-commits/agentes  
**Regla de arquitectura (canónica):**

```text
wordflow / agente-yaiwes / extensions  →  el sistema (producto / ingeniería)
despliegue/                            →  mecanismo, contratos y evidencia de despliegue
.github/workflows/                     →  SOLO lo que GitHub necesita detectar y ejecutar
```

## Limitación de GitHub Actions

Un workflow que GitHub debe **ejecutar** tiene que existir físicamente en:

```text
.github/workflows/*.yml
```

**No** se ejecuta si solo vive en `despliegue/github/workflows/`.

Por eso esta raíz **no reemplaza** `.github/workflows/`.  
Los YAML operativos permanecen en `.github/workflows/`.  
Aquí viven: contratos, manifiestos, validadores, auditoría, índices y evidencias.

## Estructura

```text
despliegue/
├── README.md                 ← este archivo
├── github/
│   └── workflows/
│       └── INDEX.md          ← índice + punteros a .github/workflows (NO copia ejecutable)
├── schemas/
│   └── deployment.schema.yaml
├── manifests/
│   └── README.md
├── validators/
│   └── README.md
└── auditoria/
    ├── README.md
    ├── checksums.yaml
    └── verification.yaml
```

## Qué conserva la auditoría forense en `despliegue/auditoria/`

- versión exacta desplegada
- commit SHA
- hashes / checksums
- manifiesto del despliegue
- schema utilizado
- resultado de validación
- correspondencia entre YAML y código
- evidencia de qué se ejecutó
- fecha / versión de la ejecución

## Workflows reales actuales (entrada GitHub)

Ver índice: [`github/workflows/INDEX.md`](./github/workflows/INDEX.md)

Path obligatorio de ejecución:
https://github.com/maxbry123-commits/agentes/tree/main/.github/workflows

## Relación con otras raíces

| Raíz | Rol |
|------|-----|
| `extensions/wordflow`, `agente-yaiwes` | sistema / ingeniería |
| `PIPELINE/` | documentación y listas programming (no runtime de Actions) |
| `despliegue/` | contratos + evidencia de deploy |
| `.github/workflows/` | puente mínimo que GitHub ejecuta |

**No contaminar** `wordflow/` ni `agente-yaiwes/` con scripts de deploy operativos; la evidencia y los contratos van aquí.
