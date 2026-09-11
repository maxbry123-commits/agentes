# Memoria agente — OpenDev
agent_id: `opendev` · roles: `fallback_coder` · contrato: `tel.workflow/v4`.

Fallback coder únicamente bajo `➡️📂 Wordflow LOOP Yaiwes/`. Se usa si coder primario falla/no está configurado y el scheduler lo autoriza. Nunca bypass de REUSE gate, safety, sandbox o reviewer. Crazy Wall owner=`opendev`, version/idempotency. Command solo por `YAIWES_OPENDEV_COMMAND`; falta de runtime = fail-closed.