# Auditoría TEAM/SDPA 01 — STRUCTURE X-Ray

**Corte:** 2026-09-01 · **Repo:** `maxbry123-commits/agentes@main`  
**Índice:** [Arquitectura fusionada YAIWES](https://github.com/maxbry123-commits/agentes/blob/main/README-ARQUITECTURA-FUSIONADA-YAIWES-XRAY-2026-09-01.md)  
**Siguiente:** [02 — Conectividad](https://github.com/maxbry123-commits/agentes/blob/main/AUDITORIA-TEAM-SDPA-02-CONECTIVIDAD-XRAY-2026-09-01.md)

## Alcance y fuentes

Cruce del árbol Git completo (12.461 entradas) con:
- `PIPELINE/03_TEAM_KERNEL_PARTE1.md`
- `PIPELINE/06_PERFIL_MAESTRO_TEAM_SEALS.md`
- `PIPELINE/10_KERNEL_THOUGHT_PROTOCOL.md`
- `PIPELINE/ARQUITECTURA_02_KERNEL.md`
- `SDPA_Architecture_Document.md` aportado por el Director
- Resumen SDPA aportado por el Director

## Localización del supuesto Agente TEAM

No existe una raíz ejecutable llamada `Agente TEAM/`, `TEAM Kernel/`, `Fables 5/` o `SDPA/`.

Las únicas rutas propias con TEAM en el nombre son documentos:

```text
main/
└── PIPELINE/
    ├── 03_TEAM_KERNEL_PARTE1.md
    └── 06_PERFIL_MAESTRO_TEAM_SEALS.md
```

La implementación más cercana está distribuida:

```text
main/
├── extensions/
│   ├── wordflow_kernel/                 código de plano de control
│   └── wordflow/                        runtime y hot path de programación
├── agente-yaiwes/
│   └── kernel-principal/                espejo/scaffold del kernel
├── control-layer/                       contratos, council y evolution
└── PIPELINE/                             arquitectura y claims
```

No hay evidencia de autoría técnica verificable de “Fables 5” en nombres de archivos, manifests o rutas. Sí hay documentos TEAM de diseño. Por tanto, la atribución a Fables 5 queda **NO VERIFICADA**.

## Conteo físico

| Raíz | Entradas | Archivos | Python | Tests Python | Placeholders | Diagnóstico |
|---|---:|---:|---:|---:|---:|---|
| `extensions/wordflow_kernel/` | 112 | 101 | 94 | 27 | 1 | Código real, parcial |
| `agente-yaiwes/kernel-principal/` | 94 | 71 | 49 | 0 | 18 | Espejo + scaffold incompleto |
| `extensions/wordflow/engine/` | 115 | 113 | 113 | 0 dentro de esa subraíz | Hot path real |
| `Agente core kernel Yaiwes principal/` | 504 | 504 | 0 | 0 | 0 | 502 ZIP; almacén, no kernel |

## Árbol localizado hasta cuatro niveles

```text
extensions/
└── wordflow_kernel/
    ├── gateway/
    │   ├── intelligence.py
    │   ├── router_http.py
    │   └── openclaw_http.py
    ├── engines/
    │   ├── port.py
    │   ├── openclaw_stub.py
    │   └── hermes_stub.py
    ├── reception/
    │   ├── convert.py
    │   └── git_apply.py
    ├── resources/
    │   ├── registry.py
    │   ├── factory.py
    │   └── loaders
    ├── stages/
    │   ├── engine.py
    │   ├── kernel_hook.py
    │   └── default_handlers.py
    ├── tests/
    │   └── 27 tests Python
    ├── workflow.py
    ├── runtime.py
    ├── instance.py
    ├── instance_store.py
    ├── ledger.py
    ├── checkpoint.py
    ├── forensic.py
    └── fail_closed.py

agente-yaiwes/
└── kernel-principal/
    ├── extension-kernel/
    │   ├── capability-registry/
    │   ├── capability-passport/
    │   ├── abi-mount/
    │   ├── native-learning/
    │   └── mount-guard/
    ├── reasoning-kernel/
    │   ├── expert-panel-router/
    │   ├── decision-on-demand/
    │   ├── consensus-trigger/
    │   ├── goal-dual-driver/
    │   └── workflow-capacity/
    ├── resource-governance/
    │   ├── resource-broker-gate/
    │   ├── circuit-breaker/
    │   ├── lease-management/
    │   ├── retry-policy/
    │   └── watchdog/
    ├── kernel-router/
    ├── stages/
    ├── runtime.py
    └── workflow.py
```

## Hallazgos STRUCTURE

1. `agente-yaiwes/kernel-principal/runtime.py` tiene el mismo blob SHA que `extensions/wordflow_kernel/runtime.py`.
2. `agente-yaiwes/kernel-principal/workflow.py` tiene el mismo blob SHA que `extensions/wordflow_kernel/workflow.py`.
3. Esto demuestra copia/espejo, no dos kernels independientes.
4. Dieciocho placeholders permanecen dentro de `kernel-principal`, incluidos nodos críticos de razonamiento, consenso, estado interno y gobierno de recursos.
5. La carpeta de 148 componentes/ZIP no es ejecución ni cableado.
6. TEAM existe como arquitectura documental, pero no como paquete único instalable o runtime autónomo.

## Veredicto

**STRUCTURE: FAIL-CLOSED / PARCIAL.**  
La base de código existe y es reutilizable, pero el TEAM Kernel descrito no está materializado como una raíz coherente, completa, testeada y atribuible.