# Setup token Cuenta B — solo móvil (1 paso)

## Toca este enlace

**Crear secret (pega el token SOLO en esa pantalla de GitHub):**

https://github.com/maxbry123-commits/agentes/settings/secrets/actions/new

| Campo | Valor exacto |
|-------|----------------|
| Name | `GITHUB_EXTERNAL_B_TOKEN` |
| Secret | *(tu token — solo ahí, nunca en el chat)* |

Guarda.

## Después del secret

En el chat dile al agente **solo**:

```text
owner: abc1tienda-web
repo: NOMBRE_EXACTO
branch: main
```

(sustituye owner/repo por los reales)

El código ya espera el secret con ese nombre. No hace falta PC ni Contabo ni pegar el token en el chat.

## Comprobar (opcional)

Actions → workflow `validate-external-github` → Run workflow
(solo verifica que el secret existe y la API responde; no imprime el token)
