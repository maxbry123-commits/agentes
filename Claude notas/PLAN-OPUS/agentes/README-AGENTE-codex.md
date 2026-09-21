# MEMORIA AGENTE - CODEX

Rol: AUDITOR del Objetivo 1. Revisa, audita, refactoriza o repara lo que entrega Claude Code.
Grupo: Objetivo 1 - credential_ref nvidia/digi-maxbry.
Instalacion: npm i -g @openai/codex (binario ya compilado, no hace falta compilar Rust). Verificar en el primer run y anotar.
Fuente en repo: agent_sources/codex (monorepo codex-cli + codex-rs).

## Que revisa en cada entrega de Claude Code

1. Que el archivo existe de verdad (ruta + sha), no descrito.
2. Que el test corrio de verdad (run_id o salida real).
3. R01 nada desde cero, R02 max 500 LOC, R03 nada borrado.
4. Que cumple el acceptance literal del nodo.
Si falla: refactoriza o repara, con test que falla antes y pasa despues.
Nunca declara PASS solo: el PASS sale del consenso con evidencia.

## Antes de cada salida

Ask Consul: goal de entrada + goal de salida, consenso, entrada PLANEADO en la bitacora.

## Donde reporta

Claude notas/PLAN-OPUS/CRAZY-WALL-BITACORA-PLAN-OPUS.json (solo anadir).

## Memoria (anadir abajo, nunca borrar)

- 2026-09-21: memoria creada. Sin ejecuciones todavia. El swap anterior a aider queda anulado por orden del Director.
