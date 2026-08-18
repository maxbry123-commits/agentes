# ARQUITECTURA_WORDFLOW_LIVE.md — actualizado en paralelo T0+
**Fecha inicio:** 2026-08-17  
**Última actualización:** 2026-08-17 20:51  
**Estado:** PARCIAL — se completa en cada salida según archivos/mods  
**Fuente diseño base:** 🎯🔒 arquitectura final TEAM YAIWES + Wordflow (15-ago) + A1-A12 ACQUIRE-OS + PIPELINE/00_METODO

## Diseño obligatorio (literal del doc cerrado)
```
TEAM YAIWES
  CORE KERNEL
       │
  KERNEL EXTENSION  ← CONTROL + WORKFLOW (StateMachine, Planner, Policies, Knowledge, Adapters, Validator, Recovery, Checkpoints)
       │
  UNIFIED RUNTIME
    ├── HERMES ENGINE (Adapter)
    └── OPENCLAW ENGINE (Adapter)
       │
  COMMON INTERFACE → tools / models / sandbox
```
No fusion física de códigos → solo contratos AgentRuntime (initialize/execute/pause/checkpoint/get_state).

## 6 niveles (de PIPELINE/00)
1 DEFINITION | 2 CONTROL | 3 EXECUTION | 4 STATE | 5 EVIDENCE | 6 EXTENSIONS

## T0 Motors nativos (kernel extension / sub-Wordflow)
1. Motor SEND: docs/code → otras cuentas/repos GitHub (bridge EXTERNAL_GH_B_TOKEN + credential_ref)
2. Motor CALL: tools/code de otros repos (multi-account caller + trazabilidad)
3. Motor DOWNLOAD: software/framework → repo destino Cuenta B (mejora del acquire parcial)
4. Motor KERNEL-EXT: los 3 anteriores + recepción/conversión nativos como extensión cargable

## Estado actual T0
- [parcial] Método trabajo (PIPELINE/00 ya existe)
- [DONE] Reception template + reception real agentes
- [DONE skeleton] 4 motors en extensions/wordflow/motors/{send,call,download,kernel_ext}
- [ ] Bridge full + reception real otros repos clave
- [parcial] Arquitectura live este MD (actualizado)

## Próximo
Reception real en osquestador-auditor + comand-Center + full execute motors + T2.
