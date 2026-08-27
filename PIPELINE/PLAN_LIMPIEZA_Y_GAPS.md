# PLAN LIMPIEZA Y GAPS — para GPT (hacer AL FINAL)

## 0. PARA QUÉ ES LA PLANTILLA (obligatorio leer)

La plantilla del Director NO es un plan.
Es el MOLDE para fabricar cada plan nuevo.

Archivos (NO editar, NO borrar, NO mover):
- PIPELINE/Guia-plan/MOLDE_MAESTRO_UNIVERSAL_v2.md          = receta del plan
- PIPELINE/Guia-plan/MOLDE_MAESTRO_UNIVERSAL_v2_PARCHE_1.md
- PIPELINE/Guia-plan/MOLDE_MAESTRO_UNIVERSAL_v2_PARCHE_1-1.md
- PIPELINE/Guia-plan/DESPLIEGUE-DETERMINISTA-UNIVERSAL-v2.md = cómo entra el lote
- PIPELINE/Guia-plan/PROMPT_MAESTRO_CHAT_A_CHAT_B_VERSION_MADURA.md = Chat A diseña / Chat B ejecuta
- UOOS parte 1 = documentos a generar
- UOOS parte 2 = DSL para ejecutar UOOS1

Cómo se usa:
1. Copiar molde+parches a PIPELINE/planes/PLAN_XX.md
2. Rellenar INPUT BLOCK (PLAN_ID, tarea, destinos, N_DESPLEGAR)
3. Cada salida del plan usa el schema del molde (sheriff, guardian, watchdog, Desplegar N, Refactoria, checkpoint)
4. GPT no inventa otro método. Si no está en el molde, HOLD.

Receta = molde. PLAN_01..05 = instancia. Desplegar N = inbox. Refactoria = mesa. No tocar el vivo primero.

No reescribir: PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md
No fabricar PASS. HTTP 200 ≠ PASS.

## A. GAPS YAIWES (antes de borrar raíces)
G1 G3 G4: Director corre https://github.com/maxbry123-commits/agentes/actions/workflows/verify-gap-indexes.yml
Evidencia = URL del run + PIPELINE/checkpoints/G1_G3_CI_PASS.md creado por Actions.
G2: PARCIAL + residual listado.
G5: BLOCKER sin source p01-p12. No inventar.
G6 G7: no reabrir si evidencia OpenClaw sigue.

## B. LIMPIEZA main (último)
Vivo: Desplegar, PIPELINE (YAIWES + Guia-plan + planes + este plan), Método de trabajo, Refactoria, Yaiwes wordflow, Wordflow Code.
Candidatos a basura (listar → Director aprueba → entonces borrar):
agente-yaiwes, agents, TASK-GAPS, docs sueltos, PIPELINE/00-64 historicos, wordflow/, groups/, memory/ si no son destino canónico.
No borrar extensions/wordflow (hot path) hasta que Wordflow Code sea el cuerpo real.
despliegue/ ≠ Desplegar/.

## C. COPIAS GT1 (cuerpo, no URL)
Grupo-Trabajo-1/METODO-DE-TRABAJO.md → Método de trabajo/
TAREA-GITHUB-FINAL-V1.1.md → Método de trabajo/
