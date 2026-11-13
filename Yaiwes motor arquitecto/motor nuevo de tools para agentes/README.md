# 📂motor tools — Gateway de tools nativos

Convierte los motores de la raíz en tools que un agente ejecuta de forma nativa, con workflow y recuperación.
Stdlib only. Sin credenciales en código. Fail-closed.

## Archivos
- motor_tool_gateway.py — registro de tools, validación, workflow con ledger, descarga reanudable y partes.
- test_tool_gateway.py — 7 tests deterministas sin red.
- tools.schema.json — generado por `--emit-tools`. NO editar a mano.
- README.md — este documento.

## Registrar en un agente
    python motor_tool_gateway.py --emit-tools > tools.schema.json
Cada tool trae `name`, `description`, `input_schema` (JSON Schema). El agente llama por `--call` o por `--stdio`.

## Modos
    --emit-tools
    --call TOOL --args-json '{...}'   |  --call TOOL --args-file args.json
    --workflow plan.json --state ledger.json [--wait]
    --stdio        # líneas {id, tool, args} -> {id, ok, result|error}; {"method":"tools/list"} lista tools

## Tools
motores_extract_zip · motores_download_queue · motores_copy_batches · motores_move_batches ·
motores_copy_root · motores_fetch_resumable · motores_workflow

## Workflow (schema yaiwes.tools.workflow.v1)
steps: {id, tool, args, needs, max_retries}. Orden topológico + id (determinista).
El ledger vive FUERA de la raíz canónica y de la raíz destino.

## Recuperación
DONE no se re-ejecuta · RUNNING tras crash -> PENDING · fallo agotado -> FAILED y dependientes BLOCKED ·
rate-limit -> next_retry_at con cooldown (x4) · plan modificado -> WORKFLOW_PLAN_CHANGED_GAP (ledger nuevo).
Relanzar SIEMPRE con el mismo --state.

## Archivos grandes y límites de GitHub
motores_fetch_resumable: reanudación HTTP Range sobre `.partial`, partes <=95 MiB (default 12),
manifiesto SHA-256 por parte y verificación de reensamblado. Ningún archivo >=100 MiB se publica entero.
Peticiones espaciadas (GITHUB_MIN_INTERVAL_SECONDS, default 1 s) y respeto de Retry-After / X-RateLimit-Reset.

## Variables de entorno
FETCH_TIMEOUT_SECONDS=60 · GITHUB_MIN_INTERVAL_SECONDS=1.0 · TOOL_MAX_RETRIES=3 · STEP_TIMEOUT_SECONDS=3600

## Seguridad
El código no lee ni imprime tokens. La autenticación git la resuelve el entorno (credential helper / SSH).
Los destinos SIEMPRE los entrega el usuario; no hay defaults de destino.
