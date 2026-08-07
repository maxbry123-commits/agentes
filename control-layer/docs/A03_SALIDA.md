# A03 COMPLETA · rules · graph · reverse · compiler

## Entregables

- `rules/routing.yaml` · `modifiers.yaml` · `dependencies.yaml`
- `rules.py` · `graph.py` · `reverse.py` · `compiler.py`
- `tests/test_compiler.py`

## Pipeline

```
fingerprint → threat → base routes → modifiers → graph deps → reverse → ContractSet
```

## Checks

- [x] 0% LLM
- [x] mismo input → mismo set_hash
- [x] WRITE+secret → CREDENTIAL_ACCESS + C47
- [x] ciclos → CycleError
- [x] reverse C47 sin secret → ERROR_DE_CLASIFICACION (strict)

## Siguiente

**A04** — Sentinela/Router de schemas
