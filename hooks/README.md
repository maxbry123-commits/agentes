# 🪝 Hooks — automatización (NO son skills)

> Documento canónico: prompt M3 DSL DAG SHERIFF V7, sección E.

## Diferencia clave
- **Skill** = algo que un agente **carga y ejecuta** bajo demanda.
- **Hook** = función que el **gateway** llama automáticamente en un momento puntual.

## Catálogo (6 hooks)

| hook | cuándo se dispara | puede... | uso típico |
|------|-------------------|----------|------------|
| `before_tool_call`    | Antes de ejecutar una tool | bloquear, loggear, mutar args | validar permisos, PII redaction |
| `before_agent_reply`  | Antes de enviar la respuesta al usuario | mutar, truncar, agregar footer | inyectar TODOs pendientes, formato Max (≤6 líneas) |
| `/new`                | Cuando el usuario lo tipea | crear sesión limpia | reset de contexto |
| `/reset`              | Cuando el usuario lo tipea | borrar memoria de la sesión | empezar de cero |
| `on-gateway-start`    | Al arrancar el gateway | cargar config, init registries | precargar skills prioritarios |
| `on-task-end`         | Cuando una tarea termina | loggear métricas, persistir memory | alimentar el memory registry |

## Estructura

```
hooks/<nombre>/
├── README.md      # contrato + ejemplo
├── hook.yaml      # manifest (cuándo se dispara, args, output)
└── handler.py     # spec del handler (NO se ejecuta en sandbox)
```

## Estado
- 6/6 carpetas creadas con README + hook.yaml + handler.py.
