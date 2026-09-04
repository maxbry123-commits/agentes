# Advanced Engineering Standard V3 + Forensic v1.3 + COPY-FIRST

**Forense:** PIPELINE/FORENSIC_CODE_AUDIT.md  
**Code:** extensions/wordflow/standards/

## LEY COPY-FIRST (obligatoria — ejecutor y forense)

```
COPY/MOVE → LINK/CONNECT → PATCH → ADAPT → GENERATE LAST
```

1. Antes de GENERATE: `ExistingCodeScanner` busca code existente (path/símbolo).
2. Si hay match → **obligatorio** COPY o ADAPT; GENERATE bloqueado.
3. Copia determinista: leer blob literal → escribir dest → registrar SOURCE→DEST+SHA en Evidence.
4. Solo adaptar imports/nombres/wiring; no reescribir lógica si cumple DONE.
5. Mismo gate en **ejecutor** (`ExecutorPreImplementGate`) y en **forense** (anti regenerar lo ya cableado).

## Handoff / Context
Sin Context + método + Handoff verificado → BLOCK (no programar / no auditoría válida).

## Verificación de code
Post-implement → `ExecutorPostVerifyGate` → ForensicCodeContract + VerdictAuthority + report 4 pasadas.
LLM no declara PASS.

## LOC
preferred 300–800/archivo · review>800 · refactor>1000 · critical>1500 · proyecto sin límite
