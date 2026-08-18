# ARQUITECTURA_WORDFLOW_LIVE.md — T0+
**Última actualización:** 2026-08-17 21:17  
**Estado:** T0 motors+reception+knowledge = DONE  
**Fuente:** 🎯🔒 arquitectura final TEAM YAIWES (15-ago) + A1-A12 + PIPELINE/00

## Diseño obligatorio
TEAM YAIWES → CORE KERNEL → KERNEL EXTENSION (CONTROL+WORKFLOW) → UNIFIED RUNTIME (Hermes/OpenClaw adapters) → COMMON INTERFACE
Contratos AgentRuntime. 6 niveles: DEFINITION | CONTROL | EXECUTION | STATE | EVIDENCE | EXTENSIONS

## T0 Motors nativos = DONE
1. SEND READY  2. CALL READY  3. DOWNLOAD READY  4. KERNEL-EXT READY (get_reception_link)

## Reception + Knowledge = DONE
- agentes / osquestador-auditor / comand-Center
- KNOWLEDGE_RECEPTION_LINKS.md → agente recupera enlace si se pierde

## Residual T0
- [ ] Bridge full (EXTERNAL_GH_B_TOKEN end-to-end test)
- [ ] Método trabajo universal copiado a más repos

## Próximo
T2 reception/conversion motor (leo literal → gaps → ruta exacta + PLUGIN).
