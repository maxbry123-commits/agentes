# ARQUITECTURA_WORDFLOW_LIVE.md — actualizado en paralelo T0+
**Fecha inicio:** 2026-08-17  
**Última actualización:** 2026-08-17 20:53  
**Estado:** PARCIAL  
**Fuente diseño base:** 🎯🔒 arquitectura final TEAM YAIWES + Wordflow (15-ago) + A1-A12 + PIPELINE/00_METODO

## Diseño obligatorio
```
TEAM YAIWES → CORE KERNEL → KERNEL EXTENSION (CONTROL+WORKFLOW) → UNIFIED RUNTIME (Hermes/OpenClaw adapters) → COMMON INTERFACE
```
Contratos AgentRuntime solo. 6 niveles: DEFINITION | CONTROL | EXECUTION | STATE | EVIDENCE | EXTENSIONS

## T0 Motors nativos
1. SEND  2. CALL  3. DOWNLOAD  4. KERNEL-EXT (+ recepción)

## Estado T0
- [DONE] Skeleton 4 motors (agentes/extensions/wordflow/motors/)
- [DONE] Reception template + real: agentes, osquestador-auditor, comand-Center
- [parcial] Método trabajo + bridge
- [parcial] Arquitectura live este MD

## Próximo
Full execute motors + T2 reception/conversion motor + más receptions.
