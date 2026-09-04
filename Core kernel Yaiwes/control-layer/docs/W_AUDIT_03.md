# Auditoría W12–W14 · 10x

## Pasada 1
Event chain, broker deny agent, preview confirm: OK

## Pasada 2 Literalidad
- public_view sin secret
- resolve_for_gateway solo gateway/system
- gate bloquea si requires_confirm sin user_confirmed

## Pasada 3 Gaps
Ninguno bloqueante para W15–W17

## Pasada 4 Riesgo
Secret en memoria de proceso del broker — OK para stub; prod usar secret manager
