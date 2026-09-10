# BITÁCORA CRAZY WALL — Wordflow LOOP Yaiwes

Contrato: `tel.workflow/v4` · `FAIL_CLOSED_EXECUTION_LOOP`.

## CIERRE 3 PASOS — HISTÓRICO
STEP1/STEP2/STEP3 quedaron verificados. STEP3 histórico: run `34406268016`, job `102649876845`, head `05ce5fc43a599da1ae9e80f485450d52aede07a1`, conclusion `success`; `fleet_count=18`, `council12=12`, fail-closed de runtimes no configurados.

## MIGRACIÓN DE ALCANCE — 2026-09-09
El Director fijó como única ubicación autorizada de escritura:
`maxbry123-commits/agentes/➡️📂 Wordflow LOOP Yaiwes/`.

Se corrigió el desvío anterior:
- fleet adapter/registry/health/ready → `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/agent_fleet/`;
- Ficha → `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/contracts/ficha.agent_fleet.v2.json`;
- evidencia STEP3 → `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/evidence/STEP3_AGENT_FLEET_VERIFY.json`;
- YAML STEP3 → `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/workflows/wordflow-agent-fleet-step3.yml` (referencia archivada, no Action activa);
- índice → `➡️📂 Wordflow LOOP Yaiwes/➡️📂 readme indice agentes.md`;
- router MVP → `➡️📂 Wordflow LOOP Yaiwes/wordflow_loop/wordflow_loop/model_api_router_mvp.py`.

Commit de migración principal: `2a73aba061db7dfba2b37bf6637babb2e73c4b0d`.
El índice escrito en el repo de motores fue eliminado allí por `a17e1572b9df41954597fc8c66b390c47800d081`.
El registry preexistente externo fue restaurado al blob previo `ce40e9afd13fdbea22609fe57807566770dfc1b0`.
Las rutas externas creadas por este bloque se verificaron ausentes/404.

## ESTADO ACTUAL
Fleet=18 · Council12=12 · `READY_FOR_REAL_AGENT_TEST`. Hermes, Muse/Glimmer y Goose siguen `EXTERNAL_NOT_VENDORED`. Ejecución remota real sigue evidence-gated.

## REGLA VIGENTE
No escribir ni modificar para este Wordflow fuera de `➡️📂 Wordflow LOOP Yaiwes/`. Fuentes externas pueden leerse; cualquier escritura externa requiere autorización explícita del Director.
