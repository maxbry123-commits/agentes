# ADVANCED_ENGINEERING_STANDARD_V3 — YAIWES / WORDFLOW LOOP

Estado: CANONICAL BRIDGE / PRODUCTION
Contrato: `tel.workflow/v3`

Este archivo restaura la ruta exigida por `AGENTS.md`. No crea un estándar paralelo: consolida por referencia las reglas ya aprobadas en las fuentes canónicas.

## Fuentes rectoras
1. `Readme arquitectura Yaiwes/Skills de trabajo/SKILL-ORQUESTACION-YAIWES.md`
2. `➡️📂 Wordflow LOOP Yaiwes/📂 archivos download/📂Archivo download 2/PROMPT_MAESTRO_CHAT_A_CHAT_B_VERSION_MADURA.md`
3. UOOS Parte 1 y Parte 2 cableados en CHECKPOINT.
4. `skills/wordflow-code-deploy-router/SKILL.md` para COPY/MOVE/deploy.

## Calidad mínima
Producción/SaaS; MVP prohibido salvo autorización literal del Director.

## Reglas de implementación
- `REUSE > COPY/MOVE > PATCH PEQUEÑO > ADAPTER > GENERATE DELTA`.
- No rediseñar arquitectura global dentro de una task.
- Chat B/Codex: task ≤2000 LOC estimadas; bloque entregado ≤500 LOC.
- UOOS: archivo con una responsabilidad y objetivo de ≤200 líneas cuando sea viable/aplicable.
- Contratos/schema/typing/versiones exactas cuando aplique.
- Idempotencia, timeout/deadline, errores explícitos, observabilidad, rollback y trazabilidad.
- Secrets solo por referencias protegidas; nunca valores en repo/log/chat.
- Candidate code no se ejecuta dinámicamente para inspección; análisis estático/AST y sandbox antes de ejecución.

## Gates
`INPUT → MissionContract/GoalLock → Sheriff → Validator → Execute → Test → Verifier → Sentinel/Supervisor → Judge/VerdictAuthority → Guardian → EvidencePacket`.

## Tests mínimos
Lo aplicable: unit, schema/contract, integration, regression y E2E. Un nodo no se cierra solo porque compile o exista.

## Deploy
0% LLM en decisiones de despliegue: dry-run/plan, gates de reglas y secretos, commit/push, verificación remota y `evidence.json`.

## Seguridad/conectores
Solo GitHub y Hugging Face están autorizados como conexiones externas del proyecto mientras el Director no autorice otra cosa.

## Cierre
`VERIFIED_CLOSED` exige evidencia reproducible; cualquier ausencia devuelve `GAP` y recovery.