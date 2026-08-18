# ARQUITECTURA_WORDFLOW_LIVE.md — T0+
**Última actualización:** 2026-08-17 21:16  
**Estado:** T0 skeleton ~90%  
**Fuente:** 🎯🔒 arquitectura final TEAM YAIWES (15-ago) + A1-A12 + PIPELINE/00

## Diseño obligatorio
TEAM YAIWES → CORE KERNEL → KERNEL EXTENSION (CONTROL+WORKFLOW) → UNIFIED RUNTIME (Hermes/OpenClaw adapters) → COMMON INTERFACE
Contratos AgentRuntime. 6 niveles: DEFINITION | CONTROL | EXECUTION | STATE | EVIDENCE | EXTENSIONS

## T0 Motors nativos (DONE skeleton)
1. SEND READY  2. CALL READY  3. DOWNLOAD READY  4. KERNEL-EXT READY (get_reception_link incluido)

## Reception + Knowledge
- 3 repos ✅ + KNOWLEDGE_RECEPTION_LINKS.md ✅
- Agente sabe recuperar enlace si se pierde

## Estado T0
- [DONE] 4 motors + knowledge recovery
- [DONE] Reception 3 repos
- [parcial] Bridge full + método universal copy a más repos
- [parcial] Este MD

## Próximo (T2)
Reception/conversion motor: leo literal → gaps → ruta exacta + PLUGIN + md→py/json.
