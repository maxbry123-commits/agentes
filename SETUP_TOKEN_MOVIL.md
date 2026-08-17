# Setup token Cuenta B — móvil

## Nombre del secret (obligatorio)

**`EXTERNAL_GH_B_TOKEN`**

GitHub **prohíbe** nombres que empiecen por `GITHUB_`.
Por eso `GITHUB_EXTERNAL_B_TOKEN` no se guardaba.

## Enlace

https://github.com/maxbry123-commits/agentes/settings/secrets/actions/new

| Campo | Valor |
|-------|--------|
| Name | `EXTERNAL_GH_B_TOKEN` |
| Secret | tu token (solo en GitHub) |

## Después

En el chat (sin token):

```text
owner: ...
repo: ...
branch: main
```

## Check

Workflow: `check-external-token-secret`
