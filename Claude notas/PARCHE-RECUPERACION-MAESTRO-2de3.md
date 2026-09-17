PARCHE DE RECUPERACION MAESTRO - SALIDA 2 DE 3 - 2026-09-17
Continua de PARCHE-RECUPERACION-MAESTRO-1de3.md

## INDICE COMPLETO - arquitectura wordflow loop code Yaiwes/ (20 archivos)

1. arquitectura wordflow loop code Yaiwes.md - indice + diagrama general
2. Parte 1 - Estructura completa runtime src.md - 60+ archivos catalogados
3. Parte 2 - Fase INTAKE y DAG.md - formato Glimmer
4. Parte 3 - Fase EXECUTION y GOVERNANCE CHAIN.md - formato Glimmer
5. Parte 4 - Fase RECOVERY y LEDGER.md - formato Glimmer
6. Parte 5 - UEK y Agent Fleet.md - formato Glimmer
7. Anexo - GAPS y mejoras pendientes.md - gaps 1-9
8. Anexo 2 - Pendientes nuevos y cobertura 100.md - gaps 11-19, cobertura 21/21
9. Anexo 3 - Estado real documentos Claude.md - los 20 docs son
   AUDITADO/PROPUESTA no integrado
10. Anexo 4 - Docfile y MCP y ambiguedades.md - definiciones + 3 ambiguedades
11. SCHEMA-refactorizacion.md - 15 reglas con fuente (Fowler/Beck/McCabe/Feathers)
12. SCHEMA-frontend-browser-verified.md - texto verbatim CODE+BROWSER+VISUAL PASS
13. SCHEMA-plantillas-RAG.md - biblioteca de templates antes de generar
14. PROMPT-Sol-investigar-capacidad-frontend-fleet.md
15. PROMPT-Sol-descarga-4-componentes-nuevos.md
16. RESOLUCION-3-pendientes.md - formato template, fusion Crazy Wall, clasificacion herramientas
17. DISENO-MCP-contexto-compartido.md
18. CONFIRMACION-4x-biblioteca.md - biblioteca antes de CUALQUIER schema/codigo
19. CONTRATO-skill-design-anthropic-frontend.md - gate SKILL_PASS obligatorio
20. DISENO-preguntas-siempre-activo-input-shark.md - 3 lugares: UI interface, UI backend, Input Shark

## LOS GAPS CRITICOS PENDIENTES DE CERRAR (consolidado de los 4 Anexos)

PRIORIDAD ALTA:
1. contracts/ y evidence/ (wordflow_loop/wordflow_loop/) VACIAS
2. 2 routers de agentes coexisten (agent_router.py debil vs
   agent_fleet_adapter.py robusto) - decision de deprecar el primero
   TOMADA, NO EJECUTADA
3. 7 archivos de gobernanza (sheriff/sentinel/judge/guardian/supervisor/
   validator/verifier) son de 389-804 bytes - CONTENIDO REAL SIN LEER,
   podrian ser stubs
4. 2 sistemas de Crazy Wall paralelos (raiz principal vs "Crazy Wall
   Orquestador/") - prompt de comparacion YA ESCRITO para Sol, sin ejecutar
5. Reorganizacion de raiz del repo (fusionar Skills/skills,
   Conecciones/conectividad, etc) APROBADA hace varios turnos, NO EJECUTADA

PRIORIDAD MEDIA:
6. checkpoint.py (recovery/) existe pero sin confirmar persistencia real
   vs memoria de proceso
7. source_truth_reconciler.py vs truth_reconciler.py - duplicado sin resolver
8. 13 subcarpetas de templates/skills/plugins/prompts VACIAS - biblioteca
   RAG sin construir todavia
9. AGENT_FLEET_READY_FOR_TEST.json confirma: 18 agentes registrados, CERO
   pruebas de runtime real

PENDIENTE DE DECISION DEL DIRECTOR (no de ejecucion):
10. Formato exacto que debe tener el servidor MCP antes de que Claude
    escriba el codigo (diseno ya aprobado conceptualmente)
11. Cuando activar el sistema de preguntas 3x (UI interface/backend/Input
    Shark) - diseno ya aprobado, codigo pendiente

## SIGUE EN SALIDA 3 DE 3 (instrucciones textuales completas del Director
de esta sesion + reglas de trabajo consolidadas + proximo paso exacto)
