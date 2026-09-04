# FORENSIC CODE AUDIT v1.3.1

Incluye v1.3 + **COPY-FIRST obligatorio** en pasada STRUCTURE/IMPLEMENT y en pre-audit.

## COPY-FIRST (ejecutor = forense)
- ExistingCodeScanner antes de GENERATE
- Match → COPY/ADAPT; GENERATE bloqueado
- Evidence debe registrar source_path, dest_path, sha256
- Regenerar code ya conectado = gap (orphan regenerado / unexpected_changes)

## Resto: ver secciones CORE 14, FC-01..13, 4 pasadas, enforcement, 8 subsistemas, counters (documento v1.3 previo + este añadido).

## Post-implement verification
ExecutorPostVerifyGate → ForensicCodeContract → VerdictAuthority → render_forensic_report

Código: extensions/wordflow/standards/copy_first.py · executor_gates.py · forensic_contract.py · verdict_authority.py
