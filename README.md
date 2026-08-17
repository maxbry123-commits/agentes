# agentes — YAIWES / Wordflow (Cuenta A · Sistema vivo)

**Fuente de verdad del código del sistema.** No saturar este repo con software externo ni datasets grandes.

## Arquitectura de cuentas y almacenamiento

```
CUENTA A  maxbry123-commits/agentes     ← este repo (Workflow, kernel, policies)
CUENTA A  maxbry-router / osquestador-auditor / MEMORIA
        │
        │ credential_ref (nunca token en git)
        ▼
CUENTA B  (ej. abc1tienda-web)          ← repos de software/forks/tools
        │
        │ clone / API download
        ▼
RUNTIME   VPS | HF Space | sandbox | container   ← aquí se EJECUTA
        │
HF        datasets | models | skills grandes
```

| Rol | Cuenta / sitio |
|-----|----------------|
| Sistema vivo (Wordflow, Router, Osquestador, Memoria) | **Cuenta A** |
| Almacén de software externo (no ejecuta) | **Cuenta B** |
| Datos / modelos grandes | **HuggingFace** |

Detalle: [`PIPELINE/53_MULTI_ACCOUNT_STORAGE_METHOD.md`](PIPELINE/53_MULTI_ACCOUNT_STORAGE_METHOD.md)

## Conector GitHub externo (Cuenta B)

- Código: `extensions/wordflow/connectors/github_external.py`
- Ejemplo config: `extensions/wordflow/connectors/external_accounts.example.yaml`
- Registry: `extensions/wordflow/accounts/` (`credential_ref` only)

El Director configura secretos en el entorno / secret store. **No pegar PAT en issues, chat ni commits.**

## Kernel / Wordflow

Ver [`extensions/wordflow_kernel/README_V1.md`](extensions/wordflow_kernel/README_V1.md)

## Plan activo V1

[`PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md`](PIPELINE/52_V1_PLAN_49_TAREAS_METODO_Y_XRAY.md)

## Repos hermanos (mismo método)

- https://github.com/maxbry123-commits/maxbry-router
- https://github.com/maxbry123-commits/osquestador-auditor
- https://github.com/maxbry123-commits/MEMORIA
