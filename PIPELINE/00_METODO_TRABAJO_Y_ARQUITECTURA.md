# PIPELINE 00 — MÉTODO DE TRABAJO + ARQUITECTURA

**Fecha:** 2026-08-17  
**Forense code:** PIPELINE/FORENSIC_CODE_AUDIT.md  
**Estándar:** PIPELINE/ADVANCED_ENGINEERING_STANDARD_V3.md  
**Code standards:** extensions/wordflow/standards/

## LEY de cierre de tarea de programación

1. Implementar el DONE literal (sin recortar alcance).
2. Commit real en GitHub + enlaces que abren.
3. **FORENSIC CODE AUDIT** (CORE 14 + FC-01..07).
4. Si gaps bloqueantes > 0 → FIX → RE-AUDIT (bucle ilimitado).
5. PASS solo si gaps=0, broken=0, orphans=0 y evidencia verificable.
6. Gates condicionales solo si el cambio los activa.
7. Nunca marcar DONE por afirmación propia de la IA.

## LOC y calidad
- LOC límite **por archivo** (preferido 300–800); proyecto sin límite.
- Code = profesional avanzado — **NUNCA MVP**.
- Gaps blocking (P0/P1) = 100% antes de avanzar; P2 = deuda con owner/fecha.

## Formato CONTROL DE TRABAJO
1. TOTAL TAREAS V1  
2. TERMINADAS  
3. PENDIENTES  
4. SIGUIENTE  
5. PLAN  
6. MÉTODO  
7. CONFIRMACIÓN: NO sandbox storage · GitHub = verdad  

No repetir enlaces de tareas ya cerradas si no hay cambio nuevo en esos paths.
