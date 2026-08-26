# NOTAS-2 — Salida 1 hecha + X-Ray notice

**Extensión de:** [NOTAS.md](./NOTAS.md) · [NOTAS-1.md](./NOTAS-1.md)  
No reescribe los anteriores.

## S1 entregado

| Pieza | Enlace |
|---|---|
| Yaiwes wordflow README | https://github.com/maxbry123-commits/agentes/blob/main/Yaiwes%20wordflow/Readme/README.md |
| Yaiwes SOURCE | https://github.com/maxbry123-commits/agentes/blob/main/Yaiwes%20wordflow/SOURCE.md |
| Wordflow Code README | https://github.com/maxbry123-commits/agentes/blob/main/Wordflow%20Code/Readme/README.md |
| Wordflow Code SOURCE | https://github.com/maxbry123-commits/agentes/blob/main/Wordflow%20Code/SOURCE.md |
| Desplegar | https://github.com/maxbry123-commits/agentes/blob/main/Desplegar/README.md |
| Refactoria README | https://github.com/maxbry123-commits/agentes/blob/main/Refactoria/README.md |
| Método parche | https://github.com/maxbry123-commits/agentes/blob/main/M%C3%A9todo%20de%20trabajo/Readme/README.md |

No se movió `extensions/wordflow/` (hot path). No se borró basura (S2/GPT). No se tocó `PIPELINE/PLAN_YAIWES_AGENTE_WORDFLOW.md`. No se creó `Desplegar 1/` vacío.

---

## X-RAY — NOTICE de lo único que debe quedar

### VIVO (autorizado)

1. `Desplegar/`
2. `PIPELINE/` — vivo real hoy: `PLAN_YAIWES_AGENTE_WORDFLOW.md` (el resto de PIPELINE = basura S2, salvo que S3 añada el molde)
3. `Método de trabajo/` + `README_METHOD.md` (base; no borrar en S2 sin mover a la raíz método)
4. `Refactoria/`
5. `Yaiwes wordflow/` + cuerpo `agente-yaiwes/` hasta cutover
6. `Wordflow Code/` + cuerpo `extensions/wordflow/` hasta cutover
7. `notas-trabajo-grock/`

Excepción física GitHub: `.github/workflows/` (Actions solo corre ahí). No borrar en S2 a ciegas.

### CUERPO LEGACY (no basura todavía — cutover S2)

- `agente-yaiwes/` → destino `Yaiwes wordflow/`
- `extensions/wordflow/` → destino `Wordflow Code/` (solo con tests)
- `wordflow/abi.py` → extension point; no borrar
- `code-programming-engine/` → espejo; clasificar en S2 (integrar o basura)
- `despliegue/` ≠ `Desplegar/` ; clasificar en S2
- `Refactoria/G1`…`G7` → misión actual; no borrar en S1

### BASURA / fuera de las 6 raíces (S2 GPT)

`.cursor/` · `AGENTS.md` · guías sueltas en raíz (`GUIA-*`, `METODO_ZIP_*`, `SETUP_TOKEN_MOVIL.md`, `README_ARQUITECTURA.md`, `README_FORENSIC_HANDOFF.md`, `RENAME_NOTE.md`) salvo decisión de moverlas a `Método de trabajo/`  
`TASK-GAPS/` · `agents/` · `control-layer/` · `docs/` · `groups/` · `memory/` · `scripts/` · `tools/`  
`extensions/*` que no sea `wordflow` + lo necesario del kernel  
`PIPELINE/*` excepto el plan vivo (+ molde S3)

Clasificación S2 debe ser archivo a archivo (COPY-FIRST / no borrar canónico por nombre).

---

## Estado

S1 = HECHA (anclas + notice).  
S2 = PENDIENTE (plan GPT).  
S3 = PENDIENTE (molde).  
Fase 2 = ANOTADA_NO_INICIADA.
